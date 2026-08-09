from __future__ import annotations

import math
import os
import socket
import threading
import time
from pathlib import Path
from typing import Any

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None

import customtkinter as ctk
import psutil
import tkinter as tk

from ui.hud_theme import THEME, build_dashboard_summary, build_operational_snapshot, state_to_status


def _get_module() -> Any:
    import core.reverius_opium as reverius_module

    return reverius_module


def _schedule(module: Any, delay_ms: int, callback: Any) -> None:
    try:
        module.safe_after(delay_ms, callback)
    except Exception:
        try:
            module.app.after(delay_ms, callback)
        except Exception:
            pass


def _ui_print(module: Any, target: str, text: str, color: str) -> None:
    if target == "terminal":
        try:
            terminal_widget = getattr(module, "terminal", None)
            if terminal_widget is None:
                return
            terminal_widget.configure(state="normal")
            terminal_widget.insert("end", text + "\n")
            terminal_widget.configure(state="disabled")
            terminal_widget.see("end")
        except Exception:
            pass
    else:
        try:
            logs_widget = getattr(module, "activity_feed", None)
            if logs_widget is not None:
                logs_widget.configure(state="normal")
                logs_widget.insert("end", text + "\n")
                logs_widget.configure(state="disabled")
                logs_widget.see("end")
        except Exception:
            pass


def _sync_nav_state(module: Any, active_action: str | None) -> None:
    buttons = getattr(module, "nav_buttons", {}) or {}
    for action, button in buttons.items():
        if button is None:
            continue
        is_active = action == active_action
        button.configure(
            fg_color=THEME.ACCENT if is_active else THEME.SURFACE,
            hover_color=THEME.ACCENT_SOFT if is_active else THEME.BORDER,
            border_color=THEME.ACCENT if is_active else THEME.BORDER,
            text_color=THEME.BACKGROUND if is_active else THEME.TEXT,
        )


def _draw_core_center_image(module: Any, canvas: tk.Canvas, center_x: float, center_y: float) -> None:
    original = getattr(module, "core_center_image_original", None)
    if original is None or Image is None or ImageTk is None:
        return

    try:
        angle = (time.time() * 22) % 360
        rotated = original.rotate(angle, resample=Image.BICUBIC, expand=True)
        size = getattr(module, "core_center_image_size", 120)

        background = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        offset_x = (size - rotated.width) // 2
        offset_y = (size - rotated.height) // 2
        background.paste(rotated, (offset_x, offset_y), rotated)

        module.core_center_image_tk = ImageTk.PhotoImage(background)
        canvas.delete("core_image")
        canvas.create_image(center_x, center_y, image=module.core_center_image_tk, tags="core_image")
    except Exception:
        pass


def load_core_center_image(image_path: str | Path | None, size: int = 120) -> bool:
    """Load a center image for the HUD core and enable rotation."""
    module = _get_module()
    if image_path is None:
        module.core_center_image_original = None
        module.core_center_image_tk = None
        module.core_center_image_size = size
        module.core_center_image_path = None
        _schedule(module, 0, lambda: _draw_core(module))
        return True

    if Image is None or ImageTk is None:
        return False

    path = Path(image_path)
    if not path.exists():
        return False

    try:
        with Image.open(path) as img:
            img = img.convert("RGBA")
            scale = min(size / img.width, size / img.height, 1.0)
            target = (max(1, int(img.width * scale)), max(1, int(img.height * scale)))
            img = img.resize(target, Image.LANCZOS)
            module.core_center_image_original = img.copy()
            module.core_center_image_size = size
            module.core_center_image_path = str(path)
            module.core_center_image_tk = None
        _schedule(module, 0, lambda: _draw_core(module))
        return True
    except Exception:
        return False


def set_hud_state(state: str | None, detail: str | None = None) -> None:
    module = _get_module()
    normalized = state_to_status(state)
    module.hud_ai_state = normalized
    if detail:
        module.hud_current_task = detail
    _schedule(module, 0, lambda: _apply_hud_state(module, normalized, detail))


def _apply_hud_state(module: Any, state: str, detail: str | None) -> None:
    try:
        status_label = getattr(module, "status_label", None)
        if status_label is not None:
            status_label.configure(text=f"AI STATUS {state}")
        execution_label = getattr(module, "execution_status_label", None)
        if execution_label is not None:
            execution_label.configure(text=f"EXECUTION {state}")
        core_canvas = getattr(module, "core_canvas", None)
        if core_canvas is not None:
            core_canvas.itemconfig("state_text", text=state)
        task_label = getattr(module, "current_task_label", None)
        if task_label is not None and detail:
            task_label.configure(text=f"CURRENT TASK {detail[:56]}")
        dashboard_summary = getattr(module, "dashboard_summary", None)
        if dashboard_summary is not None:
            summary = build_dashboard_summary(module)
            dashboard_summary.configure(
                text=(
                    f"{summary['personality']} • {summary['state']}\n"
                    f"{summary['mission']}\n"
                    f"{summary['operator_context']}"
                )
            )
    except Exception:
        pass


def _get_backend_info(module: Any) -> dict[str, Any]:
    try:
        import modules.ai_backend as ai_module
        if getattr(ai_module, "get_backend_info", None):
            return ai_module.get_backend_info()
    except Exception:
        pass
    return {}


def _get_backend_status(module: Any) -> str:
    info = _get_backend_info(module)
    if info:
        name = info.get("name", "Offline")
        status = info.get("status", "Offline")
        if status and status.upper() != "ONLINE":
            return f"{name.capitalize()} ({status})"
        return name.capitalize()

    try:
        if getattr(module, "jarvis_available", False):
            return "OpenJarvis"
        if getattr(module, "get_openai_client", None):
            client = module.get_openai_client()
            if client is not None:
                return "OpenAI"
    except Exception:
        pass
    return "Offline"


def refresh_hud_metrics() -> None:
    module = _get_module()
    if not getattr(module, "running", True):
        return
    try:
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory().percent
        gpu = module.get_gpu_usage() if hasattr(module, "get_gpu_usage") else None
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname) if hostname else "127.0.0.1"
        backend_info = _get_backend_info(module)
        backend = backend_info.get("name") or _get_backend_status(module)
        backend_status = backend_info.get("status", "Offline")
        memory_count = len(getattr(module, "memory_entries", {}) or {})
        plugin_count = len(getattr(module, "loaded_plugins", []) or [])
        task = getattr(module, "hud_current_task", "Awaiting command")

        labels = getattr(module, "metric_labels", None)
        if labels:
            labels["cpu"].configure(text=f"CPU {cpu:.0f}%")
            labels["ram"].configure(text=f"RAM {ram:.0f}%")
            labels["gpu"].configure(text=f"GPU {gpu.get('gpu', 0)}%" if gpu else "GPU N/A")
            labels["network"].configure(text=f"NETWORK {ip}")
            labels["backend"].configure(text=f"BACKEND {backend}")
            labels["memory"].configure(text=f"MEMORY {memory_count}")
            labels["plugins"].configure(text=f"PLUGINS {plugin_count}")
            labels["task"].configure(text=f"ACTIVE TASK {task[:40]}")

        title = getattr(module, "top_title_label", None)
        if title is not None:
            title.configure(text="REVERIUS OPIUM")

        status_text = getattr(module, "top_status_label", None)
        if status_text is not None:
            status_text.configure(text=f"SYSTEM {module.current_personality.upper()} • {module.hud_ai_state}")

        time_label = getattr(module, "top_time_label", None)
        if time_label is not None:
            time_label.configure(text=time.strftime("%H:%M:%S"))

        right_status_labels = getattr(module, "right_status_labels", None)
        if right_status_labels:
            right_status_labels["ai"].configure(text=f"AI STATUS  {module.hud_ai_state}")
            right_status_labels["backend"].configure(text=f"BACKEND  {backend}")
            right_status_labels["memory"].configure(text=f"MEMORY  {memory_count} entries")
            right_status_labels["task"].configure(text=f"ACTIVE TASK  {task[:36]}")
            right_status_labels["system"].configure(text=f"SYSTEM  {cpu:.0f}% CPU • {ram:.0f}% RAM")
            right_status_labels["tools"].configure(text=f"TOOLS  {plugin_count} plugins")

        snapshot = build_operational_snapshot(module)
        if getattr(module, "core_status_label", None) is not None:
            module.core_status_label.configure(text=f"STATE {snapshot['state']} • {snapshot['personality']}")
        if getattr(module, "core_context_label", None) is not None:
            module.core_context_label.configure(text=" • ".join(snapshot["context_tags"]))
        if getattr(module, "memory_summary_label", None) is not None:
            module.memory_summary_label.configure(text=f"{snapshot['memory_entries']} entries • {snapshot['plugin_count']} active plugins")
        if getattr(module, "backend_status_label", None) is not None:
            module.backend_status_label.configure(text=f"BACKEND {backend} ({backend_status})")
        if getattr(module, "network_status_label", None) is not None:
            module.network_status_label.configure(text=f"NETWORK {ip}")
        if getattr(module, "task_status_label", None) is not None:
            module.task_status_label.configure(text=f"TASK {task[:44]}")
        if getattr(module, "pipeline_labels", None):
            for item, label in module.pipeline_labels.items():
                stage = next((entry for entry in snapshot["pipeline"] if entry["label"] == item), None)
                if stage is None:
                    continue
                state = stage["state"]
                color = THEME.ACCENT if state == "ACTIVE" else THEME.SUCCESS if state == "COMPLETE" else THEME.MUTED
                label.configure(text=f"{item} • {state}", text_color=color)

        telemetry = getattr(module, "telemetry_box", None)
        if telemetry is not None:
            telemetry.configure(state="normal")
            telemetry.delete("1.0", "end")
            telemetry.insert(
                "end",
                f"CPU {cpu:.0f}%\n"
                f"RAM {ram:.0f}%\n"
                f"GPU {gpu.get('gpu', 0)}%\n"
                f"BACKEND {backend}\n"
                f"STATUS {backend_status}\n"
                f"REQUESTS {backend_info.get('request_count', 0)}\n"
                f"LATENCY {backend_info.get('latency_ms', 0)}ms\n"
                f"NETWORK {ip}\n"
            )
            if backend_info.get("error"):
                telemetry.insert("end", f"ERROR {backend_info['error']}\n")
            telemetry.configure(state="disabled")
        _schedule(module, 1000, refresh_hud_metrics)
    except Exception:
        _schedule(module, 1000, refresh_hud_metrics)


def _draw_core(module: Any) -> None:
    if not getattr(module, "running", True):
        return
    canvas = getattr(module, "core_canvas", None)
    if canvas is None:
        return
    try:
        canvas.delete("all")
        width = 360
        height = 360
        center_x = width / 2
        center_y = height / 2
        radius = 120
        state = getattr(module, "hud_ai_state", "IDLE")
        color = THEME.STATUS_COLORS.get(state, THEME.ACCENT)
        pulse = 0.5 + 0.5 * math.sin(time.time() * 2.2)
        canvas.create_oval(12, 12, width - 12, height - 12, outline=THEME.BORDER, width=2, tags="core")
        canvas.create_oval(28, 28, width - 28, height - 28, outline=color, width=2, tags="core")
        canvas.create_oval(44, 44, width - 44, height - 44, outline=THEME.ACCENT_SOFT, width=1, tags="core")
        for ring in (70, 92, 112):
            canvas.create_oval(center_x - ring, center_y - ring, center_x + ring, center_y + ring, outline=THEME.ACCENT_SOFT, width=1, tags="core")
        for idx in range(8):
            angle = time.time() * 0.8 + idx * 0.785
            x1 = center_x + math.cos(angle) * (radius - 14)
            y1 = center_y + math.sin(angle) * (radius - 14)
            x2 = center_x + math.cos(angle + 0.35) * (radius + 12)
            y2 = center_y + math.sin(angle + 0.35) * (radius + 12)
            canvas.create_line(x1, y1, x2, y2, fill=color, width=2, tags="core")
        for idx in range(12):
            angle = (time.time() * 0.35) + idx * (2 * math.pi / 12)
            x = center_x + math.cos(angle) * (radius - 26)
            y = center_y + math.sin(angle) * (radius - 26)
            canvas.create_oval(x - 2, y - 2, x + 2, y + 2, fill=THEME.ACCENT, outline="", tags="core")
        _draw_core_center_image(module, canvas, center_x, center_y)
        canvas.create_oval(center_x - 42, center_y - 42, center_x + 42, center_y + 42, outline=color, width=3, tags="core")
        canvas.create_oval(center_x - 26, center_y - 26, center_x + 26, center_y + 26, fill=THEME.SURFACE, outline="", tags="core")
        canvas.create_oval(center_x - 8, center_y - 8, center_x + 8, center_y + 8, fill=color, outline="", tags="core")
        canvas.create_oval(center_x - 6 - pulse * 2, center_y - 6 - pulse * 2, center_x + 6 + pulse * 2, center_y + 6 + pulse * 2, outline=color, width=1, tags="core")
        canvas.create_text(center_x, center_y - 10, text="REVERIUS", fill=THEME.TEXT, font=("Segoe UI", 18, "bold"), tags="state_text")
        canvas.create_text(center_x, center_y + 16, text=state, fill=color, font=("Segoe UI", 12, "bold"), tags="state_text")
        canvas.tag_raise("state_text")
    except Exception:
        pass
    _schedule(module, 45, lambda: _draw_core(module))


def _handle_nav(module: Any, action: str) -> None:
    if action == "home":
        set_hud_state("IDLE", "Home ready")
        try:
            module.terminal_print("[HUD] Home view refreshed", module.CYAN)
        except Exception:
            pass
    elif action == "ai":
        set_hud_state("THINKING", "Assessing system")
        threading.Thread(target=lambda: module.assistant_chat("report your current system status"), daemon=True).start()
    elif action == "memory":
        set_hud_state("PROCESSING", "Reviewing memory")
        try:
            module.show_memory()
        except Exception:
            pass
    elif action == "tools":
        set_hud_state("EXECUTING", "Launching tools")
        try:
            module.process_command("open calculator")
        except Exception:
            pass
    elif action == "plugins":
        set_hud_state("PROCESSING", "Reloading plugins")
        try:
            module.load_plugins()
            module.update_plugins_panel()
        except Exception:
            pass
    elif action == "vision":
        set_hud_state("EXECUTING", "Opening vision tools")
        try:
            module.process_command("open paint")
        except Exception:
            pass
    elif action == "voice":
        set_hud_state("LISTENING", "Voice ready")
        try:
            module.toggle_voice_mode()
        except Exception:
            pass
    elif action == "automation":
        set_hud_state("EXECUTING", "Starting automation")
        try:
            module.process_command("open chrome")
        except Exception:
            pass
    elif action == "system":
        set_hud_state("PROCESSING", "Checking telemetry")
        try:
            module.process_command("show update status")
        except Exception:
            pass
    elif action == "settings":
        set_hud_state("PROCESSING", "Opening settings")
        try:
            module.process_command("show personality")
        except Exception:
            pass


def _submit_command(module: Any) -> None:
    cmd = module.command_entry.get().strip()
    module.command_entry.delete(0, "end")
    if not cmd:
        return
    module.hud_current_task = cmd
    set_hud_state("LISTENING", cmd)
    def worker() -> None:
        set_hud_state("PROCESSING", cmd)
        try:
            module.process_command(cmd)
        except Exception as exc:
            set_hud_state("ERROR", str(exc))
            try:
                module.terminal_print(f"[HUD] Command error: {exc}", module.RED)
            except Exception:
                pass
        else:
            set_hud_state("RESPONDING", cmd)
    threading.Thread(target=worker, daemon=True).start()


def build_hud_interface() -> None:
    module = _get_module()
    try:
        for name in ["main_frame", "logo_frame", "left_panel", "center_panel", "right_panel", "bottom_panel"]:
            widget = getattr(module, name, None)
            if widget is not None:
                try:
                    widget.destroy()
                except Exception:
                    pass
    except Exception:
        pass

    module.main_frame = ctk.CTkFrame(module.app, fg_color="transparent")
    module.main_frame.pack(fill="both", expand=True, padx=12, pady=12)

    module.top_bar = ctk.CTkFrame(
        module.main_frame,
        fg_color=THEME.PANEL,
        border_width=2,
        border_color=THEME.BORDER,
        corner_radius=24,
    )
    module.top_bar.pack(fill="x", pady=(0, 10))

    title_frame = ctk.CTkFrame(module.top_bar, fg_color="transparent")
    title_frame.pack(side="left", fill="x", expand=True, padx=16, pady=12)

    ctk.CTkLabel(title_frame, text="REVERIUS OPIUM", text_color=THEME.ACCENT, font=("Segoe UI", 24, "bold")).pack(anchor="w")
    module.top_title_label = ctk.CTkLabel(title_frame, text="AI OPERATING SYSTEM", text_color=THEME.TEXT, font=("Segoe UI", 12))
    module.top_title_label.pack(anchor="w", pady=(2, 0))

    status_frame = ctk.CTkFrame(module.top_bar, fg_color="transparent")
    status_frame.pack(side="right", padx=16, pady=12)

    module.top_status_label = ctk.CTkLabel(status_frame, text="SYSTEM ONLINE", text_color=THEME.TEXT, font=("Segoe UI", 12))
    module.top_status_label.pack(anchor="e")
    module.top_time_label = ctk.CTkLabel(status_frame, text="00:00:00", text_color=THEME.ACCENT, font=("Segoe UI", 12, "bold"))
    module.top_time_label.pack(anchor="e", pady=(4, 0))

    module.top_search_entry = ctk.CTkEntry(status_frame, width=160, border_width=1, border_color=THEME.BORDER, fg_color=THEME.SURFACE, text_color=THEME.TEXT)
    module.top_search_entry.pack(anchor="e", pady=(6, 0))
    module.top_search_entry.insert(0, "search systems")

    content_frame = ctk.CTkFrame(module.main_frame, fg_color="transparent")
    content_frame.pack(fill="both", expand=True)

    module.left_panel = ctk.CTkFrame(
        content_frame,
        fg_color=THEME.PANEL,
        width=240,
        border_width=2,
        border_color=THEME.BORDER,
        corner_radius=24,
    )
    module.left_panel.pack(side="left", fill="y", padx=(0, 10))
    module.left_panel.pack_propagate(False)

    ctk.CTkLabel(module.left_panel, text="OPERATIONS", text_color=THEME.ACCENT, font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=16, pady=(16, 8))
    ctk.CTkLabel(module.left_panel, text="command modules", text_color=THEME.MUTED, font=("Segoe UI", 11)).pack(anchor="w", padx=16, pady=(0, 12))

    module.cpu_label = ctk.CTkLabel(module.left_panel, text="CPU 0%", text_color=THEME.TEXT, font=("Segoe UI", 12))
    module.cpu_label.pack(anchor="w", padx=16, pady=(2, 2))
    module.ram_label = ctk.CTkLabel(module.left_panel, text="RAM 0%", text_color=THEME.TEXT, font=("Segoe UI", 12))
    module.ram_label.pack(anchor="w", padx=16, pady=2)
    module.gpu_label = ctk.CTkLabel(module.left_panel, text="GPU 0%", text_color=THEME.TEXT, font=("Segoe UI", 12))
    module.gpu_label.pack(anchor="w", padx=16, pady=2)
    module.network_label = ctk.CTkLabel(module.left_panel, text="NETWORK 0.0.0.0", text_color=THEME.TEXT, font=("Segoe UI", 12))
    module.network_label.pack(anchor="w", padx=16, pady=2)
    module.ip_label = ctk.CTkLabel(module.left_panel, text="IP 127.0.0.1", text_color=THEME.TEXT, font=("Segoe UI", 12))
    module.ip_label.pack(anchor="w", padx=16, pady=(2, 14))

    nav_items = [
        ("DASHBOARD", "home"),
        ("CHAT", "ai"),
        ("MEMORY", "memory"),
        ("TASKS", "tools"),
        ("PLUGINS", "plugins"),
        ("AUTOMATION", "automation"),
        ("VISION", "vision"),
        ("VOICE", "voice"),
        ("CODE", "system"),
        ("SYSTEM", "system"),
        ("SETTINGS", "settings"),
    ]
    module.nav_buttons = {}
    for label, action in nav_items:
        btn = ctk.CTkButton(
            module.left_panel,
            text=label,
            fg_color=THEME.SURFACE,
            hover_color=THEME.BORDER,
            border_width=1,
            border_color=THEME.BORDER,
            text_color=THEME.TEXT,
            corner_radius=12,
            height=34,
            command=lambda action=action: _handle_nav(module, action),
        )
        btn.pack(fill="x", padx=14, pady=4)
        module.nav_buttons[action] = btn

    core_state_frame = ctk.CTkFrame(module.left_panel, fg_color=THEME.SURFACE, border_width=1, border_color=THEME.BORDER, corner_radius=16)
    core_state_frame.pack(fill="x", padx=14, pady=(10, 16))
    ctk.CTkLabel(core_state_frame, text="REVERIUS CORE", text_color=THEME.ACCENT, font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=12, pady=(10, 2))
    module.core_status_label = ctk.CTkLabel(core_state_frame, text="STATE IDLE", text_color=THEME.TEXT, font=("Segoe UI", 11))
    module.core_status_label.pack(anchor="w", padx=12)
    module.memory_summary_label = ctk.CTkLabel(core_state_frame, text="0 entries • 0 plugins", text_color=THEME.MUTED, font=("Segoe UI", 10))
    module.memory_summary_label.pack(anchor="w", padx=12, pady=(2, 10))

    module.center_panel = ctk.CTkFrame(
        content_frame,
        fg_color=THEME.PANEL,
        border_width=2,
        border_color=THEME.BORDER,
        corner_radius=26,
    )
    module.center_panel.pack(side="left", fill="both", expand=True)

    header_chip = ctk.CTkFrame(module.center_panel, fg_color=THEME.SURFACE, border_width=1, border_color=THEME.BORDER, corner_radius=16)
    header_chip.pack(fill="x", padx=18, pady=(18, 10))
    ctk.CTkLabel(header_chip, text="CENTRAL REVERIUS CORE", text_color=THEME.ACCENT, font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=14, pady=(10, 0))
    ctk.CTkLabel(header_chip, text="operational overview and live core state", text_color=THEME.MUTED, font=("Segoe UI", 11)).pack(anchor="w", padx=14, pady=(0, 10))

    core_content_frame = ctk.CTkFrame(module.center_panel, fg_color="transparent")
    core_content_frame.pack(fill="x", padx=18)

    module.core_canvas = tk.Canvas(core_content_frame, width=360, height=360, bg=THEME.BACKGROUND, highlightthickness=0)
    module.core_canvas.pack(side="left", pady=(4, 8))

    info_frame = ctk.CTkFrame(core_content_frame, fg_color="transparent")
    info_frame.pack(side="left", fill="both", expand=True, padx=(12, 0))

    module.current_task_label = ctk.CTkLabel(info_frame, text="CURRENT TASK Awaiting command", text_color=THEME.TEXT, font=("Segoe UI", 12))
    module.current_task_label.pack(anchor="w", pady=(0, 6))
    module.execution_status_label = ctk.CTkLabel(info_frame, text="EXECUTION IDLE", text_color=THEME.ACCENT, font=("Segoe UI", 12, "bold"))
    module.execution_status_label.pack(anchor="w", pady=(0, 6))
    module.status_label = ctk.CTkLabel(info_frame, text="STATUS ONLINE", text_color=THEME.ACCENT, font=("Segoe UI", 12, "bold"))
    module.status_label.pack(anchor="w", pady=(0, 8))
    module.core_context_label = ctk.CTkLabel(info_frame, text="Core • AI • Systems", text_color=THEME.MUTED, font=("Segoe UI", 11), justify="left", wraplength=260)
    module.core_context_label.pack(anchor="w", pady=(0, 6))

    module.dashboard_summary = ctk.CTkLabel(
        info_frame,
        text="",
        text_color=THEME.TEXT,
        font=("Segoe UI", 12),
        wraplength=300,
        justify="left",
    )
    module.dashboard_summary.pack(anchor="w", pady=(6, 8))

    pipeline_frame = ctk.CTkFrame(module.center_panel, fg_color=THEME.SURFACE, border_width=1, border_color=THEME.BORDER, corner_radius=16)
    pipeline_frame.pack(fill="x", padx=18, pady=(6, 10))
    ctk.CTkLabel(pipeline_frame, text="AI PIPELINE", text_color=THEME.ACCENT, font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=14, pady=(10, 8))
    module.pipeline_labels = {}
    for label_text in ["INPUT", "INTENT", "PLAN", "MEMORY", "TOOLS", "RESPONSE"]:
        label = ctk.CTkLabel(pipeline_frame, text=f"{label_text} • WAITING", text_color=THEME.MUTED, font=("Segoe UI", 11))
        label.pack(anchor="w", padx=14, pady=2)
        module.pipeline_labels[label_text] = label

    overview_frame = ctk.CTkFrame(module.center_panel, fg_color="transparent")
    overview_frame.pack(fill="x", padx=18, pady=(0, 10))

    module.memory_panel = ctk.CTkFrame(overview_frame, fg_color=THEME.SURFACE, border_width=1, border_color=THEME.BORDER, corner_radius=16)
    module.memory_panel.pack(side="left", fill="both", expand=True, padx=(0, 8))
    ctk.CTkLabel(module.memory_panel, text="MEMORY", text_color=THEME.ACCENT, font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=12, pady=(10, 4))
    module.memory_status_label = ctk.CTkLabel(module.memory_panel, text="Working memory active", text_color=THEME.TEXT, font=("Segoe UI", 11))
    module.memory_status_label.pack(anchor="w", padx=12, pady=(0, 10))

    module.task_panel = ctk.CTkFrame(overview_frame, fg_color=THEME.SURFACE, border_width=1, border_color=THEME.BORDER, corner_radius=16)
    module.task_panel.pack(side="left", fill="both", expand=True, padx=(0, 8))
    ctk.CTkLabel(module.task_panel, text="ACTIVE TASKS", text_color=THEME.ACCENT, font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=12, pady=(10, 4))
    module.task_status_label = ctk.CTkLabel(module.task_panel, text="Awaiting command", text_color=THEME.TEXT, font=("Segoe UI", 11), wraplength=220, justify="left")
    module.task_status_label.pack(anchor="w", padx=12, pady=(0, 10))

    module.backend_panel = ctk.CTkFrame(overview_frame, fg_color=THEME.SURFACE, border_width=1, border_color=THEME.BORDER, corner_radius=16)
    module.backend_panel.pack(side="left", fill="both", expand=True)
    ctk.CTkLabel(module.backend_panel, text="BACKEND", text_color=THEME.ACCENT, font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=12, pady=(10, 4))
    module.backend_status_label = ctk.CTkLabel(module.backend_panel, text="Offline", text_color=THEME.TEXT, font=("Segoe UI", 11))
    module.backend_status_label.pack(anchor="w", padx=12, pady=(0, 4))
    module.network_status_label = ctk.CTkLabel(module.backend_panel, text="Network unavailable", text_color=THEME.MUTED, font=("Segoe UI", 11))
    module.network_status_label.pack(anchor="w", padx=12, pady=(0, 10))

    module.right_panel = ctk.CTkFrame(
        content_frame,
        fg_color=THEME.PANEL,
        width=280,
        border_width=2,
        border_color=THEME.BORDER,
        corner_radius=22,
    )
    module.right_panel.pack(side="right", fill="y", padx=(10, 0))
    module.right_panel.pack_propagate(False)

    ctk.CTkLabel(module.right_panel, text="SYSTEM TELEMETRY", text_color=THEME.ACCENT, font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=16, pady=(16, 8))
    ctk.CTkLabel(module.right_panel, text="provider status and live feed", text_color=THEME.MUTED, font=("Segoe UI", 11)).pack(anchor="w", padx=16, pady=(0, 10))

    module.clock_label = ctk.CTkLabel(module.right_panel, text="00:00:00", text_color=THEME.ACCENT, font=("Segoe UI", 16, "bold"))
    module.clock_label.pack(anchor="w", padx=16, pady=(8, 2))
    module.date_label = ctk.CTkLabel(module.right_panel, text="00-00-0000", text_color=THEME.TEXT, font=("Segoe UI", 12))
    module.date_label.pack(anchor="w", padx=16, pady=(0, 10))

    module.personality_selector = ctk.CTkOptionMenu(
        module.right_panel,
        values=["DRAKEN CORE", "OMEN SHADOW CORE", "JARVIS", "TITAN", "SENTINEL"],
        button_color=THEME.SURFACE,
        button_hover_color=THEME.BORDER,
        text_color=THEME.TEXT,
    )
    module.personality_selector.set(getattr(module, "current_personality", "OMEN SHADOW CORE"))
    module.personality_selector.pack(fill="x", padx=16, pady=(0, 8))

    module.voice_toggle_button = ctk.CTkButton(
        module.right_panel,
        text="VOICE ON",
        width=140,
        fg_color=THEME.SURFACE,
        hover_color=THEME.BORDER,
        text_color=THEME.TEXT,
        corner_radius=10,
        command=lambda: _handle_nav(module, "voice"),
    )
    module.voice_toggle_button.pack(anchor="w", padx=16, pady=(0, 10))

    module.update_status_label = ctk.CTkLabel(module.right_panel, text="AI Version: ready", text_color=THEME.TEXT, font=("Segoe UI", 11), wraplength=240, justify="left")
    module.update_status_label.pack(anchor="w", padx=16, pady=(0, 8))

    module.right_status_labels = {}
    for key, label in [
        ("ai", "AI STATUS IDLE"),
        ("backend", "BACKEND Offline"),
        ("memory", "MEMORY 0 entries"),
        ("task", "ACTIVE TASK Awaiting command"),
        ("system", "SYSTEM 0% CPU • 0% RAM"),
        ("tools", "TOOLS 0 plugins"),
    ]:
        module.right_status_labels[key] = ctk.CTkLabel(module.right_panel, text=label, text_color=THEME.TEXT, font=("Segoe UI", 12), anchor="w")
        module.right_status_labels[key].pack(anchor="w", padx=18, pady=4)

    module.bottom_panel = ctk.CTkFrame(module.main_frame, fg_color=THEME.PANEL, border_width=2, border_color=THEME.BORDER, corner_radius=22)
    module.bottom_panel.pack(fill="x", pady=(10, 0))

    module.terminal = None
    module.logs_box = None

    input_frame = ctk.CTkFrame(module.bottom_panel, fg_color="transparent")
    input_frame.pack(fill="x", padx=14, pady=(14, 8))

    module.command_entry = ctk.CTkEntry(input_frame, border_width=1, border_color=THEME.BORDER, fg_color=THEME.SURFACE, text_color=THEME.TEXT, font=("Segoe UI", 13))
    module.command_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
    module.command_entry.bind("<Return>", lambda event=None: (_submit_command(module), "break"))

    module.voice_button = ctk.CTkButton(input_frame, text="VOICE", width=90, fg_color=THEME.SURFACE, hover_color=THEME.BORDER, text_color=THEME.TEXT, corner_radius=10, command=lambda: _handle_nav(module, "voice"))
    module.voice_button.pack(side="left", padx=(0, 8))

    module.send_button = ctk.CTkButton(input_frame, text="SEND", width=90, fg_color=THEME.ACCENT, hover_color=THEME.ACCENT_SOFT, text_color=THEME.BACKGROUND, corner_radius=10, command=lambda: _submit_command(module))
    module.send_button.pack(side="left")

    dock_frame = ctk.CTkFrame(module.bottom_panel, fg_color="transparent")
    dock_frame.pack(fill="x", padx=14, pady=(0, 10))
    for label in ["TERMINAL", "CODE EDITOR", "BROWSER", "FILES", "NOTES", "CALCULATOR", "+"]:
        btn = ctk.CTkButton(dock_frame, text=label, width=88, fg_color=THEME.SURFACE, hover_color=THEME.BORDER, text_color=THEME.TEXT, corner_radius=10)
        btn.pack(side="left", padx=(0, 8))

    footer_frame = ctk.CTkFrame(module.bottom_panel, fg_color="transparent")
    footer_frame.pack(fill="x", padx=14, pady=(0, 14))

    module.activity_feed = ctk.CTkTextbox(footer_frame, width=520, height=110, fg_color=THEME.SURFACE, text_color=THEME.TEXT, font=("Consolas", 11), border_width=1, border_color=THEME.BORDER)
    module.activity_feed.pack(side="left", fill="both", expand=True, padx=(0, 8))
    module.activity_feed.configure(state="disabled")

    module.terminal = module.activity_feed
    module.logs_box = module.activity_feed

    module.telemetry_box = ctk.CTkTextbox(footer_frame, width=240, height=110, fg_color=THEME.SURFACE, text_color=THEME.TEXT, font=("Consolas", 11), border_width=1, border_color=THEME.BORDER)
    module.telemetry_box.pack(side="right")
    module.telemetry_box.configure(state="disabled")

    module.history_box = ctk.CTkTextbox(footer_frame, width=240, height=110, fg_color=THEME.SURFACE, text_color=THEME.TEXT, font=("Consolas", 11), border_width=1, border_color=THEME.BORDER)
    module.history_box.pack(side="right", padx=(8, 0))
    module.history_box.configure(state="disabled")

    module.radar_canvas = tk.Canvas(module.right_panel, width=220, height=140, bg=THEME.BACKGROUND, highlightthickness=0)
    module.radar_canvas.pack(fill="x", padx=14, pady=(0, 8))
    module.radar_dots = []

    module.metric_labels = {
        "cpu": ctk.CTkLabel(module.top_bar, text="CPU 0%", text_color=THEME.TEXT, font=("Segoe UI", 11)),
        "ram": ctk.CTkLabel(module.top_bar, text="RAM 0%", text_color=THEME.TEXT, font=("Segoe UI", 11)),
        "gpu": ctk.CTkLabel(module.top_bar, text="GPU 0%", text_color=THEME.TEXT, font=("Segoe UI", 11)),
        "network": ctk.CTkLabel(module.top_bar, text="NETWORK 0.0.0.0", text_color=THEME.TEXT, font=("Segoe UI", 11)),
        "backend": ctk.CTkLabel(module.top_bar, text="BACKEND Offline", text_color=THEME.TEXT, font=("Segoe UI", 11)),
        "memory": ctk.CTkLabel(module.top_bar, text="MEMORY 0", text_color=THEME.TEXT, font=("Segoe UI", 11)),
        "plugins": ctk.CTkLabel(module.top_bar, text="PLUGINS 0", text_color=THEME.TEXT, font=("Segoe UI", 11)),
        "task": ctk.CTkLabel(module.top_bar, text="ACTIVE TASK Awaiting", text_color=THEME.TEXT, font=("Segoe UI", 11)),
    }
    for label in module.metric_labels.values():
        label.pack(side="left", padx=(0, 10), pady=12)

    module.hud_ai_state = getattr(module, "hud_ai_state", "IDLE")
    module.hud_current_task = getattr(module, "hud_current_task", "Awaiting command")
    module.current_personality = getattr(module, "current_personality", "OMEN SHADOW CORE")

    module.terminal_print = getattr(module, "terminal_print", None)
    module.add_log = getattr(module, "add_log", None)
    if module.terminal_print is not None:
        def terminal_wrapper(text: str, color: str = module.GREEN) -> None:
            def _run() -> None:
                _ui_print(module, "terminal", text, color)
                if getattr(module, "activity_feed", None) is not None:
                    try:
                        module.activity_feed.configure(state="normal")
                        module.activity_feed.insert("end", text + "\n")
                        module.activity_feed.configure(state="disabled")
                        module.activity_feed.see("end")
                    except Exception:
                        pass
            try:
                module.app.after(0, _run)
            except Exception:
                _run()
        module.terminal_print = terminal_wrapper

    if module.add_log is not None:
        def log_wrapper(text: str, color: str = module.GREEN) -> None:
            def _run() -> None:
                _ui_print(module, "logs", text, color)
                if getattr(module, "telemetry_box", None) is not None:
                    try:
                        module.telemetry_box.configure(state="normal")
                        module.telemetry_box.insert("end", text + "\n")
                        module.telemetry_box.configure(state="disabled")
                        module.telemetry_box.see("end")
                    except Exception:
                        pass
            try:
                module.app.after(0, _run)
            except Exception:
                _run()
        module.add_log = log_wrapper

    _sync_nav_state(module, "home")
    set_hud_state(getattr(module, "hud_ai_state", "IDLE"), getattr(module, "hud_current_task", "Awaiting command"))
    refresh_hud_metrics()
    _draw_core(module)
