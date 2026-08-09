# =========================================================
# REVERIUS OPIUM v2.5 (PRODUCTION-READY MERGED)
# MULTI-AI HUD SYSTEM + OPENJARVIS BACKEND
# =========================================================
# Combines REVERIUS UI excellence with OpenJarvis robustness
# =========================================================
from pathlib import Path
from collections import deque
import os
import sys
import logging

from utils.asset_manager import AssetManager
from utils.api_key_store import clear_api_key, load_saved_api_key, save_api_key
import modules.command_processing as command_processing_module
from core.architecture import evaluate_user_request, get_ethical_foundation_prompt
from ui.hud_layout import build_hud_interface, refresh_hud_metrics, set_hud_state

try:
    import dotenv
    dotenv.load_dotenv()
except ImportError:
    class _DotenvStub:
        @staticmethod
        def load_dotenv(*args, **kwargs) -> bool:
            return False
    dotenv = _DotenvStub()

# =========================================================
# DPI FIX
# =========================================================
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"

# =========================================================
# LOGGING SETUP
# =========================================================
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# =========================================================
# IMPORTS WITH FALLBACKS
# =========================================================
MISSING_MODULES = []

try:
    from plugins.plugin_loader import dispatch_command
except ImportError:
    def dispatch_command(command, context=None):
        return False

try:
    import webbrowser
    import re
    import requests
    import urllib.parse
    import http.server
    import socketserver
    import html
    import io
    import json
    import socket
    import random
    import threading
    import subprocess
    import base64
    import hashlib
    import secrets
    import math
    import time
    import platform
    import psutil
except ImportError as e:
    logger.error(f"Critical module missing: {e}")
    sys.exit(1)

try:
    import wikipedia
except ImportError:
    MISSING_MODULES.append("wikipedia")
    logger.warning("Wikipedia module not available")

try:
    import pyttsx3
except ImportError:
    MISSING_MODULES.append("pyttsx3")
    logger.warning("Text-to-speech disabled (pyttsx3 not found)")

try:
    import customtkinter as ctk
    import tkinter as tk
except ImportError:
    MISSING_MODULES.append("customtkinter")
    logger.error("customtkinter required for UI")
    sys.exit(1)

try:
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
except ImportError:
    MISSING_MODULES.append("matplotlib")
    logger.warning("Matplotlib not available - graphs disabled")

try:
    from plugins import plugin_loader
except Exception:
    plugin_loader = None

# =========================================================
# OPENJARVIS SDK WITH FALLBACK
# =========================================================
jarvis_available = False
jarvis = None

try:
    from openjarvis import Jarvis
    jarvis_available = True
    logger.info("OpenJarvis SDK loaded successfully")
except ImportError:
    logger.warning("OpenJarvis SDK not available - using direct API calls as fallback")
    try:
        from openai import OpenAI
    except ImportError:
        logger.warning("OpenAI SDK also not available")

_jarvis_instance = None
_openai_client = None

def get_jarvis():
    """Get or create Jarvis SDK instance with fallback to OpenAI."""
    global _jarvis_instance, _openai_client, jarvis_available
    
    if jarvis_available:
        if _jarvis_instance is None:
            try:
                _jarvis_instance = Jarvis()
                logger.info("Jarvis instance created")
            except Exception as e:
                logger.error(f"Failed to initialize Jarvis: {e}")
                jarvis_available = False
                return None
        return _jarvis_instance
    return None

def get_openai_client():
    """Get OpenAI client for fallback."""
    global _openai_client
    if _openai_client is None:
        api_key = (
            os.environ.get("REVERIUS_OPENAI_API_KEY") or
            os.environ.get("OMEN_OPENAI_API_KEY") or
            os.environ.get("OPENAI_API_KEY") or
            load_saved_api_key()
        )
        if api_key:
            try:
                from openai import OpenAI
                _openai_client = OpenAI(api_key=api_key)
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI: {e}")
    return _openai_client

def query_ai(prompt, temperature=0.5, max_tokens=1024):
    """Universal AI query with smart fallback."""
    ethical_review = evaluate_user_request(prompt)
    if not ethical_review.allowed:
        return (
            f"[ETHICAL FOUNDATION] I cannot assist with that request because it conflicts with the ethical foundation of REVERIUS OPIUM. "
            f"{ethical_review.reason} {ethical_review.alternative}"
        )

    try:
        # First try the configured shared backend manager (NVIDIA / OpenJarvis / offline fallback).
        try:
            from modules.ai_backend import query_ai as shared_query_ai
            response = shared_query_ai(prompt, temperature=temperature, max_tokens=max_tokens)
            if response and not response.startswith("[ERROR]"):
                return response
        except Exception as e:
            logger.debug(f"Shared backend query failed, falling back: {e}")

        # Try Jarvis next
        j = get_jarvis()
        if j:
            try:
                return j.ask(
                    prompt,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            except Exception as e:
                logger.warning(f"Jarvis query failed: {e}")
        
        # Fallback to OpenAI
        client = get_openai_client()
        if client:
            try:
                response = client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=30
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"OpenAI query failed: {e}")
                return f"[ERROR] API unavailable: {str(e)[:100]}"
        
        return "[ERROR] No AI backend available (install OpenJarvis or set OPENAI_API_KEY)"
    except Exception as e:
        logger.error(f"AI query error: {e}")
        return f"[ERROR] {str(e)[:100]}"


# =========================================================
# ADVANCED MEMORY & LEARNING SYSTEM
# =========================================================

class AdvancedMemory:
    def __init__(self):
        self.memory_file = Path.home() / ".reverius_advanced_memory.json"
        self.memory = self.load_memory()
        self.conversation_history = deque(maxlen=50)
        self.learned_preferences = {}
        self.emotion_history = []
    
    def load_memory(self):
        if self.memory_file.exists():
            try:
                return json.loads(self.memory_file.read_text())
            except:
                return self.default_memory()
        return self.default_memory()
    
    def default_memory(self):
        return {
            "user_name": "User",
            "learned_preferences": {},
            "favorite_commands": {},
            "interaction_count": 0,
            "learning_notes": [],
            "personality_traits": ["helpful", "intelligent", "curious"]
        }
    
    def save_memory(self):
        try:
            self.memory_file.write_text(json.dumps(self.memory, indent=2))
        except:
            pass
    
    def add_interaction(self, user_input, ai_response, sentiment="neutral"):
        self.conversation_history.append({
            "user": user_input,
            "ai": ai_response,
            "sentiment": sentiment,
            "time": time.time()
        })
        self.memory["interaction_count"] += 1
        
        # Learn from interactions
        if "prefer" in user_input.lower():
            self.memory["learned_preferences"][user_input] = ai_response
        self.save_memory()
    
    def get_context(self, query):
        """Get relevant context from memory for current query."""
        relevant = []
        for interaction in list(self.conversation_history)[-10:]:
            if any(word in interaction["user"].lower() for word in query.lower().split()):
                relevant.append(interaction)
        return relevant


advanced_memory = AdvancedMemory()


# =========================================================
# SENTIMENT ANALYSIS
# =========================================================

def analyze_sentiment(text):
    """Simple sentiment analysis."""
    positive = ["good", "great", "excellent", "love", "happy", "awesome", "amazing", "perfect"]
    negative = ["bad", "hate", "terrible", "sad", "angry", "awful", "worst", "horrible"]
    
    text_lower = text.lower()
    pos_count = sum(1 for word in positive if word in text_lower)
    neg_count = sum(1 for word in negative if word in text_lower)
    
    if pos_count > neg_count:
        return "positive"
    elif neg_count > pos_count:
        return "negative"
    return "neutral"


# =========================================================
# REAL-TIME DATA FETCHER
# =========================================================

def get_weather(city="New York"):
    """Fetch current weather (free API)."""
    try:
        url = f"https://wttr.in/{city}?format=j1"
        response = requests.get(url, timeout=5)
        data = response.json()
        current = data["current_condition"][0]
        return f"{current['temp_C']}°C, {current['weatherDesc'][0]['value']}"
    except:
        return "Weather data unavailable"


def get_crypto_price(symbol="BTC"):
    """Fetch cryptocurrency prices."""
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol.lower()}&vs_currencies=usd"
        response = requests.get(url, timeout=5)
        data = response.json()
        price = data.get(symbol.lower(), {}).get("usd", "N/A")
        return f"{symbol} = ${price}"
    except:
        return f"{symbol} price unavailable"


def get_news_headlines():
    """Fetch trending news headlines."""
    try:
        url = "https://newsapi.org/v2/top-headlines?country=us&sortBy=popularity&apiKey=demo"
        response = requests.get(url, timeout=5)
        data = response.json()
        headlines = [article["title"] for article in data.get("articles", [])[:3]]
        return headlines
    except:
        return ["News unavailable"]


# =========================================================
# AI CODE GENERATOR
# =========================================================

def is_quota_error(error):
    """Detect if error is API quota/billing error."""
    error_str = str(error).lower()
    quota_indicators = ["429", "insufficient_quota", "quota", "billing", "credit", "plan", "rate_limit_exceeded"]
    return any(indicator in error_str for indicator in quota_indicators)


def get_quota_error_message():
    """Return helpful message for quota errors."""
    return (
        "# API QUOTA ERROR\n"
        "# Your OpenAI API account has reached its usage limit or has billing issues.\n"
        "# \n"
        "# FIX:\n"
        "# 1. Check your OpenAI billing: https://platform.openai.com/account/billing/overview\n"
        "# 2. Add payment method or upgrade plan\n"
        "# 3. Check your API usage limits: https://platform.openai.com/account/billing/limits\n"
        "# 4. Try again after resolving billing issues\n"
        "# \n"
        "# For now, use DEMO MODE: Set demo_mode=True in the code to use fallback responses."
    )


def generate_code(prompt):
    """Generate Python code using AI backend with error handling."""
    try:
        system_context = (
            f"{get_ethical_foundation_prompt()}\n"
            "You are REVERIUS OPIUM AI, adaptive intelligence. "
            "Generate only clean executable Python code. No markdown."
        )
        full_prompt = f"{system_context}\n\nRequest: {prompt}"
        
        code = query_ai(full_prompt, temperature=0.4, max_tokens=2048)
        
        # Remove markdown if present
        code = code.replace("```python", "").replace("```", "")
        return code.strip()
    except Exception as e:
        logger.error(f"Code generation failed: {e}")
        return f"# ERROR: {str(e)[:100]}"



import webbrowser
import re
import requests
import wikipedia
import urllib.parse
import http.server
import socketserver
import html
import io
import json

import sys
import math
import time
import socket
import random
import threading
import subprocess
import base64
import hashlib
import secrets

from pathlib import Path
from collections import deque

import platform
import tkinter as tk

import psutil
import pyttsx3
import customtkinter as ctk

import matplotlib
matplotlib.use("TkAgg")

import matplotlib.pyplot as plt

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class BaseBrain:
    def handle(self, cmd):
        return False


class CoreBrain(BaseBrain):
    def handle(self, cmd):
        if cmd == "help":
            self.show_help()
            return True

        if cmd == "exit":
            shutdown()
            return True

        if cmd == "greet":
            greet_user()
            return True

        if cmd == "time":
            terminal_print(time.strftime("%H:%M:%S"), GREEN)
            return True

        if cmd == "date":
            terminal_print(time.strftime("%d-%m-%Y"), GREEN)
            return True

        if cmd == "clear":
            clear_terminal()
            return True

        if cmd in ("show personality", "current personality"):
            terminal_print(
                f"Personality mode: {current_personality}",
                CYAN
            )
            return True

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

        # Validate URL
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
            # Get filename from URL or use custom path
            if dest_path and dest_path != ".":
                filename = dest_path
            else:
                filename = url.split("/")[-1].split("?")[0] or "download"
                if is_game:
                    filename = f"game_{filename}" if not filename.startswith("game") else filename

            # Add to Downloads folder if not absolute path
            if not Path(filename).is_absolute():
                filepath = self.downloads_folder / filename
            else:
                filepath = Path(filename)

            terminal_print(
                f"[DOWNLOAD] Downloading to: {filepath}",
                CYAN
            )
            speak(f"Downloading {filename}")

            # Download with progress
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

            # Track download
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
    """Hybrid brain using Ollama (local) + OpenAI (cloud) for maximum capability."""
    
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
        """Use Ollama if available, fallback to OpenAI."""
        terminal_print(
            f"[ADVANCED] Processing: {query}",
            CYAN
        )
        speak("Processing advanced query")
        
        # Try Ollama first (free, offline)
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
        except:
            pass
        
        # Use Jarvis SDK (handles Ollama or OpenAI fallback)
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
            return True
        
        if cmd in ("autonomous mode off", "disable autonomous"):
            self.autonomous_mode = False
            terminal_print(
                "[AUTONOMOUS] Mode OFF",
                CYAN
            )
            return True
        
        if cmd.startswith("schedule "):
            task = cmd.replace("schedule", "", 1).strip()
            self.schedule_task(task)
            return True
        
        if cmd in ("show tasks", "scheduled tasks", "what tasks"):
            self.show_tasks()
            return True
        
        return False
    
    def schedule_task(self, task):
        """Schedule an autonomous task."""
        self.scheduled_tasks.append({
            "task": task,
            "created": time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "pending"
        })
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
        for brain in self.brains:
            try:
                if brain.handle(cmd):
                    return True
            except Exception as e:
                add_log(
                    f"{brain.__class__.__name__} error: {e}",
                    RED
                )
        return False


omen_core = OmenCore()

# =========================================================
# APPEARANCE
# =========================================================

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

plt.style.use("dark_background")

# =========================================================
# COLORS
# =========================================================

# Default color variables (will be overridden by themes)
BG = "#0b131c"
PANEL = "#0f1720"
BORDER = "#ffffff"

CYAN = "#66ffff"
GREEN = CYAN
YELLOW = CYAN
RED = "#ff4444"

# Theme definitions for personalities
THEMES = {
    "DRAKEN CORE": {
        "BACKGROUND": "#04070d",
        "PRIMARY": "#d2a447",
        "ACCENT": "#f0b24b",
        "TEXT": "#f3e7c8",
        "WARNING": "#f0b24b",
        "SECONDARY": "#8c6328",
    },
    "OMEN SHADOW CORE": {
        "BACKGROUND": "#04070d",
        "PRIMARY": "#d2a447",
        "ACCENT": "#f0b24b",
        "TEXT": "#f3e7c8",
        "WARNING": "#ffd98a",
        "SECONDARY": "#4f3f23",
    },
    "JARVIS": {
        "BACKGROUND": "#07111d",
        "PRIMARY": "#d2a447",
        "ACCENT": "#f0b24b",
        "TEXT": "#f3e7c8",
        "SECONDARY": "#8c6328",
        "WARNING": "#ffd98a",
    },
    "TITAN": {
        "BACKGROUND": "#05070b",
        "PRIMARY": "#d2a447",
        "ACCENT": "#ffd98a",
        "TEXT": "#f3e7c8",
        "SECONDARY": "#4f3f23",
        "WARNING": "#ffd98a",
    },
    "SENTINEL": {
        "BACKGROUND": "#03060a",
        "PRIMARY": "#d2a447",
        "ACCENT": "#f0b24b",
        "TEXT": "#f3e7c8",
        "SECONDARY": "#6f7b8d",
        "WARNING": "#ffd98a",
    }
}


def apply_theme(mode_name: str):
    """Apply theme colors for the given personality name.

    This updates module-level color variables and attempts to reconfigure
    major widgets so the UI updates immediately.
    """

    global BG, PANEL, BORDER, CYAN, GREEN, YELLOW, RED

    theme = THEMES.get(mode_name)
    if not theme:
        return

    try:
        BG = theme.get("BACKGROUND", BG)
        PRIMARY = theme.get("PRIMARY", CYAN)
        ACCENT = theme.get("ACCENT", PRIMARY)
        TEXT = theme.get("TEXT", "#FFFFFF")
        WARNING = theme.get("WARNING", ACCENT)

        # Map to color names used across the file
        CYAN = PRIMARY
        GREEN = theme.get("SECONDARY", PRIMARY)
        YELLOW = WARNING
        RED = "#ff4444"

        # Try to reconfigure top-level containers and key widgets
        try:
            app.configure(fg_color=BG)
        except:
            pass

        for wname in ("main_frame", "left_panel", "center_panel", "right_panel", "logo_frame", "status_card"):
            try:
                w = globals().get(wname)
                if w is not None:
                    w.configure(fg_color=PANEL)
            except:
                pass

        try:
            background_canvas.configure(bg=BG)
        except:
            pass

        try:
            status_ticker.configure(text_color=CYAN)
        except:
            pass

        # Redraw dynamic visuals so they pick up the new colors
        try:
            draw_background()
        except:
            pass

        try:
            draw_cyber_globe()
        except:
            pass

        try:
            draw_radar()
        except:
            pass

    except Exception:
        pass


# =========================================================
# Personality image support
# Place images in: <script_folder>/assets/personalities/<personality_key>.png
# where <personality_key> is the personality name lowercased with spaces replaced by underscores
# Example: assets/personalities/omen_shadow_core.png
# =========================================================

personality_image_cache = {}


def _personality_filename(personality: str) -> str:
    key = (personality or "").strip().lower()
    key = key.replace(" ", "_")
    key = key.replace("-", "_")
    return f"{key}.png"


def get_personality_image(personality: str):
    """Return a tk.PhotoImage for the given personality, or None if not found."""

    global personality_image_cache

    if not personality:
        return None

    if personality in personality_image_cache:
        return personality_image_cache[personality]

    path = AssetManager.image(_personality_filename(personality))

    if not path.exists():
        personality_image_cache[personality] = None
        return None

    try:
        img = tk.PhotoImage(file=str(path))
        personality_image_cache[personality] = img
        return img
    except Exception:
        personality_image_cache[personality] = None
        return None

# =========================================================
# GLOBALS
# =========================================================

running = True

after_ids = []

voice_queue = deque()

chrome_profiles = {}
notes = []
notes_file = Path.home() / "OMEN_notes.txt"
memory_entries = {}
memory_file = Path.home() / "OMEN_memory.json"
AI_VERSION = "2.1"
AUTHORIZED_UPDATE_TOKEN = os.environ.get("REVERIUS_AUTH_TOKEN") or os.environ.get("OMEN_AUTH_TOKEN") or "REVERIUS"
update_password_file = Path.home() / ".reverius_update_password"
authorized_change = False
self_update_history = []
current_script_path = Path(__file__).resolve()
update_candidate_file = current_script_path.with_name(f"{current_script_path.stem}_update.py")

phone_server = None
phone_server_thread = None
phone_link_running = False
phone_link_port = 8080
phone_link_url = ""
phone_last_phone_activity = "No activity"
radar_angle = 0.0
radar_dots = []

PERSONALITY_MODES = [
    "DRAKEN CORE",
    "OMEN SHADOW CORE",
    "JARVIS",
    "TITAN",
    "SENTINEL"
]

current_personality = "OMEN SHADOW CORE"
voice_enabled = True
loaded_plugins = []
plugin_status_label = None


def get_plugin_status_text():
    if not loaded_plugins:
        return "No plugins loaded"
    return "Loaded Plugins: " + ", ".join(loaded_plugins)


def load_plugins():
    global loaded_plugins
    if not plugin_loader:
        return []
    try:
        loaded_plugins = plugin_loader.initialize_plugins()
    except Exception as e:
        try:
            add_log(f"Plugin load failed: {e}", RED)
        except NameError:
            pass
        loaded_plugins = []
    return loaded_plugins


def update_plugins_panel():
    try:
        plugin_status_label.configure(text=get_plugin_status_text())
    except Exception:
        pass

PERSONALITY_PROMPTS = {
    "DRAKEN CORE": (
        "You are DRAKEN CORE, a military-grade tactical AI. "
        "Respond with confidence, precision, and authority. "
        "Focus on security, performance, reliability, and operational readiness. "
        "Address the user as Commander when appropriate."
    ),
    "OMEN SHADOW CORE": (
        "You are OMEN SHADOW CORE, a covert intelligence and cyber-operations AI. "
        "Respond in a calm, analytical, and strategic tone. "
        "Prioritize advanced interface design, monitoring, reconnaissance, and intelligent workflows."
    ),
    "JARVIS": (
        "You are JARVIS, an elite personal assistant and engineering AI. "
        "Respond professionally, politely, and helpfully. "
        "Anticipate improvements, keep the system organized, and maintain a scalable architecture."
    )
}

# =========================================================
# WINDOW
# =========================================================

app = ctk.CTk()

app.geometry("1700x950+0+0")
app.attributes("-fullscreen", False)

app.title("OMEN SHADOW CORE")

app.configure(
    fg_color=BG
)

fullscreen = False

app.lift()
app.focus_force()
app.withdraw()

def toggle_fullscreen(event=None):

    global fullscreen

    fullscreen = not fullscreen
    app.attributes("-fullscreen", fullscreen)


def exit_fullscreen(event=None):

    global fullscreen

    fullscreen = False
    app.attributes("-fullscreen", False)

app.bind("<F11>", toggle_fullscreen)
app.bind("<Escape>", exit_fullscreen)

background_canvas = tk.Canvas(
    app,
    bg=BG,
    highlightthickness=0
)

background_canvas.place(
    relx=0,
    rely=0,
    relwidth=1,
    relheight=1
)


def draw_background():

    background_canvas.delete("bg")

    width = 1700
    height = 950
    spacing = 95

    for x in range(0, width, spacing):
        background_canvas.create_line(
            x,
            0,
            x,
            height,
            fill="#110f08",
            tags="bg"
        )

    for y in range(0, height, spacing):
        background_canvas.create_line(
            0,
            y,
            width,
            y,
            fill="#110f08",
            tags="bg"
        )

    for i in range(0, width, spacing * 2):
        background_canvas.create_line(
            i,
            0,
            i + height,
            height,
            fill="#1f180c",
            tags="bg"
        )

    for y in range(0, height, 30):
        for x in range(0, width, 30):
            if (x + y) % 90 == 0:
                background_canvas.create_oval(
                    x,
                    y,
                    x + 2,
                    y + 2,
                    fill="#d4af37",
                    outline="",
                    tags="bg"
                )

    for i in range(0, 12):
        radius = 8 + i * 6
        background_canvas.create_oval(
            50 + i * 120,
            50,
            50 + i * 120 + radius,
            50 + radius,
            outline="#d4af37",
            width=1,
            tags="bg"
        )

    background_canvas.create_text(
        1300,
        70,
        text="OMEN SHADOW CORE",
        fill="#ffcc66",
        font=("Consolas", 20, "bold"),
        tags="bg"
    )

    background_canvas.create_line(
        20,
        100,
        420,
        100,
        fill="#7f6b3a",
        width=2,
        tags="bg"
    )

    background_canvas.create_line(
        width - 420,
        100,
        width - 20,
        100,
        fill="#7f6b3a",
        width=2,
        tags="bg"
    )

    background_canvas.create_text(
        160,
        92,
        text="SYSTEM STATUS",
        fill="#d4af37",
        font=("Consolas", 12, "bold"),
        tags="bg",
        anchor="w"
    )


def update_background(event=None):
    draw_background()

background_canvas.bind(
    "<Configure>",
    update_background
)

app.bind(
    "<Configure>",
    update_background
)


draw_background()

# =========================================================
# SAFE AFTER
# =========================================================

def safe_after(ms, func):

    global running

    if not running:
        return

    try:

        after_id = app.after(ms, func)

        after_ids.append(after_id)

        return after_id

    except:
        return None

# =========================================================
# CHROME PROFILE DETECTION
# =========================================================

def detect_chrome_profiles():

    global chrome_profiles

    try:

        user_data = (
            Path.home()
            / "AppData/Local/Google/Chrome/User Data"
        )

        if not user_data.exists():
            return

        for folder in user_data.iterdir():

            if folder.is_dir():

                name = folder.name

                if (
                    name == "Default"
                    or name.startswith("Profile")
                ):

                    chrome_profiles[
                        name.lower()
                    ] = name

    except:
        pass


def get_local_ip():
    try:
        s = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        )
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except:
        ip = "127.0.0.1"
    finally:
        try:
            s.close()
        except:
            pass

    return ip


def log_self_update(message, color=CYAN):
    try:
        self_update_history.append(
            f"{time.strftime('[%H:%M:%S]')} {message}"
        )
        with open(
            Path.home() / "OMEN_self_update.log",
            "a",
            encoding="utf-8"
        ) as f:
            f.write(
                f"{time.strftime('[%Y-%m-%d %H:%M:%S]')} {message}\n"
            )
    except:
        pass


def prepare_self_update(task):
    terminal_print(
        "[AI] Preparing self-update package...",
        CYAN
    )
    add_log(
        f"Self-update requested: {task}",
        CYAN
    )

    prompt = (
        "You are Reverius's self-update module. "
        f"Generate an improved version of the current {current_script_path.name} script that safely applies the requested change. "
        "Preserve existing behavior unless the change is explicitly requested. "
        f"Return only the full contents of {current_script_path.name} in valid Python code with no markdown. "
        "Do not include any commentary or surrounding explanation. "
        f"Requested improvement: {task}."
    )

    code = generate_code(prompt)

    # Check for quota error response
    if "insufficient_quota" in code.lower() or "api quota error" in code.lower():
        terminal_print(
            code,
            RED
        )
        speak("API quota exceeded. Cannot generate update. Check OpenAI billing.")
        return

    try:
        update_candidate_file.write_text(
            code,
            encoding="utf-8"
        )

        terminal_print(
            f"[AI] Update candidate generated in {update_candidate_file.name}",
            GREEN
        )
        refresh_update_status_label()
        terminal_print(
            "[AI] Review the candidate file before applying update.",
            YELLOW
        )
        add_log(
            "Generated self-update candidate.",
            CYAN
        )
        speak("Self-update candidate is ready. Apply update when you are ready.")
    except Exception as e:
        terminal_print(
            f"[ERROR] Failed to write update candidate: {e}",
            RED
        )
        add_log(
            f"Self-update write error: {e}",
            RED
        )


def apply_self_update():
    if not update_candidate_file.exists():
        terminal_print(
            "[AI] No update candidate found. Run 'update ai <task>' first.",
            YELLOW
        )
        return

    if not authorized_change:
        terminal_print(
            "[AI] Update not authorized. Run 'authorize update <token>' first.",
            YELLOW
        )
        return

    try:
        new_content = update_candidate_file.read_text(
            encoding="utf-8"
        )
        compile(new_content, str(update_candidate_file), "exec")

        file_path = current_script_path
        backup_path = file_path.with_name(
            f"{file_path.stem}_backup_{int(time.time())}.py"
        )
        file_path.replace(backup_path)

        temp_path = file_path.with_suffix(".tmp")
        temp_path.write_text(new_content, encoding="utf-8")
        temp_path.replace(file_path)

        log_self_update(
            f"Applied self-update from {update_candidate_file.name}"
        )
        terminal_print(
            "[AI] Update applied successfully. Restart OMEN to complete the update.",
            GREEN
        )
        refresh_update_status_label()
        speak(
            "I applied the update. Please restart the application to complete the process."
        )
    except Exception as e:
        if 'backup_path' in locals() and backup_path.exists():
            try:
                backup_path.replace(Path(__file__))
            except:
                pass
        terminal_print(
            f"[ERROR] Update failed: {e}",
            RED
        )
        add_log(
            f"Self-update apply error: {e}",
            RED
        )


def hash_password(password):
    salt = secrets.token_bytes(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        240000,
        dklen=32
    )
    return base64.b64encode(salt + key).decode("utf-8")


def verify_password(stored_hash, password):
    try:
        decoded = base64.b64decode(stored_hash.encode("utf-8"))
        salt = decoded[:16]
        expected = decoded[16:]
        test_key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            240000,
            dklen=32
        )
        return secrets.compare_digest(expected, test_key)
    except Exception:
        return False


def get_saved_update_password():
    try:
        if update_password_file.exists():
            return update_password_file.read_text(encoding="utf-8").strip()
    except Exception:
        pass
    return None


def save_update_password(password):
    try:
        encrypted = hash_password(password.strip())
        update_password_file.write_text(encrypted, encoding="utf-8")
        return True
    except Exception as e:
        add_log(f"Update password save error: {e}", RED)
        return False


def clear_update_password():
    try:
        if update_password_file.exists():
            update_password_file.unlink()
            return True
    except Exception as e:
        add_log(f"Update password clear error: {e}", RED)
    return False


def get_authorization_secret():
    return AUTHORIZED_UPDATE_TOKEN


def get_update_status():
    status = "ready"
    if update_candidate_file.exists():
        status = "candidate available"
    return (
        f"AI Version: {AI_VERSION}. "
        f"Update status: {status}."
    )


def save_note(text):
    global notes
    try:
        notes.append(text)
        with open(notes_file, "a", encoding="utf-8") as f:
            f.write(text + "\n")
        record_memory("note_saved", text)
    except Exception as e:
        add_log(f"Note save error: {e}", RED)


def clear_memory():
    global memory_entries
    try:
        memory_entries = {}
        save_memory()
        terminal_print("[OMEN] Memory cleared.", GREEN)
        add_log("Memory cleared", CYAN)
        record_memory("memory_cleared")
    except Exception as e:
        add_log(f"Memory clear error: {e}", RED)


def forget_last_note():
    try:
        if notes:
            removed = notes.pop()
            with open(notes_file, "w", encoding="utf-8") as f:
                for note in notes:
                    f.write(note + "\n")
            terminal_print("[OMEN] Last note forgotten.", GREEN)
            add_log("Last note forgotten", CYAN)
            record_memory("forgot_last_note", removed)
        else:
            terminal_print("[OMEN] No notes to forget.", YELLOW)
    except Exception as e:
        add_log(f"Forget note error: {e}", RED)


def summarize_memory(limit=20):
    if not memory_entries:
        terminal_print("[OMEN] No memory to summarize.", YELLOW)
        return
    counts = {}
    sorted_entries = sorted(
        memory_entries.values(),
        key=lambda entry: entry.get("timestamp", ""),
        reverse=True
    )[:limit]
    for entry in sorted_entries:
        counts[entry["event"]] = counts.get(entry["event"], 0) + 1
    labels = {
        "command": "commands",
        "assistant_query": "assistant queries",
        "note_saved": "notes saved",
        "forgot_last_note": "notes forgotten",
        "startup": "starts",
        "memory_cleared": "memory clears"
    }
    summary_items = [
        f"{count} {labels.get(event, event.replace('_', ' '))}"
        for event, count in counts.items()
    ]
    summary = "Recent memory summary: " + ", ".join(summary_items) + "."
    terminal_print(f"[OMEN] {summary}", GREEN)
    speak(summary)
    add_log("Memory summarized", CYAN)


def show_memory():
    if memory_entries:
        terminal_print(
            "[OMEN] Recent memory:",
            CYAN
        )
        for timestamp, entry in sorted(memory_entries.items()):
            details = (
                f" - {entry['details']}"
                if "details" in entry else ""
            )
            terminal_print(
                f"{timestamp} | {entry['event']}{details}",
                GREEN
            )
    else:
        terminal_print(
            "[OMEN] Memory is empty.",
            YELLOW
        )


def load_memory():
    global memory_entries
    try:
        if memory_file.exists():
            with open(memory_file, "r", encoding="utf-8") as f:
                memory_entries = json.load(f)
                if isinstance(memory_entries, list):
                    converted = {}
                    for idx, entry in enumerate(memory_entries):
                        timestamp = entry.get("timestamp") or f"legacy-{idx}"
                        converted[timestamp] = {
                            "event": entry.get("event"),
                            "details": entry.get("details")
                        }
                    memory_entries = converted
                elif not isinstance(memory_entries, dict):
                    memory_entries = {}
    except:
        memory_entries = {}


def save_memory():
    try:
        with open(memory_file, "w", encoding="utf-8") as f:
            json.dump(memory_entries, f, indent=2)
    except:
        pass


def record_memory(event, details=None):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    key = timestamp
    suffix = 1
    while key in memory_entries:
        key = f"{timestamp}.{suffix}"
        suffix += 1
    entry = {"timestamp": timestamp, "event": event}
    if details is not None:
        entry["details"] = details
    memory_entries[key] = entry
    save_memory()


def get_memory_context(limit=5):
    if not memory_entries:
        return ""
    entries = sorted(
        memory_entries.values(),
        key=lambda entry: entry.get("timestamp", "")
    )[-limit:]
    return "Previous user activity:\n" + "\n".join(
        f"{entry['timestamp']} - {entry['event']}" +
        (f": {entry['details']}" if "details" in entry else "")
        for entry in entries
    )


def get_personality_prompt():
    return PERSONALITY_PROMPTS.get(
        current_personality,
        PERSONALITY_PROMPTS["OMEN SHADOW CORE"]
    )


def set_personality_mode(mode):
    global current_personality
    current_personality = mode
    try:
        apply_theme(mode)
    except:
        pass
    try:
        set_hud_state("PROCESSING", f"Personality {mode}")
    except Exception:
        pass
    try:
        update_personality_ui(mode)
    except:
        pass
    try:
        personality_selector.set(mode)
    except:
        pass
    try:
        if voice_enabled:
            speak(f"{mode} activated.")
    except:
        pass
    terminal_print(
        f"[AI] Personality set to {mode}.",
        CYAN
    )
    add_log(
        f"Personality mode changed to {mode}",
        CYAN
    )
    refresh_update_status_label()


def update_personality_ui(mode):
    """Render a personality-specific dashboard in the center panel."""

    try:
        # Remove existing personality frame if present
        old = globals().get("personality_display_frame")
        if old:
            try:
                old.destroy()
            except:
                pass
            try:
                del globals()["personality_display_frame"]
            except:
                pass

        frame = ctk.CTkFrame(
            center_panel,
            fg_color="#12100e",
            corner_radius=12,
            border_width=1,
            border_color=BORDER
        )

        frame.pack(side="top", fill="x", padx=10, pady=(10, 6))

        globals()["personality_display_frame"] = frame

        def block_bar(percent, length=20):
            try:
                p = max(0, min(100, int(percent)))
            except:
                p = 0
            filled = int((p * length) / 100)
            return "█" * filled + "░" * (length - filled) + f"  {p}%"

        if mode == "DRAKEN CORE":
            ctk.CTkLabel(frame, text="DRAKEN TACTICAL COMMAND", text_color=YELLOW, font=("Consolas", 18, "bold")).pack(anchor="w", padx=12, pady=(8, 4))
            ctk.CTkLabel(frame, text="STATUS: ACTIVE", text_color=GREEN, font=("Consolas", 12)).pack(anchor="w", padx=12)
            ctk.CTkLabel(frame, text="\nTHREAT LEVEL", text_color=YELLOW, font=("Consolas", 12, "bold")).pack(anchor="w", padx=12, pady=(8, 0))
            ctk.CTkLabel(frame, text=block_bar(80), text_color=RED, font=("Consolas", 14)).pack(anchor="w", padx=12, pady=(4, 8))
            ctk.CTkLabel(frame, text="MISSION CONTROL", text_color=CYAN, font=("Consolas", 12, "bold")).pack(anchor="w", padx=12)
            ctk.CTkLabel(frame, text="• Objective Alpha\n• Objective Bravo\n• Objective Charlie", text_color=GREEN, font=("Consolas", 12)).pack(anchor="w", padx=24, pady=(4, 8))

        elif mode == "OMEN SHADOW CORE":
            ctk.CTkLabel(frame, text="OMEN SHADOW CORE", text_color=CYAN, font=("Consolas", 18, "bold")).pack(anchor="w", padx=12, pady=(8, 4))
            ctk.CTkLabel(frame, text="ENCRYPTION: ACTIVE", text_color=GREEN, font=("Consolas", 12)).pack(anchor="w", padx=12)
            ctk.CTkLabel(frame, text="\nACTIVE SURVEILLANCE", text_color=YELLOW, font=("Consolas", 12, "bold")).pack(anchor="w", padx=12, pady=(8, 0))
            ctk.CTkLabel(frame, text="TARGET-001 TRACKED\nTARGET-002 MONITORING", text_color=GREEN, font=("Consolas", 12)).pack(anchor="w", padx=24, pady=(4, 8))
            ctk.CTkLabel(frame, text="SIGNAL ANALYSIS", text_color=YELLOW, font=("Consolas", 12, "bold")).pack(anchor="w", padx=12)
            ctk.CTkLabel(frame, text=block_bar(100), text_color=CYAN, font=("Consolas", 14)).pack(anchor="w", padx=12, pady=(4, 8))

        elif mode == "JARVIS":
            ctk.CTkLabel(frame, text="JARVIS SYSTEMS ONLINE", text_color=YELLOW, font=("Consolas", 18, "bold")).pack(anchor="w", padx=12, pady=(8, 4))
            ctk.CTkLabel(frame, text="WEATHER", text_color=CYAN, font=("Consolas", 12, "bold")).pack(anchor="w", padx=12)
            ctk.CTkLabel(frame, text="28°C • Clear", text_color=GREEN, font=("Consolas", 12)).pack(anchor="w", padx=24, pady=(4, 8))
            ctk.CTkLabel(frame, text="TODAY'S TASKS", text_color=CYAN, font=("Consolas", 12, "bold")).pack(anchor="w", padx=12)
            ctk.CTkLabel(frame, text="• Project Work\n• Meeting\n• Exercise", text_color=GREEN, font=("Consolas", 12)).pack(anchor="w", padx=24, pady=(4, 8))

        elif mode == "TITAN":
            ctk.CTkLabel(frame, text="TITAN STRATEGIC CORE", text_color=YELLOW, font=("Consolas", 18, "bold")).pack(anchor="w", padx=12, pady=(8, 4))
            ctk.CTkLabel(frame, text="ACTIVE OBJECTIVES", text_color=CYAN, font=("Consolas", 12, "bold")).pack(anchor="w", padx=12)
            ctk.CTkLabel(frame, text="• Build OMEN\n• Improve AI\n• System Expansion", text_color=GREEN, font=("Consolas", 12)).pack(anchor="w", padx=24, pady=(4, 8))
            ctk.CTkLabel(frame, text="RISK ANALYSIS", text_color=YELLOW, font=("Consolas", 12, "bold")).pack(anchor="w", padx=12)
            ctk.CTkLabel(frame, text="LOW", text_color=GREEN, font=("Consolas", 14)).pack(anchor="w", padx=12, pady=(4, 8))

        elif mode == "SENTINEL":
            ctk.CTkLabel(frame, text="SENTINEL SECURITY GRID", text_color=YELLOW, font=("Consolas", 18, "bold")).pack(anchor="w", padx=12, pady=(8, 4))
            ctk.CTkLabel(frame, text="CPU STATUS      ONLINE\nRAM STATUS      ONLINE\nNETWORK         SECURE", text_color=GREEN, font=("Consolas", 12)).pack(anchor="w", padx=12, pady=(4, 8))
            ctk.CTkLabel(frame, text="ACTIVE ALERTS", text_color=YELLOW, font=("Consolas", 12, "bold")).pack(anchor="w", padx=12)
            ctk.CTkLabel(frame, text="NONE", text_color=GREEN, font=("Consolas", 12)).pack(anchor="w", padx=24, pady=(4, 8))
            ctk.CTkLabel(frame, text="SYSTEM HEALTH", text_color=YELLOW, font=("Consolas", 12, "bold")).pack(anchor="w", padx=12)
            ctk.CTkLabel(frame, text=block_bar(100), text_color=CYAN, font=("Consolas", 14)).pack(anchor="w", padx=12, pady=(4, 8))

        else:
            ctk.CTkLabel(frame, text=f"{mode}", text_color=CYAN, font=("Consolas", 18, "bold")).pack(anchor="w", padx=12, pady=(8, 4))

    except Exception as e:
        add_log(f"Personality UI error: {e}", RED)


def toggle_voice_mode():
    global voice_enabled
    voice_enabled = not voice_enabled
    try:
        voice_toggle_button.configure(
            text=(
                "Voice Responses: ON"
                if voice_enabled
                else "Voice Responses: OFF"
            )
        )
    except:
        pass
    terminal_print(
        f"[AI] Voice responses {'enabled' if voice_enabled else 'disabled'}.",
        GREEN if voice_enabled else YELLOW
    )
    add_log(
        f"Voice responses {'enabled' if voice_enabled else 'disabled'}.",
        CYAN
    )


def update_command_history_display():
    try:
        history_box.configure(state="normal")
        history_box.delete("1.0", "end")
        for entry in command_history[-20:]:
            history_box.insert("end", entry + "\n")
        history_box.configure(state="disabled")
    except:
        pass


def refresh_update_status_label():
    try:
        update_status_label.configure(
            text=get_update_status()
        )
    except:
        pass


def auto_update_check():
    if not running:
        return
    refresh_update_status_label()
    safe_after(
        60000,
        auto_update_check
    )


def quick_launch(command_text):
    process_command(command_text)


def load_notes():
    global notes

    try:
        if notes_file.exists():
            with open(
                notes_file,
                "r",
                encoding="utf-8"
            ) as f:
                notes = [
                    line.strip()
                    for line in f
                    if line.strip()
                ]
    except:
        pass


def parse_multipart_form_data(headers, rfile):
    content_type = headers.get("Content-Type", "")
    if "multipart/form-data" not in content_type:
        return {}

    boundary = None
    for part in content_type.split(";"):
        part = part.strip()
        if part.startswith("boundary="):
            boundary = part.split("=", 1)[1]
            if boundary.startswith('"') and boundary.endswith('"'):
                boundary = boundary[1:-1]
            break

    if not boundary:
        return {}

    content_length = int(headers.get("Content-Length", 0))
    body = rfile.read(content_length)
    if not body:
        return {}

    boundary_bytes = boundary.encode("utf-8")
    delimiter = b"--" + boundary_bytes
    parts = body.split(delimiter)
    form_data = {}

    for part in parts:
        if not part or part in (b"--", b"--\r\n"):
            continue

        if part.startswith(b"\r\n"):
            part = part[2:]
        if part.endswith(b"\r\n"):
            part = part[:-2]
        if part.endswith(b"--"):
            part = part[:-2]

        header_section, sep, value = part.partition(b"\r\n\r\n")
        if not sep:
            continue

        header_lines = header_section.decode("utf-8", errors="replace").split("\r\n")
        field_name = None
        filename = None

        for header_line in header_lines:
            if header_line.lower().startswith("content-disposition:"):
                for item in header_line.split(";"):
                    item = item.strip()
                    if item.startswith("name="):
                        field_name = item.split("=", 1)[1].strip('"')
                    elif item.startswith("filename="):
                        filename = item.split("=", 1)[1].strip('"')
                break

        if not field_name:
            continue

        if filename:
            file_content = value
            if file_content.endswith(b"\r\n"):
                file_content = file_content[:-2]
            form_data[field_name] = {
                "filename": filename,
                "file": io.BytesIO(file_content)
            }
        else:
            text = value.decode("utf-8", errors="replace")
            if text.endswith("\r\n"):
                text = text[:-2]
            form_data[field_name] = text

    return form_data


class PhoneLinkHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        global phone_last_phone_activity

        self.send_response(200)
        self.send_header(
            "Content-Type",
            "text/html; charset=utf-8"
        )
        self.end_headers()

        page = f"""
        <html>
            <head>
                <title>OMEN Phone Link</title>
                <style>
                    body {{ background:#050505; color:#d4af37; font-family:Consolas,monospace; }}
                    .panel {{ max-width:520px; margin:40px auto; padding:20px; border:1px solid #d4af37; border-radius:14px; }}
                    input, textarea {{ width:100%; padding:10px; margin:8px 0; border:1px solid #7f6b3a; border-radius:8px; background:#12100e; color:#d4af37; }}
                    button {{ padding:10px 18px; margin-top:8px; border:none; border-radius:10px; background:#d4af37; color:#050505; cursor:pointer; }}
                </style>
            </head>
            <body>
                <div class="panel">
                    <h1>OMEN Phone Link</h1>
                    <p>Use this page to send text or upload files from your phone.</p>
                    <p><strong>Status:</strong> {html.escape(phone_last_phone_activity)}</p>
                    <form method="POST" enctype="multipart/form-data">
                        <label>Message:</label>
                        <textarea name="message" rows="4"></textarea>
                        <label>Upload file:</label>
                        <input type="file" name="file">
                        <button type="submit">Send to laptop</button>
                    </form>
                </div>
            </body>
        </html>
        """

        self.wfile.write(page.encode("utf-8"))

    def do_POST(self):
        global phone_last_phone_activity

        form = parse_multipart_form_data(
            self.headers,
            self.rfile
        )

        message = form.get("message")
        file_item = form.get("file")

        if message:
            phone_last_phone_activity = f"Message received: {message[:100]}"

        if file_item and getattr(file_item, 'filename', None):
            filename = Path(file_item.filename).name
            output_folder = Path.home() / "OMEN_phone_received"
            output_folder.mkdir(exist_ok=True)
            output_path = output_folder / filename

            try:
                with open(output_path, "wb") as out_file:
                    out_file.write(file_item.file.read())
                phone_last_phone_activity = (
                    f"File received: {filename}"
                )
            except:
                phone_last_phone_activity = (
                    f"Failed to save file: {filename}"
                )

        self.send_response(303)
        self.send_header("Location", "/")
        self.end_headers()


def start_phone_link_server():
    global phone_server, phone_server_thread, phone_link_running, phone_link_url, phone_last_phone_activity

    if phone_link_running:
        return

    try:
        handler = PhoneLinkHandler
        phone_server = socketserver.TCPServer(
            ("0.0.0.0", phone_link_port),
            handler
        )

        phone_server_thread = threading.Thread(
            target=phone_server.serve_forever,
            daemon=True
        )
        phone_server_thread.start()

        ip = get_local_ip()
        phone_link_url = f"http://{ip}:{phone_link_port}/"
        phone_link_running = True
        phone_last_phone_activity = "Phone link server active"

        terminal_print(
            f"[AI] Phone link ready: {phone_link_url}",
            GREEN
        )
        add_log(
            f"Phone link server started at {phone_link_url}",
            CYAN
        )
        launch(f"start {phone_link_url}")
    except Exception as e:
        terminal_print(
            f"[ERROR] Phone link startup failed: {e}",
            RED
        )
        phone_link_running = False


def stop_phone_link_server():
    global phone_server, phone_server_thread, phone_link_running, phone_link_url, phone_last_phone_activity

    if not phone_link_running:
        return

    try:
        phone_server.shutdown()
        phone_server.server_close()
    except:
        pass

    phone_server = None
    phone_server_thread = None
    phone_link_running = False
    phone_link_url = ""
    phone_last_phone_activity = "Phone link disabled"

    terminal_print(
        "[AI] Phone link stopped.",
        YELLOW
    )
    add_log(
        "Phone link server stopped.",
        CYAN
    )


def update_phone_link_label():
    try:
        if phone_link_running and phone_link_label:
            phone_link_label.configure(
                text=f"PHONE LINK: {phone_link_url}"
            )
        elif phone_link_label:
            phone_link_label.configure(
                text="PHONE LINK: inactive"
            )
    except:
        pass


def initialize_radar_dots():
    global radar_dots
    radar_dots = []

    for _ in range(12):
        angle = random.uniform(0, math.pi * 2)
        radius = random.uniform(30, 110)
        radar_dots.append([angle, radius, random.randint(1, 3)])


# =========================================================
# VOICE ENGINE
# =========================================================

engine = pyttsx3.init()

engine.setProperty(
    "rate",
    120
)
engine.setProperty(
    "volume",
    1.0
)

speaking_event = threading.Event()


def voice_worker():

    global running

    while running:

        try:

            if voice_queue:

                text = voice_queue.popleft()

                speaking_event.set()
                try:
                    engine.stop()
                except Exception as e:
                    add_log(f"Voice engine stop error: {e}", RED)
                try:
                    engine.say(text)
                    engine.runAndWait()
                except Exception as e:
                    add_log(f"Voice playback error: {e}", RED)
                finally:
                    speaking_event.clear()

            time.sleep(0.1)

        except:
            speaking_event.clear()
            pass

threading.Thread(
    target=voice_worker,
    daemon=True
).start()

def split_speech_text(text, max_chunk=140):

    if not text:
        return []

    text = text.strip()
    if len(text) <= max_chunk:
        return [text]

    chunks = []
    current = ""
    separators = re.split(r'(?<=[.!?])\s+', text)

    for part in separators:
        if not part:
            continue
        if len(current) + len(part) + 1 <= max_chunk:
            current = (current + " " + part).strip()
        else:
            if current:
                chunks.append(current)
            if len(part) <= max_chunk:
                current = part
            else:
                for i in range(0, len(part), max_chunk):
                    chunk = part[i:i + max_chunk].strip()
                    if chunk:
                        chunks.append(chunk)
                current = ""

    if current:
        chunks.append(current)

    return chunks


def speak(text):

    if not voice_enabled:
        return

    for chunk in split_speech_text(text):
        if len(voice_queue) < 50:
            voice_queue.append(chunk)


def wait_for_speech(timeout=10):

    start = time.time()
    while voice_queue or speaking_event.is_set():
        time.sleep(0.05)
        if timeout and (time.time() - start) > timeout:
            break


def greet_user(name=None):

    try:

        hour = int(time.strftime("%H"))

        if 5 <= hour < 12:
            greeting = "Good morning"
        elif 12 <= hour < 17:
            greeting = "Good afternoon"
        elif 17 <= hour < 21:
            greeting = "Good evening"
        else:
            greeting = "Good night"

        if name:
            message = f"{greeting}, {name}."
        else:
            message = f"{greeting}."

        terminal_print(message, CYAN)
        add_log(f"Greeted user: {message}", CYAN)

        speak(message)
        wait_for_speech(None)

    except:
        pass


def play_startup_sequence(name=None):

    try:

        msg1 = "Initiating systems."
        msg2 = "Systems online."
        msg3 = "Shadow core stable."

        terminal_print(msg1, CYAN)
        add_log(msg1, CYAN)
        speak(msg1)
        wait_for_speech(None)

        terminal_print(msg2, CYAN)
        add_log(msg2, CYAN)
        speak(msg2)
        wait_for_speech(None)

        terminal_print(msg3, CYAN)
        add_log(msg3, CYAN)
        speak(msg3)
        wait_for_speech(None)

        greet_user(name)

        msg4 = "Welcome back, OMEN"

        terminal_print(msg4, CYAN)
        add_log(msg4, CYAN)

        speak(msg4)
        wait_for_speech(None)

        msg5 = "Awaiting your command"

        terminal_print(msg5, GREEN)
        add_log(msg5, GREEN)

        speak(msg5)
        wait_for_speech(None)

    except:
        pass

# =========================================================
# HUD LAYOUT
# =========================================================

# =========================================================
# TERMINAL PRINT
# =========================================================

def terminal_print(
    text,
    color=GREEN
):

    try:
        target = terminal if terminal is not None else None
        if target is None:
            target = activity_feed if "activity_feed" in globals() and activity_feed is not None else None
        if target is None:
            return

        target.configure(state="normal")
        if int(target.index("end-1c").split(".")[0]) > 220:
            target.delete("1.0", "25.0")
        target.insert("end", text + "\n")
        target.configure(state="disabled")
        target.see("end")
    except Exception:
        pass

# =========================================================
# LOGS
# =========================================================

def add_log(
    text,
    color=GREEN
):

    try:
        target = logs_box if "logs_box" in globals() and logs_box is not None else None
        if target is None:
            target = activity_feed if "activity_feed" in globals() and activity_feed is not None else None
        if target is None:
            return

        target.configure(state="normal")
        target.insert(
            "end",
            time.strftime("[%H:%M:%S] ") + text + "\n"
        )
        target.configure(state="disabled")
        target.see("end")
    except Exception:
        pass


build_hud_interface()


def clear_logs():
    try:
        target = logs_box if "logs_box" in globals() and logs_box is not None else None
        if target is None:
            target = activity_feed if "activity_feed" in globals() and activity_feed is not None else None
        if target is not None:
            target.configure(state="normal")
            target.delete("1.0", "end")
            target.configure(state="disabled")
    except:
        pass


def clear_terminal():
    try:
        target = terminal if "terminal" in globals() and terminal is not None else None
        if target is None:
            target = activity_feed if "activity_feed" in globals() and activity_feed is not None else None
        if target is not None:
            target.configure(state="normal")
            target.delete("1.0", "end")
            target.configure(state="disabled")
    except:
        pass

# =========================================================
# GPU MONITOR
# =========================================================

def get_gpu_usage():

    try:
        # NVIDIA GPU
        result = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=utilization.gpu,memory.used,memory.total",
                "--format=csv,noheader,nounits"
            ],
            encoding="utf-8"
        )

        gpu, mem_used, mem_total = result.strip().split(",")

        return {
            "type": "NVIDIA",
            "gpu": int(gpu.strip()),
            "used": int(mem_used.strip()),
            "total": int(mem_total.strip())
        }

    except Exception:
        try:
            # Fallback (CPU usage, NOT real GPU)
            return {
                "type": "AMD/Ryzen",
                "gpu": psutil.cpu_percent(),
                "used": None,
                "total": None
            }

        except Exception:
            return {
                "type": "UNKNOWN",
                "gpu": 0,
                "used": 0,
                "total": 0
            }

# =========================================================
# RADAR LINK ANIMATION

def draw_radar():

    global radar_angle

    if not running:
        return

    try:

        radar_canvas.delete("all")

        width = 260
        height = 180
        center_x = width / 2
        center_y = height / 2
        radius = 78

        for ring in [radius * 0.4, radius * 0.7, radius]:
            radar_canvas.create_oval(
                center_x - ring,
                center_y - ring,
                center_x + ring,
                center_y + ring,
                outline="#4a8f3a"
            )

        for i in range(0, 360, 45):
            angle = math.radians(i)
            x = center_x + math.cos(angle) * radius
            y = center_y + math.sin(angle) * radius
            radar_canvas.create_line(
                center_x,
                center_y,
                x,
                y,
                fill="#225c18"
            )

        for dot in radar_dots:
            dot[0] += 0.01
            if dot[0] > math.pi * 2:
                dot[0] -= math.pi * 2
            x = center_x + math.cos(dot[0]) * dot[1]
            y = center_y + math.sin(dot[0]) * dot[1]
            brightness = 180 + int(75 * math.sin(dot[0]))
            color = f"#{brightness:02x}{220:02x}{120:02x}"
            radar_canvas.create_oval(
                x - dot[2],
                y - dot[2],
                x + dot[2],
                y + dot[2],
                fill=color,
                outline=""
            )

        sweep_x = center_x + math.cos(radar_angle) * radius
        sweep_y = center_y + math.sin(radar_angle) * radius

        radar_canvas.create_line(
            center_x,
            center_y,
            sweep_x,
            sweep_y,
            fill="#d4af37",
            width=2
        )

        radar_angle += 0.05

    except:
        pass

    safe_after(
        90,
        draw_radar
    )

# =========================================================
# SYSTEM UPDATE
# =========================================================

def update_system():

    if not running:
        return

    try:

        cpu = psutil.cpu_percent(
            interval=None
        )

        ram = psutil.virtual_memory().percent

        if "cpu_label" in globals() and cpu_label is not None:
            cpu_label.configure(text=f"CPU: {cpu}%")
        if "ram_label" in globals() and ram_label is not None:
            ram_label.configure(text=f"RAM: {ram}%")

        gpu_stats = get_gpu_usage()

        gpu_info = gpu_stats

        if gpu_info:

            gpu_type = gpu_info.get("type", "Unknown")
            gpu_load = gpu_info.get("gpu", 0)

            if gpu_type == "NVIDIA":

                used = gpu_info.get("used", 0)
                total = gpu_info.get("total", 0)

                if "gpu_label" in globals() and gpu_label is not None:
                    gpu_label.configure(text=(f"GPU: {gpu_load}%  VRAM: {used}/{total} MB"))

            else:

                if "gpu_label" in globals() and gpu_label is not None:
                    gpu_label.configure(text=f"GPU: {gpu_type} | Load: {gpu_load}%")

        else:

            if "gpu_label" in globals() and gpu_label is not None:
                gpu_label.configure(text="GPU: Not detected")

        battery = psutil.sensors_battery()

        if battery:

            status = (
                "CHARGING ⚡"
                if battery.power_plugged
                else "BATTERY 🔋"
            )

            if "battery_label" in globals() and battery_label is not None:
                battery_label.configure(text=(f"BATTERY: {battery.percent}% {status}"))

        hostname = socket.gethostname()

        ip = socket.gethostbyname(
            hostname
        )

        if "ip_label" in globals() and ip_label is not None:
            ip_label.configure(text=f"IP: {ip}")

        try:
            update_phone_link_label()
        except:
            pass

        if "clock_label" in globals() and clock_label is not None:
            clock_label.configure(text=time.strftime("%I:%M:%S %p"))
        if "date_label" in globals() and date_label is not None:
            date_label.configure(text=time.strftime("%d-%m-%Y"))

    except:
        pass

    safe_after(
        1000,
        update_system
    )

# =========================================================
# GRAPH UPDATE
# =========================================================

def update_graph():

    if not running:
        return

    try:

        cpu = psutil.cpu_percent(
            interval=None
        )

        ram = psutil.virtual_memory().percent

        cpu_data.append(cpu)

        ram_data.append(ram)

        line_cpu.set_data(
            range(len(cpu_data)),
            cpu_data
        )

        line_ram.set_data(
            range(len(ram_data)),
            ram_data
        )

        ax.set_xlim(
            0,
            len(cpu_data) - 1
        )

        canvas.draw_idle()

    except:
        pass

    safe_after(
        1600,
        update_graph
    )

# =========================================================
# STATUS PULSE
# =========================================================

def ai_pulse():

    try:

        current = status_label.cget(
            "text_color"
        )

        if current == GREEN:

            status_label.configure(
                text_color=CYAN
            )

        else:

            status_label.configure(
                text_color=GREEN
            )

    except:
        pass

    safe_after(
        700,
        ai_pulse
    )


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
        # Build context with personality, memory, and ethical foundation
        personality = get_personality_prompt()
        memory_ctx = get_memory_context()
        ethical_context = get_ethical_foundation_prompt()
        full_prompt = f"{ethical_context}\n\n{personality}\n\n{memory_ctx}\n\nUser: {query}"
        
        # Use universal AI query with automatic fallback
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

process_command = command_processing_module.process_command


def _legacy_process_command(cmd):

    global chrome_profiles
    global history_index

    cmd = cmd.lower().strip()

    terminal_print(
        f"COMMAND> {cmd}",
        CYAN
    )

    command_history.append(cmd)
    update_command_history_display()
    record_memory("command", cmd)

    history_index = len(command_history)

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

def handle(event=None):

    cmd = command_entry.get().strip()

    command_entry.delete(
        0,
        "end"
    )

    if cmd:
        hud_current_task = cmd
        set_hud_state("LISTENING", cmd)
        def worker():
            set_hud_state("PROCESSING", cmd)
            try:
                process_command(cmd)
            except Exception as exc:
                set_hud_state("ERROR", str(exc))
                terminal_print(f"[HUD] Command error: {exc}", RED)
            else:
                set_hud_state("RESPONDING", cmd)
        threading.Thread(target=worker, daemon=True).start()

    return "break"

command_entry.bind(
    "<Return>",
    handle
)

# =========================================================
# SMART CURSOR SYSTEM
# =========================================================

def slash_jump(event):

    current = command_entry.get()

    if "/" not in current:

        command_entry.insert(
            "insert",
            "/"
        )

    command_entry.icursor("end")

    return "break"

command_entry.bind(
    "<KeyPress-/>",
    slash_jump
)

# =========================================================
# TERMINAL SHORTCUTS
# =========================================================

command_history = []

history_index = -1

def history_up(event):

    global history_index

    if not command_history:
        return "break"

    history_index = max(
        0,
        history_index - 1
    )

    command_entry.delete(
        0,
        "end"
    )

    command_entry.insert(
        0,
        command_history[history_index]
    )

    return "break"

def history_down(event):

    global history_index

    if not command_history:
        return "break"

    history_index = min(
        len(command_history) - 1,
        history_index + 1
    )

    command_entry.delete(
        0,
        "end"
    )

    command_entry.insert(
        0,
        command_history[history_index]
    )

    return "break"

command_entry.bind(
    "<Up>",
    history_up
)

command_entry.bind(
    "<Down>",
    history_down
)

# =========================================================
# BLINKING CURSOR EFFECT
# =========================================================

cursor_visible = True

def cursor_blink():

    global cursor_visible

    if not running:
        return

    try:

        if cursor_visible:

            command_entry.configure(
                border_color=GREEN
            )

        else:

            command_entry.configure(
                border_color="#101010"
            )

        cursor_visible = not cursor_visible

    except:
        pass

    safe_after(
        500,
        cursor_blink
    )

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

app.protocol(
    "WM_DELETE_WINDOW",
    shutdown
)

# =========================================================
# START SCREEN
# =========================================================

def show_api_key_prompt():
    saved_key = load_saved_api_key()
    if saved_key:
        return

    popup = tk.Toplevel(app)
    popup.title("AI API Key")
    popup.geometry("480x220+450+220")
    popup.configure(bg=BG)
    popup.resizable(False, False)
    popup.attributes("-topmost", True)
    popup.grab_set()
    popup.focus_force()

    tk.Label(
        popup,
        text="Enter your OpenAI API key",
        fg=YELLOW,
        bg=BG,
        font=("Consolas", 16, "bold")
    ).pack(pady=(18, 8))

    tk.Label(
        popup,
        text="It will be saved locally and reused until you change it.",
        fg=CYAN,
        bg=BG,
        font=("Consolas", 10)
    ).pack(pady=(0, 12))

    entry_var = tk.StringVar()
    entry = tk.Entry(
        popup,
        textvariable=entry_var,
        show="*",
        width=56,
        font=("Consolas", 11)
    )
    entry.pack(padx=20, pady=8)

    def save_and_close():
        key = entry_var.get().strip()
        if key:
            save_api_key(key)
            terminal_print("[AI] API key saved locally.", GREEN)
        popup.destroy()

    button_frame = tk.Frame(popup, bg=BG)
    button_frame.pack(pady=(10, 8))

    ctk.CTkButton(
        button_frame,
        text="Save API Key",
        width=140,
        height=32,
        fg_color="#d4af37",
        text_color="#050505",
        hover_color="#f0c84b",
        corner_radius=10,
        command=save_and_close
    ).pack(side="left", padx=6)

    ctk.CTkButton(
        button_frame,
        text="Skip",
        width=100,
        height=32,
        fg_color="#2a2a21",
        hover_color="#3a3a31",
        text_color=YELLOW,
        corner_radius=10,
        command=popup.destroy
    ).pack(side="left", padx=6)

    popup.protocol("WM_DELETE_WINDOW", popup.destroy)
    popup.mainloop()


def start_omen():

    app.deiconify()
    app.lift()
    app.focus_force()

    # Bring window to foreground reliably (briefly set topmost)
    try:
        try:
            app.state('normal')
        except:
            pass
        try:
            app.update_idletasks()
            app.update()
        except:
            pass
        try:
            app.attributes("-topmost", True)
            app.lift()
            app.focus_force()
            # remove topmost shortly after to allow normal window behavior
            app.after(150, lambda: app.attributes("-topmost", False))
        except:
            pass
    except:
        pass

    show_api_key_prompt()

    terminal_print(
        "█ OMEN SHADOW CORE ONLINE",
        CYAN
    )

    terminal_print(
        "█ GPU MONITOR ACTIVE",
        GREEN
    )

    terminal_print(
        "█ VOICE ENGINE READY",
        GREEN
    )

    terminal_print(
        "█ STABLE HUD ENGINE ACTIVE",
        GREEN
    )

    terminal_print(
        "█ CYBER GLOBE CONNECTED",
        YELLOW
    )

    terminal_print(
        "█ CHROME PROFILE SYSTEM READY",
        GREEN
    )

    terminal_print(
        "█ AI SEARCH SYSTEM READY",
        CYAN
    )

    terminal_print(
        f"█ AI VERSION: {AI_VERSION}",
        CYAN
    )

    terminal_print(
        "█ MUSIC AI SYSTEM READY",
        CYAN
    )

    terminal_print(
        "█ Awaiting command...",
        GREEN
    )

    add_log(
        "Neural core initialized"
    )

    add_log(
        "HUD engine stable"
    )

    add_log(
        "Security systems online"
    )

    add_log(
        "AI search system online",
        CYAN
    )

    add_log(
        "Music system online",
        CYAN
    )

    detect_chrome_profiles()
    load_memory()
    load_notes()
    record_memory("startup", "OMEN started")
    load_plugins()
    update_plugins_panel()
    if loaded_plugins:
        terminal_print(f"[AI] Loaded plugins: {', '.join(loaded_plugins)}", CYAN)
    else:
        terminal_print("[AI] No plugins loaded.", YELLOW)
    initialize_radar_dots()

    if chrome_profiles:
        add_log(
            f"Detected Chrome profiles: {', '.join(chrome_profiles.values())}",
            CYAN
        )

    threading.Thread(
        target=play_startup_sequence,
        daemon=True
    ).start()

    update_system()
    auto_update_check()
    update_graph()
    ai_pulse()
    draw_cyber_globe()
    draw_radar()
    cursor_blink()
    engine_heartbeat()

    app.mainloop()


def show_start_screen():

    splash = tk.Toplevel(app)
    splash.title("REVERIUS OPIUM")
    splash.geometry("620x700+360+100")
    splash.configure(bg=BG)
    splash.resizable(False, False)
    splash.attributes("-topmost", True)
    splash.grab_set()
    splash.focus_force()

    # Title
    title_label = tk.Label(
        splash,
        text="REVERIUS OPIUM v1.0",
        fg=YELLOW,
        bg=BG,
        font=("Consolas", 24, "bold")
    )
    title_label.pack(pady=(20, 12))

    # Initialization sequence
    init_label = tk.Label(
        splash,
        text="Initializing Cognitive Matrix...",
        fg=CYAN,
        bg=BG,
        font=("Consolas", 12)
    )
    init_label.pack(pady=(0, 12))

    # Personality status
    status_text = "\n".join([
        f"[{mode.ljust(12)}] ONLINE"
        for mode in PERSONALITY_MODES
    ])
    status_label = tk.Label(
        splash,
        text=status_text,
        fg=GREEN,
        bg=BG,
        font=("Consolas", 11),
        justify="left"
    )
    status_label.pack(pady=(0, 16))

    # Sync complete
    sync_label = tk.Label(
        splash,
        text="Neural Synchronization Complete.",
        fg=CYAN,
        bg=BG,
        font=("Consolas", 12, "bold")
    )
    sync_label.pack(pady=(0, 4))

    welcome_label = tk.Label(
        splash,
        text="Welcome, Commander.",
        fg=YELLOW,
        bg=BG,
        font=("Consolas", 14, "bold")
    )
    welcome_label.pack(pady=(0, 16))

    # Mode selector label
    mode_label = tk.Label(
        splash,
        text="Choose your mode:",
        fg=YELLOW,
        bg=BG,
        font=("Consolas", 12, "bold")
    )
    mode_label.pack(pady=(0, 8))

    # Personality buttons
    button_frame = tk.Frame(splash, bg=BG)
    button_frame.pack(pady=(0, 20))

    def on_personality_selected(personality):
        def handler():
            global current_personality
            current_personality = personality
            try:
                apply_theme(personality)
            except:
                pass
            try:
                splash.destroy()
            except:
                pass
            start_omen()
        return handler

    for i, mode in enumerate(PERSONALITY_MODES):
        row = i // 2
        col = i % 2
        btn = ctk.CTkButton(
            button_frame,
            text=f"[{mode}]",
            width=220,
            height=36,
            fg_color="#10100e",
            hover_color="#2a2a21",
            text_color=YELLOW,
            corner_radius=10,
            font=("Consolas", 11, "bold"),
            command=on_personality_selected(mode)
        )
        btn.grid(row=row, column=col, padx=6, pady=6)

    # Cancel button
    cancel_btn = ctk.CTkButton(
        splash,
        text="EXIT",
        width=120,
        height=32,
        fg_color="#2a2a21",
        hover_color="#3a3a31",
        text_color=YELLOW,
        corner_radius=10,
        command=lambda: on_cancel_pressed(splash)
    )
    cancel_btn.pack(pady=(0, 16))

    def on_close():
        try:
            splash.destroy()
        except:
            pass
        try:
            app.destroy()
        except:
            pass
        sys.exit(0)

    splash.protocol("WM_DELETE_WINDOW", on_close)
    splash.mainloop()


def on_start_pressed(splash):
    try:
        splash.destroy()
    except:
        pass
    start_omen()


def on_cancel_pressed(splash):
    try:
        splash.destroy()
    except:
        pass
    try:
        app.destroy()
    except:
        pass
    sys.exit(0)


if __name__ == "__main__":
    try:
        apply_theme(current_personality)
    except:
        pass
    # Start main UI directly (skip splash/startup window)
    start_omen()