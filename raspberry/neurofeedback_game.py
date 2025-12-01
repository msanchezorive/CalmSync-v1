import pygame
import sys
import random
import os
import time
import statistics
from dataclasses import dataclass
from typing import List, Tuple, Optional

# NUEVO: leemos datos del MindWave a través del servidor TCP de udp.py
from udp import EEGClient

# ---------------------------------------------------------------------
# CONSTANTES GENERALES / CONFIG
# ---------------------------------------------------------------------

# BASE_DIR = carpeta raíz del proyecto (la que tiene 'assets' y 'raspberry')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_PATH = os.path.join(BASE_DIR, 'assets')
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

# IR mapping constants (para IR α/β, solo informativo ahora)
IR_MIN = 0.3
IR_MAX = 3.0
IR_RANGE = IR_MAX - IR_MIN

# Transición por etapas
LIGHTNING_END_THRESHOLD = 0.50    # A partir de aquí no hay rayos
SUN_START_THRESHOLD = 0.55        # A partir de aquí empieza a aparecer el sol
TRANSITION_OVERLAP = 0.05         # Pequeño solapamiento visual

# Configuración rayos
LIGHTNING_DURATION_FRAMES = 5
LIGHTNING_MIN_INTERVAL = 30
LIGHTNING_MAX_INTERVAL = 90

# Índices EEG (coinciden con udp.py si se usan)
ALPHA_IDX = [2, 3]
BETA_IDX = [4, 5]

# Suavizado
SMOOTHING_ALPHA = 0.15   # para señales EEG / eSense
SMOOTHING_IR = 0.1       # para el índice visual

# Calibración interna del IR α/β (solo para mostrar info)
CALIBRATION_DURATION = 10.0
CALIBRATION_STABLE_SECONDS = 2.0
CALIBRATION_MIN_CONFIDENCE = 0.65
CALIBRATION_MIN_SAMPLES = 90
CALIBRATION_STD_RANGE = 2.0
CALIBRATION_MIN_STD = 0.02

# Limitadores de transición IR
IR_MAX_STEP_UP = 0.06
IR_MAX_STEP_DOWN = 0.08

# Filtro ojos
EYE_FAST_ALPHA = 0.4
EYE_SLOW_ALPHA = 0.05
EYE_SPIKE_THRESHOLD = 1.7
EYE_DROP_THRESHOLD = 0.65
EYE_MIN_DELTA = 0.3
EYE_SUPPRESSION_GAIN = 0.45
EYE_SUPPRESSION_DECAY = 1.4  # s

# Sistema de confianza gradual
CONFIDENCE_INCREASE_RATE = 0.05
CONFIDENCE_DECREASE_RATE = 0.02
MIN_CONFIDENCE_THRESHOLD = 0.3


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
    x: float
    y: float
    frames_remaining: int
    
    def update(self) -> bool:
        self.frames_remaining -= 1
        return self.frames_remaining > 0


@dataclass
class GameState:
    alpha: float
    beta: float
    attention: float
    meditation: float
    confidence: float
    ir_normalized: float  # IR α/β normalizado (solo info)
    ir_smoothed: float    # IR α/β suavizado (solo info)
    frame_count: int


@dataclass
class BaselineProfile:
    """Perfil estadístico personal para normalizar IR α/β."""
    mean: float
    std: float

    @property
    def lower(self) -> float:
        return self.mean - CALIBRATION_STD_RANGE * self.std

    @property
    def upper(self) -> float:
        return self.mean + CALIBRATION_STD_RANGE * self.std

    def normalize(self, ratio: float) -> float:
        span = self.upper - self.lower
        if span <= 0:
            return 0.5
        return max(0.0, min(1.0, (ratio - self.lower) / span))


class EyeArtifactFilter:
    """Detecta cierres/aperturas de ojos y amortigua su impacto en el IR (α/β)."""

    def __init__(self):
        self.fast_alpha: Optional[float] = None
        self.slow_alpha: Optional[float] = None
        self.suppression = 0.0
        self.last_clean_ir = 0.5
        self.last_time = time.time()

    def update_alpha(self, alpha_value: float):
        alpha_value = max(alpha_value, 1e-6)
        if self.fast_alpha is None or self.slow_alpha is None:
            self.fast_alpha = alpha_value
            self.slow_alpha = alpha_value
            return

        self.fast_alpha += (alpha_value - self.fast_alpha) * EYE_FAST_ALPHA
        self.slow_alpha += (alpha_value - self.slow_alpha) * EYE_SLOW_ALPHA

        if self.slow_alpha <= 0:
            return

        ratio = self.fast_alpha / self.slow_alpha
        delta = abs(self.fast_alpha - self.slow_alpha)

        if ratio >= EYE_SPIKE_THRESHOLD and delta >= EYE_MIN_DELTA:
            self._boost_suppression(1.0)
        elif ratio <= EYE_DROP_THRESHOLD and delta >= EYE_MIN_DELTA:
            self._boost_suppression(0.6)

    def _boost_suppression(self, intensity: float):
        self.suppression = min(1.0, self.suppression + intensity * EYE_SUPPRESSION_GAIN)

    def apply(self, ir_value: float) -> float:
        now = time.time()
        dt = now - self.last_time
        self.last_time = now

        if self.suppression > 0.0:
            decay = dt / max(EYE_SUPPRESSION_DECAY, 1e-3)
            self.suppression = max(0.0, self.suppression - decay)
            blended = ((1 - self.suppression) * ir_value +
                       self.suppression * self.last_clean_ir)
        else:
            blended = ir_value

        if self.suppression < 0.05:
            self.last_clean_ir = blended

        return blended


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


# ---------------------------------------------------------------------
# VISUAL EFFECTS
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
# LIGHTNING SYSTEM
# ---------------------------------------------------------------------

class LightningSystem:
    def __init__(self, lightning_image: pygame.Surface):
        self.lightning_image = lightning_image
        self.lightnings: List[Lightning] = []
        self.frames_since_last = 0
        self.next_spawn_interval = LIGHTNING_MIN_INTERVAL
    
    def update(self, stress_level: float, ir_normalized: float):
        # Elimina rayos expirados
        self.lightnings = [l for l in self.lightnings if l.update()]
        
        # Si el índice de calma ya es suficientemente alto, no hay rayos
        if ir_normalized >= LIGHTNING_END_THRESHOLD:
            self.frames_since_last = 0
            return
        
        # Intensidad de rayos según índice (baja calma → más rayos)
        lightning_intensity = max(0.0, (LIGHTNING_END_THRESHOLD - ir_normalized) / LIGHTNING_END_THRESHOLD)
        if lightning_intensity < 0.05:
            self.frames_since_last = 0
            return
        
        self.frames_since_last += 1
        
        # Intervalo entre rayos según intensidad
        intensity_squared = lightning_intensity ** 2
        interval_range = LIGHTNING_MAX_INTERVAL - LIGHTNING_MIN_INTERVAL
        self.next_spawn_interval = int(
            LIGHTNING_MAX_INTERVAL - (interval_range * intensity_squared)
        )
        
        if self.frames_since_last >= self.next_spawn_interval:
            self.spawn_lightning()
            self.frames_since_last = 0
    
    def spawn_lightning(self):
        x = random.randint(100, SCREEN_WIDTH - 100)
        y = random.randint(50, 200)
        
        self.lightnings.append(Lightning(
            x=x,
            y=y,
            frames_remaining=LIGHTNING_DURATION_FRAMES
        ))
    
    def draw(self, effects: VisualEffects, ir_normalized: float):
        if ir_normalized >= LIGHTNING_END_THRESHOLD:
            return
        
        max_opacity = max(0.0, (LIGHTNING_END_THRESHOLD - ir_normalized) / LIGHTNING_END_THRESHOLD)
        
        for lightning in self.lightnings:
            frame_opacity = min(1.0, lightning.frames_remaining / LIGHTNING_DURATION_FRAMES)
            final_opacity = frame_opacity * max_opacity
            
            effects.draw_with_opacity(
                self.lightning_image,
                (lightning.x, lightning.y),
                final_opacity
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
# JUEGO PRINCIPAL
# ---------------------------------------------------------------------

class NeurofeedbackGame:
    def __init__(self, use_real_data: bool = True):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("CalmSync - Neurofeedback")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)

        # Sistemas visuales
        self.assets = AssetManager()
        self.effects = VisualEffects(self.screen)

        # Cargar assets
        self.bg_image = self.assets.load_image('neurofeedback_scenery/paisaje.jpg')
        self.sun_image = self.assets.load_image('neurofeedback_scenery/sol_png.png')
        lightning_image = self.assets.load_image('neurofeedback_scenery/rayo_png.png')
        cloud_image = self.assets.load_image('neurofeedback_scenery/nube_png.png')

        # Escalado del sol
        self.sun_image = pygame.transform.scale(self.sun_image, (150, 150))

        # Sistemas de clima
        self.rain = RainSystem()
        self.clouds = CloudSystem(cloud_image)
        self.lightning = LightningSystem(lightning_image)

        # EEG: ahora a través de udp.EEGClient
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
                print(f"⚠️ No se pudo inicializar EEGClient: {e}")
                print("🎮 Cambiando a modo simulación")
                self.use_real_data = False
        else:
            print("🎮 Modo: Simulación de datos")

        # Datos simulación (por si no hay sensor)
        self.alpha_data = [3.0, 3.5, 4.0, 4.5, 5.0, 6.0, 7.0, 8.0, 9.0]
        self.beta_data = [9.0, 8.0, 7.0, 6.0, 5.0, 4.5, 4.0, 3.5, 3.0]
        self.data_index = 0

        # Estado de juego
        self.state = GameState(
            alpha=3.0,
            beta=9.0,
            attention=0.0,
            meditation=0.0,
            confidence=0.0,
            ir_normalized=0.0,
            ir_smoothed=0.0,
            frame_count=0
        )

        self.running = True
        self._ir_initialized = False
        self.calibration_profile: Optional[BaselineProfile] = None
        self.calibration_summary = "Pendiente"
        if not self.use_real_data:
            self.calibration_summary = "Global (simulación)"
        self.eye_filter = EyeArtifactFilter()

    # ------------------------ LÓGICA IR / CALM ------------------------

    def _compute_ir_ratio(self, alpha: float, beta: float) -> float:
        """IR real α/β, solo para información."""
        beta = max(0.1, beta)
        return alpha / beta

    def calculate_ir_normalized(self, alpha: float, beta: float) -> float:
        ratio = self._compute_ir_ratio(alpha, beta)
        if self.calibration_profile:
            return self.calibration_profile.normalize(ratio)
        return max(0.0, min(1.0, (ratio - IR_MIN) / IR_RANGE))

    def _limit_ir_transition(self, previous: float, target: float) -> float:
        if not self._ir_initialized:
            self._ir_initialized = True
            return target

        delta = target - previous
        if delta > 0:
            delta = min(delta, IR_MAX_STEP_UP)
        else:
            delta = max(delta, -IR_MAX_STEP_DOWN)
        return previous + delta

    def compute_calm_level(self) -> float:
        """
        Índice de calma basado en eSense:
        - meditation alta → más calma
        - attention alta → resta calma
        Resultado en [0, 1].
        """
        med_norm = max(0.0, min(1.0, self.state.meditation / 100.0))
        att_norm = max(0.0, min(1.0, self.state.attention / 100.0))

        calm = 0.7 * med_norm + 0.3 * (1.0 - att_norm)
        return max(0.0, min(1.0, calm))

    # ------------------------ DATOS EEG ------------------------

    def _update_from_real_eeg(self):
        """
        Actualiza self.state usando datos de EEGClient
        y reconstruye el sistema de confianza gradual.
        """
        if not self.client:
            return

        data = self.client.get_data()
        raw_alpha = data.get("alpha", 0.0)
        raw_beta = data.get("beta", 0.0)
        raw_att = float(data.get("attention", 0))
        raw_med = float(data.get("meditation", 0))
        signal_quality = data.get("signal_quality", 200)

        # Atención y meditación suavizadas
        self.state.attention = (SMOOTHING_ALPHA * raw_att +
                                (1 - SMOOTHING_ALPHA) * self.state.attention)
        self.state.meditation = (SMOOTHING_ALPHA * raw_med +
                                 (1 - SMOOTHING_ALPHA) * self.state.meditation)

        # Confianza basada en atención/meditación
        if self.state.attention >= 20 or self.state.meditation >= 15:
            self.state.confidence = min(1.0, self.state.confidence + CONFIDENCE_INCREASE_RATE)
        else:
            self.state.confidence = max(0.0, self.state.confidence - CONFIDENCE_DECREASE_RATE)

        # Alpha/Beta suavizados y ponderados por confianza
        new_alpha = (SMOOTHING_ALPHA * raw_alpha +
                     (1 - SMOOTHING_ALPHA) * self.state.alpha)
        new_beta = (SMOOTHING_ALPHA * raw_beta +
                    (1 - SMOOTHING_ALPHA) * self.state.beta)

        c = self.state.confidence
        self.state.alpha = self.state.alpha * (1 - c) + new_alpha * c
        self.state.beta = self.state.beta * (1 - c) + new_beta * c

        # Estado de conexión (texto)
        if signal_quality >= 200:
            self.connection_status = "Sin señal"
        elif signal_quality > 50:
            self.connection_status = f"Conectado (ajusta sensor, ruido={signal_quality})"
        else:
            self.connection_status = "Conectado (buena señal)"

    def _update_from_simulation(self):
        self.state.frame_count += 1
        if self.state.frame_count >= FRAMES_PER_STEP:
            self.state.frame_count = 0
            self.data_index = (self.data_index + 1) % len(self.alpha_data)
        
        self.state.alpha = self.alpha_data[self.data_index]
        self.state.beta = self.beta_data[self.data_index]
        self.state.attention = 50.0
        self.state.meditation = 50.0
        self.state.confidence = 1.0

    def update_data(self):
        """Actualiza alpha/beta/IR y aplica filtro de ojos (para IR α/β informativo)."""
        if self.use_real_data and self.client:
            self._update_from_real_eeg()
        else:
            self._update_from_simulation()

        # Filtro de artefactos de ojos (usando alpha)
        self.eye_filter.update_alpha(self.state.alpha)
        
        # IR α/β normalizado (antes de filtro ojos, solo info)
        self.state.ir_normalized = self.calculate_ir_normalized(
            self.state.alpha, self.state.beta
        )

        # Filtro de ojos sobre el IR α/β
        filtered_ir = self.eye_filter.apply(self.state.ir_normalized)
        
        # Suavizado + limitadores de transición para IR α/β (solo info)
        blended = (SMOOTHING_IR * filtered_ir + 
                   (1 - SMOOTHING_IR) * self.state.ir_smoothed)
        self.state.ir_smoothed = self._limit_ir_transition(self.state.ir_smoothed, blended)

    # ------------------------ CALIBRACIÓN INTERNA IR α/β ------------------------

    def perform_calibration(self):
        """
        Calibración interna del IR α/β (distinta de initial_calibration.py).
        Ahora lee los datos de EEGClient a través de update_data().
        """
        if not self.use_real_data or not self.client:
            return

        print("\n🧘 Iniciando calibración personalizada de IR (α/β)...")
        print("   Si ya has hecho la 'initial calibration', esto ajusta solo tu rango α/β.\n")

        samples: List[float] = []
        stable_start: Optional[float] = None
        collection_start: Optional[float] = None

        while self.running:
            # Eventos pygame
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                        return
                    if event.key == pygame.K_SPACE:
                        print("⏭️  Calibración IR omitida por el usuario.")
                        self.calibration_summary = "Manual"
                        return

            # Actualiza datos desde EEG
            self.update_data()

            alpha = self.state.alpha
            beta = self.state.beta
            confidence = self.state.confidence
            ratio = self._compute_ir_ratio(alpha, beta)

            # Lógica de recogida de muestras
            collecting = False
            if confidence >= CALIBRATION_MIN_CONFIDENCE:
                if stable_start is None:
                    stable_start = time.time()
                    collection_start = None
                    samples.clear()

                stable_elapsed = time.time() - stable_start
                if stable_elapsed >= CALIBRATION_STABLE_SECONDS:
                    collecting = True
                    if collection_start is None:
                        collection_start = time.time()
                        samples.clear()
                    samples.append(ratio)
            else:
                stable_start = None
                collection_start = None
                samples.clear()

            progress = 0.0
            if collection_start:
                progress = min(1.0, (time.time() - collection_start) / CALIBRATION_DURATION)

            collecting_enough = (
                collection_start is not None and
                (time.time() - collection_start) >= CALIBRATION_DURATION and
                len(samples) >= CALIBRATION_MIN_SAMPLES
            )

            self._render_calibration_screen(
                progress=progress,
                confidence=confidence,
                samples=len(samples),
                collecting=collecting,
                stable=stable_start is not None
            )
            pygame.display.flip()
            self.clock.tick(FPS)

            if collecting_enough:
                break

        if not samples:
            print("⚠️ No se pudo calcular baseline de IR. Se usa mapeo genérico.")
            self.calibration_summary = "Fallback"
            return

        mean_value = statistics.fmean(samples)
        if len(samples) > 1:
            std_value = statistics.pstdev(samples)
        else:
            std_value = 0.0

        adaptive_floor = max(CALIBRATION_MIN_STD, abs(mean_value) * 0.05)
        std_value = max(std_value, adaptive_floor)

        self.calibration_profile = BaselineProfile(mean=mean_value, std=std_value)
        self.calibration_summary = f"µ={mean_value:.2f} σ={std_value:.2f}"

        print(f"✅ Calibración IR lista: {self.calibration_summary}")
        print(f"   Rango útil: {self.calibration_profile.lower:.2f} - {self.calibration_profile.upper:.2f}\n")

    def _render_calibration_screen(self, progress: float, confidence: float,
                                   samples: int, collecting: bool, stable: bool):
        self.screen.fill((15, 20, 35))

        title = self.font.render("Calibrando baseline personal (IR α/β)...", True, (200, 220, 255))
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 80))

        instructions = [
            "1. Mantén postura cómoda y mira un punto fijo.",
            "2. Respira profundo y relaja los hombros.",
            "3. Cuando veas el progreso completo la calibración termina.",
            "Pulsa ESPACIO para saltar o ESC para salir."
        ]

        for i, text in enumerate(instructions):
            surface = self.font.render(text, True, (180, 200, 230))
            self.screen.blit(surface, (80, 140 + i * 28))

        bar_width = SCREEN_WIDTH - 160
        bar_height = 20
        pygame.draw.rect(self.screen, (60, 60, 80), (80, 280, bar_width, bar_height), border_radius=8)
        inner_width = int(bar_width * progress)
        pygame.draw.rect(self.screen, (80, 200, 140), (80, 280, inner_width, bar_height), border_radius=8)

        status = f"Confianza: {confidence*100:.0f}% | Muestras: {samples}"
        stable_text = "Estable" if stable else "Esperando señal estable"
        collecting_text = "Capturando..." if collecting else "Preparando..."

        for idx, text in enumerate([status, stable_text, collecting_text, f"Baseline IR: {self.calibration_summary}"]):
            surface = self.font.render(text, True, (200, 200, 210))
            self.screen.blit(surface, (80, 320 + idx * 28))

    # ------------------------ RENDERIZADO PRINCIPAL ------------------------

    def render(self):
        """
        Orden de dibujo (cielo → paisaje → sol → nubes → lluvia → rayos → overlay → HUD).
        El clima ahora depende de CalmIdx (attention + meditation).
        """
        # Índice de calma [0,1] basado en eSense
        calm_level = self.compute_calm_level()

        # Reutilizamos ir_norm como índice de calma para el clima
        ir_norm = calm_level
        stress_level = 1.0 - ir_norm

        # Opacidad del sol
        if ir_norm < SUN_START_THRESHOLD:
            sun_opacity = 0.0
        else:
            sun_progress = (ir_norm - SUN_START_THRESHOLD) / (1.0 - SUN_START_THRESHOLD)
            sun_opacity = sun_progress ** 0.5

        cloud_density = stress_level
        rain_density = stress_level
        darkness = stress_level * 0.7

        # 1. Cielo
        self.screen.fill(COLOR_SKY)

        # 2. Paisaje
        landscape_y = SCREEN_HEIGHT - self.bg_image.get_height()
        self.screen.blit(self.bg_image, (0, landscape_y))

        # 3. Sol
        sun_x = SCREEN_WIDTH - self.sun_image.get_width() - 80
        sun_y = 30
        if sun_opacity > 0.0:
            self.effects.draw_with_opacity(self.sun_image, (sun_x, sun_y), sun_opacity)

        # 4. Nubes
        self.clouds.draw(self.effects, cloud_density)

        # 5. Lluvia
        self.rain.draw(self.screen, rain_density)

        # 6. Rayos
        self.lightning.draw(self.effects, ir_norm)

        # 7. Capa oscura
        self.effects.draw_dark_overlay(darkness)

        # 8. HUD
        self._draw_info(ir_norm, stress_level)

    def _draw_info(self, ir_norm: float, stress_level: float):
        """
        ir_norm aquí es CalmIdx (0–1).
        Mostramos también IR α/β real y α, β.
        """
        text_color = (255, 255, 255) if ir_norm < 0.5 else (50, 50, 50)

        ir_ratio = self._compute_ir_ratio(self.state.alpha, self.state.beta)
        
        lines = [
            f"CalmIdx: {ir_norm:.2f} | IR α/β: {ir_ratio:.2f} | α: {self.state.alpha:.1f} | β: {self.state.beta:.1f}",
            f"Atención: {self.state.attention:.0f} | Meditación: {self.state.meditation:.0f}",
            f"Confianza: {self.state.confidence*100:.0f}% | Rayos: {len(self.lightning.lightnings)}"
        ]
        
        # Estado en función del CalmIdx
        if ir_norm < LIGHTNING_END_THRESHOLD:
            lightning_strength = ((LIGHTNING_END_THRESHOLD - ir_norm) / LIGHTNING_END_THRESHOLD) * 100
            state_text = f"⚡ ESTRESADO - Rayos: {lightning_strength:.0f}%"
        elif ir_norm < SUN_START_THRESHOLD:
            state_text = "🌥️ DESPEJANDO - Respira profundo..."
        elif ir_norm < 0.75:
            sun_strength = ((ir_norm - SUN_START_THRESHOLD) / (1.0 - SUN_START_THRESHOLD)) * 100
            state_text = f"🌤️ RELAJÁNDOSE - Sol: {sun_strength:.0f}%"
        else:
            state_text = "☀️ RELAJADO - ¡Excelente!"
        
        lines.append(state_text)
        
        mode = "REAL" if self.use_real_data else "SIMULACIÓN"
        status = self.connection_status
        lines.append(f"Modo: {mode} | Estado: {status}")
        lines.append(f"Baseline IR: {self.calibration_summary}")
        # Se ha eliminado la línea de "Ojos: ..." del HUD
        
        for i, line in enumerate(lines):
            text_surface = self.font.render(line, True, text_color)
            self.screen.blit(text_surface, (10, 10 + i * 25))

    # ------------------------ LOOP PRINCIPAL ------------------------

    def run(self):
        print("\n" + "="*60)
        print("🎮 CalmSync - Neurofeedback en Tiempo Real (vía udp.EEGClient)")
        print("="*60)
        print("📊 Sistema de transición por etapas (usando CalmIdx):")
        print(f"   • CalmIdx bajo  → ⚡ Rayos / tormenta")
        print(f"   • CalmIdx medio → 🌥️ Despejando")
        print(f"   • CalmIdx alto  → ☀️ Sol apareciendo")
        print("\n⌨️  ESC para salir\n")

        # Calibración IR α/β solo con datos reales (informativa)
        if self.use_real_data and self.client:
            self.perform_calibration()
            if not self.running:
                return
        
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False

            self.update_data()

            # Clima basado en CalmIdx (calculado dentro de render)
            calm_level = self.compute_calm_level()
            stress_level = 1.0 - calm_level

            self.rain.update(stress_level)
            self.clouds.update(calm_level)
            self.lightning.update(stress_level, calm_level)

            self.render()

            pygame.display.flip()
            self.clock.tick(FPS)

        # Cierre limpio
        if self.client:
            self.client.stop()
        
        pygame.quit()
        sys.exit()


# ---------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='CalmSync Neurofeedback Game')
    parser.add_argument('--simulate', action='store_true',
                        help='Usa datos simulados (sin MindWave)')
    args = parser.parse_args()
    
    use_real = not args.simulate
    
    game = NeurofeedbackGame(use_real_data=use_real)
    game.run()