import numpy as np
import math
from objloader import OBJ 
from OpenGL.GL import *
from OpenGL.GLU import *

class PersonajeAgent:
    def __init__(self):
        obj_personaje = OBJ("model/personaje.obj", swapyz=False)
        obj_brazo = OBJ("model/brazo.obj", swapyz=False)
        obj_pierna = OBJ("model/pierna.obj", swapyz=True)
        self.torso = obj_personaje
        self.brazo = obj_brazo
        self.pierna = obj_pierna
        
        self.posicion = np.array([0.0, 15.0, 0.0])  
        self.angulo_personaje = 0.0  
        self.estado = None
        
        self.velocidad_avance = 3.0
        self.giro_brazo_izq = 0.0
        self.velocidad_giro = 5.0
        self.giro_brazo_der = 0.0
        
        self.offset_brazo_izq = np.array([5.5, 5.4, 0.0])  # Derecha, adelante
        self.offset_brazo_der = np.array([-5.5, 5.4, 0.0])  # Izquierda, adelante
        self.offset_pierna_izq = np.array([2.0, -7.0, 0.0])  # Centro, atrás
        self.offset_pierna_der = np.array([-2.0, -7.0, 0.0])
        
        self.escala = 10.0
        self.animacion = False
        
        
        
    def calcular_matriz_torso(self):
        """
        MATRIZ PRECALCULADA TORSO:
        [e*cos(c), 0, e*sin(c), tx],
        [0, e, 0, ty],
        [-sin(c)*e, 0, cos(c)*e, tz],
        [0, 0, 0, 1]
        """
        esc = self.escala
        ang_rad = math.radians(self.angulo_personaje)
        c = math.cos(ang_rad)
        s = math.sin(ang_rad)
        tx, ty, tz = self.posicion[0], self.posicion[1], self.posicion[2] 
        
        return np.array([
            [esc*c, 0, esc*s, tx],
            [0, esc, 0, ty],
            [s*esc*-1, 0, c*esc, tz],
            [0, 0, 0, 1]
        ], dtype=float)
    
    def calcular_matriz_extremidades(self, offset, giro):
        """
        MATRIZ COLAPSADA extremidades:

        [e*cos(c), e*sin(a)*sin(c), e*sin(c)*cos(a), ox*cos(c) + oz*sin(c) + tx],
        [0, e*cos(a), -e*sin(a), oy + ty],
        [-e*sin(c), e*sin(a)*cos(c), e*cos(a)*cos(c), -ox*sin(c) + oz*cos(c) + tz],
        [0, 0, 0, 1]
        """
        tx, ty, tz = self.posicion[0], self.posicion[1], self.posicion[2]
        ang_rad = math.radians(self.angulo_personaje)
        c = math.cos(ang_rad)
        s = math.sin(ang_rad)
        ox, oy, oz = offset[0], offset[1], offset[2] 
        esc = self.escala 
        ang_rad = math.radians(giro)
        crot = math.cos(ang_rad)
        srot = math.sin(ang_rad)
        
        return np.array([
        [esc*c, esc*srot*s, esc*s*crot, ox*c + oz*s + tx],
        [0, esc*crot, (-1)*esc*srot, oy + ty],
        [(-1)*esc*s, esc*srot*c, esc*crot*c, (-1)*ox*s + oz*c + tz],
        [0, 0, 0, 1]
        ], dtype=float) 
    
    def aplicar_matriz_opengl(self, matriz):
        glMultMatrixf(matriz.T.astype(np.float32))
    
    def animation(self, factor):
        if self.giro_brazo_izq >= 50 or self.giro_brazo_der >= 50:
            self.animacion = not self.animacion
        if self.animacion:
            self.giro_brazo_izq += self.velocidad_giro*factor
            self.giro_brazo_der -= self.velocidad_giro*factor
        else:
            self.giro_brazo_der += self.velocidad_giro*factor
            self.giro_brazo_izq -= self.velocidad_giro*factor
    
    def update(self, x, y):
        angulo = self.angulo_personaje
        if angulo < 0:
            angulo += 360
        if x < self.posicion[0]:
            if angulo%360 == 270:
                self.forward()
            else:
                if angulo%360 > 270 or angulo%360 <= 90:
                    self.turn_left()
                else:
                    self.turn_right()
        elif x > self.posicion[0]:
            if angulo%360 == 90:
                self.forward()
            else:
                if angulo%360 <= 270 and angulo%360 > 90:
                    self.turn_left()
                else:
                    self.turn_right()
        elif y < self.posicion[1]:
            if angulo%360 == 180:
                self.forward()
            else:
                if angulo%360 == 0 or angulo%360 > 180:
                    self.turn_left()
                else:
                    self.turn_right()
        elif y > self.posicion[1]:
            if angulo%360 == 0:
                self.forward()
            else:
                if angulo%360 <= 180:
                    self.turn_left()
                else:
                    self.turn_right()
        else:
            self.estado = "resting"

        self.angulo_personaje = angulo

    def turn_right(self):
        self.angulo_personaje -= self.velocidad_giro
        self.reset()
        self.estado = "moving"

    def turn_left(self):
        self.angulo_personaje -= self.velocidad_giro
        self.reset()
        self.estado = "moving"

    def forward(self):
        rad = math.radians(self.angulo_personaje)
        self.posicion[0] += self.velocidad_avance * math.sin(rad)
        self.posicion[2] += self.velocidad_avance * math.cos(rad)
        self.animation(1)
        self.estado = "moving"

    def reset(self):
        if abs(self.giro_brazo_izq) > 0.5:
            self.giro_brazo_izq /= self.velocidad_giro
            self.giro_brazo_der /= self.velocidad_giro
        else:
            self.giro_brazo_izq = 0.0
            self.giro_brazo_der = 0.0
    
    def draw(self):
        glPushMatrix()
        self.aplicar_matriz_opengl(self.calcular_matriz_torso())
        self.torso.render()
        glPopMatrix()
        
        glPushMatrix()
        self.aplicar_matriz_opengl(self.calcular_matriz_extremidades(self.offset_brazo_der, self.giro_brazo_der))
        self.brazo.render()
        glPopMatrix()
        
        glPushMatrix()
        self.aplicar_matriz_opengl(self.calcular_matriz_extremidades(self.offset_pierna_izq, self.giro_brazo_der))
        self.pierna.render()
        glPopMatrix()
        
        glPushMatrix()
        self.aplicar_matriz_opengl(self.calcular_matriz_extremidades(self.offset_brazo_izq, self.giro_brazo_izq))
        self.brazo.render()
        glPopMatrix()

        glPushMatrix()
        self.aplicar_matriz_opengl(self.calcular_matriz_extremidades(self.offset_pierna_der, self.giro_brazo_izq))
        self.pierna.render()
        glPopMatrix()
