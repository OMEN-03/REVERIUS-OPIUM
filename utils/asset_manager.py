from __future__ import annotations

import hashlib
import json
import logging
import sys
from collections import OrderedDict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

LOGGER = logging.getLogger(__name__)

SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tif", ".tiff", ".svg"}
SUPPORTED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".ogg", ".m4a", ".aac", ".flac", ".opus"}
SUPPORTED_FONT_EXTENSIONS = {".ttf", ".otf", ".woff", ".woff2", ".eot"}
SUPPORTED_MODEL_EXTENSIONS = {".bin", ".onnx", ".pt", ".pth", ".safetensors", ".gguf", ".ggml"}


@dataclass
class AssetRecord:
    """Metadata describing a single asset inside the pipeline."""

    name: str
    uuid: str
    path: str
    type: str
    category: str
    extension: str
    resolution: Optional[str] = None
    size_bytes: int = 0
    hash: Optional[str] = None
    created_at: str = ""
    modified_at: str = ""
    tags: list[str] = field(default_factory=list)
    theme: str = "default"
    dependencies: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AssetRegistry:
    """Indexes assets under the project asset root and writes registry reports."""

    def __init__(self, root: str | Path | None = None, project_root: str | Path | None = None) -> None:
        self.root = Path(root or AssetManager.assets_root).resolve()
        self.project_root = Path(project_root or self.root.parent).resolve()
        self.records: list[AssetRecord] = []
        self.previous_records: dict[str, AssetRecord] = {}
        self._load_previous_registry()

    def scan(self) -> list[AssetRecord]:
        self.records = []
        if not self.root.exists():
            self.root.mkdir(parents=True, exist_ok=True)
        self._collect_assets(self.root)
        self._write_registry()
        self._write_manifest()
        self._write_statistics()
        self._write_health_report()
        return self.records

    def _collect_assets(self, current: Path) -> None:
        if not current.exists():
            return
        for child in sorted(current.iterdir(), key=lambda item: item.name.lower()):
            if child.name.startswith(".") or child.name in {"__pycache__"}:
                continue
            if child.is_dir():
                self._collect_assets(child)
                continue
            if child.is_file():
                self.records.append(self._build_record(child))

    def _build_record(self, path: Path) -> AssetRecord:
        rel_path = path.relative_to(self.root)
        parts = rel_path.parts
        category = parts[0] if len(parts) > 1 else "root"
        extension = path.suffix.lower()
        record = AssetRecord(
            name=path.name,
            uuid=self._make_uuid(path),
            path=str(rel_path).replace("\\", "/"),
            type=self._classify_type(extension),
            category=category,
            extension=extension,
            resolution=self._read_resolution(path),
            size_bytes=path.stat().st_size,
            hash=self._hash_file(path),
            created_at=datetime.fromtimestamp(path.stat().st_ctime, tz=timezone.utc).isoformat(),
            modified_at=datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(),
            tags=self._infer_tags(path),
            theme="default",
            dependencies=[],
        )
        return record

    def _classify_type(self, extension: str) -> str:
        if extension in SUPPORTED_IMAGE_EXTENSIONS:
            return "image"
        if extension in SUPPORTED_AUDIO_EXTENSIONS:
            return "audio"
        if extension in SUPPORTED_FONT_EXTENSIONS:
            return "font"
        if extension in SUPPORTED_MODEL_EXTENSIONS:
            return "model"
        return "binary"

    def _infer_tags(self, path: Path) -> list[str]:
        tags: list[str] = []
        suffix = path.suffix.lower()
        if suffix in SUPPORTED_IMAGE_EXTENSIONS:
            tags.append("image")
        if suffix in SUPPORTED_AUDIO_EXTENSIONS:
            tags.append("audio")
        if suffix in SUPPORTED_FONT_EXTENSIONS:
            tags.append("font")
        if suffix in SUPPORTED_MODEL_EXTENSIONS:
            tags.append("model")
        if path.name.lower().startswith("logo"):
            tags.append("branding")
        return tags

    def _read_resolution(self, path: Path) -> Optional[str]:
        suffix = path.suffix.lower()
        if suffix not in SUPPORTED_IMAGE_EXTENSIONS:
            return None
        try:
            from PIL import Image
        except Exception:
            return None
        try:
            with Image.open(path) as image:
                return f"{image.width}x{image.height}"
        except Exception:
            return None

    def _hash_file(self, path: Path) -> Optional[str]:
        if not path.exists():
            return None
        digest = hashlib.sha256()
        try:
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
        except OSError:
            return None
        return digest.hexdigest()

    def _make_uuid(self, path: Path) -> str:
        return hashlib.sha256(str(path.resolve()).encode("utf-8")).hexdigest()[:16]

    def _load_previous_registry(self) -> None:
        registry_path = self.project_root / "assets_registry.json"
        if not registry_path.exists():
            return
        try:
            content = json.loads(registry_path.read_text(encoding="utf-8"))
            records = content.get("records", [])
            self.previous_records = {item["path"]: AssetRecord(**item) for item in records}
        except Exception as exc:
            LOGGER.warning("Unable to load previous registry: %s", exc)

    def _write_registry(self) -> None:
        payload = {
            "project": "REVERIUS OPIUM",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "asset_root": str(self.root.relative_to(self.project_root)).replace("\\", "/"),
            "records": [record.to_dict() for record in self.records],
            "changes": self._detect_changes(),
        }
        registry_path = self.project_root / "assets_registry.json"
        registry_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _write_manifest(self) -> None:
        manifest_path = self.project_root / "assets_manifest.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "project": "REVERIUS OPIUM",
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "asset_root": str(self.root.relative_to(self.project_root)).replace("\\", "/"),
                    "assets": [
                        {"path": record.path, "type": record.type, "category": record.category}
                        for record in self.records
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    def _write_statistics(self) -> None:
        by_category: dict[str, int] = {}
        by_type: dict[str, int] = {}
        total_size = 0
        for record in self.records:
            by_category[record.category] = by_category.get(record.category, 0) + 1
            by_type[record.type] = by_type.get(record.type, 0) + 1
            total_size += record.size_bytes
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_assets": len(self.records),
            "total_size_bytes": total_size,
            "by_category": by_category,
            "by_type": by_type,
        }
        (self.project_root / "asset_statistics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _write_health_report(self) -> None:
        validator = AssetValidator(root=self.root, registry=self)
        report = validator.validate()
        (self.project_root / "asset_health.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        (self.project_root / "assets_report.md").write_text(self._build_markdown_report(report), encoding="utf-8")

    def _build_markdown_report(self, report: dict[str, Any]) -> str:
        summary = report.get("summary", {})
        sections = [
            "# Asset Pipeline Report",
            "",
            f"- Total assets: {summary.get('total_assets', 0)}",
            f"- Health score: {summary.get('health_score', 0)}/100",
            f"- Duplicates: {summary.get('duplicate_names', 0)}",
            f"- Broken references: {summary.get('broken_references', 0)}",
            f"- Empty folders: {summary.get('empty_folders', 0)}",
            "",
            "## Findings",
        ]
        sections.extend([f"- {item['type']}: {item['path']} ({item['detail']})" for item in report.get("findings", [])])
        return "\n".join(sections)

    def _detect_changes(self) -> dict[str, list[str]]:
        current_paths = {record.path for record in self.records}
        previous_paths = set(self.previous_records)
        return {
            "new": sorted(current_paths - previous_paths),
            "deleted": sorted(previous_paths - current_paths),
            "renamed": [],
            "duplicates": [],
            "corrupt": [],
        }


class AssetValidator:
    """Validates asset integrity and writes a human-readable report."""

    def __init__(self, root: str | Path | None = None, registry: Optional[AssetRegistry] = None) -> None:
        self.root = Path(root or AssetManager.assets_root).resolve()
        self.registry = registry
        self.project_root = self.root.parent

    def validate(self) -> dict[str, Any]:
        registry = self.registry or AssetRegistry(root=self.root, project_root=self.project_root)
        if not registry.records:
            registry.scan()
        records = registry.records
        findings: list[dict[str, Any]] = []

        for record in records:
            asset_path = self.root / record.path
            if not asset_path.exists():
                findings.append({"type": "missing_file", "path": record.path, "detail": "asset file missing"})
            if record.dependencies:
                for dependency in record.dependencies:
                    dependency_path = self.root / dependency
                    if not dependency_path.exists():
                        findings.append({"type": "broken_reference", "path": record.path, "detail": dependency})

            if record.category in {"images", "image"} and record.extension not in SUPPORTED_IMAGE_EXTENSIONS:
                findings.append({"type": "wrong_extension", "path": record.path, "detail": "unsupported image extension"})
            if record.category in {"audio"} and record.extension not in SUPPORTED_AUDIO_EXTENSIONS:
                findings.append({"type": "wrong_extension", "path": record.path, "detail": "unsupported audio extension"})
            if record.category in {"fonts", "font"} and record.extension not in SUPPORTED_FONT_EXTENSIONS:
                findings.append({"type": "wrong_extension", "path": record.path, "detail": "unsupported font extension"})
            if record.category in {"models", "model"} and record.extension not in SUPPORTED_MODEL_EXTENSIONS:
                findings.append({"type": "wrong_extension", "path": record.path, "detail": "unsupported model extension"})

        for directory in sorted(self.root.rglob("*")):
            if directory.is_dir() and not any(directory.iterdir()):
                findings.append({"type": "empty_folder", "path": str(directory.relative_to(self.root)).replace("\\", "/"), "detail": "folder contains no files"})

        name_groups: dict[str, list[str]] = {}
        for record in records:
            name_groups.setdefault(record.name.lower(), []).append(record.path)
        for name, paths in name_groups.items():
            if len(paths) > 1:
                findings.append({"type": "duplicate_name", "path": ", ".join(paths), "detail": "multiple assets share the same name"})

        for record in records:
            asset_path = self.root / record.path
            if record.type == "image":
                try:
                    from PIL import Image
                except Exception:
                    continue
                try:
                    with Image.open(asset_path) as image:
                        if image.width <= 0 or image.height <= 0:
                            findings.append({"type": "invalid_image_size", "path": record.path, "detail": "invalid image dimensions"})
                except Exception:
                    findings.append({"type": "invalid_image_size", "path": record.path, "detail": "unable to decode image"})
            if record.type == "audio":
                if record.size_bytes <= 0:
                    findings.append({"type": "invalid_audio_format", "path": record.path, "detail": "empty audio payload"})

        summary = {
            "total_assets": len(records),
            "missing_files": sum(1 for item in findings if item["type"] == "missing_file"),
            "broken_references": sum(1 for item in findings if item["type"] == "broken_reference"),
            "wrong_extensions": sum(1 for item in findings if item["type"] == "wrong_extension"),
            "empty_folders": sum(1 for item in findings if item["type"] == "empty_folder"),
            "duplicate_names": sum(1 for item in findings if item["type"] == "duplicate_name"),
            "invalid_image_sizes": sum(1 for item in findings if item["type"] == "invalid_image_size"),
            "invalid_audio_formats": sum(1 for item in findings if item["type"] == "invalid_audio_format"),
        }
        health_score = max(0, 100 - (summary["missing_files"] * 15) - (summary["broken_references"] * 12) - (summary["wrong_extensions"] * 8) - (summary["empty_folders"] * 5) - (summary["duplicate_names"] * 6) - (summary["invalid_image_sizes"] * 7) - (summary["invalid_audio_formats"] * 5))
        summary["health_score"] = health_score
        report = {"summary": summary, "findings": findings}
        self._write_report(report)
        return report

    def _write_report(self, report: dict[str, Any]) -> None:
        validation_path = self.project_root / "validation_report.md"
        validation_path.write_text(self._render_markdown(report), encoding="utf-8")

    def _render_markdown(self, report: dict[str, Any]) -> str:
        summary = report.get("summary", {})
        lines = [
            "# Validation Report",
            "",
            f"- Total assets: {summary.get('total_assets', 0)}",
            f"- Missing files: {summary.get('missing_files', 0)}",
            f"- Broken references: {summary.get('broken_references', 0)}",
            f"- Empty folders: {summary.get('empty_folders', 0)}",
            f"- Duplicate names: {summary.get('duplicate_names', 0)}",
            f"- Health score: {summary.get('health_score', 0)}/100",
            "",
            "## Findings",
        ]
        for item in report.get("findings", []):
            lines.append(f"- [{item['type']}] {item['path']}: {item['detail']}")
        return "\n".join(lines)


class AssetCache:
    """A lightweight LRU cache for asset metadata and payloads."""

    def __init__(self, max_entries: int = 128) -> None:
        self.max_entries = max_entries
        self._store: OrderedDict[str, Any] = OrderedDict()

    def get(self, key: str) -> Any:
        if key not in self._store:
            return None
        value = self._store.pop(key)
        self._store[key] = value
        return value

    def put(self, key: str, value: Any) -> None:
        if key in self._store:
            self._store.pop(key)
        self._store[key] = value
        while len(self._store) > self.max_entries:
            self._store.popitem(last=False)

    def clear(self) -> None:
        self._store.clear()

    def stats(self) -> dict[str, Any]:
        return {"entries": len(self._store), "max_entries": self.max_entries}


class AssetThemeEngine:
    """Simple theme manager supporting built-in and custom themes."""

    built_in_themes = {
        "Obsidian Gold": {"icons": "gold", "wallpapers": "obsidian", "sounds": "amber", "fonts": "serif", "animations": "glow", "colors": ["#d4af37", "#111111"]},
        "Emerald Matrix": {"icons": "green", "wallpapers": "matrix", "sounds": "neon", "fonts": "mono", "animations": "grid", "colors": ["#00ff88", "#07251d"]},
        "Royal Crimson": {"icons": "crimson", "wallpapers": "royal", "sounds": "velvet", "fonts": "ornate", "animations": "pulse", "colors": ["#dc143c", "#1b0408"]},
        "Frozen Steel": {"icons": "steel", "wallpapers": "ice", "sounds": "glacier", "fonts": "sans", "animations": "freeze", "colors": ["#8ecae6", "#0f172a"]},
        "Midnight Blue": {"icons": "blue", "wallpapers": "night", "sounds": "aurora", "fonts": "sans", "animations": "drift", "colors": ["#3b82f6", "#020617"]},
    }

    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root or AssetManager.assets_root / "themes").resolve()

    def list_themes(self) -> list[str]:
        themes = list(self.built_in_themes)
        if self.root.exists():
            for theme_dir in sorted(self.root.iterdir()):
                if theme_dir.is_dir() and theme_dir.name not in themes:
                    themes.append(theme_dir.name)
        return themes

    def load_theme(self, theme_name: str) -> dict[str, Any]:
        if theme_name in self.built_in_themes:
            return self.built_in_themes[theme_name]
        theme_dir = self.root / theme_name
        if theme_dir.exists() and (theme_dir / "theme.json").exists():
            return json.loads((theme_dir / "theme.json").read_text(encoding="utf-8"))
        return {"name": theme_name, "icons": "default", "wallpapers": "default", "sounds": "default", "fonts": "default", "animations": "default", "colors": ["#ffffff", "#000000"]}


class AssetManager:
    """Centralized asset path resolver and pipeline entry point for REVERIUS OPIUM."""

    project_root = Path(__file__).resolve().parent.parent
    assets_root = project_root / "assets"
    cache = AssetCache()
    _theme_engine: Optional[AssetThemeEngine] = None

    @classmethod
    def resolve(cls, relative_path: str | Path, category: str = "") -> Path:
        base = cls.assets_root
        if category:
            base = base / category
        path = Path(relative_path)
        if path.is_absolute():
            return path
        return (base / path).resolve()

    @classmethod
    def image(cls, name: str | Path) -> Path:
        return cls.resolve(name, "images")

    @classmethod
    def icon(cls, name: str | Path) -> Path:
        return cls.resolve(name, "images/icons")

    @classmethod
    def wallpaper(cls, name: str | Path) -> Path:
        return cls.resolve(name, "images/wallpapers")

    @classmethod
    def logo(cls, name: str | Path) -> Path:
        return cls.resolve(name, "images/logos")

    @classmethod
    def sound(cls, name: str | Path) -> Path:
        return cls.resolve(name, "audio")

    @classmethod
    def font(cls, name: str | Path) -> Path:
        return cls.resolve(name, "fonts")

    @classmethod
    def model(cls, name: str | Path) -> Path:
        return cls.resolve(name, "models")

    @classmethod
    def prompt(cls, name: str | Path) -> Path:
        return cls.resolve(name, "prompts")

    @classmethod
    def config(cls, name: str | Path) -> Path:
        return cls.resolve(name, "configs")

    @classmethod
    def data(cls, name: str | Path) -> Path:
        return cls.resolve(name, "data")

    @classmethod
    def doc(cls, name: str | Path) -> Path:
        return cls.resolve(name, "docs")

    @classmethod
    def template(cls, name: str | Path) -> Path:
        return cls.resolve(name, "templates")

    @classmethod
    def theme(cls, name: str | Path) -> Path:
        return cls.resolve(name, "themes")

    @classmethod
    def ensure_exists(cls, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def personality_image(cls, personality: str) -> Optional[Path]:
        if not personality:
            return None
        key = (personality or "").strip().lower().replace(" ", "_").replace("-", "_")
        candidates = [
            cls.assets_root / "images" / f"{key}.png",
            cls.assets_root / "images" / "personalities" / f"{key}.png",
            cls.assets_root / "images" / "avatars" / f"{key}.png",
            cls.assets_root / "images" / "logos" / f"{key}.png",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    @classmethod
    def initialize_pipeline(cls) -> dict[str, Any]:
        registry = AssetRegistry(root=cls.assets_root, project_root=cls.project_root)
        registry.scan()
        validator = AssetValidator(root=cls.assets_root, registry=registry)
        report = validator.validate()
        cls.cache.put("last_registry", registry.records)
        cls.cache.put("last_validation", report)
        return report

    @classmethod
    def scan_assets(cls) -> list[AssetRecord]:
        registry = AssetRegistry(root=cls.assets_root, project_root=cls.project_root)
        return registry.scan()

    @classmethod
    def validate_assets(cls) -> dict[str, Any]:
        validator = AssetValidator(root=cls.assets_root)
        return validator.validate()

    @classmethod
    def optimize_assets(cls) -> dict[str, Any]:
        registry = AssetRegistry(root=cls.assets_root, project_root=cls.project_root)
        records = registry.scan()
        preview_dir = cls.assets_root / ".cache" / "previews"
        preview_dir.mkdir(parents=True, exist_ok=True)
        for record in records:
            asset_path = cls.assets_root / record.path
            if record.type == "image" and asset_path.exists():
                try:
                    from PIL import Image
                except Exception:
                    continue
                with Image.open(asset_path) as image:
                    if image.mode in {"RGBA", "LA"}:
                        image.save(preview_dir / f"{asset_path.stem}.webp", "WEBP")
        return {"preview_dir": str(preview_dir), "asset_count": len(records)}

    @classmethod
    def clean_assets(cls) -> list[str]:
        removed: list[str] = []
        for directory in sorted(cls.assets_root.rglob("*")):
            if directory.is_dir() and not any(directory.iterdir()):
                directory.rmdir()
                removed.append(str(directory.relative_to(cls.project_root)).replace("\\", "/"))
        return removed

    @classmethod
    def duplicate_assets(cls) -> list[dict[str, Any]]:
        registry = AssetRegistry(root=cls.assets_root, project_root=cls.project_root)
        records = registry.scan()
        grouped: dict[str, list[AssetRecord]] = {}
        for record in records:
            grouped.setdefault(record.name.lower(), []).append(record)
        duplicates = []
        for name, items in grouped.items():
            if len(items) > 1:
                duplicates.append({"name": name, "paths": [item.path for item in items]})
        return duplicates

    @classmethod
    def theme_list(cls) -> list[str]:
        return cls.theme_engine.list_themes()

    @classmethod
    def theme_load(cls, theme_name: str) -> dict[str, Any]:
        return cls.theme_engine.load_theme(theme_name)

    @classmethod
    def cache_stats(cls) -> dict[str, Any]:
        return cls.cache.stats()

    @classmethod
    def run_cli(cls, argv: Optional[list[str]] = None) -> int:
        argv = list(argv or sys.argv[1:])
        if not argv:
            print("Usage: asset <command> [args]")
            return 0

        command = argv[0]
        if command == "scan":
            records = cls.scan_assets()
            print(f"Scanned {len(records)} assets")
            return 0
        if command == "validate":
            report = cls.validate_assets()
            print(json.dumps(report["summary"], indent=2))
            return 0
        if command == "stats":
            registry = AssetRegistry(root=cls.assets_root, project_root=cls.project_root)
            print(json.dumps({"asset_count": len(registry.scan())}, indent=2))
            return 0
        if command == "optimize":
            result = cls.optimize_assets()
            print(json.dumps(result, indent=2))
            return 0
        if command == "clean":
            removed = cls.clean_assets()
            print(json.dumps(removed, indent=2))
            return 0
        if command == "duplicate":
            print(json.dumps(cls.duplicate_assets(), indent=2))
            return 0
        if command == "info" and len(argv) > 1:
            asset_path = cls.resolve(argv[1])
            print(str(asset_path))
            return 0
        if command == "cache":
            print(json.dumps(cls.cache_stats(), indent=2))
            return 0
        if command == "theme" and len(argv) > 1 and argv[1] == "list":
            print(json.dumps(cls.theme_list(), indent=2))
            return 0
        if command == "theme" and len(argv) > 1 and argv[1] == "load":
            theme_name = argv[2] if len(argv) > 2 else "Midnight Blue"
            print(json.dumps(cls.theme_load(theme_name), indent=2))
            return 0
        print("Unknown command")
        return 1


if __name__ == "__main__":
    raise SystemExit(AssetManager.run_cli())