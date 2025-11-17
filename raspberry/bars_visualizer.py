import pygame
import sys
import threading
import serial
from typing import Optional, Tuple
from collections import deque

# Importamos las funciones del parser
from generic_parser import parse_packet, extract_data_from_payload

# ---------------------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------------------
import serial
import sys
import time

# ==== CONFIG ====
PORT = "/dev/rfcomm0"  # Cambiar seg�n tu sistema (Windows: "COM7")
BAUD = 57600
TIMEOUT = 1
MAX_RETRIES = 5       # N�mero m�ximo de intentos
RETRY_DELAY = 2       # Segundos entre intentos

# ==== CONEXI�N SERIAL CON REINTENTOS ====
ser = None
for attempt in range(1, MAX_RETRIES + 1):
    try:
        ser = serial.Serial(PORT, BAUD, timeout=TIMEOUT)
        print(f"Conectado a {PORT} en el intento {attempt}.")
        break
    except serial.SerialException as e:
        print(f"Intento {attempt} fallido: {e}")
        if attempt < MAX_RETRIES:
            print(f"Reintentando en {RETRY_DELAY} segundos...")
            time.sleep(RETRY_DELAY)
        else:
            print("No se pudo conectar al MindWave. Saliendo del programa.")
            sys.exit(1)

# En este punto `ser` est� listo para ser usado por tu parser


NEUROSKY_PORT = "/dev/rfcomm0"  # o "COM10" en Windows
NEUROSKY_BAUD = 57600

CODE_HANDLERS_EEG = {0x83: 'eeg_power'}

ALPHA_IDX = [2, 3]
BETA_IDX = [4, 5]

SMOOTHING_ALPHA = 0.15

# Configuración visual
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 400
FPS = 30

# Colores
COLOR_BG = (20, 20, 30)
COLOR_ALPHA = (100, 200, 255)  # Azul claro
COLOR_BETA = (255, 150, 100)   # Naranja
COLOR_TEXT = (255, 255, 255)
COLOR_GRID = (50, 50, 70)

# Escala de barras
MAX_POWER_DISPLAY = 50000  # Ajusta según tus valores típicos
BAR_WIDTH = 80
BAR_SPACING = 50


# ---------------------------------------------------------------------
# LECTOR DE NEUROSKY (simplificado)
# ---------------------------------------------------------------------

class NeuroSkyReader:
    """Lee solo Alpha y Beta del NeuroSky."""
    
    def __init__(self, port: str, baud: int):
        self.port = port
        self.baud = baud
        
        self.alpha = 0.0
        self.beta = 0.0
        
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.serial_port: Optional[serial.Serial] = None
        self.connection_status = "Desconectado"
        
        self.lock = threading.Lock()
    
    def get_alpha_from_payload(self, payload: bytes) -> Optional[float]:
        data = extract_data_from_payload(payload, CODE_HANDLERS_EEG)
        if 'eeg_power' in data:
            powers = data['eeg_power']
            return sum([powers[i] for i in ALPHA_IDX]) / len(ALPHA_IDX)
        return None
    
    def get_beta_from_payload(self, payload: bytes) -> Optional[float]:
        data = extract_data_from_payload(payload, CODE_HANDLERS_EEG)
        if 'eeg_power' in data:
            powers = data['eeg_power']
            return sum([powers[i] for i in BETA_IDX]) / len(BETA_IDX)
        return None
    
    def _read_loop(self):
        try:
            self.serial_port = serial.Serial(self.port, self.baud, timeout=1)
            self.connection_status = "Conectado"
            print(f"✅ NeuroSky conectado en {self.port}")
            
            while self.running:
                payload = parse_packet(self.serial_port)
                
                if payload is None:
                    continue
                
                raw_alpha = self.get_alpha_from_payload(payload)
                raw_beta = self.get_beta_from_payload(payload)
                
                with self.lock:
                    if raw_alpha is not None:
                        self.alpha = (SMOOTHING_ALPHA * raw_alpha + 
                                    (1 - SMOOTHING_ALPHA) * self.alpha)
                    
                    if raw_beta is not None:
                        self.beta = (SMOOTHING_ALPHA * raw_beta + 
                                   (1 - SMOOTHING_ALPHA) * self.beta)
        
        except serial.SerialException as e:
            self.connection_status = f"Error: {e}"
            print(f"❌ Error de conexión: {e}")
        
        finally:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
            self.connection_status = "Desconectado"
    
    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._read_loop, daemon=True)
            self.thread.start()
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
    
    def get_values(self) -> Tuple[float, float]:
        with self.lock:
            return self.alpha, self.beta


# ---------------------------------------------------------------------
# VISUALIZADOR DE BARRAS
# ---------------------------------------------------------------------

class EEGBarsVisualizer:
    """Visualiza Alpha y Beta como barras verticales animadas."""
    
    def __init__(self, use_real_data: bool = True):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("EEG Barras - Alpha & Beta")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 24)
        
        # Inicializa NeuroSky
        self.use_real_data = use_real_data
        self.neurosky: Optional[NeuroSkyReader] = None
        
        if use_real_data:
            try:
                self.neurosky = NeuroSkyReader(NEUROSKY_PORT, NEUROSKY_BAUD)
                self.neurosky.start()
                print("🧠 Modo: Datos reales")
            except Exception as e:
                print(f"⚠️ Error: {e}")
                print("🎮 Modo simulación")
                self.use_real_data = False
        else:
            print("🎮 Modo simulación")
        
        # Datos de simulación
        self.sim_alpha = 5000.0
        self.sim_beta = 5000.0
        self.sim_direction_alpha = 1
        self.sim_direction_beta = -1
        
        # Estado actual
        self.alpha = 0.0
        self.beta = 0.0
        
        # Histórico para suavizado visual
        self.alpha_history = deque(maxlen=5)
        self.beta_history = deque(maxlen=5)
        
        self.running = True
    
    def update_data(self):
        """Actualiza los valores de Alpha y Beta."""
        if self.use_real_data and self.neurosky:
            self.alpha, self.beta = self.neurosky.get_values()
        else:
            # Simulación: oscilación automática
            self.sim_alpha += 100 * self.sim_direction_alpha
            self.sim_beta += 80 * self.sim_direction_beta
            
            if self.sim_alpha > 40000:
                self.sim_direction_alpha = -1
            elif self.sim_alpha < 2000:
                self.sim_direction_alpha = 1
            
            if self.sim_beta > 35000:
                self.sim_direction_beta = -1
            elif self.sim_beta < 2000:
                self.sim_direction_beta = 1
            
            self.alpha = self.sim_alpha
            self.beta = self.sim_beta
        
        # Suavizado visual adicional
        self.alpha_history.append(self.alpha)
        self.beta_history.append(self.beta)
    
    def get_smoothed_values(self) -> Tuple[float, float]:
        """Retorna valores suavizados para animación fluida."""
        if len(self.alpha_history) > 0:
            alpha_smooth = sum(self.alpha_history) / len(self.alpha_history)
            beta_smooth = sum(self.beta_history) / len(self.beta_history)
            return alpha_smooth, beta_smooth
        return self.alpha, self.beta
    
    def draw_bar(self, x: int, value: float, max_value: float, color: Tuple[int, int, int], label: str):
        """Dibuja una barra vertical animada."""
        # Calcula altura de la barra
        bar_height_max = SCREEN_HEIGHT - 150  # Espacio para labels
        bar_height = (value / max_value) * bar_height_max
        bar_height = min(bar_height, bar_height_max)
        
        # Posición
        bar_y = SCREEN_HEIGHT - 100 - bar_height
        bar_rect = pygame.Rect(x - BAR_WIDTH // 2, bar_y, BAR_WIDTH, bar_height)
        
        # Dibuja barra con gradiente simulado (3 tonos)
        for i in range(3):
            offset_y = bar_y + (bar_height * i // 3)
            sub_height = bar_height // 3
            brightness = 1.0 - (i * 0.2)
            sub_color = tuple(int(c * brightness) for c in color)
            sub_rect = pygame.Rect(x - BAR_WIDTH // 2, offset_y, BAR_WIDTH, sub_height)
            pygame.draw.rect(self.screen, sub_color, sub_rect)
        
        # Borde
        pygame.draw.rect(self.screen, (255, 255, 255), bar_rect, 2)
        
        # Label
        label_surface = self.font_large.render(label, True, color)
        label_rect = label_surface.get_rect(center=(x, SCREEN_HEIGHT - 60))
        self.screen.blit(label_surface, label_rect)
        
        # Valor numérico
        value_text = f"{int(value)}"
        value_surface = self.font_small.render(value_text, True, COLOR_TEXT)
        value_rect = value_surface.get_rect(center=(x, SCREEN_HEIGHT - 30))
        self.screen.blit(value_surface, value_rect)
    
    def draw_grid(self):
        """Dibuja líneas de referencia."""
        for i in range(1, 5):
            y = 50 + (i * (SCREEN_HEIGHT - 150) // 5)
            pygame.draw.line(self.screen, COLOR_GRID, (50, y), (SCREEN_WIDTH - 50, y), 1)
    
    def draw_ir_indicator(self, alpha: float, beta: float):
        """Dibuja indicador del ratio IR en la parte superior."""
        beta = max(0.1, beta)
        ir = alpha / beta
        
        # Mapeo a rango 0.3-3.0
        ir_normalized = max(0.0, min(1.0, (ir - 0.3) / (3.0 - 0.3)))
        
        # Texto
        if ir_normalized < 0.35:
            state = "ESTRESADO"
            color = (255, 100, 100)
        elif ir_normalized < 0.65:
            state = "NEUTRAL"
            color = (255, 255, 100)
        else:
            state = "RELAJADO"
            color = (100, 255, 100)
        
        text = f"IR: {ir:.2f} - {state}"
        text_surface = self.font_small.render(text, True, color)
        text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, 20))
        self.screen.blit(text_surface, text_rect)
        
        # Barra de IR
        bar_width = 300
        bar_x = (SCREEN_WIDTH - bar_width) // 2
        bar_y = 40
        bar_height = 15
        
        # Fondo
        pygame.draw.rect(self.screen, (50, 50, 50), 
                        (bar_x, bar_y, bar_width, bar_height))
        
        # Relleno según IR
        fill_width = int(bar_width * ir_normalized)
        pygame.draw.rect(self.screen, color, 
                        (bar_x, bar_y, fill_width, bar_height))
        
        # Borde
        pygame.draw.rect(self.screen, (255, 255, 255), 
                        (bar_x, bar_y, bar_width, bar_height), 2)
    
    def render(self):
        """Renderiza el frame completo."""
        # Fondo
        self.screen.fill(COLOR_BG)
        
        # Grid de referencia
        self.draw_grid()
        
        # Obtiene valores suavizados
        alpha_smooth, beta_smooth = self.get_smoothed_values()
        
        # Dibuja barras
        alpha_x = SCREEN_WIDTH // 3
        beta_x = 2 * SCREEN_WIDTH // 3
        
        self.draw_bar(alpha_x, alpha_smooth, MAX_POWER_DISPLAY, COLOR_ALPHA, "ALPHA")
        self.draw_bar(beta_x, beta_smooth, MAX_POWER_DISPLAY, COLOR_BETA, "BETA")
        
        # Indicador IR
        self.draw_ir_indicator(self.alpha, self.beta)
        
        # Estado de conexión
        status = "REAL" if self.use_real_data else "SIMULACIÓN"
        if self.neurosky:
            status += f" - {self.neurosky.connection_status}"
        
        status_surface = self.font_small.render(status, True, COLOR_TEXT)
        self.screen.blit(status_surface, (10, SCREEN_HEIGHT - 25))
    
    def run(self):
        """Bucle principal."""
        print("\n" + "="*60)
        print("📊 Visualizador de Barras EEG")
        print("="*60)
        print("🔵 ALPHA - Banda de relajación")
        print("🟠 BETA  - Banda de actividad/concentración")
        print("\n⌨️  Presiona ESC para salir\n")
        
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
            
            self.update_data()
            self.render()
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        if self.neurosky:
            self.neurosky.stop()
        
        pygame.quit()
        sys.exit()


# ---------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='EEG Bars Visualizer')
    parser.add_argument('--simulate', action='store_true')
    args = parser.parse_args()
    
    visualizer = EEGBarsVisualizer(use_real_data=not args.simulate)
    visualizer.run()