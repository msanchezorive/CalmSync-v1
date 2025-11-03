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

# Códigos de NeuroSky
CODE_HANDLERS_EEG = {0x83: 'eeg_power'}
CODE_HANDLERS_ATT_MED = {0x04: 'attention', 0x05: 'meditation'}

# Índices de bandas
ALPHA_IDX = [2, 3]  # Low-Alpha, High-Alpha
BETA_IDX = [4, 5]   # Low-Beta, High-Beta

# NUEVO: Suavizado más agresivo para evitar cambios bruscos
SMOOTHING_ALPHA = 0.15  # Más lento = más suave (antes era 0.2)
SMOOTHING_IR = 0.1      # Suavizado extra para el índice IR

# NUEVO: Umbrales de calidad de señal
MIN_ATTENTION_QUALITY = 20   # Atención mínima para considerar válido
MIN_MEDITATION_QUALITY = 15  # Meditación mínima para considerar válido

# ---------------------------------------------------------------------
# CONFIGURATION & CONSTANTS
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

# NUEVO: Configuración de rayos
LIGHTNING_DURATION_FRAMES = 5  # Cuánto dura visible un rayo
LIGHTNING_MIN_INTERVAL = 30    # Mínimo frames entre rayos
LIGHTNING_MAX_INTERVAL = 90    # Máximo frames entre rayos


# ---------------------------------------------------------------------
# LECTOR DE NEUROSKY CON FILTRADO DE CALIDAD
# ---------------------------------------------------------------------

class NeuroSkyReader:
    """
    MEJORA 1: Ahora también lee Atención y Meditación para filtrar 
    datos de mala calidad (como al abrir/cerrar ojos).
    """
    
    def __init__(self, port: str, baud: int):
        self.port = port
        self.baud = baud
        
        # Estado actual
        self.alpha = 0.0
        self.beta = 0.0
        self.attention = 0.0      # NUEVO
        self.meditation = 0.0     # NUEVO
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
        """Extrae Alpha del payload."""
        data = extract_data_from_payload(payload, CODE_HANDLERS_EEG)
        if 'eeg_power' in data:
            powers = data['eeg_power']
            alpha_val = sum([powers[i] for i in ALPHA_IDX]) / len(ALPHA_IDX)
            return alpha_val
        return None
    
    def get_beta_from_payload(self, payload: bytes) -> Optional[float]:
        """Extrae Beta del payload."""
        data = extract_data_from_payload(payload, CODE_HANDLERS_EEG)
        if 'eeg_power' in data:
            powers = data['eeg_power']
            beta_val = sum([powers[i] for i in BETA_IDX]) / len(BETA_IDX)
            return beta_val
        return None
    
    def get_attention_meditation(self, payload: bytes) -> Tuple[Optional[float], Optional[float]]:
        """
        MEJORA 2: Extrae Atención y Meditación para validar calidad.
        """
        data = extract_data_from_payload(payload, CODE_HANDLERS_ATT_MED)
        att = data.get('attention')
        med = data.get('meditation')
        return att, med
    
    def _read_loop(self):
        """Bucle de lectura con validación de calidad."""
        try:
            self.serial_port = serial.Serial(self.port, self.baud, timeout=1)
            self.connection_status = "Conectado"
            print(f"✅ NeuroSky conectado en {self.port}")
            
            while self.running:
                payload = parse_packet(self.serial_port)
                
                if payload is None:
                    continue
                
                # Extrae todos los datos
                raw_alpha = self.get_alpha_from_payload(payload)
                raw_beta = self.get_beta_from_payload(payload)
                att, med = self.get_attention_meditation(payload)
                
                with self.lock:
                    # MEJORA 3: Actualiza atención y meditación siempre
                    if att is not None:
                        self.attention = (SMOOTHING_ALPHA * att + 
                                        (1 - SMOOTHING_ALPHA) * self.attention)
                    
                    if med is not None:
                        self.meditation = (SMOOTHING_ALPHA * med + 
                                         (1 - SMOOTHING_ALPHA) * self.meditation)
                    
                    # MEJORA 4: Solo actualiza Alpha/Beta si hay buena calidad
                    # (evita ruido al abrir/cerrar ojos)
                    quality_ok = (self.attention >= MIN_ATTENTION_QUALITY or 
                                 self.meditation >= MIN_MEDITATION_QUALITY)
                    
                    if quality_ok:
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
    
    def get_values(self) -> Tuple[float, float, float, float]:
        """
        MEJORA 5: Ahora también devuelve atención y meditación.
        """
        with self.lock:
            return self.alpha, self.beta, self.attention, self.meditation


# ---------------------------------------------------------------------
# DATA CLASSES
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
class Lightning:
    """
    MEJORA 6: Nueva clase para manejar rayos múltiples.
    """
    x: float
    y: float
    frames_remaining: int
    
    def update(self) -> bool:
        """Retorna True si sigue visible."""
        self.frames_remaining -= 1
        return self.frames_remaining > 0


@dataclass
class GameState:
    alpha: float
    beta: float
    attention: float
    meditation: float
    ir_normalized: float
    ir_smoothed: float  # NUEVO: IR con suavizado extra
    frame_count: int


# ---------------------------------------------------------------------
# ASSET MANAGEMENT
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
# VISUAL EFFECTS
# ---------------------------------------------------------------------

class VisualEffects:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.dark_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

    def draw_with_opacity(self, image: pygame.Surface, pos: Tuple[int, int], opacity: float):
        """
        MEJORA 7: Dibuja imágenes con opacidad controlada.
        """
        opacity = max(0.0, min(1.0, opacity))
        alpha = int(255 * opacity)

        if alpha < 255:
            img_copy = image.copy()
            img_copy.set_alpha(alpha)
            self.screen.blit(img_copy, pos)
        else:
            self.screen.blit(image, pos)

    def draw_dark_overlay(self, opacity: float):
        """Dibuja capa oscura (tormenta)."""
        alpha = int(255 * max(0.0, min(1.0, opacity)))
        self.dark_overlay.fill(COLOR_DARK_OVERLAY + (alpha,))
        self.screen.blit(self.dark_overlay, (0, 0))


# ---------------------------------------------------------------------
# LIGHTNING SYSTEM
# ---------------------------------------------------------------------

class LightningSystem:
    """
    MEJORA 8: Sistema de rayos múltiples que aparecen según el estrés.
    """
    
    def __init__(self, lightning_image: pygame.Surface):
        self.lightning_image = lightning_image
        self.lightnings: List[Lightning] = []
        self.frames_since_last = 0
        self.next_spawn_interval = LIGHTNING_MIN_INTERVAL
    
    def update(self, stress_level: float):
        """
        stress_level: 0.0 = relajado, 1.0 = muy estresado
        """
        # Actualiza rayos existentes
        self.lightnings = [l for l in self.lightnings if l.update()]
        
        # Solo genera rayos si hay suficiente estrés
        if stress_level < 0.3:  # Umbral mínimo de estrés
            self.frames_since_last = 0
            return
        
        self.frames_since_last += 1
        
        # Calcula intervalo basado en estrés (más estrés = más rayos)
        stress_factor = stress_level ** 2  # Cuadrático para más dramatismo
        interval_range = LIGHTNING_MAX_INTERVAL - LIGHTNING_MIN_INTERVAL
        self.next_spawn_interval = int(LIGHTNING_MAX_INTERVAL - 
                                       (interval_range * stress_factor))
        
        # Genera nuevo rayo si es momento
        if self.frames_since_last >= self.next_spawn_interval:
            self.spawn_lightning()
            self.frames_since_last = 0
    
    def spawn_lightning(self):
        """Crea un nuevo rayo en posición aleatoria."""
        x = random.randint(100, SCREEN_WIDTH - 100)
        y = random.randint(50, 200)
        
        self.lightnings.append(Lightning(
            x=x,
            y=y,
            frames_remaining=LIGHTNING_DURATION_FRAMES
        ))
    
    def draw(self, effects: VisualEffects, stress_level: float):
        """Dibuja todos los rayos activos."""
        if stress_level < 0.3:
            return
        
        for lightning in self.lightnings:
            # Opacidad basada en frames restantes (efecto de parpadeo)
            opacity = min(1.0, lightning.frames_remaining / LIGHTNING_DURATION_FRAMES)
            opacity *= stress_level  # También modulado por estrés
            
            effects.draw_with_opacity(
                self.lightning_image,
                (lightning.x, lightning.y),
                opacity
            )


# ---------------------------------------------------------------------
# RAIN SYSTEM
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
# CLOUD SYSTEM
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
# MAIN GAME
# ---------------------------------------------------------------------

class NeurofeedbackGame:
    """Juego de neurofeedback con datos reales y transiciones suaves."""
    
    def __init__(self, use_real_data: bool = True):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("CalmSync - Neurofeedback en Tiempo Real")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)

        # Initialize systems
        self.assets = AssetManager()
        self.effects = VisualEffects(self.screen)

        # Load assets
        self.bg_image = self.assets.load_image('neurofeedback_scenery/paisaje.jpg')
        self.sun_image = self.assets.load_image('neurofeedback_scenery/sol_png.png')
        lightning_image = self.assets.load_image('neurofeedback_scenery/rayo_png.png')
        cloud_image = self.assets.load_image('neurofeedback_scenery/nube_png.png')

        # MEJORA 9: Escala el sol para que sea más visible
        self.sun_image = pygame.transform.scale(self.sun_image, (150, 150))

        # Initialize game systems
        self.rain = RainSystem()
        self.clouds = CloudSystem(cloud_image)
        self.lightning = LightningSystem(lightning_image)  # NUEVO

        # Inicializa NeuroSky
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
            attention=0.0,
            meditation=0.0,
            ir_normalized=0.0,
            ir_smoothed=0.0,  # NUEVO
            frame_count=0
        )

        self.running = True

    def calculate_ir_normalized(self, alpha: float, beta: float) -> float:
        """Calcula IR normalizado."""
        beta = max(0.1, beta)
        ir = alpha / beta
        return max(0.0, min(1.0, (ir - IR_MIN) / IR_RANGE))

    def update_data(self):
        """
        MEJORA 10: Actualiza datos con suavizado extra en el IR.
        """
        if self.use_real_data and self.neurosky:
            # Obtiene datos reales
            alpha, beta, att, med = self.neurosky.get_values()
            self.state.alpha = alpha
            self.state.beta = beta
            self.state.attention = att
            self.state.meditation = med
        else:
            # Datos simulados
            self.state.frame_count += 1
            if self.state.frame_count >= FRAMES_PER_STEP:
                self.state.frame_count = 0
                self.data_index = (self.data_index + 1) % len(self.alpha_data)
            
            self.state.alpha = self.alpha_data[self.data_index]
            self.state.beta = self.beta_data[self.data_index]
            self.state.attention = 50.0
            self.state.meditation = 50.0
        
        # Calcula IR normalizado
        self.state.ir_normalized = self.calculate_ir_normalized(
            self.state.alpha, self.state.beta
        )
        
        # MEJORA 11: Aplica suavizado EXTRA al IR para evitar saltos bruscos
        self.state.ir_smoothed = (SMOOTHING_IR * self.state.ir_normalized + 
                                  (1 - SMOOTHING_IR) * self.state.ir_smoothed)

    def render(self):
        """
        MEJORA 12: Renderizado mejorado con sol visible y rayos.
        """
        # Usa el IR suavizado para transiciones más suaves
        ir_norm = self.state.ir_smoothed
        stress_level = 1.0 - ir_norm  # Inverso: alto estrés = valor alto

        # Parámetros visuales
        sun_opacity = ir_norm ** 0.5  # Raíz cuadrada para que aparezca antes
        cloud_density = stress_level
        rain_density = stress_level
        darkness = stress_level * 0.7  # Menos oscuridad para ver mejor

        # 1. Cielo base
        self.screen.fill(COLOR_SKY)

        # 2. SOL (dibujado PRIMERO para que esté detrás)
        # MEJORA 13: Posición más visible del sol
        sun_x = SCREEN_WIDTH - self.sun_image.get_width() - 80
        sun_y = 30
        self.effects.draw_with_opacity(self.sun_image, (sun_x, sun_y), sun_opacity)

        # 3. Paisaje
        landscape_y = SCREEN_HEIGHT - self.bg_image.get_height()
        self.screen.blit(self.bg_image, (0, landscape_y))

        # 4. Nubes (con densidad según estrés)
        self.clouds.draw(self.effects, cloud_density)

        # 5. Lluvia
        self.rain.draw(self.screen, rain_density)

        # 6. RAYOS (solo cuando hay estrés)
        self.lightning.draw(self.effects, stress_level)

        # 7. Capa oscura (menos intensa para ver mejor)
        self.effects.draw_dark_overlay(darkness)

        # 8. Info en pantalla
        self._draw_info(ir_norm, stress_level)

    def _draw_info(self, ir_norm: float, stress_level: float):
        """Dibuja información en pantalla."""
        text_color = (255, 255, 255) if ir_norm < 0.5 else (50, 50, 50)
        
        lines = [
            f"IR: {ir_norm:.2f} | α: {self.state.alpha:.1f} | β: {self.state.beta:.1f}",
            f"Atención: {self.state.attention:.0f} | Meditación: {self.state.meditation:.0f}",
            f"Estrés: {stress_level*100:.0f}% | Rayos: {len(self.lightning.lightnings)}"
        ]
        
        # Estado mental
        if ir_norm < 0.35:
            state_text = "⚡ ESTRESADO - Respira profundo"
        elif ir_norm < 0.65:
            state_text = "😐 NEUTRAL - Sigue así"
        else:
            state_text = "☀️ RELAJADO - ¡Excelente!"
        lines.append(state_text)
        
        # Modo
        mode = "REAL" if self.use_real_data else "SIMULACIÓN"
        status = self.neurosky.connection_status if self.neurosky else "N/A"
        lines.append(f"Modo: {mode} | Estado: {status}")
        
        # Dibuja cada línea
        for i, line in enumerate(lines):
            text_surface = self.font.render(line, True, text_color)
            self.screen.blit(text_surface, (10, 10 + i * 25))

    def run(self):
        """Bucle principal del juego."""
        print("\n" + "="*60)
        print("🎮 CalmSync - Neurofeedback en Tiempo Real")
        print("="*60)
        print("📊 El escenario cambia según tu estado mental:")
        print("   • Relajado (IR alto)  → ☀️ Sol, cielo despejado")
        print("   • Estresado (IR bajo) → ⚡ Rayos, tormenta")
        print("\n⌨️  Presiona ESC para salir\n")
        
        while self.running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False

            # Actualiza datos
            self.update_data()

            # Actualiza sistemas
            stress_level = 1.0 - self.state.ir_smoothed
            self.rain.update(stress_level)
            self.clouds.update(self.state.ir_smoothed)
            self.lightning.update(stress_level)  # NUEVO

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
    import argparse
    
    parser = argparse.ArgumentParser(description='CalmSync Neurofeedback Game')
    parser.add_argument('--simulate', action='store_true', 
                       help='Usa datos simulados en lugar del NeuroSky')
    args = parser.parse_args()
    
    use_real = not args.simulate
    
    game = NeurofeedbackGame(use_real_data=use_real)
    game.run()