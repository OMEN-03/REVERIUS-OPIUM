from config.settings import SETTINGS
from modules.ai_backend import *
from modules.memory import *

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