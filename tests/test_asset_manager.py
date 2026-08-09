import json
from pathlib import Path

from utils.asset_manager import AssetCache, AssetManager, AssetRegistry, AssetValidator


def test_asset_manager_resolves_project_asset_paths():
    image_path = AssetManager.image("logo.png")

    assert image_path.name == "logo.png"
    assert image_path.parent.name == "images"
    assert image_path.parent.exists()
    assert image_path.is_absolute()


def test_asset_registry_scans_and_writes_registry(tmp_path):
    asset_dir = tmp_path / "assets"
    (asset_dir / "images").mkdir(parents=True)
    (asset_dir / "images" / "logo.png").write_bytes(b"fake-image")
    (asset_dir / "audio").mkdir()
    (asset_dir / "audio" / "intro.wav").write_bytes(b"fake-audio")

    registry = AssetRegistry(root=asset_dir)
    records = registry.scan()

    assert len(records) == 2
    assert any(record.name == "logo.png" for record in records)
    assert (tmp_path / "assets_registry.json").exists()


def test_validator_reports_findings(tmp_path):
    asset_dir = tmp_path / "assets"
    (asset_dir / "images").mkdir(parents=True)
    (asset_dir / "images" / "broken.png").write_bytes(b"not-an-image")
    (asset_dir / "audio").mkdir()
    (asset_dir / "audio" / "bad.wav").write_bytes(b"")
    (asset_dir / "empty_folder").mkdir()

    registry = AssetRegistry(root=asset_dir)
    registry.scan()
    validator = AssetValidator(root=asset_dir)
    report = validator.validate()

    assert report["summary"]["total_assets"] == 2
    assert report["summary"]["empty_folders"] == 1
    assert any(item["type"] == "empty_folder" for item in report["findings"])


def test_asset_cache_lru_behavior():
    cache = AssetCache(max_entries=2)
    cache.put("one", 1)
    cache.put("two", 2)
    cache.get("one")
    cache.put("three", 3)

    assert cache.get("one") == 1
    assert cache.get("two") is None
    assert cache.get("three") == 3
