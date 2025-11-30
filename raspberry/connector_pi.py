# -*- coding: utf-8 -*-
import serial
import threading
import time
import queue
from datetime import datetime

# Importa tu parser
from generic_parser import parse_packet, extract_data_from_payload

# Cola compartida GLOBAL para los datos EEG
cola_eeg = queue.Queue()

MINDWAVE_MAC = "A4:DA:32:04:0C:4F"
RFCOMM_PORT = "/dev/rfcomm0"
BAUD_RATE = 57600
MAX_RETRIES = 5
RETRY_DELAY = 2

# Códigos que quieres capturar
CODE_HANDLERS = {
    0x04: 'attention',
    0x05: 'meditation',
    0x80: 'raw_wave',
    0x83: 'eeg_power'
}


def conectar_mindwave():
    """Conecta al MindWave con reintentos"""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            ser = serial.Serial(
                port=RFCOMM_PORT,
                baudrate=BAUD_RATE,
                timeout=1
            )
            print(f"? Conectado a {RFCOMM_PORT} en el intento {attempt}")
            return ser

        except serial.SerialException as e:
            print(f"? Intento {attempt}/{MAX_RETRIES} - Error: {e}")
            
            if attempt < MAX_RETRIES:
                print(f"   Reintentando en {RETRY_DELAY} segundos...")
                time.sleep(RETRY_DELAY)
            else:
                print(f"\n? No se pudo conectar después de {MAX_RETRIES} intentos")
                print(f"\nEjecuta en terminal:")
                print(f"sudo rfcomm bind {RFCOMM_PORT} {MINDWAVE_MAC} 1")
                print(f"\nLuego vuelve a ejecutar este script")
                return None


def leer_del_sensor():
    """Lee del MindWave y envía datos a la cola"""
    ser = conectar_mindwave()
    if not ser:
        return
    
    contador = 0
    print("\n? Sistema iniciado. Leyendo del sensor...\n")
    
    while True:
        try:
            payload = parse_packet(ser)
            if payload:
                datos = extract_data_from_payload(payload, CODE_HANDLERS)
                datos['timestamp'] = datetime.now().isoformat()
                datos['id'] = contador
                
                cola_eeg.put(datos)
                print(f"[SENSOR] Datos {contador}: {datos}")
                contador += 1
            
        except Exception as e:
            print(f"[SENSOR] Error: {e}")
            time.sleep(0.1)


if __name__ == "__main__":
    print("=" * 60)
    print("SERVIDOR DE DATOS EEG")
    print("=" * 60)
    print("? Lee del MindWave y distribuye por cola_eeg")
    print("? Los scripts pueden importar cola_eeg desde aquí\n")
    
    thread_sensor = threading.Thread(target=leer_del_sensor, daemon=False)
    thread_sensor.start()
    
    try:
        thread_sensor.join()
    except KeyboardInterrupt:
        print("\n[MAIN] Cerrando...")