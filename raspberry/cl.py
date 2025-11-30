import socket
import json
import threading
import time

class EEGClient:
    """Cliente TCP para leer datos de MindWave desde eeg_service.py."""

    def __init__(self, host="127.0.0.1", port=12345, reconnect_delay=2):
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
                        raw = s.recv(1024)
                        if not raw:
                            break
                        buffer += raw.decode()
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
    client = EEGClient()
    client.start()
    try:
        while True:
            data = client.get_data()
            print(data)
            time.sleep(0.5)
    except KeyboardInterrupt:
        client.stop()
        print("Cliente EEG detenido")
