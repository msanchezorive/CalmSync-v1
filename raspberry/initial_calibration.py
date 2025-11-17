"""
NEUROSKY CALIBRATION SYSTEM -

WHAT THIS CODE DOES
-------------------
Before using the EEG sensor, this program checks that:
1. The sensor is properly placed on your head
2. The signal is stable (no noise)
3. The data received is valid

HOW IT WORKS
------------
1. Connect to the NeuroSky sensor via Bluetooth
2. Read data for 25 seconds
3. If the signal is good for 5 consecutive seconds → ✅ READY
4. If not → ❌ Ask to adjust the sensor
"""

import pygame
import sys
import threading
import serial
import time
from collections import deque
import numpy as np

from generic_parser import parse_packet, extract_data_from_payload

# =====================================================================
# BASIC CONFIGURATION
# =====================================================================

NEUROSKY_PORT = "/dev/rfcomm0" # Mac/Linux
# NEUROSKY_PORT = "COM10"  # Windows
NEUROSKY_BAUD = 57600

CODE_SIGNAL_QUALITY = {0x02: 'signal_quality'}  # Signal quality
CODE_ALPHA_BETA = {0x83: 'eeg_power'}           # Brain waves

# Calibration timings
TIEMPO_TOTAL = 35        # Total seconds for calibration
TIEMPO_ESTABLE = 5       # Consecutive seconds with good signal

# Quality thresholds (what we consider "good signal")
MAX_CALIDAD_ACEPTABLE = 50    # Signal quality < 50 = OK
MIN_ALPHA = 500               # Alpha must be > 500
MIN_BETA = 500                # Beta must be > 500

# Interface colors
COLOR_FONDO = (15, 20, 35)           # Dark blue
COLOR_BIEN = (50, 200, 100)          # Green
COLOR_REGULAR = (255, 180, 50)       # Orange
COLOR_MAL = (255, 80, 80)            # Red
COLOR_TEXTO = (220, 230, 255)        # Light blue


# =====================================================================
# SENSOR READER (background thread)
# =====================================================================

class LectorNeuroSky:
    """ Continuously reads data from the NeuroSky sensor in the background """
    
    def __init__(self, puerto: str, velocidad: int):
        self.puerto = puerto
        self.velocidad = velocidad
        self.calidad = 200
        self.alpha = 0.0
        self.beta = 0.0
        self.historico_alpha = deque(maxlen=10)
        self.historico_beta = deque(maxlen=10)
        self.corriendo = False
        self.hilo = None
        self.puerto_serial = None
        self.estado = "Disconnected"
        self.candado = threading.Lock()
    
    def _bucle_lectura(self):
        try:
            self.puerto_serial = serial.Serial(self.puerto, self.velocidad, timeout=1)
            self.estado = "Connected ✅"
            print(f"✅ Connected to {self.puerto}")
            
            while self.corriendo:
                paquete = parse_packet(self.puerto_serial)
                if paquete is None:
                    continue
                
                with self.candado:
                    datos_calidad = extract_data_from_payload(paquete, CODE_SIGNAL_QUALITY)
                    if 'signal_quality' in datos_calidad:
                        self.calidad = datos_calidad['signal_quality']
                    
                    datos_ondas = extract_data_from_payload(paquete, CODE_ALPHA_BETA)
                    if 'eeg_power' in datos_ondas:
                        potencias = datos_ondas['eeg_power']
                        self.alpha = (potencias[2] + potencias[3]) / 2
                        self.beta = (potencias[4] + potencias[5]) / 2
                        self.historico_alpha.append(self.alpha)
                        self.historico_beta.append(self.beta)
        
        except Exception as e:
            self.estado = f"Error: {e}"
            print(f"❌ Error: {e}")
        
        finally:
            if self.puerto_serial and self.puerto_serial.is_open:
                self.puerto_serial.close()
            self.estado = "Disconnected"
    
    def iniciar(self):
        if not self.corriendo:
            self.corriendo = True
            self.hilo = threading.Thread(target=self._bucle_lectura, daemon=True)
            self.hilo.start()
    
    def detener(self):
        self.corriendo = False
        if self.hilo:
            self.hilo.join(timeout=2)
    
    def obtener_metricas(self) -> dict:
        with self.candado:
            alpha_estable = False
            if len(self.historico_alpha) >= 5:
                variacion_alpha = np.std(list(self.historico_alpha))
                alpha_estable = variacion_alpha < 5000
            
            beta_estable = False
            if len(self.historico_beta) >= 5:
                variacion_beta = np.std(list(self.historico_beta))
                beta_estable = variacion_beta < 5000
            
            return {
                'calidad': self.calidad,
                'alpha': self.alpha,
                'beta': self.beta,
                'alpha_estable': alpha_estable,
                'beta_estable': beta_estable,
                'estado': self.estado
            }


# =====================================================================
# CALIBRATION SCREEN (visual interface)
# =====================================================================

class PantallaCalibracion:
    """ Shows calibration window with signal validation """
    
    def __init__(self):
        pygame.init()
        self.pantalla = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("CalmSync - Calibration")
        self.reloj = pygame.time.Clock()
        self.fuente_grande = pygame.font.Font(None, 56)
        self.fuente_normal = pygame.font.Font(None, 32)
        self.fuente_pequeña = pygame.font.Font(None, 24)
        self.lector = LectorNeuroSky(NEUROSKY_PORT, NEUROSKY_BAUD)
        self.inicio_calibracion = None
        self.inicio_señal_estable = None
        self.calibracion_completa = False
        self.corriendo = True
    
    def señal_es_valida(self, metricas: dict) -> tuple:
        problemas = []
        if metricas['calidad'] > MAX_CALIDAD_ACEPTABLE:
            problemas.append(f"Poor connection ({metricas['calidad']}/200)")
        if metricas['alpha'] < MIN_ALPHA:
            problemas.append("Alpha too low")
        elif not metricas['alpha_estable']:
            problemas.append("Alpha unstable")
        if metricas['beta'] < MIN_BETA:
            problemas.append("Beta too low")
        elif not metricas['beta_estable']:
            problemas.append("Beta unstable")
        
        if len(problemas) == 0:
            return True, "✅ Perfect signal"
        else:
            return False, " | ".join(problemas)
    
    def dibujar_barra(self, progreso: float, y: int, etiqueta: str, color: tuple):
        ancho_barra = 600
        alto_barra = 40
        x = 100
        texto = self.fuente_normal.render(etiqueta, True, COLOR_TEXTO)
        self.pantalla.blit(texto, (x, y - 30))
        pygame.draw.rect(self.pantalla, (40, 50, 70), (x, y, ancho_barra, alto_barra), border_radius=10)
        ancho_relleno = int(ancho_barra * progreso)
        if ancho_relleno > 0:
            pygame.draw.rect(self.pantalla, color, (x, y, ancho_relleno, alto_barra), border_radius=10)
        pygame.draw.rect(self.pantalla, COLOR_TEXTO, (x, y, ancho_barra, alto_barra), width=2, border_radius=10)
        porcentaje = f"{int(progreso * 100)}%"
        texto_porcentaje = self.fuente_pequeña.render(porcentaje, True, COLOR_TEXTO)
        self.pantalla.blit(texto_porcentaje, (x + ancho_barra // 2 - 20, y + alto_barra + 10))
    
    def dibujar_metrica(self, x: int, y: int, titulo: str, valor: str, color: tuple):
        ancho = 150
        alto = 90
        pygame.draw.rect(self.pantalla, (40, 50, 70), (x, y, ancho, alto), border_radius=10)
        pygame.draw.rect(self.pantalla, color, (x, y, ancho, alto), width=3, border_radius=10)
        texto_titulo = self.fuente_pequeña.render(titulo, True, COLOR_TEXTO)
        self.pantalla.blit(texto_titulo, (x + 10, y + 15))
        texto_valor = self.fuente_normal.render(valor, True, color)
        self.pantalla.blit(texto_valor, (x + 10, y + 50))
    
    def renderizar(self, metricas: dict, tiempo_total: float, tiempo_estable: float):
        self.pantalla.fill(COLOR_FONDO)
        
        if self.calibracion_completa:
            titulo = "✅ READY!"
            color_titulo = COLOR_BIEN
        else:
            titulo = "🧠 Calibrating..."
            color_titulo = (100, 150, 255)
        
        texto_titulo = self.fuente_grande.render(titulo, True, color_titulo)
        self.pantalla.blit(texto_titulo, (250, 30))
        
        progreso_total = min(1.0, tiempo_total / TIEMPO_TOTAL)
        self.dibujar_barra(progreso_total, 120, "Calibration time", (100, 150, 255))
        
        es_valida, mensaje = self.señal_es_valida(metricas)
        
        if es_valida:
            progreso_estable = min(1.0, tiempo_estable / TIEMPO_ESTABLE)
            color_barra = COLOR_BIEN if progreso_estable >= 1.0 else COLOR_REGULAR
            self.dibujar_barra(progreso_estable, 210, f"Stable signal ({int(tiempo_estable)}s / {TIEMPO_ESTABLE}s)", color_barra)
        else:
            self.dibujar_barra(0.0, 210, "❌ Adjust the sensor", COLOR_MAL)
        
        y_metricas = 320
        color_calidad = COLOR_BIEN if metricas['calidad'] < MAX_CALIDAD_ACEPTABLE else COLOR_MAL
        self.dibujar_metrica(100, y_metricas, "Quality", f"{metricas['calidad']}/200", color_calidad)
        color_alpha = COLOR_BIEN if metricas['alpha'] > MIN_ALPHA and metricas['alpha_estable'] else COLOR_REGULAR
        self.dibujar_metrica(280, y_metricas, "Alpha", f"{int(metricas['alpha'])}", color_alpha)
        color_beta = COLOR_BIEN if metricas['beta'] > MIN_BETA and metricas['beta_estable'] else COLOR_REGULAR
        self.dibujar_metrica(460, y_metricas, "Beta", f"{int(metricas['beta'])}", color_beta)
        
        texto_estado = self.fuente_pequeña.render(mensaje, True, COLOR_BIEN if es_valida else COLOR_REGULAR)
        self.pantalla.blit(texto_estado, (100, 450))
        
        if not self.calibracion_completa:
            instrucciones = [
                "• Adjust the sensor on your forehead",
                "• Place the clip on your earlobe",
                "• Relax and breathe normally"
            ]
            for i, texto in enumerate(instrucciones):
                texto_inst = self.fuente_pequeña.render(texto, True, COLOR_TEXTO)
                self.pantalla.blit(texto_inst, (100, 500 + i * 30))
        else:
            texto_exito = self.fuente_normal.render("Press ENTER to continue!", True, COLOR_BIEN)
            self.pantalla.blit(texto_exito, (150, 520))
    
    def ejecutar(self) -> bool:
        print("\n" + "="*60)
        print("🧠 STARTING CALIBRATION")
        print("="*60)
        self.lector.iniciar()
        time.sleep(1)
        self.inicio_calibracion = time.time()
        
        while self.corriendo:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    self.lector.detener()
                    pygame.quit()
                    return False
                elif evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_ESCAPE:
                        print("\n❌ Cancelled by user")
                        self.lector.detener()
                        pygame.quit()
                        return False
                    elif evento.key == pygame.K_RETURN and self.calibracion_completa:
                        print("\n✅ Calibration successful!")
                        self.lector.detener()
                        pygame.quit()
                        return True
            
            metricas = self.lector.obtener_metricas()
            tiempo_total = time.time() - self.inicio_calibracion
            es_valida, mensaje = self.señal_es_valida(metricas)
            
            if es_valida:
                if self.inicio_señal_estable is None:
                    self.inicio_señal_estable = time.time()
                    print(f"✅ Stable signal detected")
                tiempo_estable = time.time() - self.inicio_señal_estable
                if tiempo_estable >= TIEMPO_ESTABLE:
                    self.calibracion_completa = True
                    print(f"🎉 CALIBRATION COMPLETE!")
            else:
                if self.inicio_señal_estable is not None:
                    print(f"⚠️  Signal lost: {mensaje}")
                self.inicio_señal_estable = None
                tiempo_estable = 0
            
            self.renderizar(metricas, tiempo_total, tiempo_estable)
            pygame.display.flip()
            self.reloj.tick(30)
            
            if tiempo_total > TIEMPO_TOTAL and not self.calibracion_completa:
                print("\n⏱️  Time ran out without stable signal")
                print("💡 Make sure the sensor is properly placed")
                self.corriendo = False
        
        self.lector.detener()
        pygame.quit()
        return self.calibracion_completa


# =====================================================================
# MAIN PROGRAM
# =====================================================================

if __name__ == "__main__":
    calibracion = PantallaCalibracion()
    exito = calibracion.ejecutar()
    if exito:
        print("\n✅ System ready to use")
        sys.exit(0)
    else:
        print("\n❌ Calibration failed")
        sys.exit(1)