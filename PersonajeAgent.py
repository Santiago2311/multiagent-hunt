import numpy as np
import math
from objloader import OBJ 
from OpenGL.GL import *
from OpenGL.GLU import *
import requests

class PersonajeAgent:
    def __init__(self, agent_id, base_url="http://localhost:8000"):
        obj_personaje = OBJ("model/personaje.obj", swapyz=False)
        obj_brazo = OBJ("model/brazo.obj", swapyz=False)
        obj_pierna = OBJ("model/pierna.obj", swapyz=True)
        self.torso = obj_personaje
        self.brazo = obj_brazo
        self.pierna = obj_pierna
        
        self.agent_id = agent_id
        self.base_url = base_url
        
        self.posicion = np.array([0.0, 15.0, 0.0])  
        self.angulo_personaje = 0.0  
        self.estado = "resting"
        
        self.velocidad_avance = 3.0
        self.giro_brazo_izq = 0.0
        self.velocidad_giro = 5.0
        self.giro_brazo_der = 0.0
        
        self.offset_brazo_izq = np.array([5.5, 5.4, 0.0])
        self.offset_brazo_der = np.array([-5.5, 5.4, 0.0])
        self.offset_pierna_izq = np.array([2.0, -7.0, 0.0])
        self.offset_pierna_der = np.array([-2.0, -7.0, 0.0])
        
        self.escala = 10.0
        self.animacion = False
        
        self.target_pos = None
        self.moving_to_target = False

        self.turning = False
        self.angle_to_target = 0.0
        
        self.init_position_from_server()
        
    def grid_to_world(self, grid_x, grid_y):
        center_col = 8
        center_row = 7
        cell_size = 50.0
        
        world_x = (grid_x - center_col) * cell_size
        world_z = (grid_y - center_row) * cell_size
        
        return world_x, world_z
        
    def calcular_matriz_torso(self):
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
    
    def fetch_state_from_server(self):
        response = requests.get(f"{self.base_url}/agent/{self.agent_id}")
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"Failed to fetch agent {self.agent_id}: {response.status_code}")
            return None
    
    def step_on_server(self):
        response = requests.post(f"{self.base_url}/agent/{self.agent_id}/step")
        if response.status_code == 200:
            data = response.json()
            return data.get("agent")
        else:
            print(f"Failed to step agent {self.agent_id}: {response.status_code}")
            return None
            
    def init_position_from_server(self):
        agent_data = self.fetch_state_from_server()
        if agent_data:
            grid_pos = agent_data.get("pos")
            if grid_pos:
                world_x, world_z = self.grid_to_world(grid_pos[0], grid_pos[1])
                self.posicion = np.array([world_x, 15.0, world_z])
    
    def update(self):
        if not self.moving_to_target:
            agent_data = self.step_on_server()
        
            if agent_data is None:
                return
        
            grid_pos = agent_data.get("pos")
            if grid_pos:
                target_x, target_z = self.grid_to_world(grid_pos[0], grid_pos[1])
                new_target = np.array([target_x, 15.0, target_z])
            
                if self.target_pos is None or not np.allclose(new_target, self.target_pos, atol=1.0):
                    self.target_pos = new_target
                    self.moving_to_target = True
        
        if self.moving_to_target and self.target_pos is not None:
            diff = self.target_pos - self.posicion
            #diff[1] = 0  # Don't move in Y direction
            distance = np.linalg.norm(diff)
            
            if distance > 1.0:  # Still moving
                if abs(diff[0]) > 0.01 or abs(diff[2]) > 0.01 and not self.turning:
                    self.angle_to_target = (math.degrees(math.atan2(diff[0], diff[2])) + 360) % 360                    #self.angulo_personaje = angle_to_target
                    #self.angle_to_target -= self.angle_to_target % 90
                    self.angle_to_target = round(self.angle_to_target / 90) * 90
                    self.angle_to_target %= 360
                    self.angulo_personaje = abs(self.angulo_personaje) % 360
                    self.turning = True
                
                if self.turning and self.angulo_personaje != self.angle_to_target:
                    self.angulo_personaje += self.velocidad_giro
                    if self.angulo_personaje == self.angle_to_target:
                        self.turning = False
                else:
                    direction = diff / distance
                    move_amount = min(self.velocidad_avance, distance)
                    self.posicion += direction * move_amount
                
                    self.animation(1)
                    self.estado = "moving"
            else:  # Reached target
                self.posicion = self.target_pos.copy()
                self.moving_to_target = False
                self.reset()
                self.estado = "resting"

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
