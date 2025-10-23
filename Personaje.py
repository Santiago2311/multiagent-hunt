import numpy as np
import math
from OpenGL.GL import *
from OpenGL.GLU import *

class Personaje:
    def __init__(self, obj_personaje, obj_brazo, obj_pierna):
        self.torso = obj_personaje
        self.brazo = obj_brazo
        self.pierna = obj_pierna
        
        self.posicion = np.array([0.0, 0.0, 0.0])  
        self.angulo_personaje = 0.0  
        
        self.velocidad_avance = 2.0
        self.giro_brazo_izq = 0.0
        self.velocidad_giro = 5.0
        self.giro_brazo_der = 0.0
        
        self.estado = "REPOSO"  
        
        self.offset_brazo_izq = np.array([7.0, 3.0, 13.0])  # Derecha, adelante
        self.offset_brazo_der = np.array([-7.0, 3.0, 13.0])  # Izquierda, adelante
        self.offset_pierna_izq = np.array([0.0, 3.0, -13.0])  # Centro, atrás
        self.offset_pierna_der = np.array([0.0, 0.0, 0.0])
        
        self.escala = 10.0
        self.animacion = False
        
        #T(pos) * R_y(a)
        """[cos(a), 0, sin(a), tx],
            [0, 1, 0, ty],
            [-sin(a), 0, cos(a), tz],
            [0, 0, 0, 1]"""
        #matriz_punto_inicial
        #Punto_inicial * E(s)
        """[e*cos(a), 0, e*sin(a), tx],
            [0, e, 0, ty],
            [-sin(a)*e, 0, cos(a)*e, tz],
            [0, 0, 0, 1]"""
        #matriz_carroceria = 
        #Punto_inicial * T(offset) * R_y(b) * R_x(c) * E(s)
        """[e*(-sin(a)*sin(b) + cos(a)*cos(b)), e*(sin(a)*cos(b) + sin(b)*cos(a))*sin(c), e*(sin(a)*cos(b) + sin(b)*cos(a))*cos(c)
            , ox*cos(a) + oz*sin(a) + tx],
            [0, e*cos(c), -e*sin(c), oy + ty],
            [e*(-sin(a)*cos(b) - sin(b)*cos(a)), e*(-sin(a)*sin(b) + cos(a)*cos(b))*sin(c), e*(-sin(a)*sin(b) + cos(a)*cos(b))*cos(
            c), -ox*sin(a) + oz*cos(a) + tz],
            [0, 0, 0, 1]"""
        #matriz_llanta_derecha = 
        #Punto_inicial * T(offset) * R_y(b) * R_x(c) * E(s)
        """[e*(-sin(a)*sin(b) + cos(a)*cos(b)), e*(sin(a)*cos(b) + sin(b)*cos(a))*sin(c), e*(sin(a)*cos(b) + sin(b)*cos(a))*cos(c)
            , ox*cos(a) + oz*sin(a) + tx],
            [0, e*cos(c), -e*sin(c), oy + ty],
            [e*(-sin(a)*cos(b) - sin(b)*cos(a)), e*(-sin(a)*sin(b) + cos(a)*cos(b))*sin(c), e*(-sin(a)*sin(b) + cos(a)*cos(b))*cos(
            c), -ox*sin(a) + oz*cos(a) + tz],
            [0, 0, 0, 1]"""
        #matriz_llanta_izquieda =
        #Punto_inicial * T(offset) * R_x(c) * E(s)
        """[e*cos(a), e*sin(a)*sin(c), e*sin(a)*cos(c), ox*cos(a) + oz*sin(a) + tx],
            [0, e*cos(c), -e*sin(c), oy + ty],
            [-e*sin(a), e*sin(c)*cos(a), e*cos(a)*cos(c), -ox*sin(a) + oz*cos(a) + tz],
            [0, 0, 0, 1]"""
        #matriz_llantas_traseras =
        
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
        [(-1)*esc*s, esc*srot*c, esc*crot*c, (-1)*s + oz*c + tz],
        [0, 0, 0, 1]
        ], dtype=float) 
    
    def aplicar_matriz_opengl(self, matriz):
        glMultMatrixf(matriz.T.astype(np.float32))
    
    def actualizar_estado(self, teclas_presionadas):
        w_pressed = teclas_presionadas.get('W', False)
        s_pressed = teclas_presionadas.get('S', False)
        a_pressed = teclas_presionadas.get('A', False)
        d_pressed = teclas_presionadas.get('D', False)
        
        if w_pressed and not a_pressed and not d_pressed:
            self.estado = "AVANZAR"
        elif s_pressed and not a_pressed and not d_pressed:
            self.estado = "RETROCEDER"
        elif w_pressed and a_pressed:
            self.estado = "AVANZAR_GIRAR_IZQ"
        elif w_pressed and d_pressed:
            self.estado = "AVANZAR_GIRAR_DER"
        elif s_pressed and a_pressed:
            self.estado = "RETROCEDER_GIRAR_DER"
        elif s_pressed and d_pressed:
            self.estado = "RETROCEDER_GIRAR_IZQ"
        elif a_pressed:
            self.estado = "GIRAR_IZQ_ESTATICO"
        elif d_pressed:
            self.estado = "GIRAR_DER_ESTATICO"
        else:
            self.estado = "REPOSO"

    def animation(self):
        if self.giro_brazo_izq >= 30 or self.giro_brazo_der >= 30:
            self.animacion = not self.animacion
        if self.animacion:
            self.giro_brazo_izq += self.velocidad_giro
            self.giro_brazo_der += self.velocidad_giro
        else:
            self.giro_brazo_der += self.velocidad_giro
            self.giro_brazo_izq -= self.velocidad_giro
    
    def update(self):
        if self.estado == "AVANZAR":
            rad = math.radians(self.angulo_personaje)
            self.posicion[0] += self.velocidad_avance * math.sin(rad)
            self.posicion[2] += self.velocidad_avance * math.cos(rad)
            self.animation()
            
        elif self.estado == "RETROCEDER":
            rad = math.radians(self.angulo_carrito)
            self.posicion[0] -= self.velocidad_avance * math.sin(rad)
            self.posicion[2] -= self.velocidad_avance * math.cos(rad)
            self.animation()
            
        elif self.estado == "AVANZAR_GIRAR_IZQ":
            self.angulo_personaje += self.velocidad_giro
            rad = math.radians(self.angulo_carrito)
            self.posicion[0] += self.velocidad_avance * math.sin(rad)
            self.posicion[2] += self.velocidad_avance * math.cos(rad)
            self.animation() 

        elif self.estado == "AVANZAR_GIRAR_DER":
            self.angulo_carrito -= self.velocidad_giro
            rad = math.radians(self.angulo_carrito)
            self.posicion[0] += self.velocidad_avance * math.sin(rad)
            self.posicion[2] += self.velocidad_avance * math.cos(rad)
            self.animation()
            
        elif self.estado == "RETROCEDER_GIRAR_DER":
            self.angulo_carrito -= self.velocidad_giro
            rad = math.radians(self.angulo_carrito)
            self.posicion[0] -= self.velocidad_avance * math.sin(rad)
            self.posicion[2] -= self.velocidad_avance * math.cos(rad)
            self.animation()
            
        elif self.estado == "RETROCEDER_GIRAR_IZQ":
            self.angulo_carrito += self.velocidad_giro
            rad = math.radians(self.angulo_carrito)
            self.posicion[0] -= self.velocidad_avance * math.sin(rad)
            self.posicion[2] -= self.velocidad_avance * math.cos(rad)
            self.animation()
            
        elif self.estado == "GIRAR_IZQ_ESTATICO":
            self.angulo_personaje += self.velocidad_giro
            
        elif self.estado == "GIRAR_DER_ESTATICO":
            self.angulo_personaje -= self.velocidad_giro
            
        elif self.estado == "REPOSO":
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
