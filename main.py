import numpy as np
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import requests

from Personaje import Personaje
from map import Mapa
from PersonajeAgent import PersonajeAgent

screen_width = 1200
screen_height = 800

FOVY = 60.0
ZNEAR = 0.01
ZFAR = 2000.0

EYE_X = 0.0
EYE_Y = 150.0
EYE_Z = 200.0
CENTER_X = 0
CENTER_Y = 0
CENTER_Z = 0
UP_X = 0
UP_Y = 1
UP_Z = 0

camera_mode = "ADELANTE"

DimBoard = 500

X_MIN = -600
X_MAX = 600
Y_MIN = -100
Y_MAX = 300
Z_MIN = -600
Z_MAX = 600

lab = None
humano = None
personajes = None

texture_grass = None
texture_wall = None
texture_sky = None


def load_texture(filename):

    texture_surface = pygame.image.load(filename)
    texture_data = pygame.image.tostring(texture_surface, "RGB", 1)
    width = texture_surface.get_width()
    height = texture_surface.get_height()

    texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height,
                 0, GL_RGB, GL_UNSIGNED_BYTE, texture_data)

    return texture


def Axis():
    glShadeModel(GL_FLAT)
    glLineWidth(3.0)

    glColor3f(1.0, 0.0, 0.0)
    glBegin(GL_LINES)
    glVertex3f(X_MIN, 0.0, 0.0)
    glVertex3f(X_MAX, 0.0, 0.0)
    glEnd()

    glColor3f(0.0, 1.0, 0.0)
    glBegin(GL_LINES)
    glVertex3f(0.0, Y_MIN, 0.0)
    glVertex3f(0.0, Y_MAX, 0.0)
    glEnd()

    glColor3f(0.0, 0.0, 1.0)
    glBegin(GL_LINES)
    glVertex3f(0.0, 0.0, Z_MIN)
    glVertex3f(0.0, 0.0, Z_MAX)
    glEnd()

    glLineWidth(1.0)


def dibujar_plano():
    glDisable(GL_LIGHTING)

    if texture_grass:
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texture_grass)
        glColor3f(1.0, 1.0, 1.0)
    else:
        glColor3f(0.2, 0.2, 0.2)

    glBegin(GL_QUADS)
    glTexCoord2f(0.0, 0.0)
    glVertex3d(-DimBoard, 0, -DimBoard)
    glTexCoord2f(0.0, 10.0)
    glVertex3d(-DimBoard, 0, DimBoard)
    glTexCoord2f(10.0, 10.0)
    glVertex3d(DimBoard, 0, DimBoard)
    glTexCoord2f(10.0, 0.0)
    glVertex3d(DimBoard, 0, -DimBoard)
    glEnd()

    if texture_grass:
        glDisable(GL_TEXTURE_2D)

    glColor3f(0.3, 0.3, 0.3)
    glBegin(GL_LINES)
    grid_size = 50
    for i in range(-DimBoard, DimBoard + 1, grid_size):
        glVertex3f(i, 0.1, -DimBoard)
        glVertex3f(i, 0.1, DimBoard)
        glVertex3f(-DimBoard, 0.1, i)
        glVertex3f(DimBoard, 0.1, i)
    glEnd()

    glEnable(GL_LIGHTING)


def dibujar_skybox():
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)

    if texture_sky:
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texture_sky)
        glColor3f(1.0, 1.0, 1.0)
    else:
        glColor3f(0.05, 0.05, 0.15)

    sky_size = 800

    glBegin(GL_QUADS)
    glTexCoord2f(0.0, 0.0)
    glVertex3f(-sky_size, -sky_size, -sky_size)
    glTexCoord2f(1.0, 0.0)
    glVertex3f(sky_size, -sky_size, -sky_size)
    glTexCoord2f(1.0, 1.0)
    glVertex3f(sky_size, sky_size, -sky_size)
    glTexCoord2f(0.0, 1.0)
    glVertex3f(-sky_size, sky_size, -sky_size)
    glEnd()

    glBegin(GL_QUADS)
    glTexCoord2f(0.0, 0.0)
    glVertex3f(-sky_size, -sky_size, sky_size)
    glTexCoord2f(1.0, 0.0)
    glVertex3f(sky_size, -sky_size, sky_size)
    glTexCoord2f(1.0, 1.0)
    glVertex3f(sky_size, sky_size, sky_size)
    glTexCoord2f(0.0, 1.0)
    glVertex3f(-sky_size, sky_size, sky_size)
    glEnd()

    glBegin(GL_QUADS)
    glTexCoord2f(0.0, 0.0)
    glVertex3f(-sky_size, -sky_size, -sky_size)
    glTexCoord2f(1.0, 0.0)
    glVertex3f(-sky_size, -sky_size, sky_size)
    glTexCoord2f(1.0, 1.0)
    glVertex3f(-sky_size, sky_size, sky_size)
    glTexCoord2f(0.0, 1.0)
    glVertex3f(-sky_size, sky_size, -sky_size)
    glEnd()

    glBegin(GL_QUADS)
    glTexCoord2f(0.0, 0.0)
    glVertex3f(sky_size, -sky_size, -sky_size)
    glTexCoord2f(1.0, 0.0)
    glVertex3f(sky_size, -sky_size, sky_size)
    glTexCoord2f(1.0, 1.0)
    glVertex3f(sky_size, sky_size, sky_size)
    glTexCoord2f(0.0, 1.0)
    glVertex3f(sky_size, sky_size, -sky_size)
    glEnd()

    glBegin(GL_QUADS)
    glTexCoord2f(0.0, 0.0)
    glVertex3f(-sky_size, sky_size, -sky_size)
    glTexCoord2f(1.0, 0.0)
    glVertex3f(sky_size, sky_size, -sky_size)
    glTexCoord2f(1.0, 1.0)
    glVertex3f(sky_size, sky_size, sky_size)
    glTexCoord2f(0.0, 1.0)
    glVertex3f(-sky_size, sky_size, sky_size)
    glEnd()

    if texture_sky:
        glDisable(GL_TEXTURE_2D)

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)


def celda_mapa(x, z, lab):
    celda_size = 50
    celda_x = int(round(x / celda_size)) + 7
    celda_z = int(round(z / celda_size)) + 6

    if 0 <= celda_z < lab.mat.shape[0] and 0 <= celda_x < lab.mat.shape[1]:
        return lab.mat[celda_z][celda_x]
    return 1


def actualizar_camara_seguimiento(side):
    global EYE_X, EYE_Y, EYE_Z, CENTER_X, CENTER_Y, CENTER_Z, lab

    if humano and lab:
        offset_dist = 80.0
        offset_height = 40.0

        rad = math.radians(humano.angulo_personaje)
        if side == "ATRAS":
            radside = rad
        else:
            radside = rad + math.radians(180)
        EYE_X = humano.posicion[0] + offset_dist * math.sin(radside)
        EYE_Y = humano.posicion[1] + offset_height
        EYE_Z = humano.posicion[2] + offset_dist * math.cos(radside)

        current_dist = offset_dist
        min_dist = 5.0

        while current_dist >= min_dist:
            EYE_X = humano.posicion[0] + current_dist * math.sin(radside)
            EYE_Z = humano.posicion[2] + current_dist * math.cos(radside)

            if celda_mapa(EYE_X, EYE_Z, lab) == 1:
                current_dist -= min_dist
            else:
                break

        if current_dist < min_dist:
            EYE_X = humano.posicion[0] + min_dist * math.sin(radside)
            EYE_Z = humano.posicion[2] + min_dist * math.cos(radside)

        CENTER_X = humano.posicion[0]
        CENTER_Y = humano.posicion[1] + 10
        CENTER_Z = humano.posicion[2]


def actualizar_vista():
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(EYE_X, EYE_Y, EYE_Z, CENTER_X,
              CENTER_Y, CENTER_Z, UP_X, UP_Y, UP_Z)


def fetch_game_state():
    try:
        response = requests.get("http://localhost:8000/state", timeout=0.2)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None


def compute_generator_progress(state):
    if not state:
        return 0, 0
    generators = state.get("generators", [])
    total = len(generators)
    fixed = sum(1 for gen in generators if gen.get("isFixed", False))
    return fixed, total


def draw_text_2d(text, x, y, font_size=36):
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, screen_width, screen_height, 0, -1, 1)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    
    glColor4f(0.0, 0.0, 0.0, 0.7)
    glBegin(GL_QUADS)
    glVertex2f(x - 10, y - 5)
    glVertex2f(x + len(text) * font_size * 0.6 + 10, y - 5)
    glVertex2f(x + len(text) * font_size * 0.6 + 10, y + font_size + 5)
    glVertex2f(x - 10, y + font_size + 5)
    glEnd()
    
    font = pygame.font.Font(None, font_size)
    text_surface = font.render(text, True, (255, 255, 255))
    text_data = pygame.image.tostring(text_surface, "RGBA", False)
    
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_TEXTURE_2D)
    
    text_texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, text_texture)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, text_surface.get_width(), 
                 text_surface.get_height(), 0, GL_RGBA, GL_UNSIGNED_BYTE, text_data)
    
    glColor4f(1.0, 1.0, 1.0, 1.0)
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0)
    glVertex2f(x, y)
    glTexCoord2f(1, 0)
    glVertex2f(x + text_surface.get_width(), y)
    glTexCoord2f(1, 1)
    glVertex2f(x + text_surface.get_width(), y + text_surface.get_height())
    glTexCoord2f(0, 1)
    glVertex2f(x, y + text_surface.get_height())
    glEnd()
    
    glDeleteTextures([text_texture])
    glDisable(GL_TEXTURE_2D)
    glDisable(GL_BLEND)
    
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()


def Init():
    global lab
    global personajes, humano
    global texture_grass, texture_wall, texture_sky

    screen = pygame.display.set_mode(
        (screen_width, screen_height), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Proyecto Final")

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(FOVY, screen_width / screen_height, ZNEAR, ZFAR)

    actualizar_camara_seguimiento(camera_mode)
    actualizar_vista()

    glClearColor(0.05, 0.05, 0.15, 1.0)
    glEnable(GL_DEPTH_TEST)
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    glLightfv(GL_LIGHT0, GL_POSITION, (100, 300, 100, 0.0))
    glLightfv(GL_LIGHT0, GL_AMBIENT, (0.2, 0.2, 0.3, 1.0))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.5, 0.5, 0.6, 1.0))
    glLightfv(GL_LIGHT0, GL_SPECULAR, (0.8, 0.8, 0.8, 1.0))
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)

    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glShadeModel(GL_SMOOTH)

    texture_grass = load_texture("textures/grass.jpg")
    texture_wall = load_texture("textures/wall.jpg")
    texture_sky = load_texture("textures/sky.jpg")

    lab = Mapa(texture_wall)

    humano = Personaje(lab)
    personajes = []

    personajes.append(PersonajeAgent(agent_id=5))
    personajes.append(PersonajeAgent(agent_id=6))
    personajes.append(PersonajeAgent(agent_id=7))
    personajes.append(PersonajeAgent(agent_id=8))

    print("\n=== CONTROLES ===")
    print("W: Avanzar")
    print("S: Retroceder")
    print("W+A: Avanzar girando a la izquierda")
    print("W+D: Avanzar girando a la derecha")
    print("S+A: Retroceder girando")
    print("S+D: Retroceder girando")
    print("\nCÁMARA:")
    print("C: Cambiar modo de cámara (Adelante/Atrás)")
    print("\nESC: Salir")
    print("\n=== AGENTES ===")
    print(f"Loaded {len(personajes)} agents from Julia server")

    return screen


def display(fixed, total):
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    dibujar_skybox()
    Axis()
    dibujar_plano()

    if lab:
        lab.draw()

    glBindTexture(GL_TEXTURE_2D, 0)
    if humano:
        humano.draw()

    if personajes:
        for personaje in personajes:
            personaje.draw()
    
    draw_text_2d(f"Generators: {fixed}/{total}", 20, 20, 48)

    nearby_generator = humano.get_nearby_generator() if humano else None
    if nearby_generator:
        time_left = max(nearby_generator.get("timeToFix", 0), 0)
        gen_id = nearby_generator.get("id", "?")
        if humano.is_fixing:
            draw_text_2d(f"Fixing generator {gen_id}… {time_left} time units left", 20, 90, 36)
        else:
            draw_text_2d(f"Hold F to fix generator {gen_id} ({time_left} left)", 20, 90, 36)


def main():
    global camera_mode, personajes, humano

    pygame.init()
    screen = Init()

    clock = pygame.time.Clock()
    done = False

    teclas_carrito = {
        'W': False,
        'A': False,
        'S': False,
        'D': False
    }

    estado_anterior = ""
    frame_count = 0
    cached_state = fetch_game_state()
    if cached_state:
        fixed, total = compute_generator_progress(cached_state)
        if lab:
            lab.update_generators_from_state(cached_state)
        if humano:
            humano.update_generator_cache(cached_state)
    else:
        fixed, total = 0, 0


    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    done = True
                elif event.key == pygame.K_c:
                    camera_mode = "ATRAS" if camera_mode == "ADELANTE" else "ADELANTE"
                    print(f"Modo de cámara: {camera_mode}")

        keys = pygame.key.get_pressed()

        teclas_carrito['W'] = keys[pygame.K_w]
        teclas_carrito['S'] = keys[pygame.K_s]
        teclas_carrito['A'] = keys[pygame.K_a]
        teclas_carrito['D'] = keys[pygame.K_d]
        fix_pressed = keys[pygame.K_f]

        actualizar_camara_seguimiento(camera_mode)
        actualizar_vista()

        if humano:
            humano.set_fixing_input(fix_pressed)
            humano.actualizar_estado(teclas_carrito)
            humano.update()

            if humano.estado != estado_anterior:
                print(f"Estado: {humano.estado}")
                estado_anterior = humano.estado

        if personajes:
            for personaje in personajes:
                personaje.update()
        
        frame_count += 1
        if frame_count % 30 == 0:
            latest_state = fetch_game_state()
            if latest_state:
                cached_state = latest_state
                fixed, total = compute_generator_progress(cached_state)
                if lab:
                    lab.update_generators_from_state(cached_state)
                if humano:
                    humano.update_generator_cache(cached_state)
            frame_count = 0

        display(fixed, total)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


main()
