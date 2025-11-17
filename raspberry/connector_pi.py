# -- coding: utf-8 --
import serial

MINDWAVE_MAC = "A4:DA:32:04:0C:4F"
RFCOMM_PORT = "/dev/rfcomm0"
BAUD_RATE = 57600

try:
    ser = serial.Serial(
        port=RFCOMM_PORT,
        baudrate=BAUD_RATE,
        timeout=1
    )
    print("Conectado al MindWave")

except serial.SerialException as e:
    print("Error al conectar:", e)
    print("\nPrimero ejecuta en terminal:")
    print(f"sudo rfcomm bind {RFCOMM_PORT} {MINDWAVE_MAC} 1")
    ser = None