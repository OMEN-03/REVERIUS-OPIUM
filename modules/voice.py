from config.settings import SETTINGS
from modules.utilities import *
from modules.system_modules import terminal_print, add_log

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

    if not SETTINGS.enable_voice:
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