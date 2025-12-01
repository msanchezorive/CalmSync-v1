import sys
import time
import serial
import threading
import customtkinter as ctk

# =========================
# CONFIGURACIÓN SERIAL
# =========================
PORT = "/dev/ttyACM0"   # cámbialo si tu Arduino usa otro puerto
BAUD = 9600
TIMEOUT = 1

# Intentamos conectar al Arduino
try:
    arduino = serial.Serial(PORT, BAUD, timeout=TIMEOUT)
    time.sleep(2)  # pequeño delay para que el Arduino reinicie
    serial_ok = True
except serial.SerialException as e:
    print(f"[BPM] No se pudo abrir el puerto {PORT}: {e}")
    serial_ok = False
    arduino = None

# =========================
# CONFIGURACIÓN UI
# =========================
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Monitor Cardiaco")
app.geometry("420x240")
app.resizable(False, False)

# Colores a juego con CalmSync
COLOR_BG = "#FAFBFC"
COLOR_CARD = "#FFFFFF"
COLOR_TEXT = "#6B7A9E"
COLOR_SUBTEXT = "#A0A9BE"

app.configure(fg_color=COLOR_BG)

# ---------- Contenedor principal ----------
main_frame = ctk.CTkFrame(app, fg_color=COLOR_BG)
main_frame.pack(fill="both", expand=True, padx=20, pady=20)

card = ctk.CTkFrame(main_frame, fg_color=COLOR_CARD, corner_radius=20)
card.pack(fill="both", expand=True)

# ---------- Título ----------
title_label = ctk.CTkLabel(
    card,
    text="Heart Rate",
    font=("Helvetica", 22, "bold"),
    text_color=COLOR_TEXT
)
title_label.pack(pady=(16, 0))

subtitle_label = ctk.CTkLabel(
    card,
    text="Live BPM monitor",
    font=("Helvetica", 14),
    text_color=COLOR_SUBTEXT
)
subtitle_label.pack(pady=(0, 10))

# ---------- BPM grande ----------
bpm_var = ctk.StringVar(value="--")
bpm_label = ctk.CTkLabel(
    card,
    textvariable=bpm_var,
    font=("Helvetica", 64, "bold"),
)
bpm_label.pack(pady=(0, 4))

# ---------- Estado ----------
status_var = ctk.StringVar(
    value="Connecting..." if serial_ok else "No device detected"
)
status_label = ctk.CTkLabel(
    card,
    textvariable=status_var,
    font=("Helvetica", 13),
    text_color=COLOR_SUBTEXT
)
status_label.pack(pady=(0, 8))

# ---------- Nota pequeña ----------
hint_label = ctk.CTkLabel(
    card,
    text="Close this window to stop monitoring.",
    font=("Helvetica", 11),
    text_color=COLOR_SUBTEXT
)
hint_label.pack(pady=(0, 10))

# =========================
# LÓGICA DE LECTURA
# =========================
running = True

def color_for_bpm(bpm: int) -> str:
    """
    Devuelve un color de texto según el rango de BPM.
    """
    if bpm <= 0:
        return "#6B7A9E"  # gris si algo raro
    if bpm < 50 or bpm > 110:
        return "#E57373"  # rojo suave
    if 50 <= bpm <= 60 or 90 <= bpm <= 110:
        return "#FFB74D"  # amarillo suave
    # rango típico reposo
    return "#43A047"      # verde

def leer_bpm():
    global running
    if not serial_ok or arduino is None:
        return

    # marcamos como conectado
    status_var.set(f"Connected on {PORT}")

    while running:
        try:
            if arduino.in_waiting > 0:
                linea = arduino.readline().decode("utf-8", errors="ignore").strip()
                if "BPM:" in linea:
                    try:
                        bpm_str = linea.split(":")[1].strip()
                        bpm_val = int(bpm_str)

                        # Actualizamos UI en el hilo principal
                        def update_ui():
                            bpm_var.set(f"{bpm_val}")
                            bpm_label.configure(text_color=color_for_bpm(bpm_val))

                        app.after(0, update_ui)
                    except ValueError:
                        # línea corrupta, la ignoramos
                        pass
        except serial.SerialException as e:
            def set_error():
                status_var.set(f"Serial error: {e}")
                bpm_label.configure(text_color="#E57373")
            app.after(0, set_error)
            break

        time.sleep(0.05)

# =========================
# CIERRE LIMPIO
# =========================
def on_close():
    global running
    running = False
    try:
        if arduino and arduino.is_open:
            arduino.close()
    except Exception:
        pass
    app.destroy()

app.protocol("WM_DELETE_WINDOW", on_close)

# Lanzamos hilo de lectura si hay serie
if serial_ok:
    t = threading.Thread(target=leer_bpm, daemon=True)
    t.start()

# =========================
# MAIN LOOP
# =========================
app.mainloop()