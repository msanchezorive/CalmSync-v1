import serial
import struct
import matplotlib.pyplot as plt
from collections import deque

# ============ PARSER CODE (from your first file) ============
class ThinkGearParser(object):
    def __init__(self, recorders=None):
        self.recorders = []
        if recorders is not None:
            self.recorders += recorders
        self.input_data = ""
        self.parser = self.parse()
        next(self.parser)  # Python 3 compatible

    def feed(self, data):
        """Feed bytes to the parser"""
        for c in data:
            # Handle both bytes and strings
            byte_val = c if isinstance(c, int) else ord(c)
            self.parser.send(byte_val)
        for recorder in self.recorders:
            recorder.finish_chunk()
        self.input_data += data if isinstance(data, str) else data.decode('latin-1')

    def dispatch_data(self, key, value):
        """Send parsed data to all recorders"""
        for recorder in self.recorders:
            recorder.dispatch_data(key, value)

    def parse(self):
        """Generator that parses one byte at a time"""
        while True:
            byte = yield
            if byte == 0xaa:
                byte = yield
                if byte == 0xaa:
                    # Packet synced by 0xAA 0xAA
                    packet_length = yield
                    packet_code = yield
                    
                    if packet_code == 0xd4:
                        self.state = "standby"
                    elif packet_code == 0xd0:
                        self.state = "connected"
                    elif packet_code == 0xd2:
                        data_len = yield
                        headset_id = yield
                        headset_id += yield
                        self.dongle_state = "disconnected"
                    else:
                        left = packet_length - 2
                        while left > 0:
                            if packet_code == 0x80:  # Raw value
                                row_length = yield
                                a = yield
                                b = yield
                                value = struct.unpack("<h", chr(b) + chr(a))[0]
                                self.dispatch_data("raw", value)
                                left -= 2
                            elif packet_code == 0x02:  # Poor signal
                                a = yield
                                self.dispatch_data("poor_signal", a)
                                left -= 1
                            elif packet_code == 0x04:  # Attention
                                a = yield
                                if 0 < a <= 100:
                                    self.dispatch_data("attention", a)
                                left -= 1
                            elif packet_code == 0x05:  # Meditation
                                a = yield
                                if 0 < a <= 100:
                                    self.dispatch_data("meditation", a)
                                left -= 1
                            elif packet_code == 0x16:  # Blink Strength
                                a = yield
                                self.dispatch_data("blink", a)
                                left -= 1
                            elif packet_code == 0x83:  # EEG bands
                                vlength = yield
                                bands = []
                                for row in range(8):
                                    a = yield
                                    b = yield
                                    c = yield
                                    value = a * 255 * 255 + b * 255 + c
                                    bands.append(value)
                                left -= vlength
                                self.dispatch_data("bands", bands)
                            
                            if left > 0:
                                packet_code = yield


# ============ CUSTOM RECORDER FOR PLOTTING ============
class RealtimePlotRecorder:
    """Recorder that updates a matplotlib plot in real-time"""
    def __init__(self, window_size=250):
        self.window_size = window_size
        self.raw_data = deque([0] * window_size, maxlen=window_size)
        self.attention_values = []
        self.meditation_values = []
        
        # Setup plot
        plt.ion()
        self.fig, self.ax = plt.subplots()
        self.line, = self.ax.plot(self.raw_data, color='tab:blue')
        self.ax.set_ylim(-500, 500)
        self.ax.set_xlim(0, window_size)
        self.ax.set_title("EEG Raw Data (MindWave)")
        self.ax.set_xlabel("Tiempo (muestras)")
        self.ax.set_ylabel("µV (valor crudo)")
        
    def dispatch_data(self, key, value):
        """Handle different types of parsed data"""
        if key == "raw":
            print(f"Raw: {value}")
            self.raw_data.append(value)
            
            # Update plot
            self.line.set_ydata(self.raw_data)
            self.ax.draw_artist(self.ax.patch)
            self.ax.draw_artist(self.line)
            self.fig.canvas.flush_events()
            
        elif key == "attention":
            self.attention_values.append(value)
            print(f"Attention: {value}")
            
        elif key == "meditation":
            self.meditation_values.append(value)
            print(f"Meditation: {value}")
            
        elif key == "blink":
            print(f"Blink detected! Strength: {value}")
            
        elif key == "poor_signal":
            if value > 0:
                print(f"Poor signal: {value}")
    
    def finish_chunk(self):
        """Called after processing a chunk of data"""
        pass  # Not needed for real-time plotting


# ============ MAIN CODE ============
PORT = "COM10"
BAUD = 115200

# Create recorder and parser
recorder = RealtimePlotRecorder(window_size=250)
parser = ThinkGearParser(recorders=[recorder])

try:
    ser = serial.Serial(PORT, BAUD, timeout=1)
    print(f"✅ Conectado a {PORT}. Graficando señal EEG cruda...\n")

    while True:
        # Read available data and feed to parser
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting)
            parser.feed(data)
            
except KeyboardInterrupt:
    print("\n🧠 Lectura detenida por el usuario.")
finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()
        print("🔌 Puerto cerrado correctamente.")