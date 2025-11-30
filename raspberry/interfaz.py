import customtkinter as ctk
from PIL import Image, ImageDraw, ImageTk
import subprocess

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("CalmSync")
app.geometry("1024x768")  # iPad resolution
app.resizable(False, False)
app.attributes('-fullscreen', True)  # Pantalla completa

# ---- Cargar logo del header ----
try:
    logo_img = Image.open("logo.png")
    logo_img = logo_img.resize((100, 100), Image.Resampling.LANCZOS)
    logo_icon = ImageTk.PhotoImage(logo_img)
except FileNotFoundError:
    print("🚨 Advertencia: No se encontró 'logo.png'.")
    logo_icon = None

# ---- Frame principal ----
main_frame = ctk.CTkFrame(app, fg_color="#FAFBFC")
main_frame.pack(fill="both", expand=True)

# ---- Header ----
header_frame = ctk.CTkFrame(main_frame, fg_color="#F3F5FB", corner_radius=0, height=140)
header_frame.pack(fill="x", padx=0, pady=0)
header_frame.pack_propagate(False)

title_content_frame = ctk.CTkFrame(header_frame, fg_color=None)
title_content_frame.pack(expand=True, pady=15)

if logo_icon:
    logo_label = ctk.CTkLabel(title_content_frame, image=logo_icon, text="")
    logo_label.pack(side="left", padx=30)

title_text_frame = ctk.CTkFrame(title_content_frame, fg_color=None)
title_text_frame.pack(side="left", padx=20, fill="both", expand=True)

title_label = ctk.CTkLabel(
    title_text_frame,
    text="CalmSync",
    font=("Helvetica", 64, "bold"),
    text_color="#6B7A9E"
)
title_label.pack(anchor="w")

subtitle_label = ctk.CTkLabel(
    title_text_frame,
    text="Your Stress-Free Life Starts Here!",
    font=("Helvetica", 16, "normal"),
    text_color="#A0A9BE"
)
subtitle_label.pack(anchor="w", pady=(3, 0))

# ---- Ãrea central con 4 grandes botones tÃ¡ctiles ----
buttons_frame = ctk.CTkFrame(main_frame, fg_color=None)
buttons_frame.pack(fill="both", expand=True, padx=30, pady=40)

buttons_frame.grid_columnconfigure((0, 1), weight=1, uniform="col")
buttons_frame.grid_rowconfigure((0, 1), weight=1, uniform="row")

# ---- Funciones para cada módulo :para ejecute el codigo correspondiente 
def abrir_wave_visualization():
    print("ð Opening wave visualization...")
    try:
        subprocess.Popen(["python", "wave_visualization.py"])
    except Exception as e:
        print(f"Error: {e}")

def abrir_game1():
    print("ð¯ Starting game 1...")
    try:
        subprocess.Popen(["python", "game1.py"])
    except Exception as e:
        print(f"Error: {e}")

def abrir_neurofeedback():
    print("â¡ Starting neurofeedback...")
    try:
        subprocess.Popen(["python", "neurofeedback_game.py"])
    except Exception as e:
        print(f"Error: {e}")

def abrir_report():
    print("ð Generating report...")
    try:
        subprocess.Popen(["python", "report.py"])
    except Exception as e:
        print(f"Error: {e}")

# Datos de botones: (nombre, emoji, función, color, tecla)
botones_data = [
    ("Wave\nVisualization", "ð", abrir_wave_visualization, "#8A94B8", "1"),
    ("Game 1", "ð®", abrir_game1, "#9FA8C4", "2"),
    ("Neurofeedback", "â¡", abrir_neurofeedback, "#A8B5D1", "3"),
    ("Report", "ð", abrir_report, "#B4BDDA", "4"),
]

# Crear 4 botones enormes
for idx, (text, emoji, cmd, color, key) in enumerate(botones_data):
    row = idx // 2
    col = idx % 2
    
    btn_container = ctk.CTkFrame(buttons_frame, fg_color=None)
    btn_container.grid(row=row, column=col, padx=20, pady=20, sticky="nsew")
    
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

# ---- Footer ----
footer_frame = ctk.CTkFrame(main_frame, fg_color="#F3F5FB", corner_radius=0, height=100)
footer_frame.pack(fill="x", side="bottom", padx=0, pady=0)
footer_frame.pack_propagate(False)

footer_content = ctk.CTkFrame(footer_frame, fg_color=None)
footer_content.pack(expand=True)

try:
    logo_footer_img = Image.open("logo.png")
    logo_footer_img = logo_footer_img.resize((50, 50), Image.Resampling.LANCZOS)
    small_logo = ImageTk.PhotoImage(logo_footer_img)
    logo_footer = ctk.CTkLabel(footer_content, image=small_logo, text="")
    logo_footer.pack(side="left", padx=25)
except FileNotFoundError:
    pass

footer_text_frame = ctk.CTkFrame(footer_content, fg_color=None)
footer_text_frame.pack(side="left", padx=15, fill="both", expand=True)

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
