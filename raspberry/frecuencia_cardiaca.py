import serial
import tkinter as tk
from threading import Thread
import time

# Conectar Arduino
arduino = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
time.sleep(2)

# Crear ventana
ventana = tk.Tk()
ventana.title("Monitor Cardiaco")
ventana.geometry("400x200")
ventana.configure(bg='black')

# Etiqueta BPM
label = tk.Label(ventana, text="--", font=("Arial", 70), bg='black', fg='green')
label.pack(expand=True)

# Funcion para leer datos
def leer():
    while True:
        if arduino.in_waiting > 0:
            linea = arduino.readline().decode('utf-8').strip()
            if "BPM:" in linea:
                bpm = linea.split(":")[1]
                label.config(text=bpm + " BPM")
        time.sleep(0.1)

# Iniciar lectura en segundo plano
Thread(target=leer, daemon=True).start()

# Mostrar ventana
ventana.mainloop()