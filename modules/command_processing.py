from config.settings import SETTINGS
from modules.ai_backend import *
from modules.memory import *
from core.engine import omen_core
from core.architecture import CommandRouter, EventBus, PluginRegistry
from core.kernel import Kernel, PluginSpec
from core.orchestrator import AIOrchestrator
from core.intent import IntentEngine
from plugins.plugin_loader import dispatch_command

try:
    from core.reverius_opium import CYAN, GREEN, YELLOW, RED
except Exception:  # pragma: no cover - fallback for lightweight imports
    CYAN = "#66ffff"
    GREEN = "#66ffff"
    YELLOW = "#66ffff"
    RED = "#ff4444"


def _fallback_terminal_print(message, color=None):
    """Lightweight compatibility shim for tests and headless imports."""
    return None


def _dynamic_terminal_print(message, color=None):
    fn = _get_reverius_attr("terminal_print")
    if callable(fn):
        return fn(message, color)
    return _fallback_terminal_print(message, color)


terminal_print = _dynamic_terminal_print


def _get_reverius_attr(name: str):
    try:
        import core.reverius_opium as reverius
        return getattr(reverius, name)
    except Exception:
        return None


def _safe_call_reverius(name: str, *args, **kwargs):
    fn = _get_reverius_attr(name)
    if fn:
        return fn(*args, **kwargs)
    return None


def update_command_history_display():
    return _safe_call_reverius("update_command_history_display")


def refresh_update_status_label():
    return _safe_call_reverius("refresh_update_status_label")


def show_memory():
    return _safe_call_reverius("show_memory")


def _dynamic_add_log(message, color=None):
    fn = _get_reverius_attr("add_log")
    if callable(fn):
        return fn(message, color)
    return _fallback_terminal_print(message, color)


add_log = _dynamic_add_log


_core_command_router = CommandRouter()
_core_intent_engine = IntentEngine()
_core_event_bus = EventBus()
_core_plugin_registry = PluginRegistry()
_core_kernel = Kernel()
_pipeline_orchestrator = AIOrchestrator(backend_manager=get_shared_backend_manager())


_default_kernel_plugins = [
    PluginSpec(name="search", description="Search capability", supported_intents=("search",)),
    PluginSpec(name="browser", description="Browser capability", supported_intents=("search",)),
    PluginSpec(name="http", description="HTTP capability", supported_intents=("search",)),
    PluginSpec(name="planner", description="Planning capability", supported_intents=("coding",)),
    PluginSpec(name="reasoning", description="Reasoning capability", supported_intents=("coding",)),
    PluginSpec(name="code_generator", description="Code generation capability", supported_intents=("coding",)),
    PluginSpec(name="compiler", description="Compiler capability", supported_intents=("coding",)),
    PluginSpec(name="vision", description="Vision capability", supported_intents=("vision",)),
    PluginSpec(name="ocr", description="OCR capability", supported_intents=("vision",)),
    PluginSpec(name="image_processor", description="Image processor", supported_intents=("vision",)),
    PluginSpec(name="voice", description="Voice capability", supported_intents=("voice",)),
    PluginSpec(name="speech_recognition", description="Speech recognition", supported_intents=("voice",)),
    PluginSpec(name="benchmark", description="Benchmark capability", supported_intents=("diagnostics",)),
    PluginSpec(name="testing", description="Testing capability", supported_intents=("diagnostics",)),
    PluginSpec(name="diagnostics", description="Diagnostics capability", supported_intents=("diagnostics",)),
]

_core_kernel.discover_plugins(_default_kernel_plugins)


def register_command_handler(command: str, handler):
    """Register a command handler with the shared command router."""
    _core_command_router.register(command, handler)


def register_plugin(name: str, plugin, enabled: bool = True):
    """Register a plugin instance with the shared plugin registry."""
    _core_plugin_registry.register(name, plugin, enabled=enabled)


def publish_event(event_name: str, payload=None):
    """Publish an event through the shared event bus."""
    _core_event_bus.publish(event_name, payload)


def subscribe_event(event_name: str, handler):
    """Subscribe to an event via the shared event bus."""
    _core_event_bus.subscribe(event_name, handler)


def resolve_kernel_plugins(command: str):
    """Resolve the minimal plugin set required for a command."""
    return _core_kernel.load_plugins(command)

# =========================================================
# AI WEB SEARCH SYSTEM
# =========================================================

def ai_answer(query):

    try:

        terminal_print(
            f"[OMEN] Searching: {query}",
            CYAN
        )

        add_log(
            f"AI search request: {query}",
            CYAN
        )

        # =========================
        # WIKIPEDIA SEARCH
        # =========================

        result = None

        try:
            result = wikipedia.summary(query, sentences=2)

        except wikipedia.exceptions.DisambiguationError as e:
            try:
                result = wikipedia.summary(e.options[0], sentences=2)
            except:
                result = None

        except wikipedia.exceptions.PageError:
            result = None

        except Exception:
            result = None

        # =========================
        # IF RESULT FOUND
        # =========================

        if result and isinstance(result, str) and result.strip():

            terminal_print(result, GREEN)
            add_log(result, CYAN)

            threading.Thread(
                target=speak,
                args=(result,),
                daemon=True
            ).start()

            return

        # =========================
        # FALLBACK DUCKDUCKGO SUMMARY
        # =========================

        summary = None

        try:
            response = requests.get(
                "https://api.duckduckgo.com/",
                params={
                    "q": query,
                    "format": "json",
                    "t": "omen",
                    "no_html": 1,
                    "skip_disambig": 1
                },
                timeout=10
            )

            data = response.json()
            summary = data.get("AbstractText", "")

        except Exception:
            summary = None

        if summary and summary.strip():
            terminal_print(summary, GREEN)
            add_log(summary, CYAN)
            threading.Thread(
                target=speak,
                args=(summary,),
                daemon=True
            ).start()
            return

        terminal_print(
            "[OMEN] No direct answer found. Opening Google...",
            YELLOW
        )

        encoded = urllib.parse.quote(query)
        url = f"https://www.google.com/search?q={encoded}"

        webbrowser.open(url)

        speak(f"Opening Google search for {query}")

    except Exception as e:

        terminal_print(
            f"[ERROR] {e}",
            RED
        )


def tell_joke():
    jokes = [
        "Why did the computer show up late? It had a hard drive.",
        "Why did the programmer quit his job? Because he didn't get arrays.",
        "Why do robots have summer holidays? To recharge their batteries.",
        "What do you call a computer that sings? A Dell."
    ]

    joke = random.choice(jokes)

    terminal_print(joke, GREEN)
    add_log("AI joke delivered", CYAN)
    speak(joke)


def assistant_chat(query):
    """Chat with REVERIUS via AI backend with error handling."""
    if not query:
        terminal_print(
            "[OMEN] Ask me anything, I'm listening.",
            YELLOW
        )
        return

    terminal_print(
        f"[OMEN] Processing: {query}",
        CYAN
    )
    add_log(
        f"OMEN query: {query}",
        CYAN
    )
    record_memory("assistant_query", query)

    try:
        pipeline_result = asyncio.run(_pipeline_orchestrator.handle_request(query))
        answer = pipeline_result.response
        if not answer:
            personality = get_personality_prompt()
            memory_ctx = get_memory_context()
            full_prompt = f"{personality}\n\n{memory_ctx}\n\nUser: {query}"
            answer = query_ai(full_prompt, temperature=0.5, max_tokens=1024)

        if answer and not answer.startswith("[ERROR]"):
            terminal_print(answer, GREEN)
            if voice_enabled:
                threading.Thread(
                    target=speak,
                    args=(answer,),
                    daemon=True
                ).start()
            return

    except Exception as e:
        logger.error(f"Assistant chat error: {e}")
        add_log(
            f"AI error: {e}",
            RED
        )

    terminal_print(
        "[AI] I could not generate an answer. Try again.",
        RED
    )

# =========================================================
# LAUNCH SYSTEM
# =========================================================

def launch(command):

    try:

        subprocess.Popen(
            command,
            shell=True
        )

    except:

        terminal_print(
            "[ERROR] Failed to launch",
            RED
        )

# =========================================================
# COMMANDS
# =========================================================

def _show_manual():
    terminal_print("MANUAL", CYAN)
    terminal_print("- help: show this manual", GREEN)
    terminal_print("- status: check if I am online", GREEN)
    terminal_print("- time / date: show current time or date", GREEN)
    terminal_print("- clear: clear the terminal", GREEN)
    terminal_print("- exit: close the session", GREEN)
    terminal_print("- ask <query>: ask a question", GREEN)


def process_command(cmd):

    global chrome_profiles
    global history_index

    cmd = cmd.lower().strip()

    if cmd in {"help", "manual", "commands", "lzbr salva"}:
        _show_manual()
        return True

    analysis = _core_intent_engine.analyze(cmd)
    if analysis.primary_intent is not None and analysis.primary_intent.confidence >= 0.75:
        result = _core_intent_engine.execute(analysis.primary_intent)
        if result.success:
            terminal_print(f"[INTENT] {analysis.primary_intent.name.upper()} -> {result.message}", CYAN)
            return True

    if analysis.primary_intent is not None and analysis.primary_intent.requires_confirmation:
        terminal_print(f"[INTENT] Confirmation required for {analysis.primary_intent.name}", YELLOW)
        return True

    terminal_print(
        f"COMMAND> {cmd}",
        CYAN
    )

    command_history.append(cmd)
    update_command_history_display()
    record_memory("command", cmd)

    history_index = len(command_history)

    resolve_kernel_plugins(cmd)

    if dispatch_command(cmd):
        return

    if omen_core.route(cmd):
        return

    # =====================================================
    # CHROME
    # =====================================================

    if cmd == "open chrome":

        if "default" in chrome_profiles:

            launch(
                f'start chrome --profile-directory="{chrome_profiles["default"]}"'
            )

        else:

            launch("start chrome")

    elif cmd == "open personal chrome":

        launch(
            'start chrome --profile-directory="Profile 10"'
        )

        terminal_print(
            "[AI] Opening personal Chrome profile: Profile 10",
            GREEN
        )

    elif cmd == "open work chrome":

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

    elif cmd == "link phone":

        start_phone_link_server()

    elif cmd == "stop phone":

        stop_phone_link_server()

    elif cmd == "show phone link":

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

    elif cmd == "open phone page":

        if not phone_link_running:
            start_phone_link_server()
        if phone_link_url:
            launch(f"start {phone_link_url}")

    elif cmd == "phone status":

        status_text = (
            "active" if phone_link_running else "inactive"
        )
        terminal_print(
            f"PHONE LINK status: {status_text}",
            GREEN if phone_link_running else YELLOW
        )

    elif cmd.startswith("update ai") or cmd.startswith("update omen"):

        task = cmd.replace(
            "update ai",
            "",
            1
        ).replace(
            "update omen",
            "",
            1
        ).strip()

        if not task:
            terminal_print(
                "[AI] Use 'update ai <task>' or 'update omen <task>' to describe what to improve.",
                YELLOW
            )
        else:
            prepare_self_update(task)

    elif cmd in ("apply update", "self update", "self-update", "apply omen update"):

        apply_self_update()

    elif cmd in ("show update status", "update status"):

        refresh_update_status_label()
        terminal_print(
            get_update_status(),
            CYAN
        )

    elif cmd in ("show personality", "current personality"):

        terminal_print(
            f"Personality mode: {current_personality}",
            CYAN
        )

    elif cmd.startswith("set personality"):

        choice = cmd.replace(
            "set personality",
            "",
            1
        ).strip().upper()

        if choice in PERSONALITY_MODES:
            set_personality_mode(choice)
        else:
            terminal_print(
                "Available personalities: DRAKEN CORE, OMEN SHADOW CORE, JARVIS.",
                YELLOW
            )

    elif cmd in ("voice on", "enable voice"):

        if not voice_enabled:
            toggle_voice_mode()
        else:
            terminal_print(
                "Voice responses are already enabled.",
                YELLOW
            )

    elif cmd in ("voice off", "disable voice"):

        if voice_enabled:
            toggle_voice_mode()
        else:
            terminal_print(
                "Voice responses are already disabled.",
                YELLOW
            )

    elif cmd in ("show command history", "command history"):

        update_command_history_display()
        terminal_print(
            "Command history refreshed.",
            CYAN
        )

    elif cmd == "refresh update status":

        refresh_update_status_label()
        terminal_print(
            "Update status refreshed.",
            CYAN
        )

    elif cmd == "show memory":

        show_memory()

    elif cmd in ("clear memory", "forget memory", "omen clear memory", "assistant forget memory"):

        clear_memory()

    elif cmd in ("forget last note", "clear last note"):

        forget_last_note()

    elif cmd == "summarize memory":

        summarize_memory()

    elif cmd.startswith("ask omen "):

        question = cmd.replace(
            "ask omen",
            "",
            1
        ).strip()

        assistant_chat(question)

    elif cmd.startswith("omen"):

        query = cmd.replace(
            "omen",
            "",
            1
        ).strip()

        if query.startswith(","):
            query = query[1:].strip()

        if query:
            assistant_chat(query)
        else:
            terminal_print(
                "[OMEN] Say something after 'omen'.",
                YELLOW
            )

    elif cmd.startswith("ask assistant "):

        question = cmd.replace(
            "ask assistant",
            "",
            1
        ).strip()

        assistant_chat(question)

    elif cmd.startswith("assistant"):

        query = cmd.replace(
            "assistant",
            "",
            1
        ).strip()

        if query.startswith(","):
            query = query[1:].strip()

        if query.startswith("tell me a joke") or "joke" in query:
            tell_joke()

        elif query.startswith("note "):
            note_text = query.replace(
                "note",
                "",
                1
            ).strip()

            if note_text:
                save_note(note_text)
                terminal_print(
                    "[AI] Note saved.",
                    GREEN
                )
                speak(
                    "Note saved."
                )
            else:
                terminal_print(
                    "[AI] Please tell me what to note.",
                    YELLOW
                )

        elif query.startswith("show notes") or query == "notes":
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

        elif query in ("forget memory", "clear memory"):
            clear_memory()

        elif query in ("forget last note", "clear last note"):
            forget_last_note()

        elif query == "show memory":
            show_memory()

        elif query == "summarize memory":
            summarize_memory()

        elif query.startswith("status") or query.startswith("what is your status"):
            terminal_print(
                "[AI] I am online and ready to assist.",
                GREEN
            )
            speak(
                "I am online and ready to assist."
            )

        elif query.startswith("generate code"):
            prompt = query.replace(
                "generate code",
                "",
                1
            ).strip()

            if not prompt:
                terminal_print(
                    "[AI] No prompt given",
                    RED
                )
                speak(
                    "No prompt given"
                )
            else:
                code = generate_code(prompt)
                with open(
                    "generated.py",
                    "w",
                    encoding="utf-8"
                ) as f:
                    f.write(code)
                terminal_print(
                    "[AI] Code saved to generated.py",
                    GREEN
                )
                add_log(
                    "AI code generated successfully",
                    CYAN
                )
                print(
                    "\n===== GENERATED CODE =====\n"
                )
                print(code)
                speak(
                    "Code generated successfully"
                )

        else:
            assistant_chat(query)

      # =====================================================
    # AI CODE GENERATOR
    # =====================================================

    elif cmd.startswith("generate code"):

        try:

            terminal_print(
                "[OMEN] Generating code...",
                CYAN
            )

            speak(
                "Generating code"
            )

            prompt = (
                cmd.replace(
                    "generate code",
                    ""
                ).strip()
            )

            if not prompt:

                terminal_print(
                    "[AI] No prompt given",
                    RED
                )

                speak(
                    "No prompt given"
                )

                return

            code = generate_code(prompt)

            with open(
                "generated.py",
                "w",
                encoding="utf-8"
            ) as f:

                f.write(code)

            terminal_print(
                "[AI] Code saved to generated.py",
                GREEN
            )

            add_log(
                "AI code generated successfully",
                CYAN
            )

            print(
                "\n===== GENERATED CODE =====\n"
            )

            print(code)

            speak(
                "Code generated successfully"
            )

        except Exception as e:

            terminal_print(
                f"[ERROR] {e}",
                RED
            )

            add_log(
                f"Generator error: {e}",
                RED
            )

            speak(
                "Code generation failed"
            )
    # =====================================================
    # MUSIC SYSTEM
    # =====================================================

    elif cmd.startswith("play ") and " omen" in cmd:

        song = (
            cmd.replace("play", "")
            .replace("omen", "")
            .strip()
        )

        playlist_url = (
            "https://youtube.com/playlist?"
            "list=PLAyjIa5pABjSV7KrX5PNviOxzmE6XKR3u"
            "&si=S98f2kJe9uYWC5XB"
        )

        terminal_print(
            f"[AI] Playing {song}",
            GREEN
        )

        add_log(
            f"Music request detected: {song}",
            CYAN
        )

        speak(
            f"Playing {song}"
        )

        launch(
            f"start {playlist_url}"
        )

    # =====================================================
    # AI SEARCH COMMANDS
    # =====================================================

    elif cmd.startswith("who is "):

        question = cmd.replace(
            "who is",
            ""
        ).strip()

        ai_answer(question)

    elif cmd.startswith("what is "):

        question = cmd.replace(
            "what is",
            ""
        ).strip()

        ai_answer(question)

    elif cmd.startswith("search "):

        question = cmd.replace(
            "search",
            ""
        ).strip()

        ai_answer(question)

    elif cmd.startswith("tell me about "):

        question = cmd.replace(
            "tell me about",
            ""
        ).strip()

        ai_answer(question)

    # =====================================================
    # WEB
    # =====================================================

    elif cmd == "open edge":

        launch("start msedge")

    elif cmd == "open google":

        launch(
            "start https://google.com"
        )

    elif cmd == "open youtube":

        launch(
            "start https://youtube.com"
        )

    # =====================================================
    # APPS
    # =====================================================

    elif cmd == "open notepad":

        launch("notepad")

    elif cmd == "open discord":

        launch("start discord")

    elif cmd == "open spotify":

        launch("start spotify")

    elif cmd == "open paint":

        launch("mspaint")

    elif cmd == "open calculator":

        launch("calc")

    # =====================================================
    # GAMES
    # =====================================================

    elif cmd == "open warframe":

        launch(
            "start steam://rungameid/230410"
        )

    elif cmd == "open valorant":

        terminal_print(
            "[AI] Valorant launcher unavailable",
            RED
        )

    # =====================================================
    # CODING
    # =====================================================

    elif cmd == "open codex":

        launch(
            "start https://www.programiz.com/c-programming/online-compiler/"
        )

    # =====================================================
    # CORE
    # =====================================================

    elif cmd == "greet":

        greet_user()

    elif cmd == "time":

        terminal_print(
            time.strftime("%H:%M:%S"),
            GREEN
        )

    elif cmd == "date":

        terminal_print(
            time.strftime("%d-%m-%Y"),
            GREEN
        )

    elif cmd == "clear":

        terminal.delete(
            "1.0",
            "end"
        )

    elif cmd == "help":

        terminal_print(
            "AVAILABLE COMMANDS:",
            YELLOW
        )

        terminal_print(
            "open chrome",
            GREEN
        )

        terminal_print(
            "open youtube",
            GREEN
        )

        terminal_print(
            "play phonk omen",
            GREEN
        )

        terminal_print(
            "who is elon musk",
            GREEN
        )

        terminal_print(
            "search cyberpunk ui",
            GREEN
        )

        terminal_print(
            "open paint",
            GREEN
        )

        terminal_print(
            "open calculator",
            GREEN
        )

        terminal_print(
            "assistant tell me a joke",
            GREEN
        )

        terminal_print(
            "assistant note remember to buy coffee",
            GREEN
        )

        terminal_print(
            "assistant show notes",
            GREEN
        )

        terminal_print(
            "assistant forget memory",
            GREEN
        )

        terminal_print(
            "assistant clear memory",
            GREEN
        )

        terminal_print(
            "assistant summarize memory",
            GREEN
        )

        terminal_print(
            "show memory",
            GREEN
        )

        terminal_print(
            "show personality",
            GREEN
        )

        terminal_print(
            "set personality <name>",
            GREEN
        )

        terminal_print(
            "voice on / voice off",
            GREEN
        )

        terminal_print(
            "forget last note",
            GREEN
        )

        terminal_print(
            "time",
            GREEN
        )

        terminal_print(
            "date",
            GREEN
        )

        terminal_print(
            "clear",
            GREEN
        )

        terminal_print(
            "exit",
            GREEN
        )

    elif cmd == "exit":

        shutdown()

    else:

        terminal_print(
            "[AI] Unknown command",
            RED
        )

# =========================================================
# ENTRY HANDLER
# =========================================================

def _get_command_entry():
    """Return the UI entry widget when available for interactive use."""
    entry = globals().get("command_entry")
    if entry is None:
        return None
    return entry


def handle(event=None):
    entry = _get_command_entry()
    if entry is None:
        return "break"

    cmd = entry.get().strip()

    entry.delete(0, "end")

    if cmd:
        process_command(cmd)

    return "break"


def _bind_entry_handlers() -> None:
    entry = _get_command_entry()
    if entry is None:
        return

    entry.bind("<Return>", handle)
    entry.bind("<KeyPress-/>", slash_jump)
    entry.bind("<Up>", history_up)
    entry.bind("<Down>", history_down)


# =========================================================
# SMART CURSOR SYSTEM
# =========================================================

def slash_jump(event):
    entry = _get_command_entry()
    if entry is None:
        return "break"

    current = entry.get()

    if "/" not in current:
        entry.insert("insert", "/")

    entry.icursor("end")

    return "break"

# =========================================================
# TERMINAL SHORTCUTS
# =========================================================

command_history = []

history_index = -1

def history_up(event):
    global history_index

    entry = _get_command_entry()
    if entry is None:
        return "break"

    if not command_history:
        return "break"

    history_index = max(0, history_index - 1)

    entry.delete(0, "end")
    entry.insert(0, command_history[history_index])

    return "break"


def history_down(event):
    global history_index

    entry = _get_command_entry()
    if entry is None:
        return "break"

    if not command_history:
        return "break"

    history_index = min(len(command_history) - 1, history_index + 1)

    entry.delete(0, "end")
    entry.insert(0, command_history[history_index])

    return "break"


_bind_entry_handlers()

# =========================================================
# BLINKING CURSOR EFFECT
# =========================================================

cursor_visible = True

def cursor_blink():
    global cursor_visible

    if not running:
        return

    entry = _get_command_entry()
    if entry is None:
        return

    try:
        if cursor_visible:
            entry.configure(border_color=GREEN)
        else:
            entry.configure(border_color="#101010")

        cursor_visible = not cursor_visible
    except Exception:
        pass

    safe_after(500, cursor_blink)

# =========================================================
# ENGINE HEARTBEAT
# =========================================================

def engine_heartbeat():

    if not running:
        return

    try:

        cpu = psutil.cpu_percent(
            interval=None
        )

        app.title(
            f"OMEN SHADOW CORE | CPU {cpu}%"
        )

    except:
        pass

    safe_after(
        3000,
        engine_heartbeat
    )

# =========================================================
# SHUTDOWN
# =========================================================

def shutdown():

    global running

    running = False

    try:

        for after_id in after_ids:

            try:

                app.after_cancel(
                    after_id
                )

            except:
                pass

    except:
        pass

    try:

        plt.close("all")

    except:
        pass

    try:

        app.destroy()

    except:
        pass

    sys.exit(0)

def _bind_window_shutdown() -> None:
    app_instance = globals().get("app")
    if app_instance is None:
        return
    try:
        app_instance.protocol("WM_DELETE_WINDOW", shutdown)
    except Exception:
        pass


_bind_window_shutdown()
