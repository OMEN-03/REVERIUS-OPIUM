from config.settings import SETTINGS
from modules.utilities import *

# =========================================================
# CYBER GLOBE
# =========================================================

def rotate_y(x, z, angle):
    new_x = (
        x * math.cos(angle)
        - z * math.sin(angle)
    )

    new_z = (
        x * math.sin(angle)
        + z * math.cos(angle)
    )

    return new_x, new_z


def rotate_x(y, z, angle):
    new_y = (
        y * math.cos(angle)
        - z * math.sin(angle)
    )

    new_z = (
        y * math.sin(angle)
        + z * math.cos(angle)
    )

    return new_y, new_z


def draw_cyber_globe():

    global rotation_y

    if not running:
        return

    try:

        globe_canvas.delete("all")

        for sx, sy, size in globe_stars:

            globe_canvas.create_oval(
                sx,
                sy,
                sx + size,
                sy + size,
                fill=CYAN,
                outline=""
            )

        points = []

        for point in globe_points:

            x, y, z = point

            x, z = rotate_y(
                x,
                z,
                rotation_y
            )

            y, z = rotate_x(
                y,
                z,
                rotation_x
            )

            distance = 260

            scale = (
                distance
                / (distance + z)
            )

            px = (
                x * scale
                + GLOBE_WIDTH // 2
            )

            py = (
                y * scale
                + GLOBE_HEIGHT // 2
            )

            points.append((px, py, z))

        points.sort(
            key=lambda p: p[2]
        )

        for i in range(0, len(points), 6):

            x1, y1, z1 = points[i]

            for j in range(
                i + 1,
                min(i + 10, len(points))
            ):

                x2, y2, z2 = points[j]

                dist = math.sqrt(
                    (x2 - x1) ** 2
                    + (y2 - y1) ** 2
                )

                if dist < 24:

                    globe_canvas.create_line(
                        x1,
                        y1,
                        x2,
                        y2,
                        fill="#2e9a9f"
                    )

        for px, py, z in points:

            brightness = int(
                max(
                    80,
                    min(255, 180 + z)
                )
            )

            color = (
                f"#00{brightness:02x}{brightness:02x}"
            )

            globe_canvas.create_oval(
                px - 1,
                py - 1,
                px + 1,
                py + 1,
                fill=color,
                outline=""
            )

        for y in range(
            0,
            GLOBE_HEIGHT,
            5
        ):

            globe_canvas.create_line(
                0,
                y,
                GLOBE_WIDTH,
                y,
                fill="#1b160f"
            )

        center_x = GLOBE_WIDTH // 2
        center_y = GLOBE_HEIGHT // 2

        globe_canvas.create_oval(
            center_x - GLOBE_RADIUS,
            center_y - GLOBE_RADIUS,
            center_x + GLOBE_RADIUS,
            center_y + GLOBE_RADIUS,
            outline=CYAN,
            width=2
        )

        globe_canvas.create_oval(
            center_x - GLOBE_RADIUS + 12,
            center_y - GLOBE_RADIUS + 12,
            center_x + GLOBE_RADIUS - 12,
            center_y + GLOBE_RADIUS - 12,
            outline=CYAN,
            width=1
        )

        globe_canvas.create_arc(
            center_x - GLOBE_RADIUS - 10,
            center_y - GLOBE_RADIUS - 10,
            center_x + GLOBE_RADIUS + 10,
            center_y + GLOBE_RADIUS + 10,
            start=30,
            extent=120,
            style="arc",
            outline=CYAN,
            width=1
        )

        globe_canvas.create_arc(
            center_x - GLOBE_RADIUS - 10,
            center_y - GLOBE_RADIUS - 10,
            center_x + GLOBE_RADIUS + 10,
            center_y + GLOBE_RADIUS + 10,
            start=210,
            extent=120,
            style="arc",
            outline=CYAN,
            width=1
        )

        rotation_y += 0.03

    except Exception:
        pass

    safe_after(
        65,
        draw_cyber_globe
    )

# =========================================================
# TERMINAL PRINT
# =========================================================

def terminal_print(
    text,
    color=GREEN
):

    try:

        tag = f"tag_{color}"

        terminal.tag_config(
            tag,
            foreground=color
        )

        if int(
            terminal.index(
                "end-1c"
            ).split(".")[0]
        ) > 220:

            terminal.delete(
                "1.0",
                "25.0"
            )

        terminal.insert(
            "end",
            text + "\n",
            tag
        )

        terminal.see("end")

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

        tag = f"log_{color}"

        logs_box.tag_config(
            tag,
            foreground=color
        )

        timestamp = time.strftime(
            "[%H:%M:%S] "
        )

        logs_box.insert(
            "end",
            timestamp + text + "\n",
            tag
        )

        logs_box.see("end")

    except Exception:
        pass


def clear_logs():
    try:
        logs_box.delete("1.0", "end")
    except Exception:
        pass


def clear_terminal():
    try:
        terminal.delete("1.0", "end")
    except Exception:
        pass

# =========================================================
# GPU MONITOR
# =========================================================

def get_gpu_usage():

    try:
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
# =========================================================

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

    except Exception:
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

        cpu_label.configure(
            text=f"CPU: {cpu}%"
        )

        ram_label.configure(
            text=f"RAM: {ram}%"
        )

        gpu_stats = get_gpu_usage()

        gpu_info = gpu_stats

        if gpu_info:

            gpu_type = gpu_info.get("type", "Unknown")
            gpu_load = gpu_info.get("gpu", 0)

            if gpu_type == "NVIDIA":

                used = gpu_info.get("used", 0)
                total = gpu_info.get("total", 0)

                gpu_label.configure(
                    text=(
                        f"GPU: {gpu_load}%  "
                        f"VRAM: {used}/{total} MB"
                    )
                )

            else:

                gpu_label.configure(
                    text=f"GPU: {gpu_type} | Load: {gpu_load}%"
                )

        else:

            gpu_label.configure(
                text="GPU: Not detected"
            )

        battery = psutil.sensors_battery()

        if battery:

            status = (
                "CHARGING âš¡"
                if battery.power_plugged
                else "BATTERY ðŸ”‹"
            )

            battery_label.configure(
                text=(
                    f"BATTERY: "
                    f"{battery.percent}% "
                    f"{status}"
                )
            )

        hostname = socket.gethostname()

        ip = socket.gethostbyname(
            hostname
        )

        ip_label.configure(
            text=f"IP: {ip}"
        )

        try:
            update_phone_link_label()
        except Exception:
            pass

        clock_label.configure(
            text=time.strftime(
                "%I:%M:%S %p"
            )
        )

        date_label.configure(
            text=time.strftime(
                "%d-%m-%Y"
            )
        )

    except Exception:
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

    except Exception:
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

    except Exception:
        pass

    safe_after(
        700,
        ai_pulse
    )

# =========================================================
# PHONE LINK STATUS
# =========================================================

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
    except Exception:
        pass


def initialize_radar_dots():
    global radar_dots
    radar_dots = []

    for _ in range(12):
        angle = random.uniform(0, math.pi * 2)
        radius = random.uniform(30, 110)
        radar_dots.append([angle, radius, random.randint(1, 3)])
