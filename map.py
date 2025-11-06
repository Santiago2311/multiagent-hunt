import numpy as np
from OpenGL.GL import *
from objloader import OBJ

mat = [[1,1,1,1,1,1,0,1,1,1,1,1,1],
        [1,0,0,0,0,1,0,0,0,0,1,0,1],
        [1,0,0,1,0,0,0,1,1,0,0,0,1],
        [1,0,1,1,0,0,1,0,0,0,1,1,1],
        [1,0,0,0,0,1,0,0,1,0,0,0,1],
        [1,0,1,0,1,1,1,1,1,0,0,0,1],
        [1,0,1,1,1,0,0,0,1,1,0,0,1],
        [1,0,0,0,1,0,0,0,0,0,0,1,1],
        [1,1,0,1,1,0,0,0,1,0,0,1,1],
        [1,0,0,0,0,1,1,1,0,0,0,0,1],
        [1,0,1,1,1,1,0,0,0,1,1,0,1],
        [1,0,0,0,0,0,0,1,0,1,0,0,1],
        [1,1,1,1,1,1,1,1,1,1,1,1,1]]

genpos = [
    [1, 1],
    [1, 4],
    [1, 11],
    [4, 4],
    [4, 11],
    [5, 9],
    [9, 1],
    [9, 4],
    [9, 11],
    [10, 11]
]

class Mapa:
    def __init__(self):
        generador = OBJ("model/generador.obj", swapyz=True) 
        
        self.generador = generador
        self.centro = (6, 7)
        self.num_generadores = 3
        self.posiciones = np.random.choice(len(genpos), self.num_generadores, replace=False)
        self.mat = np.array(mat)
        self.gens = []
        self.genpositions()
    
    def draw_cube(self, size=1.0):
        hs = size / 2.0
        glBegin(GL_QUADS)
        # Frente
        glVertex3f(-hs, -hs, hs)
        glVertex3f(hs, -hs, hs)
        glVertex3f(hs, hs, hs)
        glVertex3f(-hs, hs, hs)
        # Atrás
        glVertex3f(-hs, -hs, -hs)
        glVertex3f(-hs, hs, -hs)
        glVertex3f(hs, hs, -hs)
        glVertex3f(hs, -hs, -hs)
        # Izquierda
        glVertex3f(-hs, -hs, -hs)
        glVertex3f(-hs, -hs, hs)
        glVertex3f(-hs, hs, hs)
        glVertex3f(-hs, hs, -hs)
        # Derecha
        glVertex3f(hs, -hs, -hs)
        glVertex3f(hs, hs, -hs)
        glVertex3f(hs, hs, hs)
        glVertex3f(hs, -hs, hs)
        # Arriba
        glVertex3f(-hs, hs, -hs)
        glVertex3f(-hs, hs, hs)
        glVertex3f(hs, hs, hs)
        glVertex3f(hs, hs, -hs)
        # Abajo
        glVertex3f(-hs, -hs, -hs)
        glVertex3f(hs, -hs, -hs)
        glVertex3f(hs, -hs, hs)
        glVertex3f(-hs, -hs, hs)
        glEnd()

    def draw(self):
        glColor3f(0.5, 0.5, 0.5)
        for fila in range(len(mat)):
            for columna in range(len(mat[0])):
                if mat[fila][columna] == 1:
                    glPushMatrix()
                    x = columna - self.centro[1]
                    z = fila - self.centro[0]
                    glTranslatef(x * 50.0, 1.0, z * 50.0)
                    glScalef(50.0, 150.0, 50.0)
                    self.draw_cube(1.0)
                    glPopMatrix()
        
        for idx in self.posiciones:
            r, c = genpos[idx]
            x = c - self.centro[1]
            z = r - self.centro[0]
            glPushMatrix()
            glTranslatef(x * 50, 0.0, z * 50)
            glScalef(5.0, 6.0, 5.0)
            self.generador.render()
            glPopMatrix()

    def genpositions(self):
        for idx in self.posiciones:
            r, c = genpos[idx]
            x = (c - self.centro[1]) * 50
            z = (r - self.centro[0]) * 50
            self.gens.append([x, z])

