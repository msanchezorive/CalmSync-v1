import customtkinter as ctk
import subprocess

# ==============================
# CONFIG GENERAL
# ==============================

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# Paleta inspirada en tablet dashboard, muy suave
APP_BG      = "#F4F3FF"   # fondo general lila muy claro
HEADER_BG   = "#F1EFFF"   # header
FOOTER_BG   = "#F1EFFF"
CARD_BG     = "#FFFFFF"   # tarjetas principales
SIDE_BG     = "#F7F5FF"   # panel lateral

ACCENT      = "#6762D9"   # morado calmado
ACCENT_SOFT = "#E2E0FF"   # pill suave

TEXT_MAIN   = "#25263A"
TEXT_SOFT   = "#8687A3"

# Tipos de letra (serif para títulos, sans para cuerpo)
TITLE_FONT         = ("Times New Roman", 38, "bold")
SUBTITLE_FONT      = ("Helvetica", 13)
SECTION_TITLE_FONT = ("Times New Roman", 18, "bold")
STEP_TITLE_FONT    = ("Times New Roman", 16, "bold")
BODY_FONT          = ("Helvetica", 12)
SMALL_FONT         = ("Helvetica", 11)

app = ctk.CTk()
app.title("CalmSync")
app.geometry("1024x768")
app.resizable(False, False)
app.attributes("-fullscreen", True)
app.configure(fg_color=APP_BG)

# ==============================
# DEFINICIÓN DE STEPS (FLOW 1–5)
# ==============================

STEPS_CONFIG = [
    {
        "id": 1,
        "code": "CAL",
        "title": "Calibration",
        "subtitle": "Check signal quality and prepare your baseline.",
        "btn_text": "Begin Calibration",
        "script": "initial_calibration.py",
        "shortcut": "1",
        "approx": "~8 min",
    },
    {
        "id": 2,
        "code": "WAV",
        "title": "Bars Visualizer",
        "subtitle": "See your Alpha/Beta waves in real time.",
        "btn_text": "Watch Your Waves",
        "script": "bars_visualizer.py",
        "shortcut": "2",
        "approx": "flexible",
    },
    {
        "id": 3,
        "code": "NF",
        "title": "Neurofeedback Game (pre)",
        "subtitle": "Play before Stroop to capture your initial state.",
        "btn_text": "Play Neurofeedback",
        "script": "neurofeedback_game.py",
        "shortcut": "3",
        "approx": "~5–10 min",
    },
    {
        "id": 4,
        "code": "ST",
        "title": "Stroop Game",
        "subtitle": "Test cognitive control in a gentle way.",
        "btn_text": "Take Stroop Test",
        "script": "test_stroop_tactil.py",
        "shortcut": "4",
        "approx": "~5 min",
    },
    {
        "id": 5,
        "code": "NF",
        "title": "Neurofeedback Game (post)",
        "subtitle": "Repeat the game and see how your brain changed.",
        "btn_text": "Play Neurofeedback Again",
        "script": "neurofeedback_game.py",
        "shortcut": "5",
        "approx": "~5–10 min",
    },
]

# Estados: ready / locked / running / done
steps_state = {}
for step in STEPS_CONFIG:
    if step["id"] == 1:
        steps_state[step["id"]] = {"status": "ready", "process": None}
    else:
        steps_state[step["id"]] = {"status": "locked", "process": None}

step_widgets = {}
button_refs = []

# ==============================
# LÓGICA DE FLUJO
# ==============================

def cerrar_app(event=None):
    app.quit()
    app.destroy()

def start_step(step_id: int):
    """Lanza el script de un paso si está listo."""
    state = steps_state[step_id]
    if state["status"] not in ("ready", "done"):
        return

    cfg = next(s for s in STEPS_CONFIG if s["id"] == step_id)
    try:
        proc = subprocess.Popen(["python", cfg["script"]])
    except Exception as e:
        print(f"Error launching {cfg['script']}: {e}")
        return

    state["process"] = proc
    state["status"] = "running"
    refresh_ui()

def unlock_next_step(current_id: int):
    """Desbloquea el siguiente step en el flujo 1–5."""
    ids = [s["id"] for s in STEPS_CONFIG]
    if current_id not in ids:
        return
    idx = ids.index(current_id)
    if idx + 1 < len(ids):
        next_id = ids[idx + 1]
        if steps_state[next_id]["status"] == "locked":
            steps_state[next_id]["status"] = "ready"

def get_progress():
    """Devuelve (step_actual, total_steps)."""
    ids = [s["id"] for s in STEPS_CONFIG]
    total = len(ids)
    # actual = primer step no completado, o el último si todos done
    if all(steps_state[i]["status"] == "done" for i in ids):
        current = ids[-1]
    else:
        current = next(i for i in ids if steps_state[i]["status"] != "done")
    return current, total

def poll_processes():
    """Comprueba periódicamente si los scripts han terminado."""
    for step in STEPS_CONFIG:
        sid = step["id"]
        state = steps_state[sid]
        proc = state["process"]
        if proc is not None:
            ret = proc.poll()
            if ret is not None:
                state["process"] = None
                state["status"] = "done"
                unlock_next_step(sid)
                refresh_ui()
    app.after(2000, poll_processes)

# ==============================
# HEADER
# ==============================

main_frame = ctk.CTkFrame(app, fg_color=APP_BG, corner_radius=0)
main_frame.pack(fill="both", expand=True)

header_frame = ctk.CTkFrame(
    main_frame,
    fg_color=HEADER_BG,
    corner_radius=0,
    height=110,
)
header_frame.pack(fill="x", padx=0, pady=0)
header_frame.pack_propagate(False)

# BPM button (esquina izq)
heart_button = ctk.CTkButton(
    header_frame,
    text="BPM ♥",            # corazón + espacio + BPM
    font=("Helvetica", 14, "bold"),
    fg_color="white",
    hover_color="#EBE9FF",
    text_color=ACCENT,        # mismo morado que el resto
    width=80,                 # un pelín más ancho para que quepa
    height=30,
    corner_radius=18,
    command=lambda: subprocess.Popen(["python", "frecuencia_cardiaca.py"]),
    cursor="hand2",
    border_width=1,
    border_color="#D3D0FF"
)
heart_button.place(x=22, y=24)

# Close button (gris suave)
close_button = ctk.CTkButton(
    header_frame,
    text="✕",
    font=("Helvetica", 18, "bold"),
    fg_color="white",
    hover_color="#EAE8F7",
    text_color="#9795AA",
    width=44,
    height=30,
    corner_radius=18,
    command=cerrar_app,
    cursor="hand2",
    border_width=1,
    border_color="#D1CFDF"
)
close_button.place(relx=1.0, x=-70, y=24)

title_container = ctk.CTkFrame(header_frame, fg_color="transparent")
title_container.pack(expand=True)

title_label = ctk.CTkLabel(
    title_container,
    text="CalmSync",
    font=TITLE_FONT,
    text_color="#4F4A8F",
)
title_label.pack(anchor="center")

subtitle_label = ctk.CTkLabel(
    title_container,
    text="Real-time neurofeedback to rethink anxiety.",
    font=SUBTITLE_FONT,
    text_color=TEXT_SOFT
)
subtitle_label.pack(anchor="center", pady=(2, 0))

# ==============================
# ZONA CENTRAL (DOS COLUMNAS)
# ==============================

center_frame = ctk.CTkFrame(main_frame, fg_color=APP_BG)
center_frame.pack(fill="both", expand=True, padx=64, pady=(24, 16))

card_outer = ctk.CTkFrame(
    center_frame,
    fg_color=CARD_BG,
    corner_radius=22,
    border_width=1,
    border_color="#DBD8F2"
)
card_outer.pack(expand=True, fill="both")

inner = ctk.CTkFrame(card_outer, fg_color="transparent")
inner.pack(expand=True, fill="both", padx=20, pady=16)

inner.grid_columnconfigure(0, weight=1)
inner.grid_columnconfigure(1, weight=2)
inner.grid_rowconfigure(0, weight=1)

# ----- COLUMNA IZQUIERDA: Welcome / Flow -----

left_panel = ctk.CTkFrame(
    inner,
    fg_color=SIDE_BG,
    corner_radius=18
)
left_panel.grid(row=0, column=0, sticky="nsew", padx=(4, 10), pady=4)

left_inner = ctk.CTkFrame(left_panel, fg_color="transparent")
left_inner.pack(expand=True, fill="both", padx=18, pady=16)

welcome_label = ctk.CTkLabel(
    left_inner,
    text="Welcome to CalmSync",
    font=SECTION_TITLE_FONT,
    text_color=TEXT_MAIN
)
welcome_label.pack(anchor="w", pady=(0, 6))

welcome_text = (
    "CalmSync uses EEG-based neurofeedback to\n"
    "observe and gently shift your mental state.\n"
    "This showroom session is designed as a closed loop:"
)
welcome_body = ctk.CTkLabel(
    left_inner,
    text=welcome_text,
    font=BODY_FONT,
    text_color=TEXT_SOFT,
    justify="left"
)
welcome_body.pack(anchor="w", pady=(0, 10))

flow_label = ctk.CTkLabel(
    left_inner,
    text="Session flow",
    font=("Times New Roman", 14, "bold"),
    text_color=TEXT_MAIN
)
flow_label.pack(anchor="w", pady=(0, 4))

flow_lines = [
    "1 → Calibrate sensor & baseline.",
    "2 → Watch your Alpha/Beta ratio in real time.",
    "3 → Play the Neurofeedback game (pre-Stroop).",
    "4 → Run the Stroop test to gently raise demand.",
    "5 → Play Neurofeedback again and compare\n     before/after mental state.",
]

for line in flow_lines:
    lbl = ctk.CTkLabel(
        left_inner,
        text=line,
        font=BODY_FONT,
        text_color=TEXT_SOFT,
        justify="left"
    )
    lbl.pack(anchor="w")

tip_label = ctk.CTkLabel(
    left_inner,
    text="\nTip: Sit comfortably, relax your shoulders\nand breathe slowly throughout the session.",
    font=SMALL_FONT,
    text_color=TEXT_SOFT,
    justify="left"
)
tip_label.pack(anchor="w", pady=(6, 0))

# ----- COLUMNA DERECHA: cards de steps -----

right_panel = ctk.CTkFrame(inner, fg_color="transparent")
right_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 4), pady=4)

# 3 filas: 0 = header, 1 = subtítulo, 2 = lista de steps
right_panel.grid_rowconfigure(0, weight=0)
right_panel.grid_rowconfigure(1, weight=0)
right_panel.grid_rowconfigure(2, weight=1)
right_panel.grid_columnconfigure(0, weight=1)

# Fila 0: título + progreso
header_right = ctk.CTkFrame(right_panel, fg_color="transparent")
header_right.grid(row=0, column=0, sticky="ew", pady=(0, 4), padx=2)

session_title = ctk.CTkLabel(
    header_right,
    text="Session · Relax & Focus",
    font=SECTION_TITLE_FONT,
    text_color=TEXT_MAIN
)
session_title.pack(side="left", anchor="w")

progress_label = ctk.CTkLabel(
    header_right,
    text="",
    font=SMALL_FONT,
    text_color=TEXT_SOFT
)
progress_label.pack(side="right", anchor="e")

# Fila 1: subtítulo
sub_right = ctk.CTkLabel(
    right_panel,
    text="Follow the steps in order for a full before/after experience.",
    font=BODY_FONT,
    text_color=TEXT_SOFT,
    anchor="w",
    justify="left"
)
sub_right.grid(row=1, column=0, sticky="w", pady=(0, 8), padx=2)

# Fila 2: contenedor de cards
steps_container = ctk.CTkFrame(right_panel, fg_color="transparent")
steps_container.grid(row=2, column=0, sticky="nsew", pady=(4, 0))
steps_container.grid_columnconfigure(0, weight=1)
for r in range(5):
    steps_container.grid_rowconfigure(r, weight=1, uniform="rows")

# Contenedor de cards
steps_container = ctk.CTkFrame(right_panel, fg_color="transparent")
steps_container.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
steps_container.grid_columnconfigure(0, weight=1)
for r in range(5):
    steps_container.grid_rowconfigure(r, weight=1, uniform="rows")

# ==============================
# CREAR CARDS DE STEPS
# ==============================

def create_step_cards():
    for idx, cfg in enumerate(STEPS_CONFIG):
        sid = cfg["id"]

        frame = ctk.CTkFrame(
            steps_container,
            fg_color=CARD_BG,
            corner_radius=18,
            border_width=1,
            border_color="#E0DEF5"
        )
        step_widgets[sid] = {
            "frame": frame,
            "icon": None,
            "title": None,
            "subtitle": None,
            "button": None,
            "status": None,
        }

        frame.grid(row=idx, column=0, padx=2, pady=6, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=0)

        # Lado izquierdo: icon bubble + texto
        left = ctk.CTkFrame(frame, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(16, 8), pady=10)

        # "iconito" circular con código (CAL, WAV, NF, ST...)
        icon = ctk.CTkLabel(
            left,
            text=cfg["code"],
            font=("Helvetica", 11, "bold"),
            text_color=ACCENT,
            fg_color=ACCENT_SOFT,
            corner_radius=999,
            width=40,
            height=24
        )
        icon.pack(anchor="w")

        title_label = ctk.CTkLabel(
            left,
            text=cfg["title"],
            font=STEP_TITLE_FONT,
            text_color=TEXT_MAIN
        )
        title_label.pack(anchor="w", pady=(4, 0))

        subtitle_label = ctk.CTkLabel(
            left,
            text=cfg["subtitle"],
            font=BODY_FONT,
            text_color=TEXT_SOFT,
            justify="left"
        )
        subtitle_label.pack(anchor="w", pady=(1, 0))

        status_label = ctk.CTkLabel(
            left,
            text="",
            font=SMALL_FONT,
            text_color=TEXT_SOFT
        )
        status_label.pack(anchor="w", pady=(2, 0))

        # Lado derecho: botón “burbuja”
        right = ctk.CTkFrame(frame, fg_color="transparent")
        right.grid(row=0, column=1, sticky="e", padx=(0, 16), pady=10)

        btn = ctk.CTkButton(
            right,
            text=cfg["btn_text"],
            font=("Helvetica", 13, "bold"),
            text_color="white",
            fg_color=ACCENT,
            hover_color="#5751C7",
            corner_radius=20,
            width=190,
            height=34,
            command=lambda sid=sid: start_step(sid),
            cursor="hand2"
        )
        btn.pack(anchor="e")

        step_widgets[sid]["icon"] = icon
        step_widgets[sid]["title"] = title_label
        step_widgets[sid]["subtitle"] = subtitle_label
        step_widgets[sid]["button"] = btn
        step_widgets[sid]["status"] = status_label

        # Atajos de teclado (1–5)
        button_refs.append(
            (btn, cfg["shortcut"], lambda sid=sid: start_step(sid))
        )

def refresh_ui():
    current_step, total_steps = get_progress()
    progress_label.configure(
        text=f"Step {current_step} of {total_steps} · approx 15–20 min total"
    )

    for cfg in STEPS_CONFIG:
        sid = cfg["id"]
        w = step_widgets[sid]
        state = steps_state[sid]
        status = state["status"]

        frame = w["frame"]
        icon = w["icon"]
        btn = w["button"]
        status_lbl = w["status"]

        # Reset estilo base
        frame.configure(border_color="#E0DEF5")
        icon.configure(text_color=ACCENT, fg_color=ACCENT_SOFT)
        btn.configure(text=cfg["btn_text"], fg_color=ACCENT, state="normal")
        status_text = ""

        if status == "locked":
            btn.configure(state="disabled", fg_color="#D2CFFA")
            status_text = "Locked · complete previous step first."
            icon.configure(text_color="#A09CC4", fg_color="#E8E6FF")
        elif status == "ready":
            status_text = f"Ready · {cfg['approx']}"
        elif status == "running":
            btn.configure(text="Running…", state="disabled")
            status_text = "In progress…"
            frame.configure(border_color=ACCENT)
        elif status == "done":
            status_text = f"Completed · {cfg['approx']}"
            btn.configure(text="Run again", fg_color="#5751C7", state="normal")
            icon.configure(text="✓", text_color="white", fg_color=ACCENT)
            frame.configure(border_color=ACCENT)

        status_lbl.configure(text=status_text)

# ==============================
# FOOTER
# ==============================

footer_frame = ctk.CTkFrame(
    main_frame,
    fg_color=FOOTER_BG,
    corner_radius=0,
    height=60
)
footer_frame.pack(fill="x", side="bottom", padx=0, pady=0)
footer_frame.pack_propagate(False)

footer_inner = ctk.CTkFrame(footer_frame, fg_color="transparent")
footer_inner.pack(expand=True, fill="both", padx=24)

footer_label1 = ctk.CTkLabel(
    footer_inner,
    text="Affordable Wellness · CalmSync",
    font=("Helvetica", 11, "bold"),
    text_color=TEXT_MAIN
)
footer_label1.pack(anchor="w")

footer_label2 = ctk.CTkLabel(
    footer_inner,
    text="Demonstrating real-time brain state detection and modulation.",
    font=SMALL_FONT,
    text_color=TEXT_SOFT
)
footer_label2.pack(anchor="w", pady=(1, 0))

footer_hint = ctk.CTkLabel(
    footer_inner,
    text="Use 1–5 to open steps · Esc to exit",
    font=SMALL_FONT,
    text_color=TEXT_SOFT
)
footer_hint.pack(anchor="e")

# ==============================
# TECLADO
# ==============================

def on_key(event):
    for _btn, key, cmd in button_refs:
        if event.char == key:
            cmd()
    if event.keysym == "Escape":
        cerrar_app()

app.bind("<Key>", on_key)

# ==============================
# INIT & LOOP
# ==============================

create_step_cards()
refresh_ui()
poll_processes()

app.mainloop()