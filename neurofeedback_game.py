import pygame
import sys
import random
import os
import threading
import serial
from dataclasses import dataclass
from typing import List, Tuple, Optional

# Importamos las funciones del parser (¡SIN MODIFICAR!)
from generic_parser import parse_packet, extract_data_from_payload

# ---------------------------------------------------------------------
# CONFIGURACIÓN DEL NEUROSKY
# ---------------------------------------------------------------------

# ¡CAMBIA ESTO SEGÚN TU SISTEMA!
NEUROSKY_PORT = "/dev/tty.MindWaveMobile"  # o "COM10" en Windows
NEUROSKY_BAUD = 57600

# Códigos de NeuroSky (mismo que en more_functions)
CODE_HANDLERS_EEG = {0x83: 'eeg_power'}

# Índices de bandas (mismo que en more_functions)
ALPHA_IDX = [2, 3]  # Low-Alpha, High-Alpha
BETA_IDX = [4, 5]   # Low-Beta, High-Beta

# Suavizado exponencial (mismo que en more_functions)
SMOOTHING_ALPHA = 0.2

# ---------------------------------------------------------------------
# CONFIGURATION & CONSTANTS (del juego original)
# ---------------------------------------------------------------------

ASSETS_PATH = 'assets'
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 30

COLOR_SKY = (20, 20, 30)
COLOR_RAIN = (100, 100, 120)
COLOR_DARK_OVERLAY = (0, 0, 0)

FRAMES_PER_STEP = 30
MAX_RAIN_PARTICLES = 200
RAIN_FALL_SPEED = 15
CLOUD_BASE_SPEED = 5
RAIN_LENGTH_RANGE = (5, 10)

# IR mapping constants
IR_MIN = 0.3
IR_MAX = 3.0
IR_RANGE = IR_MAX - IR_MIN


# ---------------------------------------------------------------------
# NUEVO: LECTOR DE NEUROSKY EN TIEMPO REAL
# ---------------------------------------------------------------------

class NeuroSkyReader:
    """
    Lee datos del NeuroSky en un hilo separado.
    
    PASO 1: Usa las mismas funciones de 'more_functions.py' pero adaptadas
    para que se ejecuten continuamente en segundo plano.
    """
    
    def __init__(self, port: str, baud: int):
        self.port = port
        self.baud = baud
        
        # Estado actual (igual que en more_functions)
        self.alpha = 0.0
        self.beta = 0.0
        self.last_raw_alpha = 0.0
        self.last_raw_beta = 0.0
        
        # Control del hilo
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.serial_port: Optional[serial.Serial] = None
        self.connection_status = "Desconectado"
        
        # Lock para acceso thread-safe
        self.lock = threading.Lock()
    
    def get_alpha_from_payload(self, payload: bytes) -> Optional[float]:
        """
        PASO 2: Extrae Alpha del payload (copiado de more_functions.py)
        """
        data = extract_data_from_payload(payload, CODE_HANDLERS_EEG)
        if 'eeg_power' in data:
            powers = data['eeg_power']
            alpha_val = sum([powers[i] for i in ALPHA_IDX]) / len(ALPHA_IDX)
            return alpha_val
        return None
    
    def get_beta_from_payload(self, payload: bytes) -> Optional[float]:
        """
        PASO 3: Extrae Beta del payload (copiado de more_functions.py)
        """
        data = extract_data_from_payload(payload, CODE_HANDLERS_EEG)
        if 'eeg_power' in data:
            powers = data['eeg_power']
            beta_val = sum([powers[i] for i in BETA_IDX]) / len(BETA_IDX)
            return beta_val
        return None
    
    def _read_loop(self):
        """
        PASO 4: Bucle continuo que lee del puerto serial.
        Se ejecuta en un hilo separado para no bloquear el juego.
        """
        try:
            self.serial_port = serial.Serial(self.port, self.baud, timeout=1)
            self.connection_status = "Conectado"
            print(f"✅ NeuroSky conectado en {self.port}")
            
            while self.running:
                # Lee un paquete usando el parser genérico
                payload = parse_packet(self.serial_port)
                
                if payload is None:
                    continue
                
                # Extrae Alpha y Beta
                raw_alpha = self.get_alpha_from_payload(payload)
                raw_beta = self.get_beta_from_payload(payload)
                
                # PASO 5: Aplica suavizado exponencial (mismo que more_functions)
                with self.lock:  # Thread-safe
                    if raw_alpha is not None:
                        self.last_raw_alpha = raw_alpha
                        self.alpha = (SMOOTHING_ALPHA * raw_alpha + 
                                    (1 - SMOOTHING_ALPHA) * self.alpha)
                    
                    if raw_beta is not None:
                        self.last_raw_beta = raw_beta
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
        """Inicia la lectura en segundo plano."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._read_loop, daemon=True)
            self.thread.start()
    
    def stop(self):
        """Detiene la lectura."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
    
    def get_values(self) -> Tuple[float, float]:
        """
        PASO 6: Obtiene valores suavizados de forma thread-safe.
        El juego llamará a esto en cada frame.
        """
        with self.lock:
            return self.alpha, self.beta


# ---------------------------------------------------------------------
# DATA CLASSES (sin cambios)
# ---------------------------------------------------------------------

@dataclass
class RainParticle:
    x: float
    y: float
    length: int

    def update(self) -> bool:
        self.y += RAIN_FALL_SPEED
        return self.y < SCREEN_HEIGHT


@dataclass
class GameState:
    alpha: float
    beta: float
    ir_normalized: float
    frame_count: int


# ---------------------------------------------------------------------
# ASSET MANAGEMENT (sin cambios)
# ---------------------------------------------------------------------

class AssetManager:
    def __init__(self):
        self.images = {}

    def load_image(self, filename: str, use_alpha: bool = True) -> pygame.Surface:
        if filename in self.images:
            return self.images[filename]

        path = os.path.join(ASSETS_PATH, filename)
        try:
            img = pygame.image.load(path)
            img = img.convert_alpha() if use_alpha else img.convert()
            self.images[filename] = img
            return img
        except pygame.error as e:
            print(f"Error loading {filename}: {e}")
            placeholder = pygame.Surface((100, 100))
            placeholder.fill((255, 0, 255))
            self.images[filename] = placeholder
            return placeholder

    def get_image(self, filename: str) -> pygame.Surface:
        return self.images.get(filename)


# ---------------------------------------------------------------------
# VISUAL EFFECTS (sin cambios)
# ---------------------------------------------------------------------

class VisualEffects:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.dark_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

    def draw_with_opacity(self, image: pygame.Surface, pos: Tuple[int, int], opacity: float):
        opacity = max(0.0, min(1.0, opacity))
        alpha = int(255 * opacity)

        if alpha < 255:
            img_copy = image.copy()
            img_copy.set_alpha(alpha)
            self.screen.blit(img_copy, pos)
        else:
            self.screen.blit(image, pos)

    def draw_dark_overlay(self, opacity: float):
        alpha = int(255 * max(0.0, min(1.0, opacity)))
        self.dark_overlay.fill(COLOR_DARK_OVERLAY + (alpha,))
        self.screen.blit(self.dark_overlay, (0, 0))


# ---------------------------------------------------------------------
# RAIN SYSTEM (sin cambios)
# ---------------------------------------------------------------------

class RainSystem:
    def __init__(self):
        self.particles: List[RainParticle] = []

    def update(self, density: float):
        target_count = int(MAX_RAIN_PARTICLES * density)
        spawn_probability = density * 0.5
        
        while len(self.particles) < target_count and random.random() < spawn_probability:
            self.particles.append(RainParticle(
                x=random.randint(0, SCREEN_WIDTH),
                y=random.randint(-50, 0),
                length=random.randint(*RAIN_LENGTH_RANGE)
            ))

        self.particles = [p for p in self.particles if p.update()]

    def draw(self, screen: pygame.Surface, density: float):
        if density < 0.05:
            return

        alpha = int(255 * density)
        color = COLOR_RAIN + (alpha,)

        for p in self.particles:
            pygame.draw.line(screen, color, (p.x, p.y), (p.x, p.y + p.length), 1)


# ---------------------------------------------------------------------
# CLOUD SYSTEM (sin cambios)
# ---------------------------------------------------------------------

class CloudSystem:
    def __init__(self, cloud_image: pygame.Surface):
        self.cloud_image = cloud_image
        self.offset1 = 0
        self.offset2 = SCREEN_WIDTH / 2
        self.image_width = cloud_image.get_width()

    def update(self, relaxation_level: float):
        speed = (1.0 - (1.0 - relaxation_level)) * CLOUD_BASE_SPEED

        self.offset1 -= speed
        if self.offset1 < -self.image_width:
            self.offset1 = 0

        self.offset2 += speed
        if self.offset2 > SCREEN_WIDTH:
            self.offset2 = SCREEN_WIDTH / 2

    def draw(self, effects: VisualEffects, density: float):
        effects.draw_with_opacity(self.cloud_image, (self.offset1, 0), density)
        effects.draw_with_opacity(self.cloud_image, (self.offset2, 50), density)


# ---------------------------------------------------------------------
# MAIN GAME - MODIFICADO PARA USAR DATOS REALES
# ---------------------------------------------------------------------

class NeurofeedbackGame:
    """
    PASO 7: Juego modificado para usar datos reales del NeuroSky
    en lugar de datos simulados.
    """
    
    def __init__(self, use_real_data: bool = True):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("CalmSync - Neurofeedback en Tiempo Real")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 28)

        # Initialize systems
        self.assets = AssetManager()
        self.effects = VisualEffects(self.screen)

        # Load assets
        self.bg_image = self.assets.load_image('neurofeedback_scenery/paisaje.jpg')
        self.sun_image = self.assets.load_image('neurofeedback_scenery/sol_png.png')
        self.lightning_image = self.assets.load_image('neurofeedback_scenery/rayo_png.png')
        cloud_image = self.assets.load_image('neurofeedback_scenery/nube_png.png')

        # Initialize game systems
        self.rain = RainSystem()
        self.clouds = CloudSystem(cloud_image)

        # PASO 8: Inicializa el lector de NeuroSky
        self.use_real_data = use_real_data
        self.neurosky: Optional[NeuroSkyReader] = None
        
        if use_real_data:
            try:
                self.neurosky = NeuroSkyReader(NEUROSKY_PORT, NEUROSKY_BAUD)
                self.neurosky.start()
                print("🧠 Modo: Datos reales del NeuroSky")
            except Exception as e:
                print(f"⚠️ No se pudo conectar al NeuroSky: {e}")
                print("🎮 Cambiando a modo simulación")
                self.use_real_data = False
        else:
            print("🎮 Modo: Simulación de datos")

        # Datos de simulación (fallback)
        self.alpha_data = [3.0, 3.5, 4.0, 4.5, 5.0, 6.0, 7.0, 8.0, 9.0]
        self.beta_data = [9.0, 8.0, 7.0, 6.0, 5.0, 4.5, 4.0, 3.5, 3.0]
        self.data_index = 0

        # Game state
        self.state = GameState(
            alpha=3.0,
            beta=9.0,
            ir_normalized=0.0,
            frame_count=0
        )

        self.running = True

    def calculate_ir_normalized(self, alpha: float, beta: float) -> float:
        """
        PASO 9: Calcula el IR normalizado (mismo algoritmo que antes).
        Este valor modula el escenario entre tormenta (0.0) y calma (1.0).
        """
        beta = max(0.1, beta)  # Evita división por cero
        ir = alpha / beta
        return max(0.0, min(1.0, (ir - IR_MIN) / IR_RANGE))

    def update_data(self):
        """
        PASO 10: Actualiza los datos de Alpha/Beta según la fuente activa.
        """
        if self.use_real_data and self.neurosky:
            # Obtiene datos reales del NeuroSky
            self.state.alpha, self.state.beta = self.neurosky.get_values()
        else:
            # Usa datos simulados (para testing)
            self.state.frame_count += 1
            if self.state.frame_count >= FRAMES_PER_STEP:
                self.state.frame_count = 0
                self.data_index = (self.data_index + 1) % len(self.alpha_data)
            
            self.state.alpha = self.alpha_data[self.data_index]
            self.state.beta = self.beta_data[self.data_index]
        
        # PASO 11: Calcula el IR normalizado que controla el escenario
        self.state.ir_normalized = self.calculate_ir_normalized(
            self.state.alpha, self.state.beta
        )

    def render(self):
        """Renderiza el frame actual (sin cambios en la lógica visual)."""
        ir_norm = self.state.ir_normalized

        # Parámetros visuales basados en IR
        filter_opacity = 1.0 - ir_norm
        sun_opacity = ir_norm
        cloud_density = 1.0 - ir_norm
        rain_density = 1.0 - ir_norm

        # Draw sky
        self.screen.fill(COLOR_SKY)

        # Draw sun (más visible cuando relajado)
        sun_pos = (SCREEN_WIDTH - self.sun_image.get_width() - 50, 50)
        self.effects.draw_with_opacity(self.sun_image, sun_pos, sun_opacity)

        # Draw landscape
        landscape_y = SCREEN_HEIGHT - self.bg_image.get_height()
        self.screen.blit(self.bg_image, (0, landscape_y))

        # Draw clouds
        self.clouds.draw(self.effects, cloud_density)

        # Draw rain
        self.rain.draw(self.screen, rain_density)

        # Draw dark overlay (más oscuro cuando estresado)
        self.effects.draw_dark_overlay(filter_opacity)

        # PASO 12: Info mejorada en pantalla
        text_color = (255, 255, 255) if ir_norm < 0.5 else (0, 0, 0)
        
        # Línea 1: Datos principales
        text1 = f"IR: {ir_norm:.2f} | α: {self.state.alpha:.1f} | β: {self.state.beta:.1f}"
        text_surface1 = self.font.render(text1, True, text_color)
        self.screen.blit(text_surface1, (10, 10))
        
        # Línea 2: Estado
        mode = "REAL" if self.use_real_data else "SIMULACIÓN"
        status = self.neurosky.connection_status if self.neurosky else "N/A"
        text2 = f"Modo: {mode} | Estado: {status}"
        text_surface2 = self.font.render(text2, True, text_color)
        self.screen.blit(text_surface2, (10, 40))
        
        # Línea 3: Interpretación
        if ir_norm < 0.4:
            state_text = "ESTRESADO - Respira profundo"
        elif ir_norm < 0.7:
            state_text = "NEUTRAL - Sigue así"
        else:
            state_text = "RELAJADO - Excelente!"
        text_surface3 = self.font.render(state_text, True, text_color)
        self.screen.blit(text_surface3, (10, 70))

    def run(self):
        """Bucle principal del juego."""
        print("\n" + "="*60)
        print("🎮 CalmSync - Neurofeedback en Tiempo Real")
        print("="*60)
        print("📊 El escenario cambia según tu estado mental:")
        print("   • Alpha alto + Beta bajo = Relajación → ☀️ Sol brillante")
        print("   • Alpha bajo + Beta alto = Estrés → 🌧️ Tormenta")
        print("\n⌨️  Presiona ESC para salir\n")
        
        while self.running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False

            # PASO 13: Actualiza datos (reales o simulados)
            self.update_data()

            # Update systems
            rain_density = 1.0 - self.state.ir_normalized
            self.rain.update(rain_density)
            self.clouds.update(self.state.ir_normalized)

            # Render
            self.render()

            # Update display
            pygame.display.flip()
            self.clock.tick(FPS)

        # Cleanup
        if self.neurosky:
            self.neurosky.stop()
        
        pygame.quit()
        sys.exit()


# ---------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------

if __name__ == "__main__":
    # PASO 14: Puedes elegir el modo al ejecutar
    import argparse
    
    parser = argparse.ArgumentParser(description='CalmSync Neurofeedback Game')
    parser.add_argument('--simulate', action='store_true', 
                       help='Usa datos simulados en lugar del NeuroSky')
    args = parser.parse_args()
    
    use_real = not args.simulate
    
    game = NeurofeedbackGame(use_real_data=use_real)
    game.run()