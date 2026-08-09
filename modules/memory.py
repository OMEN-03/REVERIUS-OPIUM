from __future__ import annotations

from collections import deque
import json
import time
from pathlib import Path
from typing import Any

from config.settings import SETTINGS

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
            except (OSError, json.JSONDecodeError, ValueError):
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
        except OSError:
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
# MEMORY & NOTES STORAGE
# =========================================================

notes = []
notes_file = Path.home() / "OMEN_notes.txt"
memory_entries = {}
memory_file = Path.home() / "OMEN_memory.json"

current_personality = "OMEN SHADOW CORE"
voice_enabled = True

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


def save_note(text):
    global notes
    try:
        notes.append(text)
        with open(notes_file, "a", encoding="utf-8") as f:
            f.write(text + "\n")
        record_memory("note_saved", text)
    except OSError as exc:
        add_log(f"Note save error: {exc}", RED)


def clear_memory():
    global memory_entries
    try:
        memory_entries = {}
        save_memory()
        terminal_print("[OMEN] Memory cleared.", GREEN)
        add_log("Memory cleared", CYAN)
        record_memory("memory_cleared")
    except OSError as exc:
        add_log(f"Memory clear error: {exc}", RED)


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
    except OSError as exc:
        add_log(f"Forget note error: {exc}", RED)


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
    except (OSError, json.JSONDecodeError, ValueError):
        memory_entries = {}


def save_memory():
    try:
        with open(memory_file, "w", encoding="utf-8") as f:
            json.dump(memory_entries, f, indent=2)
    except OSError:
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
    except (NameError, AttributeError):
        pass
    try:
        update_personality_ui(mode)
    except (NameError, AttributeError):
        pass
    try:
        personality_selector.set(mode)
    except (NameError, AttributeError):
        pass
    try:
        if voice_enabled:
            speak(f"{mode} activated.")
    except (NameError, AttributeError):
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