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
CARD_BG     = "#FFFFFF"   # blanco limpio
SIDE_BG     = "#F5F6FF"   # panel lateral suave

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
# LANZADORES
# ==============================

def abrir_frecuencia_cardiaca():
    subprocess.Popen(["python", "frecuencia_cardiaca.py"])

def abrir_calibration():
    subprocess.Popen(["python", "initial_calibration.py"])

def abrir_bars_visualizer():
    subprocess.Popen(["python", "bars_visualizer.py"])

def abrir_neurofeedback():
    subprocess.Popen(["python", "neurofeedback_game.py"])

def abrir_stroop_game():
    subprocess.Popen(["python", "test_stroop_tactil.py"])

def cerrar_app(event=None):
    app.quit()
    app.destroy()

# ==============================
# LAYOUT PRINCIPAL
# ==============================

main_frame = ctk.CTkFrame(app, fg_color=APP_BG, corner_radius=0)
main_frame.pack(fill="both", expand=True)

# ---------- HEADER ----------
header_frame = ctk.CTkFrame(
    main_frame,
    fg_color=HEADER_BG,
    corner_radius=0,
    height=110,
)
header_frame.pack(fill="x", padx=0, pady=0)
header_frame.pack_propagate(False)

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
    command=abrir_frecuencia_cardiaca,
    cursor="hand2",
    border_width=1,
    border_color="#D1D5FF"
)
heart_button.place(x=22, y=24)

close_button = ctk.CTkButton(
    header_frame,
    text="✕",
    font=("Helvetica", 18, "bold"),
    fg_color="white",
    hover_color="#FFE5E5",
    text_color="#F35B5B",
    width=44,
    height=32,
    corner_radius=16,
    command=cerrar_app,
    cursor="hand2",
    border_width=1,
    border_color="#F3B6B6"
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

# ---------- ZONA CENTRAL ----------
center_frame = ctk.CTkFrame(main_frame, fg_color=APP_BG)
center_frame.pack(fill="both", expand=True, padx=72, pady=(24, 16))

cards_frame = ctk.CTkFrame(center_frame, fg_color=CARD_BG, corner_radius=20)
cards_frame.pack(expand=True, fill="both")

# Contenido interno: 2 columnas (izquierda info, derecha módulos)
content_frame = ctk.CTkFrame(cards_frame, fg_color="transparent")
content_frame.pack(expand=True, fill="both", padx=20, pady=16)

content_frame.grid_columnconfigure(0, weight=1)
content_frame.grid_columnconfigure(1, weight=2)
content_frame.grid_rowconfigure(0, weight=1)

# ----- PANEL IZQUIERDO (texto / “how to use”) -----
left_panel = ctk.CTkFrame(
    content_frame,
    fg_color=SIDE_BG,
    corner_radius=18
)
left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 14), pady=4)

left_inner = ctk.CTkFrame(left_panel, fg_color="transparent")
left_inner.pack(expand=True, fill="both", padx=18, pady=16)

welcome_label = ctk.CTkLabel(
    left_inner,
    text="Welcome to CalmSync",
    font=("Helvetica", 17, "bold"),
    text_color=TEXT_MAIN
)
welcome_label.pack(anchor="w", pady=(0, 6))

welcome_text = (
    "CalmSync helps you observe and gently\n"
    "guide your mental state using EEG-based\n"
    "neurofeedback."
)
welcome_body = ctk.CTkLabel(
    left_inner,
    text=welcome_text,
    font=("Helvetica", 12),
    text_color=TEXT_SOFT,
    justify="left"
)
welcome_body.pack(anchor="w", pady=(0, 14))

steps_label = ctk.CTkLabel(
    left_inner,
    text="Recommended flow",
    font=("Helvetica", 13, "bold"),
    text_color=TEXT_MAIN
)
steps_label.pack(anchor="w", pady=(0, 4))

steps = [
    "1 · Calibrate the sensor and baseline.",
    "2 · Watch your Alpha/Beta waves.",
    "3 · Play the Neurofeedback Game.",
    "4 · Finish with the Stroop test."
]
for s in steps:
    lbl = ctk.CTkLabel(
        left_inner,
        text=s,
        font=("Helvetica", 12),
        text_color=TEXT_SOFT,
        justify="left"
    )
    lbl.pack(anchor="w")

tip_label = ctk.CTkLabel(
    left_inner,
    text="\nTip: Sit comfortably, relax your shoulders\nand breathe slowly during sessions.",
    font=("Helvetica", 11),
    text_color=TEXT_SOFT,
    justify="left"
)
tip_label.pack(anchor="w", pady=(6, 0))

# ----- PANEL DERECHO (lista de módulos) -----
right_panel = ctk.CTkFrame(
    content_frame,
    fg_color="transparent"
)
right_panel.grid(row=0, column=1, sticky="nsew", padx=(14, 0), pady=4)

right_panel.grid_rowconfigure((0, 1, 2, 3), weight=1, uniform="rows")
right_panel.grid_columnconfigure(0, weight=1)

modules = [
    ("Calibration",
     "Check signal quality and prepare your baseline.",
     abrir_calibration,
     "1"),
    ("Bars Visualizer",
     "See your Alpha/Beta waves in real time.",
     abrir_bars_visualizer,
     "2"),
    ("Neurofeedback Game",
     "Change the weather with your mental state.",
     abrir_neurofeedback,
     "3"),
    ("Stroop Game",
     "Test cognitive control in a gentle way.",
     abrir_stroop_game,
     "4"),
]

button_refs = []

for idx, (title, desc, cmd, key) in enumerate(modules):
    row = idx

    card = ctk.CTkFrame(
        right_panel,
        fg_color=CARD_BG,
        corner_radius=16,
        border_width=1,
        border_color="#E0E3F0"
    )
    card.grid(row=row, column=0, padx=4, pady=6, sticky="nsew")

    card.grid_columnconfigure(0, weight=1)
    card.grid_columnconfigure(1, weight=0)

    left = ctk.CTkFrame(card, fg_color="transparent")
    left.grid(row=0, column=0, sticky="nsew", padx=(16, 8), pady=10)

    badge = ctk.CTkLabel(
        left,
        text=key,
        font=("Helvetica", 12, "bold"),
        text_color=ACCENT,
        fg_color=ACCENT_SOFT,
        corner_radius=999,
        width=24,
        height=22
    )
    badge.pack(anchor="w")

    title_label = ctk.CTkLabel(
        left,
        text=title,
        font=("Helvetica", 16, "bold"),
        text_color=TEXT_MAIN
    )
    title_label.pack(anchor="w", pady=(4, 0))

    desc_label = ctk.CTkLabel(
        left,
        text=desc,
        font=("Helvetica", 12),
        text_color=TEXT_SOFT,
        justify="left"
    )
    desc_label.pack(anchor="w", pady=(1, 0))

    right = ctk.CTkFrame(card, fg_color="transparent")
    right.grid(row=0, column=1, sticky="e", padx=(0, 16), pady=10)

    btn = ctk.CTkButton(
        right,
        text=f"Start  ({key})",
        font=("Helvetica", 13, "bold"),
        text_color="white",
        fg_color=ACCENT,
        hover_color="#4A57D9",
        corner_radius=18,
        width=110,
        height=32,
        command=cmd,
        cursor="hand2"
    )
    btn.pack(anchor="e")

    button_refs.append((btn, key, cmd))

# ---------- FOOTER ----------
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
    text="Press 1–4 to open modules · Esc to exit",
    font=("Helvetica", 11),
    text_color=TEXT_SOFT
)
footer_hint.pack(anchor="e")

# ==============================
# TECLADO
# ==============================

def on_key(event):
    for btn, key, cmd in button_refs:
        if event.char == key:
            cmd()
    if event.keysym == "Escape":
        cerrar_app()

app.bind("<Key>", on_key)

# ==============================
# MAINLOOP
# ==============================

app.mainloop()