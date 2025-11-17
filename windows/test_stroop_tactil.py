import pygame
import random
import sys
import time
import numpy as np

pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2)

# ----------------- Sonidos -----------------
def generar_bum(freq=250, duracion=0.3, volumen=0.8):
    samplerate = 44100
    t = np.linspace(0, duracion, int(samplerate * duracion), endpoint=False)
    envelope = np.exp(-5 * t)
    wave = np.sin(2 * np.pi * freq * t) * envelope
    wave *= 32767
    wave = wave.astype(np.int16)
    stereo_wave = np.column_stack((wave, wave))
    sound = pygame.sndarray.make_sound(stereo_wave)
    sound.set_volume(volumen)
    return sound

bum_bajo = generar_bum(freq=250)
bum_agudo = generar_bum(freq=400)
fallo_sonido = generar_bum(freq=350)

# ----------------- Ventana -----------------
WIDTH, HEIGHT = 800, 600
WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Test de Stroop Táctil v2")

FONT = pygame.font.Font(None, 100)
SMALL_FONT = pygame.font.Font(None, 40)
BUTTON_FONT = pygame.font.Font(None, 80)

COLORS = {
    "ROJO": (255, 0, 0),
    "VERDE": (0, 255, 0),
    "AMARILLO": (255, 255, 0),
    "MORADO": (128, 0, 128),
    "BLANCO": (255, 255, 255)
}

# ----------------- Botones táctiles -----------------
class Boton:
    def __init__(self, texto, color_logico, rect):
        self.texto = texto  # La letra (R, V, A, M, B)
        self.color_logico = color_logico  # El color que representa
        self.rect = pygame.Rect(rect)

    def dibujar(self, superficie):
        # Fondo blanco con borde negro
        pygame.draw.rect(superficie, (255, 255, 255), self.rect, border_radius=10)
        pygame.draw.rect(superficie, (0, 0, 0), self.rect, width=3, border_radius=10)

        # Letra negra centrada
        texto_render = BUTTON_FONT.render(self.texto, True, (0, 0, 0))
        texto_rect = texto_render.get_rect(center=self.rect.center)
        superficie.blit(texto_render, texto_rect)

    def clicado(self, pos):
        return self.rect.collidepoint(pos)

# Crear botones táctiles
def crear_botones():
    botones = []
    letras = [("R", "ROJO"), ("V", "VERDE"), ("A", "AMARILLO"), ("M", "MORADO"), ("B", "BLANCO")]
    ancho = WIDTH // len(letras)
    alto = 100
    y = HEIGHT - alto - 20
    for i, (letra, color) in enumerate(letras):
        rect = (i * ancho + 10, y, ancho - 20, alto)
        botones.append(Boton(letra, color, rect))
    return botones

botones = crear_botones()

# ----------------- Funciones -----------------
def mostrar_texto(texto, color, pos, size=100):
    font = pygame.font.Font(None, size)
    render = font.render(texto, True, color)
    rect = render.get_rect(center=pos)
    WINDOW.blit(render, rect)

def dibujar_barra_tiempo(tiempo_restante, tiempo_total):
    barra_ancho = int((tiempo_restante / tiempo_total) * (WIDTH - 100))
    x, y, h = 50, 50, 25
    if tiempo_restante > tiempo_total * 0.6:
        color = (0, 255, 0)
    elif tiempo_restante > tiempo_total * 0.3:
        color = (255, 165, 0)
    else:
        color = (255, 0, 0)
    pygame.draw.rect(WINDOW, (60, 60, 60), (x, y, WIDTH - 100, h))
    pygame.draw.rect(WINDOW, color, (x, y, barra_ancho, h))

def borde_rojo_vibrante(tiempo_restante):
    if tiempo_restante < 1.5:
        intensidad = 6
        offset = random.randint(-intensidad, intensidad)
        rojo = (255, random.randint(0, 100), random.randint(0, 100))
        thickness = 10
        pygame.draw.rect(WINDOW, rojo, (0 + offset, 0 + offset, WIDTH - offset * 2, HEIGHT - offset * 2), thickness)

def mostrar_x_error():
    fallo_sonido.play()
    WINDOW.fill((0, 0, 0))
    thickness = 20
    pygame.draw.line(WINDOW, (255, 0, 0), (100, 100), (WIDTH - 100, HEIGHT - 100), thickness)
    pygame.draw.line(WINDOW, (255, 0, 0), (WIDTH - 100, 100), (100, HEIGHT - 100), thickness)
    pygame.display.flip()
    pygame.time.wait(500)

def generar_tiempo_ronda(ronda):
    if random.random() < 0.1:
        return 0.5
    return max(1, 3 - (ronda - 1) * 0.12)

# ----------------- Main -----------------
def main():
    score = 0
    ronda = 0
    max_rondas = 15
    clock = pygame.time.Clock()

    while ronda < max_rondas:
        ronda += 1
        tiempo_por_ronda = generar_tiempo_ronda(ronda)

        palabra = random.choice(list(COLORS.keys()))
        color_texto = random.choice(list(COLORS.values()))
        color_real = [k for k, v in COLORS.items() if v == color_texto][0]

        pos_x = random.randint(200, WIDTH - 200)
        pos_y = random.randint(150, HEIGHT - 200)
        pos = (pos_x, pos_y)

        inicio = time.time()
        respuesta = None
        terminado = False

        while not terminado:
            tiempo_restante = tiempo_por_ronda - (time.time() - inicio)
            WINDOW.fill((random.randint(20, 50), random.randint(20, 50), random.randint(20, 50)))

            mostrar_texto(palabra, color_texto, pos)
            dibujar_barra_tiempo(max(0, tiempo_restante), tiempo_por_ronda)
            borde_rojo_vibrante(tiempo_restante)

            ronda_txt = SMALL_FONT.render(f"Ronda {ronda}/{max_rondas}", True, (200, 200, 200))
            WINDOW.blit(ronda_txt, (WIDTH - 230, 20))

            # Dibujar botones
            for boton in botones:
                boton.dibujar(WINDOW)

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    for boton in botones:
                        if boton.clicado(mouse_pos):
                            respuesta = boton.color_logico
                            terminado = True

            if tiempo_restante <= 0:
                mostrar_x_error()
                terminado = True
            elif tiempo_restante < 1:
                if random.random() < 0.1:
                    bum_bajo.play()
                    bum_agudo.play()

            clock.tick(60)

        if respuesta != color_real:
            mostrar_x_error()
        else:
            score += 1

    # Resultado final
    WINDOW.fill((0, 0, 0))
    resultado = FONT.render(f"Puntuación: {score}/{max_rondas}", True, (255, 255, 255))
    rect = resultado.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    WINDOW.blit(resultado, rect)
    pygame.display.flip()
    pygame.time.wait(3000)
    pygame.quit()

if __name__ == "__main__":
    main()
