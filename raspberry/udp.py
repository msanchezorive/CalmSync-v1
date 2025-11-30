import os
import time
import serial
import subprocess
import threading
import json
from generic_parser import parse_packet, extract_data_from_payload
import socket

MINDWAVE_MAC = "A4:DA:32:04:0C:4F"
RFCOMM_DEV = "/dev/rfcomm0"
BAUD_RATE = 57600

# Codigos a extraer
CODE_HANDLERS = {
    0x02: "signal_quality",
    0x04: "attention",
    0x05: "meditation",
    0x83: "eeg_power"
}

ALPHA_IDX = [2, 3]
BETA_IDX = [4, 5]

# Valores globales
latest_data = {
    "alpha": 0.0,
    "beta": 0.0,
    "attention": 0,
    "meditation": 0,
    "signal_quality": 0
}
running = True

def connect_mindwave():
    try:
        os.system("sudo rfcomm release 0")
    except:
        pass
    while True:
        try:
            subprocess.Popen(
                ["sudo", "rfcomm", "connect", "0", MINDWAVE_MAC, "1"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            time.sleep(3)
            ser = serial.Serial(RFCOMM_DEV, BAUD_RATE, timeout=1)
            print("? MindWave conectado")
            return ser
        except Exception as e:
            print(f"? Error conectando MindWave: {e}, reintentando en 2s...")
            time.sleep(2)
def reader_loop():
    global latest_data, running
    ser = connect_mindwave()
    while running:
        payload = parse_packet(ser)
        if payload is None:
            continue
        data = extract_data_from_payload(payload, CODE_HANDLERS)
        if "eeg_power" in data:
            eeg = data["eeg_power"]
            latest_data["alpha"] = (eeg[ALPHA_IDX[0]] + eeg[ALPHA_IDX[1]]) / 2
            latest_data["beta"] = (eeg[BETA_IDX[0]] + eeg[BETA_IDX[1]]) / 2
        for key in ["attention", "meditation", "signal_quality"]:
            if key in data:
                latest_data[key] = data[key]

def start_reader_thread():
    t = threading.Thread(target=reader_loop, daemon=True)
    t.start()

def start_server():
    global latest_data, running
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    while True:
        try:
            server.bind(("127.0.0.1", 12345))
            break
        except OSError:
            print("? Puerto ocupado, reintentando en 2s...")
            time.sleep(2)
    server.listen(5)
    print("? EEG Server escuchando en 127.0.0.1:12345")
    while running:
        conn, addr = server.accept()
        print(f"Cliente conectado: {addr}")
        try:
            while running:
                try:
                    conn.send((json.dumps(latest_data) + "\n").encode())
                except BrokenPipeError:
                    break
                time.sleep(0.1)
        finally:
            conn.close()
            print(f"Cliente desconectado: {addr}")
class EEGClient:
    """Cliente TCP robusto para leer datos del servidor MindWave"""

    def __init__(self, host="127.0.0.1", port=12345, reconnect_delay=1.0):
        self.host = host
        self.port = port
        self.reconnect_delay = reconnect_delay
        self.running = False
        self.data = {
            "alpha": 0.0,
            "beta": 0.0,
            "attention": 0,
            "meditation": 0,
            "signal_quality": 0
        }
        self.lock = threading.Lock()
        self.thread = None

    def _connect_loop(self):
        while self.running:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((self.host, self.port))
                    buffer = ""
                    while self.running:
                        chunk = s.recv(1024).decode()
                        if not chunk:
                            break
                        buffer += chunk
                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            try:
                                parsed = json.loads(line)
                                with self.lock:
                                    self.data.update(parsed)
                            except json.JSONDecodeError:
                                continue
            except (ConnectionRefusedError, OSError):
                time.sleep(self.reconnect_delay)
    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._connect_loop, daemon=True)
            self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)

    def get_data(self):
        with self.lock:
            return self.data.copy()

if __name__ == "__main__":
    start_reader_thread()
    start_server()

