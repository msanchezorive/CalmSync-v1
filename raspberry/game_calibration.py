"""
BASELINE CALIBRATION SYSTEM

WHAT THIS CODE DOES
-------------------
After the sensor is stable, this calibrates the game to YOUR personal brainwave patterns.
Everyone has different brain activity (amplitude, rhythm), so we measure YOUR baseline.

DIFFERENCE FROM SENSOR CALIBRATION
----------------------------------
1. Sensor Calibration: Checks if sensor is properly connected (hardware check)
2. Baseline Calibration: Measures YOUR personal brain patterns (personalization)

HOW IT WORKS
------------
1. You stare at a red dot for 15 seconds
2. We collect your Alpha and Beta values in a relaxed state
3. We calculate your personal mean and standard deviation
4. The game uses these to normalize values specifically for YOU

EXAMPLE
-------
Person A: Alpha=5000, Beta=3000 in rest → IR baseline = 1.67
Person B: Alpha=25000, Beta=15000 in rest → IR baseline = 1.67

Same ratio, but VERY different amplitudes! Without calibration, Person B would
break the game (always sunshine). With calibration, both get fair gameplay.
"""

import pygame
import sys
import time
import numpy as np
from dataclasses import dataclass
from typing import Optional, List

# =====================================================================
# BASELINE DATA CLASS
# =====================================================================

@dataclass
class BaselineData:
    """
    Stores personal brainwave statistics for normalization.
    
    This data represents YOUR brain at rest, and helps the game
    adapt to your individual signal strength.
    """
    # Alpha wave statistics
    alpha_mean: float      # Your average alpha at rest
    alpha_std: float       # How variable your alpha is
    alpha_min: float       # Minimum observed
    alpha_max: float       # Maximum observed
    
    # Beta wave statistics
    beta_mean: float       # Your average beta at rest
    beta_std: float        # How variable your beta is
    beta_min: float        # Minimum observed
    beta_max: float        # Maximum observed
    
    # Combined metric
    ir_baseline: float     # Your personal Alpha/Beta ratio at rest
    
    # Quality metrics
    n_samples: int         # How many samples we collected
    
    def normalize_alpha(self, raw_alpha: float) -> float:
        """
        Converts raw alpha to normalized value relative to YOUR baseline.
        
        Uses z-score: (value - mean) / std
        
        Returns:
            z-score where 0 = your baseline, +1 = one std above, -1 = one std below
        """
        if self.alpha_std < 1.0:
            return 0.0  # Avoid division by zero
        return (raw_alpha - self.alpha_mean) / self.alpha_std
    
    def normalize_beta(self, raw_beta: float) -> float:
        """
        Converts raw beta to normalized value relative to YOUR baseline.
        """
        if self.beta_std < 1.0:
            return 0.0
        return (raw_beta - self.beta_mean) / self.beta_std
    
    def calculate_normalized_ir(self, raw_alpha: float, raw_beta: float) -> float:
        """
        Calculates IR normalized to YOUR personal baseline.
        
        Process:
        1. Calculate current IR: alpha/beta
        2. Divide by your baseline IR
        3. Result: 1.0 = same as your rest state
                  >1.0 = more relaxed than baseline
                  <1.0 = more stressed than baseline
        """
        current_ir = raw_alpha / max(raw_beta, 1.0)
        normalized_ir = current_ir / max(self.ir_baseline, 0.1)
        return normalized_ir
    
    def print_summary(self):
        """Prints a readable summary of calibration results."""
        print("\n" + "="*60)
        print("📊 BASELINE CALIBRATION RESULTS")
        print("="*60)
        print(f"✅ Successfully collected {self.n_samples} samples")
        print(f"\n🔵 ALPHA (Relaxation):")
        print(f"   Mean:    {self.alpha_mean:.1f} μV²")
        print(f"   Std Dev: {self.alpha_std:.1f} μV²")
        print(f"   Range:   [{self.alpha_min:.1f}, {self.alpha_max:.1f}]")
        print(f"\n🔴 BETA (Concentration):")
        print(f"   Mean:    {self.beta_mean:.1f} μV²")
        print(f"   Std Dev: {self.beta_std:.1f} μV²")
        print(f"   Range:   [{self.beta_min:.1f}, {self.beta_max:.1f}]")
        print(f"\n⚖️  IR BASELINE: {self.ir_baseline:.3f}")
        print("="*60 + "\n")


# =====================================================================
# BASELINE CALIBRATOR
# =====================================================================

class GameCalibration:
    """
    Runs baseline calibration session.
    
    Shows user instructions, collects data, calculates statistics.
    """
    
    def __init__(self, neurosky_reader, duration_seconds: float = 15.0):
        """
        Args:
            neurosky_reader: Active NeuroSkyReader instance (must be running)
            duration_seconds: How long to collect data (default 15s)
        """
        self.neurosky = neurosky_reader
        self.duration = duration_seconds
        
        # Data collection buffers
        self.alpha_samples: List[float] = []
        self.beta_samples: List[float] = []
        
        # UI colors
        self.bg_color = (15, 20, 35)
        self.text_color = (220, 230, 255)
        self.progress_color = (52, 152, 219)
        self.dot_color = (231, 76, 60)
        self.good_color = (50, 200, 100)
    
    def run_calibration(self, screen: pygame.Surface, font: pygame.font.Font) -> Optional[BaselineData]:
        """
        Main calibration flow.
        
        Steps:
        1. Show instructions
        2. Countdown (3, 2, 1...)
        3. Collect data for X seconds
        4. Calculate statistics
        5. Return BaselineData
        
        Returns:
            BaselineData with statistics, or None if cancelled
        """
        # PHASE 1: Instructions
        if not self._show_instructions(screen, font):
            return None  # User cancelled
        
        # PHASE 2: Countdown
        self._show_countdown(screen, font)
        
        # PHASE 3: Data collection
        baseline = self._collect_data(screen, font)
        
        if baseline:
            baseline.print_summary()
        
        return baseline
    
    def _show_instructions(self, screen: pygame.Surface, font: pygame.font.Font) -> bool:
        """
        Shows instruction screen explaining what will happen.
        
        Returns:
            True if user presses SPACE (continue)
            False if user presses ESC (cancel)
        """
        clock = pygame.time.Clock()
        waiting = True
        
        while waiting:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        waiting = False
                    elif event.key == pygame.K_ESCAPE:
                        return False
            
            # Draw screen
            screen.fill(self.bg_color)
            
            # Title
            title = font.render("🎯 BASELINE CALIBRATION", True, self.text_color)
            title_rect = title.get_rect(center=(screen.get_width()//2, 80))
            screen.blit(title, title_rect)
            
            # Instructions
            instructions = [
                "",
                "This calibration personalizes the game to YOUR brain.",
                "",
                "WHAT TO DO:",
                "  • Relax and breathe normally",
                "  • Stare at the red dot (don't look away)",
                "  • Try not to think about anything specific",
                "  • Stay still for 15 seconds",
                "",
                "WHY?",
                "  Everyone's brain is different. Your alpha might be 5,000",
                "  while someone else's is 25,000. This measures YOUR baseline",
                "  so the game responds fairly to YOUR brain activity.",
                "",
                "",
                "Press SPACE to begin",
                "Press ESC to skip (not recommended)"
            ]
            
            y = 160
            for line in instructions:
                if line.startswith("WHAT") or line.startswith("WHY"):
                    # Section headers in bold/colored
                    text = font.render(line, True, self.good_color)
                else:
                    text = font.render(line, True, self.text_color)
                
                text_rect = text.get_rect(center=(screen.get_width()//2, y))
                screen.blit(text, text_rect)
                y += 28
            
            pygame.display.flip()
            clock.tick(30)
        
        return True
    
    def _show_countdown(self, screen: pygame.Surface, font: pygame.font.Font):
        """
        Shows 3... 2... 1... countdown before data collection.
        """
        clock = pygame.time.Clock()
        large_font = pygame.font.Font(None, 120)
        
        for count in [3, 2, 1]:
            screen.fill(self.bg_color)
            
            # Large countdown number
            text = large_font.render(str(count), True, self.text_color)
            text_rect = text.get_rect(center=(screen.get_width()//2, screen.get_height()//2))
            screen.blit(text, text_rect)
            
            # Instruction reminder
            instruction = font.render("Get ready to focus on the red dot...", True, self.text_color)
            inst_rect = instruction.get_rect(center=(screen.get_width()//2, screen.get_height()//2 + 100))
            screen.blit(instruction, inst_rect)
            
            pygame.display.flip()
            time.sleep(1.0)
    
    def _collect_data(self, screen: pygame.Surface, font: pygame.font.Font) -> Optional[BaselineData]:
        """
        Main data collection loop.
        
        Displays:
        - Red fixation dot (center)
        - Progress bar (bottom)
        - Sample count
        - Time remaining
        
        Collects alpha/beta samples continuously for duration_seconds.
        
        Returns:
            BaselineData if successful, None if cancelled
        """
        clock = pygame.time.Clock()
        start_time = time.time()
        
        # Clear buffers
        self.alpha_samples.clear()
        self.beta_samples.clear()
        
        # Visual feedback state
        last_sample_time = time.time()
        sample_indicator_alpha = 0  # Fades out to show data received
        
        while True:
            elapsed = time.time() - start_time
            
            # Check if finished
            if elapsed >= self.duration:
                break
            
            # Handle events (allow cancel with ESC)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        print("\n⚠️ Baseline calibration cancelled by user")
                        return None
            
            # Collect data from NeuroSky
            alpha, beta, _, _, conf = self.neurosky.get_values()
            
            # Only save high-quality samples (confidence > 30%)
            if conf > 0.3 and alpha > 0 and beta > 0:
                self.alpha_samples.append(alpha)
                self.beta_samples.append(beta)
                sample_indicator_alpha = 1.0  # Reset indicator
                last_sample_time = time.time()
            
            # Fade sample indicator
            sample_indicator_alpha = max(0.0, sample_indicator_alpha - 0.05)
            
            # === DRAW SCREEN ===
            screen.fill(self.bg_color)
            
            # Center fixation dot (RED - very important!)
            center_x = screen.get_width() // 2
            center_y = screen.get_height() // 2
            dot_radius = 15
            
            # Pulsing effect on dot (so user knows it's active)
            pulse = abs(np.sin(elapsed * 2)) * 0.3 + 0.7  # Oscillates 0.7-1.0
            dot_color = tuple(int(c * pulse) for c in self.dot_color)
            pygame.draw.circle(screen, dot_color, (center_x, center_y), dot_radius)
            
            # Sample indicator ring (appears briefly when sample received)
            if sample_indicator_alpha > 0:
                ring_alpha = int(255 * sample_indicator_alpha)
                ring_color = self.good_color + (ring_alpha,)
                ring_surface = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
                pygame.draw.circle(ring_surface, ring_color, (center_x, center_y), dot_radius + 10, 3)
                screen.blit(ring_surface, (0, 0))
            
            # Progress bar
            bar_width = 600
            bar_height = 40
            bar_x = (screen.get_width() - bar_width) // 2
            bar_y = screen.get_height() - 120
            
            # Background
            pygame.draw.rect(screen, (40, 50, 70), (bar_x, bar_y, bar_width, bar_height), border_radius=10)
            
            # Progress fill
            progress = elapsed / self.duration
            fill_width = int(bar_width * progress)
            if fill_width > 0:
                pygame.draw.rect(screen, self.progress_color, (bar_x, bar_y, fill_width, bar_height), border_radius=10)
            
            # Border
            pygame.draw.rect(screen, self.text_color, (bar_x, bar_y, bar_width, bar_height), width=2, border_radius=10)
            
            # Time remaining text
            remaining = int(self.duration - elapsed)
            progress_text = font.render(f"Calibrating... {remaining}s remaining", True, self.text_color)
            progress_rect = progress_text.get_rect(center=(center_x, bar_y - 30))
            screen.blit(progress_text, progress_rect)
            
            # Sample count
            samples_text = font.render(f"Samples collected: {len(self.alpha_samples)}", True, self.text_color)
            samples_rect = samples_text.get_rect(center=(center_x, bar_y + bar_height + 20))
            screen.blit(samples_text, samples_rect)
            
            # Quality indicator
            if len(self.alpha_samples) < elapsed * 8:  # Expect ~10 samples/sec, warn if <8
                quality_text = font.render("⚠️ Signal quality low - adjust sensor", True, (255, 180, 50))
            else:
                quality_text = font.render("✅ Good signal quality", True, self.good_color)
            quality_rect = quality_text.get_rect(center=(center_x, bar_y + bar_height + 50))
            screen.blit(quality_text, quality_rect)
            
            pygame.display.flip()
            clock.tick(30)
        
        # Calculate statistics
        return self._calculate_baseline()
    
    def _calculate_baseline(self) -> Optional[BaselineData]:
        """
        Processes collected samples to generate baseline statistics.
        
        Returns:
            BaselineData if enough samples, None otherwise
        """
        # Validate sufficient samples
        min_samples = 50  # At least 50 samples (5 seconds at 10 Hz)
        if len(self.alpha_samples) < min_samples or len(self.beta_samples) < min_samples:
            print(f"\n⚠️ Insufficient samples: {len(self.alpha_samples)} alpha, {len(self.beta_samples)} beta")
            print(f"   Need at least {min_samples} samples")
            print("   This usually means poor sensor contact.")
            return None
        
        # Convert to numpy arrays for statistics
        alpha_arr = np.array(self.alpha_samples)
        beta_arr = np.array(self.beta_samples)
        
        # Calculate statistics
        alpha_mean = float(np.mean(alpha_arr))
        alpha_std = float(np.std(alpha_arr))
        alpha_min = float(np.min(alpha_arr))
        alpha_max = float(np.max(alpha_arr))
        
        beta_mean = float(np.mean(beta_arr))
        beta_std = float(np.std(beta_arr))
        beta_min = float(np.min(beta_arr))
        beta_max = float(np.max(beta_arr))
        
        # Calculate baseline IR
        ir_baseline = alpha_mean / max(beta_mean, 1.0)
        
        # Validate results (sanity checks)
        if alpha_mean < 100 or beta_mean < 100:
            print("\n⚠️ Suspiciously low values detected:")
            print(f"   Alpha mean: {alpha_mean}, Beta mean: {beta_mean}")
            print("   This suggests sensor is not reading properly.")
            return None
        
        if alpha_std / alpha_mean > 1.0 or beta_std / beta_mean > 1.0:
            print("\n⚠️ Very high variability detected (CV > 100%):")
            print(f"   Alpha CV: {alpha_std/alpha_mean:.2f}, Beta CV: {beta_std/beta_mean:.2f}")
            print("   User may have moved during calibration.")
            print("   Results might not be reliable.")
            # Continue anyway, but warn user
        
        return BaselineData(
            alpha_mean=alpha_mean,
            alpha_std=alpha_std,
            alpha_min=alpha_min,
            alpha_max=alpha_max,
            beta_mean=beta_mean,
            beta_std=beta_std,
            beta_min=beta_min,
            beta_max=beta_max,
            ir_baseline=ir_baseline,
            n_samples=len(self.alpha_samples)
        )


# =====================================================================
# DEMO / TEST MODE
# =====================================================================

if __name__ == "__main__":
    """
    Test baseline calibration with simulated data.
    
    This allows testing the UI without connecting hardware.
    """
    import random
    
    class FakeNeuroSkyReader:
        """Simulates NeuroSky for testing."""
        def __init__(self):
            self.connection_status = "Simulated"
            self.alpha_base = random.uniform(5000, 25000)
            self.beta_base = random.uniform(3000, 15000)
        
        def get_values(self):
            # Simulate natural variability (±20%)
            alpha = self.alpha_base * random.uniform(0.8, 1.2)
            beta = self.beta_base * random.uniform(0.8, 1.2)
            conf = random.uniform(0.5, 1.0)
            
            return alpha, beta, 50, 50, conf
    
    print("="*60)
    print("🧪 BASELINE CALIBRATION TEST MODE")
    print("="*60)
    print("\nThis demonstrates the calibration UI with simulated data.")
    print("Press SPACE to start, ESC to cancel.\n")
    
    # Initialize
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Baseline Calibration - Test Mode")
    font = pygame.font.Font(None, 28)
    
    # Create fake reader
    fake_reader = FakeNeuroSkyReader()
    print(f"Simulated baseline: Alpha={fake_reader.alpha_base:.0f}, Beta={fake_reader.beta_base:.0f}")
    
    # Run calibration
    calibrator = GameCalibration(fake_reader, duration_seconds=10.0)  # Shorter for testing
    baseline = calibrator.run_calibration(screen, font)
    
    if baseline:
        print("\n✅ Calibration completed successfully!")
        print(f"\nYou can now use these values to normalize game data:")
        print(f"  normalized_alpha = baseline.normalize_alpha(raw_alpha)")
        print(f"  normalized_ir = baseline.calculate_normalized_ir(raw_alpha, raw_beta)")
    else:
        print("\n❌ Calibration cancelled or failed")
    
    pygame.quit()
    sys.exit(0 if baseline else 1)