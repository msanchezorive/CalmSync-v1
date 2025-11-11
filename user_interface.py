import customtkinter as ctk
import subprocess

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("CalmSync")
app.geometry("1024x768")
app.resizable(False, False)
app.attributes('-fullscreen', True)

# ---- Frame principal ----
main_frame = ctk.CTkFrame(app, fg_color="#FAFBFC")
main_frame.pack(fill="both", expand=True)

# ---- Header ----
header_frame = ctk.CTkFrame(main_frame, fg_color="#F3F5FB", corner_radius=0, height=140)
header_frame.pack(fill="x", padx=0, pady=0)
header_frame.pack_propagate(False)

title_text_frame = ctk.CTkFrame(header_frame, fg_color=None)
title_text_frame.pack(expand=True, pady=15)

# Título grande
title_label = ctk.CTkLabel(
    title_text_frame,
    text="CalmSync",
    font=("Helvetica", 64, "bold"),
    text_color="#6B7A9E"
)
title_label.pack(anchor="center")

# Subtítulo
subtitle_label = ctk.CTkLabel(
    title_text_frame,
    text="Your Stress-Free Life Starts Here!",
    font=("Helvetica", 16, "normal"),
    text_color="#A0A9BE"
)
subtitle_label.pack(anchor="center", pady=(5,0))

# ---- Área central con botones ----
buttons_frame = ctk.CTkFrame(main_frame, fg_color=None)
buttons_frame.pack(fill="both", expand=True, padx=50, pady=40)

# Funciones de cada módulo
def abrir_calibration():
    subprocess.Popen(["python", "initial_calibration.py"])

def abrir_bars_visualizer():
    subprocess.Popen(["python", "bars_visualizer.py"])

def abrir_neurofeedback():
    subprocess.Popen(["python", "neurofeedback_game.py"])

def abrir_stroop_game():
    subprocess.Popen(["python", "test_stroop_tactil.py"])

# Datos de botones: texto, emoji, función, color, tecla rápida
botones_data = [
    ("Calibration", "🧠", abrir_calibration, "#8A94B8", "1"),
    ("Bars Visualizer", "📊", abrir_bars_visualizer, "#9FA8C4", "2"),
    ("Neurofeedback Game", "⚡", abrir_neurofeedback, "#A8B5D1", "3"),
    ("Stroop Game", "🎯", abrir_stroop_game, "#B4BDDA", "4"),
]

# Crear botones centrados en grid 2x2
num_botones = len(botones_data)
cols = 2
rows = (num_botones + cols - 1) // cols

botones_refs = []

for idx, (text, emoji, cmd, color, key) in enumerate(botones_data):
    row = idx // cols
    col = idx % cols
    
    btn_container = ctk.CTkFrame(buttons_frame, fg_color=None)
    btn_container.grid(row=row, column=col, padx=40, pady=40, sticky="nsew")
    
    buttons_frame.grid_columnconfigure(col, weight=1)
    buttons_frame.grid_rowconfigure(row, weight=1)
    
    btn = ctk.CTkButton(
        btn_container,
        text=f"{emoji}\n{text}",
        font=("Helvetica", 32, "bold"),
        text_color="white",
        fg_color=color,
        hover_color=color,
        corner_radius=25,
        height=0,
        command=cmd,
        cursor="hand2"
    )
    btn.pack(fill="both", expand=True)
    botones_refs.append((btn, key, cmd))  # Guardamos referencia para teclas rápidas

# ---- Soporte para teclado: teclas 1-4 ----
def on_key(event):
    for btn, key, cmd in botones_refs:
        if event.char == key:
            cmd()

app.bind("<Key>", on_key)

# ---- Footer ----
footer_frame = ctk.CTkFrame(main_frame, fg_color="#F3F5FB", corner_radius=0, height=100)
footer_frame.pack(fill="x", side="bottom", padx=0, pady=0)
footer_frame.pack_propagate(False)

footer_text_frame = ctk.CTkFrame(footer_frame, fg_color=None)
footer_text_frame.pack(expand=True)

footer_label1 = ctk.CTkLabel(
    footer_text_frame,
    text="by Affordable Wellness",
    font=("Helvetica", 14, "bold"),
    text_color="#6B7A9E"
)
footer_label1.pack(anchor="w")

footer_label2 = ctk.CTkLabel(
    footer_text_frame,
    text="Your Stress-Free Life Starts Here!",
    font=("Helvetica", 12, "normal"),
    text_color="#A0A9BE"
)
footer_label2.pack(anchor="w")

app.mainloop()
