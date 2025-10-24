import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math

from objloader import OBJ
from Personaje import Personaje

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

camera_mode = "IZQUIERDA"  

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

def actualizar_camara_seguimiento(side):
    global EYE_X, EYE_Y, EYE_Z, CENTER_X, CENTER_Y, CENTER_Z
    
    if personaje:
        offset_dist = 80.0
        offset_height = 40.0
        
        rad = math.radians(personaje.angulo_personaje)
        if side == "IZQUIERDA":
            radside = rad #+ math.pi / 2
        else:
            radside = rad + math.radians(180) 
        EYE_X = personaje.posicion[0] + offset_dist * math.sin(radside)
        EYE_Y = personaje.posicion[1] + offset_height
        EYE_Z = personaje.posicion[2] + offset_dist * math.cos(radside)
        
        CENTER_X = personaje.posicion[0]
        CENTER_Y = personaje.posicion[1] + 10
        CENTER_Z = personaje.posicion[2]

def actualizar_vista():
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(EYE_X, EYE_Y, EYE_Z, CENTER_X, CENTER_Y, CENTER_Z, UP_X, UP_Y, UP_Z)

def Init():
    global personaje 
    
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
    
    obj_personaje = OBJ("model/personaje.obj", swapyz=False)
    obj_brazo = OBJ("model/brazo.obj", swapyz=False)
    obj_pierna = OBJ("model/pierna.obj", swapyz=True)
   
    personaje = Personaje(obj_personaje, obj_brazo, obj_pierna)
    
    print("\n=== CONTROLES ===")
    print("W: Avanzar")
    print("S: Retroceder")
    print("W+A: Avanzar girando a la izquierda")
    print("W+D: Avanzar girando a la derecha")
    print("S+A: Retroceder girando")
    print("S+D: Retroceder girando")
    print("\nCÁMARA:")
    print("C: Cambiar modo de cámara (Izquieda/Derecha)")
    print("\nESC: Salir")

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    # Dibujar ejes y plano
    Axis()
    dibujar_plano()
    
    # Dibujar el carrito
    if personaje:
        personaje.draw()

def main():
    global camera_mode,personaje 
    
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
                    camera_mode = "DERECHA" if camera_mode == "IZQUIERDA" else "IZQUIERDA"
                    print(f"Modo de cámara: {camera_mode}")
        
        keys = pygame.key.get_pressed()
        
        teclas_carrito['W'] = keys[pygame.K_w]
        teclas_carrito['S'] = keys[pygame.K_s]
        teclas_carrito['A'] = keys[pygame.K_a]
        teclas_carrito['D'] = keys[pygame.K_d]
        
        actualizar_camara_seguimiento(camera_mode)
        actualizar_vista()

        if personaje:
            personaje.actualizar_estado(teclas_carrito)
            personaje.update()
            
            if personaje.estado != estado_anterior:
                print(f"Estado: {personaje.estado}")
                estado_anterior = personaje.estado
        
        display()
        
        pygame.display.flip()
        clock.tick(60)  # 60 FPS
    
    pygame.quit()

main()
