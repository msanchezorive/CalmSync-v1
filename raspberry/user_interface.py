import customtkinter as ctk
import subprocess

# ==============================
# CONFIGURACIÓN GENERAL UI
# ==============================

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# Paleta más sobria y menos lavada
APP_BG = "#E5E8F3"        # fondo general
CARD_BG = "#F9FAFF"       # tarjetas
HEADER_BG = "#E1E5FF"
FOOTER_BG = "#E1E5FF"

ACCENT = "#5865D8"        # azul-violeta calmado
ACCENT_SOFT = "#9AA3FF"
ACCENT_DARK = "#4048A8"

TEXT_MAIN = "#222741"
TEXT_SOFT = "#7A819C"

app = ctk.CTk()
app.title("CalmSync")
app.geometry("1024x768")
app.resizable(False, False)
app.attributes("-fullscreen", True)

app.configure(fg_color=APP_BG)

# ==============================
# FUNCIONES DE NAVEGACIÓN
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
    height=120
)
header_frame.pack(fill="x", padx=0, pady=0)
header_frame.pack_propagate(False)

# Botón BPM
heart_button = ctk.CTkButton(
    header_frame,
    text="BPM",
    font=("Helvetica", 16, "bold"),
    fg_color="white",
    hover_color="#D7DBFF",
    text_color=ACCENT_DARK,
    width=70,
    height=34,
    corner_radius=18,
    command=abrir_frecuencia_cardiaca,
    cursor="hand2",
    border_width=1,
    border_color="#C5CBFB"
)
heart_button.place(x=24, y=24)

# Botón cerrar
close_button = ctk.CTkButton(
    header_frame,
    text="✕",
    font=("Helvetica", 20, "bold"),
    fg_color="white",
    hover_color="#FFDADA",
    text_color="#FF5A5A",
    width=46,
    height=34,
    corner_radius=18,
    command=cerrar_app,
    cursor="hand2",
    border_width=1,
    border_color="#F3B0B0"
)
close_button.place(relx=1.0, x=-70, y=24)

# Título centrado
title_container = ctk.CTkFrame(header_frame, fg_color="transparent")
title_container.pack(expand=True)

title_label = ctk.CTkLabel(
    title_container,
    text="CalmSync",
    font=("Helvetica", 52, "bold"),
    text_color=ACCENT_DARK
)
title_label.pack(anchor="center")

subtitle_label = ctk.CTkLabel(
    title_container,
    text="Guide your mind from stormy to serene",
    font=("Helvetica", 14),
    text_color=TEXT_SOFT
)
subtitle_label.pack(anchor="center", pady=(3, 0))

# ---------- ÁREA CENTRAL ----------
center_frame = ctk.CTkFrame(main_frame, fg_color=APP_BG)
center_frame.pack(fill="both", expand=True, padx=60, pady=(24, 16))

cards_frame = ctk.CTkFrame(center_frame, fg_color=CARD_BG, corner_radius=22)
cards_frame.pack(expand=True, fill="both", padx=4, pady=4)

block_title = ctk.CTkLabel(
    cards_frame,
    text="Choose your session",
    font=("Helvetica", 18, "bold"),
    text_color=TEXT_MAIN
)
block_title.pack(anchor="w", padx=28, pady=(20, 4))

block_subtitle = ctk.CTkLabel(
    cards_frame,
    text="Begin with calibration for best results, then explore the different tools.",
    font=("Helvetica", 12),
    text_color=TEXT_SOFT
)
block_subtitle.pack(anchor="w", padx=28, pady=(0, 10))

buttons_frame = ctk.CTkFrame(cards_frame, fg_color="transparent")
buttons_frame.pack(expand=True, fill="both", padx=26, pady=18)

modules = [
    (
        "Calibration",
        "Check signal quality\nand prepare your baseline.",
        abrir_calibration,
        "1",
        ACCENT
    ),
    (
        "Bars Visualizer",
        "See your Alpha / Beta waves\nin real time.",
        abrir_bars_visualizer,
        "2",
        "#4CB2FF"
    ),
    (
        "Neurofeedback Game",
        "Turn stormy skies into sunshine\nwith your mental state.",
        abrir_neurofeedback,
        "3",
        "#41C7A3"
    ),
    (
        "Stroop Game",
        "Measure cognitive control\nunder gentle challenge.",
        abrir_stroop_game,
        "4",
        "#FF9F6B"
    ),
]

buttons_frame.grid_columnconfigure((0, 1), weight=1, uniform="col")
buttons_frame.grid_rowconfigure((0, 1), weight=1, uniform="row")

button_refs = []

for idx, (title, desc, cmd, key, color) in enumerate(modules):
    row = idx // 2
    col = idx % 2

    card = ctk.CTkFrame(
        buttons_frame,
        fg_color=CARD_BG,
        corner_radius=18,
        border_width=1,
        border_color="#D6DBF0"
    )
    card.grid(row=row, column=col, padx=14, pady=14, sticky="nsew")

    card.grid_columnconfigure(0, weight=1)
    card.grid_columnconfigure(1, weight=0)

    # Columna izquierda: badge + textos
    left = ctk.CTkFrame(card, fg_color="transparent")
    left.grid(row=0, column=0, sticky="nsew", padx=(16, 8), pady=14)

    badge = ctk.CTkLabel(
        left,
        text=key,
        font=("Helvetica", 14, "bold"),
        text_color="white",
        fg_color=color,
        corner_radius=999,
        width=26,
        height=26
    )
    badge.pack(anchor="w")

    title_label = ctk.CTkLabel(
        left,
        text=title,
        font=("Helvetica", 18, "bold"),
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

    # Columna derecha: botón compacto
    right = ctk.CTkFrame(card, fg_color="transparent")
    right.grid(row=0, column=1, sticky="e", padx=(0, 16), pady=14)

    btn = ctk.CTkButton(
        right,
        text=f"Start  ({key})",
        font=("Helvetica", 13, "bold"),
        text_color="white",
        fg_color=color,
        hover_color=ACCENT_DARK,
        corner_radius=18,
        width=120,          # evita barra larguísima
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
    height=70
)
footer_frame.pack(fill="x", side="bottom", padx=0, pady=0)
footer_frame.pack_propagate(False)

footer_inner = ctk.CTkFrame(footer_frame, fg_color="transparent")
footer_inner.pack(expand=True, fill="both", padx=26)

footer_label1 = ctk.CTkLabel(
    footer_inner,
    text="Affordable Wellness · CalmSync",
    font=("Helvetica", 12, "bold"),
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
    text="Use 1–4 to open modules · Esc to exit",
    font=("Helvetica", 11),
    text_color=TEXT_SOFT
)
footer_hint.pack(anchor="e")

# ==============================
# BINDINGS TECLADO
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