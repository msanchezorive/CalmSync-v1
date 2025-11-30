import pygame
import sys
import time
from udp import EEGClient  # Nuestro cliente TCP robusto del servicio

# =====================================================================
# CONFIGURACIï¿½N
# =====================================================================

TIEMPO_TOTAL = 50        # segundos totales para calibraciï¿½n
TIEMPO_ESTABLE = 10       # segundos consecutivos con seï¿½al estable

MAX_CALIDAD_ACEPTABLE = 50  # calidad < 50 = buena
MIN_ALPHA = 500
MIN_BETA = 500

# Interface colors - estilo suave / pastel
COLOR_FONDO    = (243, 245, 251)  # F3F5FB - fondo principal
COLOR_BIEN     = (102, 187, 255)  # Azul pastel para seï¿½al buena / ï¿½xito
COLOR_REGULAR  = (255, 183, 77)   # Amarillo suave para advertencias
COLOR_MAL      = (239, 83, 80)    # Rojo suave para mala seï¿½al
COLOR_TEXTO    = (74, 85, 104)    # Gris oscuro para texto, contraste con fondo

class PantallaCalibracion:
    """Pantalla de calibraciï¿½n idï¿½ntica a la anterior, solo que lee datos desde UDP."""

    def __init__(self):
        pygame.init()
        self.pantalla = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("CalmSync - Calibration")
        self.reloj = pygame.time.Clock()
        self.fuente_grande = pygame.font.Font(None, 56)
        self.fuente_normal = pygame.font.Font(None, 32)
        self.fuente_peque = pygame.font.Font(None, 24)
        self.client = EEGClient()  # Cliente UDP/TCP
        self.client.start()
        self.inicio_calibracion = None
        self.inicio_senal_estable = None
        self.calibracion_completa = False
        self.corriendo = True
    def senal_es_valida(self, metricas: dict):
        problemas = []
        if metricas['signal_quality'] > MAX_CALIDAD_ACEPTABLE:
            problemas.append(f"Poor connection ({metricas['signal_quality']}/200)")
        if metricas['alpha'] < MIN_ALPHA:
            problemas.append("Alpha too low")
        elif not metricas.get('alpha_estable', True):
            problemas.append("Alpha unstable")
        if metricas['beta'] < MIN_BETA:
            problemas.append("Beta too low")
        elif not metricas.get('beta_estable', True):
            problemas.append("Beta unstable")

        if len(problemas) == 0:
            return True, " Perfect signal"
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
        texto_porcentaje = self.fuente_peque.render(porcentaje, True, COLOR_TEXTO)
        self.pantalla.blit(texto_porcentaje, (x + ancho_barra // 2 - 20, y + alto_barra + 10))
    def dibujar_metrica(self, x: int, y: int, titulo: str, valor: str, color: tuple):
        ancho = 150
        alto = 90
        pygame.draw.rect(self.pantalla, (40, 50, 70), (x, y, ancho, alto), border_radius=10)
        pygame.draw.rect(self.pantalla, color, (x, y, ancho, alto), width=3, border_radius=10)
        texto_titulo = self.fuente_peque.render(titulo, True, COLOR_TEXTO)
        self.pantalla.blit(texto_titulo, (x + 10, y + 15))
        texto_valor = self.fuente_normal.render(valor, True, color)
        self.pantalla.blit(texto_valor, (x + 10, y + 50))
    def renderizar(self, metricas: dict, tiempo_total: float, tiempo_estable: float):
        self.pantalla.fill(COLOR_FONDO)

        if self.calibracion_completa:
            titulo = " READY!"
            color_titulo = COLOR_BIEN
        else:
            titulo = "Calibrating..."
            color_titulo = (100, 150, 255)

        texto_titulo = self.fuente_grande.render(titulo, True, color_titulo)
        self.pantalla.blit(texto_titulo, (250, 30))

        progreso_total = min(1.0, tiempo_total / TIEMPO_TOTAL)
        self.dibujar_barra(progreso_total, 120, "Calibration time", (100, 150, 255))

        es_valida, mensaje = self.senal_es_valida(metricas)

        if es_valida:
            progreso_estable = min(1.0, tiempo_estable / TIEMPO_ESTABLE)
            color_barra = COLOR_BIEN if progreso_estable >= 1.0 else COLOR_REGULAR
            self.dibujar_barra(progreso_estable, 210, f"Stable signal ({int(tiempo_estable)}s / {TIEMPO_ESTABLE}s)", color_barra)
        else:
            self.dibujar_barra(0.0, 210, " Adjust the sensor", COLOR_MAL)

        y_metricas = 320
        color_calidad = COLOR_BIEN if metricas['signal_quality'] < MAX_CALIDAD_ACEPTABLE else COLOR_MAL
        self.dibujar_metrica(100, y_metricas, "Noise", f"{metricas['signal_quality']}/200", color_calidad)
        color_alpha = COLOR_BIEN if metricas['alpha'] > MIN_ALPHA else COLOR_REGULAR
        self.dibujar_metrica(280, y_metricas, "Alpha", f"{int(metricas['alpha'])}", color_alpha)
        color_beta = COLOR_BIEN if metricas['beta'] > MIN_BETA else COLOR_REGULAR
        self.dibujar_metrica(460, y_metricas, "Beta", f"{int(metricas['beta'])}", color_beta)


        texto_estado = self.fuente_peque.render(mensaje, True, COLOR_BIEN if es_valida else COLOR_REGULAR)
        self.pantalla.blit(texto_estado, (100, 450))

        if not self.calibracion_completa:
            instrucciones = [
                " Adjust the sensor on your forehead",
                " Place the clip on your earlobe",
                " Relax and breathe normally"
            ]
            for i, texto in enumerate(instrucciones):
                texto_inst = self.fuente_peque.render(texto, True, COLOR_TEXTO)
                self.pantalla.blit(texto_inst, (100, 500 + i * 30))
        else:
            texto_exito = self.fuente_normal.render("Press ENTER to continue!", True, COLOR_BIEN)
            self.pantalla.blit(texto_exito, (150, 520))
    def ejecutar(self) -> bool:
        print("\n" + "="*60)
        print("STARTING CALIBRATION")
        print("="*60)
        self.inicio_calibracion = time.time()

        while self.corriendo:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    self.client.stop()
                    pygame.quit()
                    return False
                elif evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_ESCAPE:
                        print("\n Cancelled by user")
                        self.client.stop()
                        pygame.quit()
                        return False
                elif evento.type == pygame.MOUSEBUTTONDOWN:
                    if self.calibracion_completa:
                        print("\n? Calibration successful! (Touch)")
                        self.lector.detener()
                        pygame.quit()
                        return True
                    elif evento.key == pygame.K_RETURN and self.calibracion_completa:
                        print("\n Calibration successful!")
                        self.client.stop()
                        pygame.quit()
                        return True

            metricas = self.client.get_data()
            tiempo_total = time.time() - self.inicio_calibracion

            es_valida, _ = self.senal_es_valida(metricas)

            if es_valida:
                if self.inicio_senal_estable is None:
                    self.inicio_senal_estable = time.time()
                    print(f" Stable signal detected")
                tiempo_estable = time.time() - self.inicio_senal_estable
                if tiempo_estable >= TIEMPO_ESTABLE:
                    self.calibracion_completa = True
                    print(f"CALIBRATION COMPLETE!")
            else:
                if self.inicio_senal_estable is not None:
                    print(f" Signal lost")
                self.inicio_senal_estable = None
                tiempo_estable = 0

            self.renderizar(metricas, tiempo_total, tiempo_estable)
            pygame.display.flip()
            self.reloj.tick(30)

            if tiempo_total > TIEMPO_TOTAL and not self.calibracion_completa:
                print("\n Time ran out without stable signal")
                print(" Make sure the sensor is properly placed")
                self.corriendo = False

        self.client.stop()
        pygame.quit()
        return self.calibracion_completa
if __name__ == "__main__":
    calibracion = PantallaCalibracion()
    exito = calibracion.ejecutar()
    if exito:
        print("\n System ready to use")
        sys.exit(0)
    else:
        print("\n Calibration failed")
        sys.exit(1)