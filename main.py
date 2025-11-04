import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math

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

# Dimensión del plano
DimBoard = 500

# Variables para los ejes
X_MIN = -600
X_MAX = 600
Y_MIN = -100
Y_MAX = 300
Z_MIN = -600
Z_MAX = 600

# Objeto carrito
personaje = None
lab = None
humano = None
personajes = None

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
    
    glColor3f(0.2, 0.2, 0.2)
    glBegin(GL_QUADS)
    glVertex3d(-DimBoard, 0, -DimBoard)
    glVertex3d(-DimBoard, 0, DimBoard)
    glVertex3d(DimBoard, 0, DimBoard)

    glVertex3d(DimBoard, 0, -DimBoard)
    glEnd()
    
    # Líneas de cuadrícula
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
    
def celda_mapa(x, z, lab):
    celda_size = 50
    celda_x = int(round(x / celda_size)) + 7
    celda_z = int(round(z  / celda_size)) + 6
    
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
    gluLookAt(EYE_X, EYE_Y, EYE_Z, CENTER_X, CENTER_Y, CENTER_Z, UP_X, UP_Y, UP_Z)

def Init():
    global personaje 
    global lab
    global personajes, humano 
    
    screen = pygame.display.set_mode(
        (screen_width, screen_height), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Control de Carrito - Máquina de Estados")
    
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(FOVY, screen_width / screen_height, ZNEAR, ZFAR)
    
    actualizar_camara_seguimiento(camera_mode)
    actualizar_vista()
  
    glClearColor(0.1, 0.1, 0.15, 1.0)
    glEnable(GL_DEPTH_TEST)
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    
    glLightfv(GL_LIGHT0, GL_POSITION, (100, 300, 100, 0.0))
    glLightfv(GL_LIGHT0, GL_AMBIENT, (0.3, 0.3, 0.3, 1.0))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.8, 0.8, 0.8, 1.0))
    glLightfv(GL_LIGHT0, GL_SPECULAR, (1.0, 1.0, 1.0, 1.0))
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)

    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glShadeModel(GL_SMOOTH)
    
    lab = Mapa()
   
    personaje = Personaje(lab.mat)
    humano = Personaje(lab.mat)
    personajes = []

    for i in range(4):
        personajes.append(PersonajeAgent())
    
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

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    # Dibujar ejes y plano
    Axis()
    dibujar_plano()
    
    if lab:
        lab.draw()
    
    # Dibujar el carrito
    humano.draw()
    for personaje in personajes:
        personaje.draw()

def main():
    global camera_mode, personajes, humano 
    
    pygame.init()
    Init()
    
    clock = pygame.time.Clock()
    done = False
    
    teclas_carrito = {
        'W': False,
        'A': False,
        'S': False,
        'D': False
    }
    
    estado_anterior = ""
    

    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    done = True
                elif event.key == pygame.K_c:
                    # Cambiar modo de cámara
                    camera_mode = "ATRAS" if camera_mode == "ADELANTE" else "ADELANTE"
                    print(f"Modo de cámara: {camera_mode}")
        
        keys = pygame.key.get_pressed()
        
        teclas_carrito['W'] = keys[pygame.K_w]
        teclas_carrito['S'] = keys[pygame.K_s]
        teclas_carrito['A'] = keys[pygame.K_a]
        teclas_carrito['D'] = keys[pygame.K_d]
        
        actualizar_camara_seguimiento(camera_mode)
        actualizar_vista()

        if humano:
            humano.actualizar_estado(teclas_carrito)
            humano.update()
            
            if humano.estado != estado_anterior:
                print(f"Estado: {humano.estado}")
                estado_anterior = humano.estado
        
        display()
        
        pygame.display.flip()
        clock.tick(60)  # 60 FPS
    
    pygame.quit()

main()
