import customtkinter as ctk
import subprocess

# ==============================
# CONFIG GENERAL
# ==============================

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

APP_BG      = "#F3F4F8"   # gris muy claro
HEADER_BG   = "#EEF0FF"   # lavanda suave
FOOTER_BG   = "#EEF0FF"
CARD_BG     = "#FFFFFF"

ACCENT      = "#5F6DFB"   # azul-lavanda principal
ACCENT_SOFT = "#E1E4FF"

TEXT_MAIN   = "#222436"
TEXT_SOFT   = "#7A819C"


app = ctk.CTk()
app.title("CalmSync")
app.geometry("1024x768")
app.resizable(False, False)
app.attributes("-fullscreen", True)
app.configure(fg_color=APP_BG)

# ==============================
# DEFINICIÓN DE STEPS
# ==============================

# Cada step del flujo
STEPS_CONFIG = [
    {
        "id": 1,
        "title": "Calibration",
        "subtitle": "Check signal quality and prepare your baseline.",
        "btn_text": "Begin Calibration",
        "script": "initial_calibration.py",
        "shortcut": "1",
        "approx": "~8 min",
    },
    {
        "id": 2,
        "title": "Bars Visualizer",
        "subtitle": "See your Alpha/Beta waves in real time.",
        "btn_text": "Watch Your Waves",
        "script": "bars_visualizer.py",
        "shortcut": "2",
        "approx": "flexible",
    },
    {
        "id": 3,
        "title": "Neurofeedback Game (pre)",
        "subtitle": "Change the weather with your mental state (before Stroop).",
        "btn_text": "Play Neurofeedback",
        "script": "neurofeedback_game.py",
        "shortcut": "3",
        "approx": "~5–10 min",
    },
    {
        "id": 4,
        "title": "Stroop Game",
        "subtitle": "Test cognitive control in a gentle way.",
        "btn_text": "Take Stroop Test",
        "script": "test_stroop_tactil.py",
        "shortcut": "4",
        "approx": "~5 min",
    },
    {
        "id": 5,
        "title": "Neurofeedback Game (post)",
        "subtitle": "Repeat the game and observe how your brain changed.",
        "btn_text": "Play Neurofeedback Again",
        "script": "neurofeedback_game.py",
        "shortcut": "5",
        "approx": "~5–10 min",
    },
]

# Estados: locked / ready / running / done / hidden
steps_state = {}
for step in STEPS_CONFIG:
    if step["id"] == 1:
        steps_state[step["id"]] = {"status": "ready", "process": None, "visible": True}
    elif step["id"] in (2, 3, 4):
        steps_state[step["id"]] = {"status": "locked", "process": None, "visible": True}
    else:  # step 5
        steps_state[step["id"]] = {"status": "locked", "process": None, "visible": False}

step_widgets = {}  # guardaremos los widgets de cada tarjeta
button_refs = []   # para atajos de teclado


# ==============================
# UTILIDADES
# ==============================

def cerrar_app(event=None):
    app.quit()
    app.destroy()


def start_step(step_id):
    """Lanza el script del step si está listo."""
    state = steps_state[step_id]
    if state["status"] not in ("ready", "done"):
        return

    cfg = next(s for s in STEPS_CONFIG if s["id"] == step_id)
    try:
        # lanzamos el script correspondiente
        proc = subprocess.Popen(["python", cfg["script"]])
    except Exception as e:
        print(f"Error launching {cfg['script']}: {e}")
        return

    state["process"] = proc
    state["status"] = "running"
    refresh_ui()


def poll_processes():
    """Revisa periódicamente si los procesos han terminado para marcar steps como completados."""
    for step in STEPS_CONFIG:
        sid = step["id"]
        state = steps_state[sid]
        proc = state["process"]
        if proc is not None:
            ret = proc.poll()
            if ret is not None:
                # Ha terminado
                state["process"] = None
                state["status"] = "done"
                unlock_next_step(sid)
                refresh_ui()
    app.after(2000, poll_processes)


def unlock_next_step(current_id):
    """Desbloquea el siguiente paso en el flujo."""
    # Encuentra índice en la lista de config
    ids = [s["id"] for s in STEPS_CONFIG]
    if current_id not in ids:
        return
    idx = ids.index(current_id)

    # Caso especial: al terminar 4, mostramos/desbloqueamos el 5
    if current_id == 4:
        if 5 in steps_state:
            steps_state[5]["visible"] = True
            if steps_state[5]["status"] == "locked":
                steps_state[5]["status"] = "ready"
        return

    # Desbloquear siguiente si existe y está locked
    if idx + 1 < len(STEPS_CONFIG):
        next_id = STEPS_CONFIG[idx + 1]["id"]
        if steps_state[next_id]["status"] == "locked":
            steps_state[next_id]["status"] = "ready"


def get_progress():
    """Devuelve (step_actual, step_total_visible)."""
    visible_ids = [s["id"] for s in STEPS_CONFIG if steps_state[s["id"]]["visible"]]
    total = len(visible_ids)
    # actual = primer step visible no done
    current = visible_ids[-1] if all(
        steps_state[i]["status"] == "done" for i in visible_ids
    ) else next(
        i for i in visible_ids if steps_state[i]["status"] != "done"
    )
    return current, total


# ==============================
# LAYOUT: HEADER
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

# Botón BPM
heart_button = ctk.CTkButton(
    header_frame,
    text="BPM",
    font=("Helvetica", 15, "bold"),
    fg_color="white",
    hover_color="#E4E6FF",
    text_color=ACCENT,
    width=68,
    height=32,
    corner_radius=16,
    command=lambda: subprocess.Popen(["python", "frecuencia_cardiaca.py"]),
    cursor="hand2",
    border_width=1,
    border_color="#D1D5FF"
)
heart_button.place(x=22, y=24)

# Botón cerrar (suave, no rojo agresivo)
close_button = ctk.CTkButton(
    header_frame,
    text="✕",
    font=("Helvetica", 18, "bold"),
    fg_color="white",
    hover_color="#ECEEF7",
    text_color="#A0A2B5",
    width=44,
    height=32,
    corner_radius=16,
    command=cerrar_app,
    cursor="hand2",
    border_width=1,
    border_color="#D6D8E6"
)
close_button.place(relx=1.0, x=-70, y=24)

title_container = ctk.CTkFrame(header_frame, fg_color="transparent")
title_container.pack(expand=True)

title_label = ctk.CTkLabel(
    title_container,
    text="CalmSync",
    font=("Helvetica", 44, "bold"),
    text_color=ACCENT
)
title_label.pack(anchor="center")

subtitle_label = ctk.CTkLabel(
    title_container,
    text="Neurofeedback made simple and calm.",
    font=("Helvetica", 13),
    text_color=TEXT_SOFT
)
subtitle_label.pack(anchor="center", pady=(2, 0))

# ==============================
# LAYOUT: ZONA CENTRAL
# ==============================

center_frame = ctk.CTkFrame(main_frame, fg_color=APP_BG)
center_frame.pack(fill="both", expand=True, padx=72, pady=(24, 16))

card_outer = ctk.CTkFrame(center_frame, fg_color=CARD_BG, corner_radius=20)
card_outer.pack(expand=True, fill="both")

inner = ctk.CTkFrame(card_outer, fg_color="transparent")
inner.pack(expand=True, fill="both", padx=26, pady=18)

# Cabecera de sesión con progreso
session_title = ctk.CTkLabel(
    inner,
    text="Session 1 · Relax & Focus",
    font=("Helvetica", 16, "bold"),
    text_color=TEXT_MAIN
)
session_title.pack(anchor="w")

session_sub = ctk.CTkLabel(
    inner,
    text="Follow the steps in order for a full before/after experience.",
    font=("Helvetica", 12),
    text_color=TEXT_SOFT
)
session_sub.pack(anchor="w", pady=(0, 6))

progress_label = ctk.CTkLabel(
    inner,
    text="",  # lo rellenamos en refresh_ui()
    font=("Helvetica", 11),
    text_color=TEXT_SOFT
)
progress_label.pack(anchor="w", pady=(0, 12))

# Contenedor de las tarjetas de steps
steps_container = ctk.CTkFrame(inner, fg_color="transparent")
steps_container.pack(expand=True, fill="both")

steps_container.grid_columnconfigure(0, weight=1)
# max 5 filas
for r in range(5):
    steps_container.grid_rowconfigure(r, weight=1, uniform="rows")


def create_step_cards():
    """Crea las tarjetas (UI) de cada step."""
    for idx, cfg in enumerate(STEPS_CONFIG):
        sid = cfg["id"]
        row = idx  # 0..4

        frame = ctk.CTkFrame(
            steps_container,
            fg_color=CARD_BG,
            corner_radius=16,
            border_width=1,
            border_color="#E0E3F0"
        )
        # grid más tarde según visibilidad
        step_widgets[sid] = {
            "frame": frame,
            "number": None,
            "title": None,
            "subtitle": None,
            "button": None,
            "status": None,
        }

        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=0)

        # columna izquierda
        left = ctk.CTkFrame(frame, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(16, 8), pady=10)

        number_label = ctk.CTkLabel(
            left,
            text=str(sid),
            font=("Helvetica", 12, "bold"),
            text_color=ACCENT,
            fg_color=ACCENT_SOFT,
            corner_radius=999,
            width=24,
            height=22
        )
        number_label.pack(anchor="w")

        title_label = ctk.CTkLabel(
            left,
            text=cfg["title"],
            font=("Helvetica", 16, "bold"),
            text_color=TEXT_MAIN
        )
        title_label.pack(anchor="w", pady=(4, 0))

        subtitle_label = ctk.CTkLabel(
            left,
            text=cfg["subtitle"],
            font=("Helvetica", 12),
            text_color=TEXT_SOFT,
            justify="left"
        )
        subtitle_label.pack(anchor="w", pady=(1, 0))

        status_label = ctk.CTkLabel(
            left,
            text="",  # se rellena luego
            font=("Helvetica", 11),
            text_color=TEXT_SOFT
        )
        status_label.pack(anchor="w", pady=(2, 0))

        # columna derecha
        right = ctk.CTkFrame(frame, fg_color="transparent")
        right.grid(row=0, column=1, sticky="e", padx=(0, 16), pady=10)

        btn = ctk.CTkButton(
            right,
            text=cfg["btn_text"],
            font=("Helvetica", 13, "bold"),
            text_color="white",
            fg_color=ACCENT,
            hover_color="#4A57D9",
            corner_radius=18,
            width=170,
            height=32,
            command=lambda sid=sid: start_step(sid),
            cursor="hand2"
        )
        btn.pack(anchor="e")

        # guardamos referencias
        step_widgets[sid]["number"] = number_label
        step_widgets[sid]["title"] = title_label
        step_widgets[sid]["subtitle"] = subtitle_label
        step_widgets[sid]["button"] = btn
        step_widgets[sid]["status"] = status_label

        # atajos de teclado
        button_refs.append((btn, cfg["shortcut"], lambda sid=sid: start_step(sid)))


def refresh_ui():
    """Actualiza la apariencia de cada step según su estado."""
    # Progreso
    current_step, total_steps = get_progress()
    progress_label.configure(
        text=f"Step {current_step} of {total_steps} · approx 25–30 min total"
    )

    for idx, cfg in enumerate(STEPS_CONFIG):
        sid = cfg["id"]
        w = step_widgets[sid]
        state = steps_state[sid]

        frame = w["frame"]
        is_visible = state["visible"]
        if is_visible:
            frame.grid(row=idx, column=0, padx=2, pady=6, sticky="nsew")
        else:
            frame.grid_forget()
            continue

        status = state["status"]
        btn = w["button"]
        num_lbl = w["number"]
        status_lbl = w["status"]

        # reset estilos base
        frame.configure(border_color="#E0E3F0")
        num_lbl.configure(text_color=ACCENT, fg_color=ACCENT_SOFT)
        btn.configure(fg_color=ACCENT, state="normal")
        status_text = ""

        if status == "locked":
            btn.configure(state="disabled", fg_color="#DADCFA")
            status_text = "Locked · complete previous step first."
            num_lbl.configure(text_color="#A3A6C5", fg_color="#E5E7FA")
        elif status == "ready":
            status_text = f"Ready · {cfg['approx']}"
        elif status == "running":
            btn.configure(text="Running…", state="disabled", fg_color=ACCENT)
            status_text = "In progress…"
            frame.configure(border_color=ACCENT)
        elif status == "done":
            status_text = f"Completed · {cfg['approx']}"
            btn.configure(text="Run again", state="normal", fg_color="#4A57D9")
            num_lbl.configure(text="✓", text_color="white", fg_color=ACCENT)
            frame.configure(border_color=ACCENT)

        status_lbl.configure(text=status_text)


# ==============================
# FOOTER
# ==============================

footer_frame = ctk.CTkFrame(
    main_frame,
    fg_color=FOOTER_BG,
    corner_radius=0,
    height=64
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
    text="Your stress-free life starts here.",
    font=("Helvetica", 11),
    text_color=TEXT_SOFT
)
footer_label2.pack(anchor="w", pady=(1, 0))

footer_hint = ctk.CTkLabel(
    footer_inner,
    text="Press 1–5 to open steps · Esc to exit",
    font=("Helvetica", 11),
    text_color=TEXT_SOFT
)
footer_hint.pack(anchor="e")

# ==============================
# TECLADO
# ==============================

def on_key(event):
    # Atajos numéricos
    for _btn, key, cmd in button_refs:
        if event.char == key:
            cmd()
    if event.keysym == "Escape":
        cerrar_app()

app.bind("<Key>", on_key)

# ==============================
# INIT
# ==============================

create_step_cards()
refresh_ui()
poll_processes()

# ==============================
# MAINLOOP
# ==============================

app.mainloop()