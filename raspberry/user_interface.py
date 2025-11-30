import customtkinter as ctk
import subprocess

# ==============================
# CONFIGURACIÓN GENERAL UI
# ==============================

ctk.set_appearance_mode("light")          # "light" para vibe más limpio
ctk.set_default_color_theme("blue")       # tema base, luego afinamos colores

APP_BG = "#F4F6FB"        # fondo general muy suave
CARD_BG = "#FFFFFF"       # tarjetas blancas
HEADER_BG = "#EEF2FF"     # lila muy suave
FOOTER_BG = "#EEF2FF"
ACCENT = "#7C8CDF"        # azul-lila calmado
ACCENT_DARK = "#5B6AC9"
TEXT_MAIN = "#4A4F63"
TEXT_SOFT = "#8A92AA"

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

# Frame raíz
main_frame = ctk.CTkFrame(app, fg_color=APP_BG, corner_radius=0)
main_frame.pack(fill="both", expand=True)

# ---------- HEADER ----------
header_frame = ctk.CTkFrame(
    main_frame,
    fg_color=HEADER_BG,
    corner_radius=0,
    height=150
)
header_frame.pack(fill="x", padx=0, pady=0)
header_frame.pack_propagate(False)

# Botón BPM (arriba izquierda)
heart_button = ctk.CTkButton(
    header_frame,
    text="BPM",
    font=("Helvetica", 18, "bold"),
    fg_color="white",
    hover_color="#E4E7FF",
    text_color=ACCENT_DARK,
    width=80,
    height=40,
    corner_radius=20,
    command=abrir_frecuencia_cardiaca,
    cursor="hand2",
    border_width=1,
    border_color="#D0D4F8"
)
heart_button.place(x=30, y=30)

# Botón X (arriba derecha)
close_button = ctk.CTkButton(
    header_frame,
    text="✕",
    font=("Helvetica", 22, "bold"),
    fg_color="white",
    hover_color="#FFE4E4",
    text_color="#FF5A5A",
    width=50,
    height=40,
    corner_radius=20,
    command=cerrar_app,
    cursor="hand2",
    border_width=1,
    border_color="#F0B4B4"
)
close_button.place(relx=1.0, x=-80, y=30)

# Contenedor de título
title_container = ctk.CTkFrame(header_frame, fg_color="transparent")
title_container.pack(expand=True)

title_label = ctk.CTkLabel(
    title_container,
    text="CalmSync",
    font=("Helvetica", 60, "bold"),
    text_color=ACCENT_DARK
)
title_label.pack(anchor="center")

subtitle_label = ctk.CTkLabel(
    title_container,
    text="Guide your mind from stormy to serene",
    font=("Helvetica", 16),
    text_color=TEXT_SOFT
)
subtitle_label.pack(anchor="center", pady=(4, 0))

# ---------- ÁREA CENTRAL CON CARDS ----------
center_frame = ctk.CTkFrame(main_frame, fg_color=APP_BG)
center_frame.pack(fill="both", expand=True, padx=60, pady=(30, 20))

# Card contenedor
cards_frame = ctk.CTkFrame(center_frame, fg_color=CARD_BG, corner_radius=26)
cards_frame.pack(expand=True, fill="both", padx=10, pady=10)

# Título del bloque
block_title = ctk.CTkLabel(
    cards_frame,
    text="Choose your session",
    font=("Helvetica", 20, "bold"),
    text_color=TEXT_MAIN
)
block_title.pack(anchor="w", padx=30, pady=(25, 5))

block_subtitle = ctk.CTkLabel(
    cards_frame,
    text="Begin with calibration for best results, then explore the different tools.",
    font=("Helvetica", 13),
    text_color=TEXT_SOFT
)
block_subtitle.pack(anchor="w", padx=30, pady=(0, 10))

# Frame para grid de botones
buttons_frame = ctk.CTkFrame(cards_frame, fg_color="transparent")
buttons_frame.pack(expand=True, fill="both", padx=30, pady=20)

# Datos para cada módulo: (título, emoji, descripción, función, color, tecla)
modules = [
    (
        "Calibration",
        "🧭",
        "Check signal quality\nand prepare your baseline.",
        abrir_calibration,
        "#A9B8FF",
        "1"
    ),
    (
        "Bars Visualizer",
        "📊",
        "See your Alpha / Beta waves\nin real time.",
        abrir_bars_visualizer,
        "#B3D4FF",
        "2"
    ),
    (
        "Neurofeedback Game",
        "🌦️",
        "Turn stormy skies into sunshine\nwith your mental state.",
        abrir_neurofeedback,
        "#B9E6FF",
        "3"
    ),
    (
        "Stroop Game",
        "🎯",
        "Measure cognitive control\nunder gentle challenge.",
        abrir_stroop_game,
        "#C9E7FF",
        "4"
    ),
]

buttons_frame.grid_columnconfigure((0, 1), weight=1, uniform="col")
buttons_frame.grid_rowconfigure((0, 1), weight=1, uniform="row")

button_refs = []

for idx, (title, emoji, desc, cmd, color, key) in enumerate(modules):
    row = idx // 2
    col = idx % 2

    card = ctk.CTkFrame(
        buttons_frame,
        fg_color="#FFFFFF",
        corner_radius=24,
        border_width=1,
        border_color="#E2E6F5"
    )
    card.grid(row=row, column=col, padx=18, pady=18, sticky="nsew")

    # Contenido del card
    card_inner = ctk.CTkFrame(card, fg_color="transparent")
    card_inner.pack(expand=True, fill="both", padx=18, pady=18)

    # Badge de número (1–4), visible incluso si no se ven emojis
    badge = ctk.CTkLabel(
        card_inner,
        text=key,
        font=("Helvetica", 16, "bold"),
        text_color="white",
        fg_color=ACCENT,
        corner_radius=999,
        width=28,
        height=28
    )
    badge.pack(anchor="w")

    # Emoji (si la fuente los soporta; si no, simplemente no se verá pero no rompe nada)
    emoji_label = ctk.CTkLabel(
        card_inner,
        text=emoji,
        font=("Helvetica", 26),
        text_color=TEXT_MAIN
    )
    emoji_label.pack(anchor="w", pady=(4, 0))

    title_label = ctk.CTkLabel(
        card_inner,
        text=title,
        font=("Helvetica", 22, "bold"),
        text_color=TEXT_MAIN
    )
    title_label.pack(anchor="w", pady=(2, 0))

    desc_label = ctk.CTkLabel(
        card_inner,
        text=desc,
        font=("Helvetica", 13),
        text_color=TEXT_SOFT,
        justify="left"
    )
    desc_label.pack(anchor="w", pady=(3, 16))

    # Botón principal del módulo
    btn = ctk.CTkButton(
        card_inner,
        text=f"Start   ({key})",
        font=("Helvetica", 15, "bold"),
        text_color="white",
        fg_color=color,
        hover_color=ACCENT_DARK,
        corner_radius=20,
        height=38,
        command=cmd,
        cursor="hand2"
    )
    btn.pack(anchor="e", pady=(0, 0))

    button_refs.append((btn, key, cmd))

# ---------- FOOTER ----------
footer_frame = ctk.CTkFrame(
    main_frame,
    fg_color=FOOTER_BG,
    corner_radius=0,
    height=80
)
footer_frame.pack(fill="x", side="bottom", padx=0, pady=0)
footer_frame.pack_propagate(False)

footer_inner = ctk.CTkFrame(footer_frame, fg_color="transparent")
footer_inner.pack(expand=True, fill="both", padx=30)

# Parte izquierda del footer (texto marca)
footer_label1 = ctk.CTkLabel(
    footer_inner,
    text="Affordable Wellness · CalmSync",
    font=("Helvetica", 13, "bold"),
    text_color=TEXT_MAIN
)
footer_label1.pack(anchor="w")

footer_label2 = ctk.CTkLabel(
    footer_inner,
    text="Your stress-free life starts here.",
    font=("Helvetica", 12),
    text_color=TEXT_SOFT
)
footer_label2.pack(anchor="w", pady=(2, 0))

# Hint de teclado a la derecha
footer_hint = ctk.CTkLabel(
    footer_inner,
    text="Use 1–4 to open modules · Esc to exit",
    font=("Helvetica", 12),
    text_color=TEXT_SOFT
)
footer_hint.pack(anchor="e")

# ==============================
# BINDINGS TECLADO
# ==============================

def on_key(event):
    # Atajos 1–4 para abrir módulos
    for btn, key, cmd in button_refs:
        if event.char == key:
            cmd()
    # Esc para cerrar app
    if event.keysym == "Escape":
        cerrar_app()

app.bind("<Key>", on_key)

# ==============================
# MAINLOOP
# ==============================

app.mainloop()