import customtkinter as ctk
import subprocess

# =========================
# CONFIG GENERAL
# =========================
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("CalmSync")

# Pantalla completa según resolución actual
screen_w = app.winfo_screenwidth()
screen_h = app.winfo_screenheight()
app.geometry(f"{screen_w}x{screen_h}")
app.resizable(True, True)

# Si quieres modo kiosco total, descomenta:
# app.attributes("-fullscreen", True)

BG_MAIN = "#F4F2FF"
BG_CARD = "#FFFFFF"
TXT_MAIN = "#6B5EA8"
TXT_MUTED = "#A0A4C0"
ACCENT = "#5B4BE1"

app.configure(fg_color=BG_MAIN)

# =========================
# CALLBACKS
# =========================

def abrir_frecuencia_cardiaca():
    subprocess.Popen(["python3", "frecuencia_cardiaca.py"])

def abrir_calibration():
    subprocess.Popen(["python3", "initial_calibration.py"])

def abrir_bars_visualizer():
    subprocess.Popen(["python3", "bars_visualizer.py"])

def abrir_neurofeedback_pre():
    subprocess.Popen(["python3", "neurofeedback_game.py"])

def abrir_stroop_game():
    subprocess.Popen(["python3", "test_stroop_tactil.py"])

def abrir_neurofeedback_post():
    subprocess.Popen(["python3", "neurofeedback_game.py", "--post"])

def on_key(event):
    # Esc para cerrar la interfaz
    if event.keysym == "Escape":
        app.destroy()

app.bind("<Key>", on_key)

# =========================
# HEADER SUPERIOR
# =========================

header = ctk.CTkFrame(app, fg_color=BG_MAIN, corner_radius=0)
header.pack(fill="x", padx=24, pady=(16, 0))

# Botón BPM arriba a la izquierda
bpm_btn = ctk.CTkButton(
    header,
    text="BPM ♥",
    font=("Helvetica", 16, "bold"),
    fg_color="#FFFFFF",
    hover_color="#E3E4FF",
    text_color=TXT_MAIN,
    corner_radius=18,
    command=abrir_frecuencia_cardiaca,
    width=90,
    height=36
)
bpm_btn.pack(side="left", padx=(0, 16), pady=4)

# Título central
title_frame = ctk.CTkFrame(header, fg_color="transparent")
title_frame.pack(side="left", expand=True)

title_label = ctk.CTkLabel(
    title_frame,
    text="CalmSync",
    font=("Helvetica", 38, "bold"),
    text_color=TXT_MAIN
)
title_label.pack()

subtitle_label = ctk.CTkLabel(
    title_frame,
    text="Real-time neurofeedback to rethink anxiety.",
    font=("Helvetica", 14),
    text_color=TXT_MUTED
)
subtitle_label.pack()

# =========================
# CONTENIDO SCROLLABLE
# =========================

content_scroll = ctk.CTkScrollableFrame(
    app,
    fg_color=BG_MAIN,
    corner_radius=0
)
content_scroll.pack(fill="both", expand=True, padx=24, pady=(8, 16))

content_scroll.grid_columnconfigure(0, weight=1)
content_scroll.grid_columnconfigure(1, weight=2)

# =========================
# PANEL IZQUIERDO: WELCOME
# =========================

left_card = ctk.CTkFrame(content_scroll, fg_color=BG_CARD, corner_radius=24)
left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 16), pady=(0, 16))

left_card.grid_rowconfigure(0, weight=1)

welcome_title = ctk.CTkLabel(
    left_card,
    text="Welcome to CalmSync",
    font=("Helvetica", 22, "bold"),
    text_color=TXT_MAIN
)
welcome_title.pack(anchor="w", padx=20, pady=(20, 4))

welcome_body = (
    "CalmSync uses EEG-based neurofeedback to observe and gently shift\n"
    "your mental state. This showroom session is designed as a closed loop:\n\n"
    "Session flow\n"
    "1 → Calibrate sensor & baseline.\n"
    "2 → Watch your Alpha/Beta ratio in real time.\n"
    "3 → Play the Neurofeedback game (pre-Stroop).\n"
    "4 → Run the Stroop test to gently raise demand.\n"
    "5 → Play Neurofeedback again and compare before/after.\n\n"
    "Tip: Sit comfortably, relax your shoulders and breathe slowly\n"
    "throughout the session."
)

welcome_label = ctk.CTkLabel(
    left_card,
    text=welcome_body,
    justify="left",
    font=("Helvetica", 13),
    text_color=TXT_MUTED
)
welcome_label.pack(anchor="w", padx=20, pady=(0, 20))

# =========================
# PANEL DERECHO: SESIÓN
# =========================

right_column = ctk.CTkFrame(content_scroll, fg_color=BG_MAIN)
right_column.grid(row=0, column=1, sticky="nsew", pady=(0, 16))

right_column.grid_columnconfigure(0, weight=1)

session_header = ctk.CTkLabel(
    right_column,
    text="Session · Relax & Focus",
    font=("Helvetica", 18, "bold"),
    text_color=TXT_MAIN
)
session_header.grid(row=0, column=0, sticky="w", pady=(4, 8))

session_step = ctk.CTkLabel(
    right_column,
    text="Step 1 of 5 · approx 15–20 min total",
    font=("Helvetica", 11),
    text_color=TXT_MUTED
)
session_step.grid(row=1, column=0, sticky="w", pady=(0, 12))

# Helper para crear “cards” de sesión
def make_session_card(parent, row, tag, title, desc, btn_text, command=None, enabled=True):
    card = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=20)
    card.grid(row=row, column=0, sticky="ew", pady=(0, 12))
    card.grid_columnconfigure(0, weight=1)
    card.grid_columnconfigure(1, weight=0)

    tag_label = ctk.CTkLabel(
        card,
        text=tag,
        font=("Helvetica", 11, "bold"),
        text_color="#FFFFFF",
        fg_color="#C5C7F5",
        corner_radius=12,
        padx=10,
        pady=4
    )
    tag_label.grid(row=0, column=0, sticky="w", padx=16, pady=(12, 0))

    title_label = ctk.CTkLabel(
        card,
        text=title,
        font=("Helvetica", 18, "bold"),
        text_color=TXT_MAIN
    )
    title_label.grid(row=1, column=0, sticky="w", padx=16, pady=(4, 0))

    desc_label = ctk.CTkLabel(
        card,
        text=desc,
        font=("Helvetica", 12),
        text_color=TXT_MUTED
    )
    desc_label.grid(row=2, column=0, sticky="w", padx=16, pady=(0, 12))

    if enabled:
        btn_fg = ACCENT
        btn_hover = "#4C3FD2"
        text_color = "#FFFFFF"
    else:
        btn_fg = "#E3E4FF"
        btn_hover = "#D8D9FB"
        text_color = "#C0C3E0"

    btn = ctk.CTkButton(
        card,
        text=btn_text,
        font=("Helvetica", 14, "bold"),
        fg_color=btn_fg,
        hover_color=btn_hover,
        text_color=text_color,
        corner_radius=20,
        width=140,
        height=36,
        command=command if enabled else None
    )
    btn.grid(row=0, column=1, rowspan=3, padx=16, pady=12, sticky="e")

    return card

# ===== Cards =====

# 1. Calibration
make_session_card(
    right_column,
    row=2,
    tag="CAL",
    title="Calibration",
    desc="Check signal quality and prepare your baseline.\nReady · ~8 min",
    btn_text="Begin Calibration",
    command=abrir_calibration,
    enabled=True
)

# 2. Bars Visualizer
make_session_card(
    right_column,
    row=3,
    tag="WAV",
    title="Bars Visualizer",
    desc="See your Alpha/Beta waves in real time.\nRun after calibration.",
    btn_text="Watch Your Waves",
    command=abrir_bars_visualizer,
    enabled=True
)

# 3. Neurofeedback Game (pre)
make_session_card(
    right_column,
    row=4,
    tag="NF",
    title="Neurofeedback Game (pre)",
    desc="Play before Stroop to capture your initial state.",
    btn_text="Play Neurofeedback",
    command=abrir_neurofeedback_pre,
    enabled=True
)

# 4. Stroop Game
make_session_card(
    right_column,
    row=5,
    tag="ST",
    title="Stroop Game",
    desc="Increase cognitive load and gently raise stress.",
    btn_text="Run Stroop Test",
    command=abrir_stroop_game,
    enabled=True
)

# 5. Neurofeedback Game (post)
make_session_card(
    right_column,
    row=6,
    tag="NF",
    title="Neurofeedback Game (post)",
    desc="Play again after Stroop and compare your state.",
    btn_text="Play Neurofeedback",
    command=abrir_neurofeedback_post,
    enabled=True
)

# =========================
# MAIN LOOP
# =========================

app.mainloop()