import customtkinter as ctk
import subprocess

# ==============================
# CONFIG GENERAL
# ==============================

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# Paleta muy controlada
APP_BG     = "#F3F4F8"   # gris muy claro
HEADER_BG  = "#EEF0FF"   # lavanda suave
FOOTER_BG  = "#EEF0FF"
CARD_BG    = "#FFFFFF"   # blanco limpio

ACCENT     = "#5F6DFB"   # azul-lavanda principal
ACCENT_SOFT = "#E1E4FF"  # pill / badge suave

TEXT_MAIN  = "#222436"
TEXT_SOFT  = "#7A819C"

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

# BPM (ghost button)
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

# Close
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

# Título
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
cards_frame.pack(expand=True, fill="both", padx=0, pady=0)

# Título bloque
block_title = ctk.CTkLabel(
    cards_frame,
    text="Choose your session",
    font=("Helvetica", 17, "bold"),
    text_color=TEXT_MAIN
)
block_title.pack(anchor="w", padx=28, pady=(18, 3))

block_subtitle = ctk.CTkLabel(
    cards_frame,
    text="Start with calibration, then explore visualisation, neurofeedback, and Stroop.",
    font=("Helvetica", 12),
    text_color=TEXT_SOFT
)
block_subtitle.pack(anchor="w", padx=28, pady=(0, 12))

buttons_frame = ctk.CTkFrame(cards_frame, fg_color="transparent")
buttons_frame.pack(expand=True, fill="both", padx=24, pady=16)

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

buttons_frame.grid_columnconfigure((0, 1), weight=1, uniform="col")
buttons_frame.grid_rowconfigure((0, 1), weight=1, uniform="row")

button_refs = []

for idx, (title, desc, cmd, key) in enumerate(modules):
    row = idx // 2
    col = idx % 2

    card = ctk.CTkFrame(
        buttons_frame,
        fg_color=CARD_BG,
        corner_radius=18,
        border_width=1,
        border_color="#E0E3F0"
    )
    card.grid(row=row, column=col, padx=12, pady=12, sticky="nsew")

    card.grid_columnconfigure(0, weight=1)
    card.grid_columnconfigure(1, weight=0)

    # Columna izquierda: número + texto
    left = ctk.CTkFrame(card, fg_color="transparent")
    left.grid(row=0, column=0, sticky="nsew", padx=(18, 8), pady=14)

    # Número en pill suave
    badge = ctk.CTkLabel(
        left,
        text=key,
        font=("Helvetica", 13, "bold"),
        text_color=ACCENT,
        fg_color=ACCENT_SOFT,
        corner_radius=999,
        width=26,
        height=24
    )
    badge.pack(anchor="w")

    title_label = ctk.CTkLabel(
        left,
        text=title,
        font=("Helvetica", 17, "bold"),
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
    desc_label.pack(anchor="w", pady=(2, 0))

    # Columna derecha: botón único de acento
    right = ctk.CTkFrame(card, fg_color="transparent")
    right.grid(row=0, column=1, sticky="e", padx=(0, 18), pady=14)

    btn = ctk.CTkButton(
        right,
        text=f"Start  ({key})",
        font=("Helvetica", 13, "bold"),
        text_color="white",
        fg_color=ACCENT,
        hover_color="#4A57D9",
        corner_radius=18,
        width=110,
        height=34,
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