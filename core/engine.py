import logging
import socket
import time
from pathlib import Path

import psutil
import requests

from config.settings import SETTINGS

logger = logging.getLogger(__name__)

# =========================================================
# LAZY GLOBAL BINDING
# =========================================================
# The Brain classes below were written assuming names like
# terminal_print, GREEN, speak, shutdown, etc. are available as
# module globals -- they actually live in core.reverius_opium.
# Importing that module at the top of this file would be circular
# (reverius_opium -> modules.command_processing -> core.engine),
# so instead we bind the names into this module's globals() the
# first time a command is actually routed, once reverius_opium has
# finished loading. See TECHNICAL_DEBT_BASELINE.md / F405 errors.
_REQUIRED_REVERIUS_NAMES = (
    "CYAN", "GREEN", "RED", "YELLOW", "PERSONALITY_MODES",
    "add_log", "advanced_memory", "ai_answer", "analyze_sentiment",
    "apply_self_update", "assistant_chat", "chrome_profiles",
    "clear_memory", "clear_terminal", "current_personality",
    "forget_last_note", "generate_code", "get_crypto_price",
    "get_jarvis", "get_local_ip", "get_news_headlines",
    "get_saved_update_password", "get_update_status", "greet_user",
    "launch", "notes", "phone_link_running", "phone_link_url",
    "prepare_self_update", "refresh_update_status_label", "save_note",
    "save_update_password", "set_personality_mode", "show_memory",
    "shutdown", "speak", "start_phone_link_server",
    "stop_phone_link_server", "summarize_memory", "tell_joke",
    "terminal_print", "toggle_voice_mode", "update_candidate_file",
    "update_command_history_display", "verify_password",
    "voice_enabled", "AUTHORIZED_UPDATE_TOKEN",
)

_bound = False


def _bind_reverius_globals() -> None:
    """Populate this module's globals from core.reverius_opium on first use."""
    global _bound
    if _bound:
        return
    try:
        import core.reverius_opium as _rop
    except Exception:
        # UI stack (customtkinter etc.) unavailable -- leave brains
        # inert rather than crashing the whole router.
        _bound = True
        return
    g = globals()
    for name in _REQUIRED_REVERIUS_NAMES:
        if name not in g and hasattr(_rop, name):
            g[name] = getattr(_rop, name)
    # get_ollama_response is referenced by CodingBrain but was never
    # defined anywhere in the codebase -- provide a safe stub so that
    # call site degrades instead of raising NameError.
    if "get_ollama_response" not in g:
        g["get_ollama_response"] = lambda *a, **k: None
    _bound = True


class BaseBrain:
    def handle(self, cmd):
        return False


class CoreBrain(BaseBrain):
    def handle(self, cmd):
        if cmd == "help":
            self.show_help()
            try:
                jarvis = get_jarvis()
                if jarvis:
                    answer = jarvis.ask(
                        f"System: You are Reverius Advanced AI\n\nUser: {query}",
                        temperature=0.7,
                        max_tokens=1024
                    )
                    terminal_print(answer, GREEN)
                    advanced_memory.add_interaction(query, answer, analyze_sentiment(query))
                    return
            except Exception:
                pass

        if cmd.startswith("set personality"):
            choice = cmd.replace("set personality", "", 1).strip().upper()
            if choice in PERSONALITY_MODES:
                set_personality_mode(choice)
            else:
                terminal_print(
                    "Available personalities: "
                    + ", ".join(PERSONALITY_MODES),
                    YELLOW
                )
            return True

        if cmd.startswith("update ai") or cmd.startswith("update omen") or cmd.startswith("update reverius"):
            task = (
                cmd.replace("update ai", "", 1)
                .replace("update omen", "", 1)
                .replace("update reverius", "", 1)
                .strip()
            )
            if not task:
                terminal_print(
                    "[AI] Use 'update ai <task>', 'update reverius <task>', or 'update omen <task>' to describe what to improve.",
                    YELLOW
                )
            else:
                coding_module.request_change(task)
            return True

        if cmd in ("apply update", "self update", "self-update", "apply omen update", "apply authorized update"):
            apply_self_update()
            return True

        if cmd in ("show update status", "update status", "refresh update status"):
            refresh_update_status_label()
            terminal_print(
                get_update_status(),
                CYAN
            )
            return True

        if cmd in ("show command history", "command history"):
            update_command_history_display()
            terminal_print(
                "Command history refreshed.",
                CYAN
            )
            return True

        if cmd in ("status", "what is your status"):
            terminal_print(
                "[AI] I am online and ready to assist.",
                GREEN
            )
            speak("I am online and ready to assist.")
            return True

        return False

    def show_help(self):
        terminal_print("MANUAL", YELLOW)
        terminal_print("- help: show this manual", GREEN)
        terminal_print("- status: check if I am online", GREEN)
        terminal_print("- time / date: show current time or date", GREEN)
        terminal_print("- clear: clear the terminal", GREEN)
        terminal_print("- exit: close the session", GREEN)
        terminal_print("- ask <query>: ask a question", GREEN)
        terminal_print("", GREEN)
        terminal_print("AVAILABLE COMMANDS:", YELLOW)
        terminal_print("open chrome", GREEN)
        terminal_print("open youtube", GREEN)
        terminal_print("play phonk omen", GREEN)
        terminal_print("who is elon musk", GREEN)
        terminal_print("search cyberpunk ui", GREEN)
        terminal_print("open paint", GREEN)
        terminal_print("open calculator", GREEN)
        terminal_print("assistant tell me a joke", GREEN)
        terminal_print("assistant note remember to buy coffee", GREEN)
        terminal_print("assistant show notes", GREEN)
        terminal_print("assistant forget memory", GREEN)
        terminal_print("assistant clear memory", GREEN)
        terminal_print("assistant summarize memory", GREEN)
        terminal_print("show memory", GREEN)
        terminal_print("show personality", GREEN)
        terminal_print("set personality <name>", GREEN)
        terminal_print("scan devices", GREEN)
        terminal_print("tap device <target>", GREEN)
        terminal_print("hack device <target>", GREEN)
        terminal_print("think <query>", GREEN)
        terminal_print("compile mode on/off", GREEN)
        terminal_print("run code <code>", GREEN)
        terminal_print("authorize update <password>", GREEN)
        terminal_print("set update password <password>", GREEN)
        terminal_print("clear update password", GREEN)
        terminal_print("update ai <task>", GREEN)
        terminal_print("update reverius <task>", GREEN)
        terminal_print("update omen <task>", GREEN)
        terminal_print("apply update", GREEN)
        terminal_print("apply authorized update", GREEN)
        terminal_print("apply omen update", GREEN)
        terminal_print("voice on / voice off", GREEN)
        terminal_print("forget last note", GREEN)
        terminal_print("time", GREEN)
        terminal_print("date", GREEN)
        terminal_print("clear", GREEN)
        terminal_print("exit", GREEN)
        terminal_print("download file <url>", GREEN)
        terminal_print("download to <path> <url>", GREEN)
        terminal_print("download game <url>", GREEN)
        terminal_print("downloads", GREEN)
        terminal_print("ask <query>", GREEN)
        terminal_print("learn <info>", GREEN)
        terminal_print("show learning", GREEN)
        terminal_print("autonomous mode on/off", GREEN)
        terminal_print("schedule <task>", GREEN)
        terminal_print("show tasks", GREEN)
        terminal_print("weather <city>", GREEN)
        terminal_print("crypto <symbol>", GREEN)
        terminal_print("news", GREEN)


class SystemBrain(BaseBrain):
    def handle(self, cmd):
        if cmd == "open chrome":
            if "default" in chrome_profiles:
                launch(
                    f'start chrome --profile-directory="{chrome_profiles["default"]}"'
                )
            else:
                launch("start chrome")
            return True

        if cmd == "open personal chrome":
            launch('start chrome --profile-directory="Profile 10"')
            terminal_print(
                "[AI] Opening personal Chrome profile: Profile 10",
                GREEN
            )
            return True

        if cmd == "open work chrome":
            found_profile = None
            for key, value in chrome_profiles.items():
                if value != "Default":
                    found_profile = value
                    break
            if found_profile:
                launch(
                    f'start chrome --profile-directory="{found_profile}"'
                )
                terminal_print(
                    f"[AI] Opening Chrome profile: {found_profile}",
                    GREEN
                )
            else:
                terminal_print(
                    "[AI] Work Chrome profile not found",
                    RED
                )
            return True

        if cmd == "link phone":
            start_phone_link_server()
            return True

        if cmd == "stop phone":
            stop_phone_link_server()
            return True

        if cmd == "show phone link":
            if phone_link_running:
                terminal_print(
                    f"PHONE LINK: {phone_link_url}",
                    GREEN
                )
            else:
                terminal_print(
                    "PHONE LINK is not active.",
                    YELLOW
                )
            return True

        if cmd == "open phone page":
            if not phone_link_running:
                start_phone_link_server()
            if phone_link_url:
                launch(f"start {phone_link_url}")
            return True

        if cmd == "phone status":
            status_text = (
                "active" if phone_link_running else "inactive"
            )
            terminal_print(
                f"PHONE LINK status: {status_text}",
                GREEN if phone_link_running else YELLOW
            )
            return True

        web_map = {
            "open edge": "start msedge",
            "open google": "start https://google.com",
            "open youtube": "start https://youtube.com",
            "open notepad": "notepad",
            "open discord": "start discord",
            "open spotify": "start spotify",
            "open paint": "mspaint",
            "open calculator": "calc",
            "open warframe": "start steam://rungameid/230410",
            "open codex": "start https://www.programiz.com/c-programming/online-compiler/"
        }

        if cmd in web_map:
            launch(web_map[cmd])
            return True

        if cmd == "open valorant":
            terminal_print(
                "[AI] Valorant launcher unavailable",
                RED
            )
            return True

        return False


class MemoryBrain(BaseBrain):
    def handle(self, cmd):
        if cmd.startswith("assistant note ") or cmd.startswith("note "):
            note_text = cmd.replace("assistant note", "", 1).replace("note", "", 1).strip()
            if note_text:
                save_note(note_text)
                terminal_print(
                    "[AI] Note saved.",
                    GREEN
                )
                speak("Note saved.")
            else:
                terminal_print(
                    "[AI] Please tell me what to note.",
                    YELLOW
                )
            return True

        if cmd in ("assistant show notes", "show notes", "notes"):
            if notes:
                terminal_print(
                    "[AI] Here are your notes:",
                    CYAN
                )
                for note in notes:
                    terminal_print(note, GREEN)
            else:
                terminal_print(
                    "[AI] You have no saved notes.",
                    YELLOW
                )
            return True

        if cmd in ("show memory", "assistant show memory"):
            show_memory()
            return True

        if cmd in ("clear memory", "forget memory", "omen clear memory", "assistant forget memory"):
            clear_memory()
            return True

        if cmd in ("forget last note", "clear last note"):
            forget_last_note()
            return True

        if cmd == "summarize memory" or cmd == "assistant summarize memory":
            summarize_memory()
            return True

        return False


class VoiceBrain(BaseBrain):
    def handle(self, cmd):
        if cmd in ("voice on", "enable voice"):
            if not voice_enabled:
                toggle_voice_mode()
            else:
                terminal_print(
                    "Voice responses are already enabled.",
                    YELLOW
                )
            return True

        if cmd in ("voice off", "disable voice"):
            if voice_enabled:
                toggle_voice_mode()
            else:
                terminal_print(
                    "Voice responses are already disabled.",
                    YELLOW
                )
            return True

        return False


class CodingBrain(BaseBrain):
    def handle(self, cmd):
        if cmd.startswith("generate code"):
            prompt = cmd.replace("generate code", "", 1).strip()
            if not prompt:
                terminal_print(
                    "[AI] No prompt given",
                    RED
                )
                speak("No prompt given")
                return True

            code = generate_code(prompt)
            with open("generated.py", "w", encoding="utf-8") as f:
                f.write(code)

            terminal_print(
                "[AI] Code saved to generated.py",
                GREEN
            )
            add_log(
                "AI code generated successfully",
                CYAN
            )
            print("\n===== GENERATED CODE =====\n")
            print(code)
            speak("Code generated successfully")
            return True

        if cmd.startswith("authorize update "):
            token = cmd.replace("authorize update", "", 1).strip()
            coding_module.authorize(token)
            return True

        if cmd.startswith("set update password "):
            password = cmd.replace("set update password", "", 1).strip()
            coding_module.set_update_password(password)
            return True

        if cmd == "clear update password":
            coding_module.clear_update_password()
            return True

        if cmd == "review update candidate":
            coding_module.review_candidate()
            return True

        if cmd in ("apply authorized update", "apply authorized change"):
            coding_module.apply_change()
            return True

        return False


class CodingModule:
    def __init__(self):
        self.authorized = False

    def authorize(self, token):
        global authorized_change
        saved = get_saved_update_password()
        if saved:
            valid = token and verify_password(saved, token)
        else:
            valid = token and token == AUTHORIZED_UPDATE_TOKEN

        if valid:
            self.authorized = True
            authorized_change = True
            terminal_print(
                "[AI] Code update authorized.",
                GREEN
            )
            speak("Code update authorized.")
        else:
            terminal_print(
                "[AI] Authorization failed. Invalid password.",
                RED
            )
            add_log(
                "Unauthorized code update attempt.",
                RED
            )

    def set_update_password(self, password):
        if not password:
            terminal_print(
                "[AI] Provide a password with 'set update password <password>'.",
                YELLOW
            )
            return

        saved = get_saved_update_password()
        if saved and not self.authorized:
            terminal_print(
                "[AI] You must authorize before changing the update password.",
                YELLOW
            )
            return

        if save_update_password(password):
            self.authorized = True
            terminal_print(
                "[AI] Update password set successfully.",
                GREEN
            )
            speak("Update password set successfully.")
        else:
            terminal_print(
                "[AI] Failed to set update password.",
                RED
            )

    def clear_update_password(self):
        if not self.authorized:
            terminal_print(
                "[AI] You must authorize before clearing the update password.",
                YELLOW
            )
            return

        if clear_update_password():
            self.authorized = False
            terminal_print(
                "[AI] Update password cleared.",
                GREEN
            )
        else:
            terminal_print(
                "[AI] Failed to clear update password.",
                RED
            )

    def request_change(self, task):
        if not task:
            terminal_print(
                "[AI] Specify the change to make using 'update ai <task>', 'update reverius <task>', or 'update omen <task>'.",
                YELLOW
            )
            return
        prepare_self_update(task)

    def review_candidate(self):
        if update_candidate_file.exists():
            terminal_print(
                f"[AI] Update candidate ready: {update_candidate_file.name}",
                CYAN
            )
            try:
                content = update_candidate_file.read_text(encoding="utf-8")
                preview = "\n".join(content.splitlines()[:10])
                terminal_print("Preview:", CYAN)
                terminal_print(preview, GREEN)
            except Exception:
                terminal_print(
                    "[AI] Could not read update candidate.",
                    RED
                )
        else:
            terminal_print(
                "[AI] No update candidate is available.",
                YELLOW
            )

    def apply_change(self):
        if not update_candidate_file.exists():
            terminal_print(
                "[AI] No update candidate found. Run 'update ai <task>' first.",
                YELLOW
            )
            return
        if not self.authorized:
            terminal_print(
                "[AI] Update not authorized. Run 'authorize update <token>' first.",
                YELLOW
            )
            return
        apply_self_update()
        self.authorized = False


coding_module = CodingModule()


class SearchBrain(BaseBrain):
    def handle(self, cmd):
        if cmd.startswith("who is "):
            question = cmd.replace("who is", "", 1).strip()
            ai_answer(question)
            return True

        if cmd.startswith("what is "):
            question = cmd.replace("what is", "", 1).strip()
            ai_answer(question)
            return True

        if cmd.startswith("search "):
            question = cmd.replace("search", "", 1).strip()
            ai_answer(question)
            return True

        if cmd.startswith("tell me about "):
            question = cmd.replace("tell me about", "", 1).strip()
            ai_answer(question)
            return True

        if cmd.startswith("ask omen "):
            question = cmd.replace("ask omen", "", 1).strip()
            assistant_chat(question)
            return True

        if cmd.startswith("ask assistant "):
            question = cmd.replace("ask assistant", "", 1).strip()
            assistant_chat(question)
            return True

        if cmd.startswith("omen"):
            question = cmd.replace("omen", "", 1).strip()
            if question.startswith(","):
                question = question[1:].strip()
            if question:
                assistant_chat(question)
            else:
                terminal_print(
                    "[OMEN] Say something after 'omen'.",
                    YELLOW
                )
            return True

        if cmd.startswith("assistant"):
            query = cmd.replace("assistant", "", 1).strip()
            if query.startswith(","):
                query = query[1:].strip()
            if query.startswith("tell me a joke") or "joke" in query:
                tell_joke()
                return True
            if query.startswith("generate code"):
                prompt = query.replace("generate code", "", 1).strip()
                if not prompt:
                    terminal_print(
                        "[AI] No prompt given",
                        RED
                    )
                    speak("No prompt given")
                else:
                    code = generate_code(prompt)
                    with open("generated.py", "w", encoding="utf-8") as f:
                        f.write(code)
                    terminal_print(
                        "[AI] Code saved to generated.py",
                        GREEN
                    )
                    add_log(
                        "AI code generated successfully",
                        CYAN
                    )
                    print("\n===== GENERATED CODE =====\n")
                    print(code)
                    speak("Code generated successfully")
                return True
            assistant_chat(query)
            return True

        return False


class SecurityBrain(BaseBrain):
    def handle(self, cmd):
        if cmd in ("security status", "show security status"):
            terminal_print(
                "[AI] Security subsystem nominal.",
                GREEN
            )
            return True

        if cmd in ("scan system", "security scan", "scan security", "scan files"):
            self.scan_system()
            return True

        if cmd in ("scan devices", "discover devices", "list devices"):
            self.scan_devices()
            return True

        if cmd.startswith("tap device "):
            target = cmd.replace("tap device", "", 1).strip()
            self.tap_device(target)
            return True

        if cmd.startswith("hack device "):
            target = cmd.replace("hack device", "", 1).strip()
            self.hack_device(target)
            return True

        return False

    def scan_system(self):
        suspicious = []
        try:
            for proc in psutil.process_iter(["pid", "name"]):
                name = (proc.info.get("name") or "").lower()
                if any(term in name for term in ("miner", "crypto", "hack", "malware", "virus", "suspicious", "cmd.exe")):
                    suspicious.append(proc.info)
        except Exception:
            pass

        if suspicious:
            terminal_print(
                "[AI] Suspicious processes detected:",
                RED
            )
            for proc in suspicious:
                terminal_print(
                    f" - {proc.get('name')} (PID {proc.get('pid')})",
                    YELLOW
                )
        else:
            terminal_print(
                "[AI] No suspicious processes detected.",
                GREEN
            )

    def scan_devices(self):
        try:
            local_ip = get_local_ip()
            prefix = ".".join(local_ip.split(".")[:3])
            devices = []
            terminal_print(
                f"[AI] Scanning local network {prefix}.0/24 for active devices...",
                CYAN
            )
            for i in range(1, 21):
                host = f"{prefix}.{i}"
                if host == local_ip:
                    continue
                if self.is_host_up(host):
                    devices.append(host)
                    terminal_print(f" - {host}", GREEN)

            if not devices:
                terminal_print(
                    "[AI] No network devices found in the scanned range.",
                    YELLOW
                )
        except Exception as e:
            terminal_print(
                f"[ERROR] Device scan failed: {e}",
                RED
            )

    def is_host_up(self, host):
        try:
            addr = socket.gethostbyname(host)
        except Exception:
            return False
        for port in (22, 23, 80, 443, 8080):
            try:
                with socket.create_connection((addr, port), timeout=0.4):
                    return True
            except Exception:
                pass
        return False

    def probe_ports(self, host, ports=None):
        if ports is None:
            ports = (22, 23, 80, 443, 8080, 3306, 3389)
        open_ports = []
        try:
            addr = socket.gethostbyname(host)
        except Exception:
            return open_ports

        for port in ports:
            try:
                with socket.create_connection((addr, port), timeout=0.5):
                    open_ports.append(port)
            except Exception:
                pass
        return open_ports

    def get_service_banner(self, host, port):
        try:
            addr = socket.gethostbyname(host)
            with socket.create_connection((addr, port), timeout=0.8) as sock:
                sock.settimeout(0.8)
                data = sock.recv(1024)
                return data.decode(errors="ignore").strip()
        except Exception:
            return "No banner available"

    def tap_device(self, target):
        if not target:
            terminal_print(
                "[AI] Specify a target device with 'tap device <target>'.",
                YELLOW
            )
            return

        terminal_print(
            f"[AI] Tapping device {target}...",
            CYAN
        )
        ports = self.probe_ports(target)
        if not ports:
            terminal_print(
                f"[AI] No open services detected for {target}.",
                YELLOW
            )
            return

        terminal_print(
            f"[AI] Open services discovered on {target}:",
            GREEN
        )
        for port in ports:
            banner = self.get_service_banner(target, port)
            terminal_print(
                f" - Port {port}: {banner}",
                GREEN
            )

    def hack_device(self, target):
        if not target:
            terminal_print(
                "[AI] Specify a target device with 'hack device <target>'.",
                YELLOW
            )
            return

        terminal_print(
            f"[AI] Attempting to hack device {target}...",
            CYAN
        )
        ports = self.probe_ports(target)
        if not ports:
            terminal_print(
                f"[AI] No exposed services found on {target}. Hacking attempt aborted.",
                YELLOW
            )
            return

        terminal_print(
            f"[AI] Exposed services on {target}:",
            GREEN
        )
        for port in ports:
            terminal_print(
                f" - Port {port}",
                GREEN
            )

        if 23 in ports:
            terminal_print(
                "[AI] Telnet service detected. Default credentials may be available.",
                YELLOW
            )
        if 22 in ports:
            terminal_print(
                "[AI] SSH service detected. Weak credentials or reused keys may allow access.",
                YELLOW
            )
        if 80 in ports or 443 in ports:
            terminal_print(
                "[AI] HTTP/HTTPS service detected. Search for admin/default login pages.",
                YELLOW
            )
        if 3389 in ports:
            terminal_print(
                "[AI] RDP service detected. Remote desktop brute force may be possible.",
                YELLOW
            )
        if 3306 in ports:
            terminal_print(
                "[AI] Database service detected. Default credentials are a possible weakness.",
                YELLOW
            )

        if not any(port in ports for port in (22, 23, 80, 443, 3389, 3306)):
            terminal_print(
                "[AI] No standard remote entry points detected. Further reconnaissance is required.",
                CYAN
            )


class SecurityBrain(BaseBrain):
    def handle(self, cmd):
        if cmd in ("security status", "show security status"):
            terminal_print(
                "[AI] Security subsystem nominal.",
                GREEN
            )
            return True

        if cmd in ("scan system", "security scan", "scan security", "scan files"):
            self.scan_system()
            return True

        if cmd in ("scan devices", "discover devices", "list devices"):
            self.scan_devices()
            return True

        if cmd.startswith("tap device "):
            target = cmd.replace("tap device", "", 1).strip()
            self.tap_device(target)
            return True

        if cmd.startswith("hack device "):
            target = cmd.replace("hack device", "", 1).strip()
            self.hack_device(target)
            return True

        return False

    def scan_system(self):
        suspicious = []
        try:
            for proc in psutil.process_iter(["pid", "name"]):
                name = (proc.info.get("name") or "").lower()
                if any(term in name for term in ("miner", "crypto", "hack", "malware", "virus", "suspicious", "cmd.exe")):
                    suspicious.append(proc.info)
        except Exception:
            pass

        if suspicious:
            terminal_print(
                "[AI] Suspicious processes detected:",
                RED
            )
            for proc in suspicious:
                terminal_print(
                    f" - {proc.get('name')} (PID {proc.get('pid')})",
                    YELLOW
                )
        else:
            terminal_print(
                "[AI] No suspicious processes detected.",
                GREEN
            )

    def scan_devices(self):
        try:
            local_ip = get_local_ip()
            prefix = ".".join(local_ip.split(".")[:3])
            devices = []
            terminal_print(
                f"[AI] Scanning local network {prefix}.0/24 for active devices...",
                CYAN
            )
            for i in range(1, 21):
                host = f"{prefix}.{i}"
                if host == local_ip:
                    continue
                if self.is_host_up(host):
                    devices.append(host)
                    terminal_print(f" - {host}", GREEN)

            if not devices:
                terminal_print(
                    "[AI] No network devices found in the scanned range.",
                    YELLOW
                )
        except Exception as e:
            terminal_print(
                f"[ERROR] Device scan failed: {e}",
                RED
            )

    def is_host_up(self, host):
        try:
            addr = socket.gethostbyname(host)
        except Exception:
            return False
        for port in (22, 23, 80, 443, 8080):
            try:
                with socket.create_connection((addr, port), timeout=0.4):
                    return True
            except Exception:
                pass
        return False

    def probe_ports(self, host, ports=None):
        if ports is None:
            ports = (22, 23, 80, 443, 8080, 3306, 3389)
        open_ports = []
        try:
            addr = socket.gethostbyname(host)
        except Exception:
            return open_ports

        for port in ports:
            try:
                with socket.create_connection((addr, port), timeout=0.5):
                    open_ports.append(port)
            except Exception:
                pass
        return open_ports

    def get_service_banner(self, host, port):
        try:
            addr = socket.gethostbyname(host)
            with socket.create_connection((addr, port), timeout=0.8) as sock:
                sock.settimeout(0.8)
                data = sock.recv(1024)
                return data.decode(errors="ignore").strip()
        except Exception:
            return "No banner available"

    def tap_device(self, target):
        if not target:
            terminal_print(
                "[AI] Specify a target device with 'tap device <target>'.",
                YELLOW
            )
            return

        terminal_print(
            f"[AI] Tapping device {target}...",
            CYAN
        )
        ports = self.probe_ports(target)
        if not ports:
            terminal_print(
                f"[AI] No open services detected for {target}.",
                YELLOW
            )
            return

        terminal_print(
            f"[AI] Open services discovered on {target}:",
            GREEN
        )
        for port in ports:
            banner = self.get_service_banner(target, port)
            terminal_print(
                f" - Port {port}: {banner}",
                GREEN
            )

    def hack_device(self, target):
        if not target:
            terminal_print(
                "[AI] Specify a target device with 'hack device <target>'.",
                YELLOW
            )
            return

        terminal_print(
            f"[AI] Attempting to hack device {target}...",
            CYAN
        )
        ports = self.probe_ports(target)
        if not ports:
            terminal_print(
                f"[AI] No exposed services found on {target}. Hacking attempt aborted.",
                YELLOW
            )
            return

        terminal_print(
            f"[AI] Exposed services on {target}:",
            GREEN
        )
        for port in ports:
            terminal_print(
                f" - Port {port}",
                GREEN
            )

        if 23 in ports:
            terminal_print(
                "[AI] Telnet service detected. Default credentials may be available.",
                YELLOW
            )
        if 22 in ports:
            terminal_print(
                "[AI] SSH service detected. Weak credentials or reused keys may allow access.",
                YELLOW
            )
        if 80 in ports or 443 in ports:
            terminal_print(
                "[AI] HTTP/HTTPS service detected. Search for admin/default login pages.",
                YELLOW
            )
        if 3389 in ports:
            terminal_print(
                "[AI] RDP service detected. Remote desktop brute force may be possible.",
                YELLOW
            )
        if 3306 in ports:
            terminal_print(
                "[AI] Database service detected. Default credentials are a possible weakness.",
                YELLOW
            )

        if not any(port in ports for port in (22, 23, 80, 443, 3389, 3306)):
            terminal_print(
                "[AI] No standard remote entry points detected. Further reconnaissance is required.",
                CYAN
            )


class ThinkingBrain(BaseBrain):
    def handle(self, cmd):
        if cmd.startswith("think "):
            query = cmd.replace("think", "", 1).strip()
            self.deep_think(query)
            return True

        return False

    def deep_think(self, query):
        if not query:
            terminal_print(
                "[AI] What should I think about?",
                YELLOW
            )
            return

        terminal_print(
            f"[THINKING] Analyzing: {query}",
            CYAN
        )
        speak("Processing your query")

        prompt = (
            "You are Reverius, a powerful reasoning AI. "
            "Provide a deep, thoughtful analysis of the following query. "
            "Think step-by-step and provide insights. "
            "Be thorough and insightful. "
            f"Query: {query}"
        )

        try:
            jarvis = get_jarvis()
            answer = jarvis.ask(
                f"You are an elite reasoning AI. Provide deep analysis.\n\n{prompt}",
                temperature=0.7,
                max_tokens=1024
            )
            terminal_print(
                f"[ANALYSIS]\n{answer}",
                GREEN
            )
            speak(answer[:200])
        except Exception as e:
            logger.error(f"Deep thinking failed: {e}")
            terminal_print(
                f"[ERROR] Thinking process failed: {e}",
                RED
            )


class CompilerBrain(BaseBrain):
    def __init__(self):
        super().__init__()
        self.compile_mode = False
        self.code_buffer = ""

    def handle(self, cmd):
        if cmd in ("compile mode on", "enable compiler", "start compiler"):
            self.compile_mode = True
            terminal_print(
                "[COMPILER] Mode ON. Enter Python code or 'run' to execute, 'exit' to quit.",
                CYAN
            )
            speak("Compiler mode enabled")
            return True

        if cmd in ("compile mode off", "disable compiler", "stop compiler", "exit compiler"):
            self.compile_mode = False
            self.code_buffer = ""
            terminal_print(
                "[COMPILER] Mode OFF.",
                CYAN
            )
            return True

        if self.compile_mode:
            if cmd == "run":
                self.execute_code()
                return True
            elif cmd == "clear":
                self.code_buffer = ""
                terminal_print(
                    "[COMPILER] Buffer cleared.",
                    YELLOW
                )
                return True
            elif cmd == "show":
                terminal_print(
                    "[COMPILER] Current code:\n" + self.code_buffer,
                    GREEN
                )
                return True
            else:
                self.code_buffer += cmd + "\n"
                terminal_print(
                    f"[COMPILER] Added line. Current lines: {len(self.code_buffer.splitlines())}",
                    YELLOW
                )
                return True

        if cmd.startswith("run code "):
            code = cmd.replace("run code", "", 1).strip()
            self.execute_single(code)
            return True

        return False

    def execute_code(self):
        if not self.code_buffer.strip():
            terminal_print(
                "[COMPILER] No code to execute.",
                YELLOW
            )
            return

        terminal_print(
            "[COMPILER] Executing...",
            CYAN
        )

        try:
            compiled = compile(self.code_buffer, "<user_code>", "exec")
            exec_globals = {}
            exec(compiled, exec_globals)
            terminal_print(
                "[COMPILER] Code executed successfully.",
                GREEN
            )
            speak("Code executed successfully")
        except SyntaxError as e:
            terminal_print(
                f"[COMPILER] Syntax Error: {e}",
                RED
            )
            speak(f"Syntax error at line {e.lineno}")
        except Exception as e:
            terminal_print(
                f"[COMPILER] Runtime Error: {e}",
                RED
            )
            speak(f"Runtime error: {str(e)[:50]}")

    def execute_single(self, code):
        terminal_print(
            f"[COMPILER] Running: {code[:50]}...",
            CYAN
        )

        try:
            compiled = compile(code, "<inline_code>", "exec")
            exec_globals = {}
            exec(compiled, exec_globals)
            terminal_print(
                "[COMPILER] Executed.",
                GREEN
            )
        except Exception as e:
            terminal_print(
                f"[COMPILER] Error: {e}",
                RED
            )


class DownloadBrain(BaseBrain):
    def __init__(self):
        super().__init__()
        self.downloads_folder = Path.home() / "Downloads"
        self.downloads_folder.mkdir(exist_ok=True)
        self.active_downloads = {}

    def handle(self, cmd):
        if cmd.startswith("download file "):
            url = cmd.replace("download file", "", 1).strip()
            self.download_file(url)
            return True

        if cmd.startswith("download to "):
            parts = cmd.replace("download to", "", 1).strip().split(None, 1)
            if len(parts) == 2:
                dest_path = parts[0]
                url = parts[1]
                self.download_file(url, dest_path)
            return True

        if cmd.startswith("download game "):
            url = cmd.replace("download game", "", 1).strip()
            self.download_file(url, is_game=True)
            return True

        if cmd in ("downloads", "show downloads", "list downloads"):
            self.show_downloads()
            return True

        return False

    def download_file(self, url, dest_path=None, is_game=False):
        if not url:
            terminal_print(
                "[DOWNLOAD] No URL provided.",
                YELLOW
            )
            return

        if not url.startswith(("http://", "https://")):
            terminal_print(
                "[DOWNLOAD] Invalid URL. Must start with http:// or https://",
                RED
            )
            speak("Invalid download URL")
            return

        terminal_print(
            f"[DOWNLOAD] ⚠️  SECURITY WARNING: Only download from trusted sources!",
            YELLOW
        )
        terminal_print(
            f"[DOWNLOAD] Initiating download from: {url}",
            CYAN
        )

        try:
            if dest_path and dest_path != ".":
                filename = dest_path
            else:
                filename = url.split("/")[-1].split("?")[0] or "download"
                if is_game:
                    filename = f"game_{filename}" if not filename.startswith("game") else filename

            if not Path(filename).is_absolute():
                filepath = self.downloads_folder / filename
            else:
                filepath = Path(filename)

            terminal_print(
                f"[DOWNLOAD] Downloading to: {filepath}",
                CYAN
            )
            speak(f"Downloading {filename}")

            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0
            chunk_size = 8192

            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        if total_size:
                            percent = (downloaded / total_size) * 100
                            bar_length = 30
                            filled = int(bar_length * downloaded / total_size)
                            bar = "█" * filled + "░" * (bar_length - filled)
                            terminal_print(
                                f"[DOWNLOAD] {bar} {percent:.1f}% ({downloaded}/{total_size} bytes)",
                                CYAN
                            )

            file_size_mb = filepath.stat().st_size / (1024 * 1024)
            terminal_print(
                f"[DOWNLOAD] ✓ Download complete! ({file_size_mb:.2f} MB)",
                GREEN
            )
            speak(f"Download complete: {filename}")

            self.active_downloads[filename] = {
                "path": str(filepath),
                "size": filepath.stat().st_size,
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "type": "game" if is_game else "file"
            }

        except requests.exceptions.Timeout:
            terminal_print(
                "[DOWNLOAD] ✗ Download timeout - URL may be invalid or server is slow",
                RED
            )
            speak("Download timeout")
        except requests.exceptions.ConnectionError:
            terminal_print(
                "[DOWNLOAD] ✗ Connection failed - Check internet or URL",
                RED
            )
            speak("Connection failed")
        except Exception as e:
            terminal_print(
                f"[DOWNLOAD] ✗ Download failed: {e}",
                RED
            )
            speak(f"Download failed: {str(e)[:30]}")

    def show_downloads(self):
        if not self.active_downloads:
            terminal_print(
                "[DOWNLOAD] No downloads tracked yet.",
                YELLOW
            )
            return

        terminal_print(
            "[DOWNLOAD] Recent Downloads:",
            CYAN
        )
        for name, info in self.active_downloads.items():
            size_mb = info["size"] / (1024 * 1024)
            terminal_print(
                f"  • {name} ({size_mb:.2f} MB) - {info['type']} - {info['time']}",
                GREEN
            )


class AdvancedBrain(BaseBrain):
    """Advanced brain using available backends (Jarvis/OpenAI)."""

    def handle(self, cmd):
        if cmd.startswith("ask "):
            query = cmd.replace("ask", "", 1).strip()
            self.advanced_query(query)
            return True

        if cmd.startswith("learn "):
            info = cmd.replace("learn", "", 1).strip()
            self.learn_info(info)
            return True

        if cmd in ("show learning", "show learned", "what have you learned"):
            self.show_learning()
            return True

        return False

    def advanced_query(self, query):
        """Process advanced query using available backends (Jarvis/OpenAI)."""
        terminal_print(
            f"[ADVANCED] Processing: {query}",
            CYAN
        )
        speak("Processing advanced query")

        try:
            ollama_response = get_ollama_response(query)
            if ollama_response:
                terminal_print(
                    f"[OLLAMA LOCAL]\n{ollama_response}",
                    GREEN
                )
                advanced_memory.add_interaction(query, ollama_response, analyze_sentiment(query))
                speak(ollama_response[:200])
                return
        except (ValueError, RuntimeError, ConnectionError) as e:
            logger.warning("Ollama response failed: %s", e)
            pass

        try:
            jarvis = get_jarvis()
            answer = jarvis.ask(
                f"System: You are Reverius Advanced AI\n\nUser: {query}",
                temperature=0.7,
                max_tokens=1024
            )
            terminal_print(
                f"[ADVANCED]\n{answer}",
                GREEN
            )
            advanced_memory.add_interaction(query, answer, analyze_sentiment(query))
            speak(answer[:200])
        except Exception as e:
            logger.error(f"Advanced brain query failed: {e}")
            terminal_print(
                f"[ERROR] {e}",
                RED
            )

    def learn_info(self, info):
        """AI learns and remembers information."""
        terminal_print(
            f"[LEARNING] Noted: {info}",
            YELLOW
        )
        advanced_memory.memory["learning_notes"].append({
            "content": info,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        advanced_memory.save_memory()
        speak("Information learned and saved")
        terminal_print(
            "[ADVANCED] Stored in persistent memory",
            GREEN
        )

    def show_learning(self):
        """Display what AI has learned."""
        if not advanced_memory.memory["learning_notes"]:
            terminal_print(
                "[ADVANCED] Nothing learned yet. Use 'learn <info>' to teach me.",
                YELLOW
            )
            return

        terminal_print(
            "[ADVANCED] What I've Learned:",
            CYAN
        )
        for note in advanced_memory.memory["learning_notes"][-10:]:
            terminal_print(
                f"  • {note['content']} ({note['timestamp']})",
                GREEN
            )


class AutonomousBrain(BaseBrain):
    """Background task executor - AI makes decisions independently."""

    def __init__(self):
        super().__init__()
        self.autonomous_mode = False
        self.scheduled_tasks = []

    def handle(self, cmd):
        if cmd in ("autonomous mode on", "enable autonomous"):
            self.autonomous_mode = True
            terminal_print(
                "[AUTONOMOUS] Mode ON - I will monitor and act independently",
                CYAN
            )
            speak("Autonomous mode enabled")
            try:
                jarvis = get_jarvis()
                if jarvis:
                    answer = jarvis.ask(
                        f"System: You are Reverius Advanced AI\n\nUser: {query}",
                        temperature=0.7,
                        max_tokens=1024
                    )
                    terminal_print(answer, GREEN)
                    advanced_memory.add_interaction(query, answer, analyze_sentiment(query))
                    return
            except Exception:
                pass
        terminal_print(
            f"[AUTONOMOUS] Task scheduled: {task}",
            GREEN
        )
        speak(f"Task scheduled: {task}")

    def show_tasks(self):
        """Show all scheduled tasks."""
        if not self.scheduled_tasks:
            terminal_print(
                "[AUTONOMOUS] No scheduled tasks",
                YELLOW
            )
            return

        terminal_print(
            "[AUTONOMOUS] Scheduled Tasks:",
            CYAN
        )
        for task in self.scheduled_tasks:
            terminal_print(
                f"  • {task['task']} - {task['status']} ({task['created']})",
                GREEN
            )


class DataBrain(BaseBrain):
    """Real-time data fetching - weather, news, crypto, etc."""

    def handle(self, cmd):
        if cmd.startswith("weather "):
            city = cmd.replace("weather", "", 1).strip() or "New York"
            self.get_weather(city)
            return True

        if cmd in ("weather", "current weather"):
            self.get_weather()
            return True

        if cmd.startswith("crypto "):
            symbol = cmd.replace("crypto", "", 1).strip().upper()
            self.get_crypto(symbol)
            return True

        if cmd in ("news", "headlines", "trending"):
            self.get_news()
            return True

        return False

    def get_weather(self, city="New York"):
        """Fetch and display weather."""
        terminal_print(
            f"[DATA] Fetching weather for {city}...",
            CYAN
        )
        weather = get_weather(city)
        terminal_print(
            f"[WEATHER] {city}: {weather}",
            GREEN
        )
        speak(f"Weather in {city}: {weather}")

    def get_crypto(self, symbol):
        """Fetch cryptocurrency price."""
        terminal_print(
            f"[DATA] Fetching {symbol} price...",
            CYAN
        )
        price = get_crypto_price(symbol)
        terminal_print(
            f"[CRYPTO] {price}",
            GREEN
        )
        speak(price)

    def get_news(self):
        """Fetch trending news."""
        terminal_print(
            "[DATA] Fetching latest headlines...",
            CYAN
        )
        headlines = get_news_headlines()
        terminal_print(
            "[NEWS] Top Headlines:",
            CYAN
        )
        for i, headline in enumerate(headlines, 1):
            terminal_print(
                f"  {i}. {headline}",
                GREEN
            )
            speak(headline)


class OmenCore:
    def __init__(self):
        self.brains = [
            CoreBrain(),
            SystemBrain(),
            MemoryBrain(),
            VoiceBrain(),
            ThinkingBrain(),
            CompilerBrain(),
            CodingBrain(),
            SearchBrain(),
            SecurityBrain(),
            DownloadBrain(),
            AdvancedBrain(),
            AutonomousBrain(),
            DataBrain()
        ]

    def route(self, cmd):
        _bind_reverius_globals()
        for brain in self.brains:
            try:
                if brain.handle(cmd):
                    return True
            except Exception as e:
                logger.warning(
                    "%s failed to handle %r: %s",
                    brain.__class__.__name__, cmd, e
                )
                try:
                    add_log(
                        f"{brain.__class__.__name__} error: {e}",
                        RED
                    )
                except Exception:
                    pass  # add_log unavailable (e.g. headless import)
        return False


omen_core = OmenCore()