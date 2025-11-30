import pygame
import sys
import threading
import time
from typing import Optional, Tuple
from collections import deque

# Leemos datos desde el servidor EEG central
from udp import EEGClient

# ---------------------------------------------------------------------
# CONFIGURACIÓN VISUAL
# ---------------------------------------------------------------------

SCREEN_WIDTH = 600
SCREEN_HEIGHT = 400
FPS = 30

# Colores
COLOR_BG = (20, 20, 30)
COLOR_ALPHA = (100, 200, 255)  # Azul claro
COLOR_BETA = (255, 150, 100)   # Naranja
COLOR_TEXT = (255, 255, 255)
COLOR_GRID = (50, 50, 70)

# Ancho de barras
BAR_WIDTH = 80
BAR_SPACING = 50

# IR mapping (mismo rango que en el juego)
IR_MIN = 0.3
IR_MAX = 3.0
IR_RANGE = IR_MAX - IR_MIN

# Suavizado extra para la visualización
SMOOTHING_HISTORY = 5


# ---------------------------------------------------------------------
# VISUALIZADOR DE BARRAS
# ---------------------------------------------------------------------

class EEGBarsVisualizer:
    """
    Visualiza Alpha y Beta como barras verticales animadas, 
    leyendo de udp.EEGClient (mismo servidor que el resto de la app).
    """
    
    def __init__(self, use_real_data: bool = True):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("EEG Barras - Alpha & Beta")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 24)
        
        # EEG centralizado vía UDP/TCP
        self.use_real_data = use_real_data
        self.client: Optional[EEGClient] = None
        self.connection_status = "N/A"
        
        if use_real_data:
            try:
                self.client = EEGClient()
                self.client.start()
                self.connection_status = "Conectando al servidor EEG..."
                print("🧠 Modo: Datos reales vía udp.EEGClient")
            except Exception as e:
                print(f"⚠️ Error inicializando EEGClient: {e}")
                print("🎮 Pasando a modo simulación")
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
        self.attention = 0.0
        self.meditation = 0.0
        self.signal_quality = 200  # 0 = perfecto, 200 = sin contacto
        
        # Histórico para suavizado visual
        self.alpha_history = deque(maxlen=SMOOTHING_HISTORY)
        self.beta_history = deque(maxlen=SMOOTHING_HISTORY)

        # Escalado dinámico de las barras
        self.max_alpha_seen = 1.0
        self.max_beta_seen = 1.0
        # Escala mínima para que siempre se vea algo aunque los valores sean bajos
        self.min_display_scale = 1000.0
        
        self.running = True
    
    # -----------------------------------------------------------------
    # ACTUALIZACIÓN DE DATOS
    # -----------------------------------------------------------------
    
    def _update_from_real_eeg(self):
        if not self.client:
            return
        
        data = self.client.get_data()
        self.alpha = float(data.get("alpha", 0.0))
        self.beta = float(data.get("beta", 0.0))
        self.attention = float(data.get("attention", 0.0))
        self.meditation = float(data.get("meditation", 0.0))
        self.signal_quality = int(data.get("signal_quality", 200))
        
        # Estado de conexión textual
        if self.signal_quality >= 200:
            self.connection_status = "Sin señal"
        elif self.signal_quality > 50:
            self.connection_status = f"Conectado (ajusta sensor, ruido={self.signal_quality})"
        else:
            self.connection_status = "Conectado (buena señal)"
    
    def _update_from_simulation(self):
        # Simulación: oscilación automática de alpha/beta
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
        self.attention = 50
        self.meditation = 50
        self.signal_quality = 0
        self.connection_status = "Simulación"
    
    def update_data(self):
        """Actualiza los valores de Alpha y Beta."""
        if self.use_real_data and self.client:
            self._update_from_real_eeg()
        else:
            self._update_from_simulation()
        
        # Suavizado visual adicional
        self.alpha_history.append(self.alpha)
        self.beta_history.append(self.beta)

        # Actualizar máximos vistos para autoescalado
        self.max_alpha_seen = max(self.max_alpha_seen, self.alpha)
        self.max_beta_seen = max(self.max_beta_seen, self.beta)
    
    def get_smoothed_values(self) -> Tuple[float, float]:
        """Retorna valores suavizados para animación fluida."""
        if len(self.alpha_history) > 0:
            alpha_smooth = sum(self.alpha_history) / len(self.alpha_history)
            beta_smooth = sum(self.beta_history) / len(self.beta_history)
            return alpha_smooth, beta_smooth
        return self.alpha, self.beta
    
    # -----------------------------------------------------------------
    # DIBUJO DE ELEMENTOS
    # -----------------------------------------------------------------
    
    def draw_bar(self, x: int, value: float, max_value: float, color: Tuple[int, int, int], label: str):
        """Dibuja una barra vertical animada."""
        # Calcula altura de la barra
        bar_height_max = SCREEN_HEIGHT - 150  # Espacio para labels
        if max_value <= 0:
            max_value = 1.0
        bar_height = (value / max_value) * bar_height_max
        bar_height = max(0, min(bar_height, bar_height_max))
        
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
        """Dibuja líneas de referencia horizontales."""
        for i in range(1, 5):
            y = 50 + (i * (SCREEN_HEIGHT - 150) // 5)
            pygame.draw.line(self.screen, COLOR_GRID, (50, y), (SCREEN_WIDTH - 50, y), 1)
    
    def draw_ir_indicator(self, alpha: float, beta: float):
        """Dibuja indicador del ratio IR en la parte superior."""
        beta = max(0.1, beta)
        ir = alpha / beta
        
        # Normalización al rango 0–1 con IR_MIN/IR_MAX
        ir_normalized = max(0.0, min(1.0, (ir - IR_MIN) / IR_RANGE))
        
        # Estado mental aproximado
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
        
        # Valores suavizados
        alpha_smooth, beta_smooth = self.get_smoothed_values()
        
        # Dibuja barras
        alpha_x = SCREEN_WIDTH // 3
        beta_x = 2 * SCREEN_WIDTH // 3

        # Escalado dinámico: usamos el máximo observado * 1.2,
        # con una escala mínima para que siempre se vea algo.
        alpha_max = max(self.min_display_scale, self.max_alpha_seen * 1.2)
        beta_max = max(self.min_display_scale, self.max_beta_seen * 1.2)
        
        self.draw_bar(alpha_x, alpha_smooth, alpha_max, COLOR_ALPHA, "ALPHA")
        self.draw_bar(beta_x, beta_smooth, beta_max, COLOR_BETA, "BETA")
        
        # Indicador IR
        self.draw_ir_indicator(self.alpha, self.beta)
        
        # Estado de conexión + atención/meditación
        status = "REAL" if self.use_real_data else "SIMULACIÓN"
        status += f" | {self.connection_status}"
        extra = f" | Att: {self.attention:.0f}  Med: {self.meditation:.0f}"
        
        status_surface = self.font_small.render(status + extra, True, COLOR_TEXT)
        self.screen.blit(status_surface, (10, SCREEN_HEIGHT - 25))
    
    # -----------------------------------------------------------------
    # LOOP PRINCIPAL
    # -----------------------------------------------------------------
    
    def run(self):
        """Bucle principal."""
        print("\n" + "="*60)
        print("📊 Visualizador de Barras EEG (udp.EEGClient)")
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
        
        if self.client:
            self.client.stop()
        
        pygame.quit()
        sys.exit()


# ---------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='EEG Bars Visualizer (udp.EEGClient)')
    parser.add_argument('--simulate', action='store_true',
                        help='Usa datos simulados (sin MindWave)')
    args = parser.parse_args()
    
    visualizer = EEGBarsVisualizer(use_real_data=not args.simulate)
    visualizer.run()