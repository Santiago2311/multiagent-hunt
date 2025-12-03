import numpy as np
import math
import requests
from objloader import OBJ 
from OpenGL.GL import *
from OpenGL.GLU import *

class Personaje:
    def __init__(self, mapa):
        obj_personaje = OBJ("model/personaje.obj", swapyz=False)
        obj_brazo = OBJ("model/brazo.obj", swapyz=False)
        obj_pierna = OBJ("model/pierna.obj", swapyz=True)
        self.torso = obj_personaje
        self.brazo = obj_brazo
        self.pierna = obj_pierna
        
        self.map_obj = mapa
        self.mapa = mapa.mat
        self.bound_radio = 10
        
        self.posicion = np.array([0.0, 15.0, 0.0])  
        self.angulo_personaje = 0.0  
        
        self.velocidad_avance = 3.0
        self.giro_brazo_izq = 0.0
        self.velocidad_giro = 5.0
        self.giro_brazo_der = 0.0
        
        self.estado = "REPOSO"  
        
        self.offset_brazo_izq = np.array([5.5, 5.4, 0.0])  # Derecha, adelante
        self.offset_brazo_der = np.array([-5.5, 5.4, 0.0])  # Izquierda, adelante
        self.offset_pierna_izq = np.array([2.0, -7.0, 0.0])  # Centro, atrás
        self.offset_pierna_der = np.array([-2.0, -7.0, 0.0])
        
        self.escala = 10.0
        self.animacion = False
        self.animacionrepair = False

        self.base_url = "http://localhost:8000"
        self.last_sent_grid_pos = None
        self.caught = False
        self.has_escaped = False
        self.frame_count = 0
        self.generator_cache = []
        self.fix_input_active = False
        self.last_fix_frame = 0
        self.fix_cooldown_frames = 15
        self.is_fixing = False

    def world_to_grid(self, world_x, world_z):
        center_col = 8
        center_row = 7
        cell_size = 50.0
        
        grid_x = int(round(world_x / cell_size)) + center_col
        grid_y = int(round(world_z / cell_size)) + center_row
        
        return grid_x, grid_y
    
    def grid_to_world(self, grid_x, grid_y):
        center_col = 8
        center_row = 7
        cell_size = 50.0
        
        world_x = (grid_x - center_col) * cell_size
        world_z = (grid_y - center_row) * cell_size
        
        return world_x, world_z

    def set_fixing_input(self, is_pressed):
        self.fix_input_active = is_pressed

    def update_generator_cache(self, state):
        if not state:
            return
        generators = state.get("generators", [])
        if generators:
            self.generator_cache = sorted(
                generators,
                key=lambda gen: gen.get("id", 0)
            )
        
    def send_position_to_server(self):
        grid_x, grid_y = self.world_to_grid(self.posicion[0], self.posicion[2])
        
        if self.last_sent_grid_pos != (grid_x, grid_y):
            try:
                response = requests.post(
                    f"{self.base_url}/human/position",
                    json={"x": grid_x, "y": grid_y},
                    timeout=0.1
                )
                if response.status_code == 200:
                    self.last_sent_grid_pos = (grid_x, grid_y)
            except:
                pass
    
    def check_server_position(self):
        try:
            response = requests.get(
                f"{self.base_url}/human/position",
                timeout=0.1
            )
            if response.status_code == 200:
                data = response.json()
                server_grid_pos = tuple(data.get("pos", []))
                current_grid_pos = self.world_to_grid(self.posicion[0], self.posicion[2])
                
                if server_grid_pos and server_grid_pos != current_grid_pos:
                    world_x, world_z = self.grid_to_world(server_grid_pos[0], server_grid_pos[1])
                    self.posicion = np.array([world_x, 15.0, world_z])
                    self.caught = True
                    self.last_sent_grid_pos = server_grid_pos
                    print("Player was caught! Respawning at safe zone.")
                    return True
        except:
            pass
        return False
    
    def check_door_escape(self):
        try:
            response = requests.get(f"{self.base_url}/state", timeout=0.1)
            if response.status_code == 200:
                state = response.json()
                doors = state.get("doors", [])
                generators = state.get("generators", [])
                
                all_fixed = all(gen.get("isFixed", False) for gen in generators)
                
                if all_fixed:
                    grid_x, grid_y = self.world_to_grid(self.posicion[0], self.posicion[2])
                    
                    for door in doors:
                        door_pos = door.get("pos", [])
                        if door_pos and door_pos[0] == grid_x and door_pos[1] == grid_y:
                            if door.get("isOpen", False):
                                self.has_escaped = True
                                print("YOU ESCAPED! YOU WIN!")
                                return True
        except:
            pass
        return False
        
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

    def animation(self, factor):
        if self.giro_brazo_izq >= 50 or self.giro_brazo_der >= 50:
            self.animacion = not self.animacion
        if self.animacion:
            self.giro_brazo_izq += self.velocidad_giro*factor
            self.giro_brazo_der -= self.velocidad_giro*factor
        else:
            self.giro_brazo_der += self.velocidad_giro*factor
            self.giro_brazo_izq -= self.velocidad_giro*factor

    def repairing(self):
        if self.giro_brazo_izq:
            None
            
    def generator_close(self, nueva_pos):
        celda_size = 50.0
        cx, cz = nueva_pos[0], nueva_pos[2]
        
        rad = self.bound_radio
        ang_rad = math.radians(self.angulo_personaje)
        c = math.cos(ang_rad)
        s = math.sin(ang_rad)
        
        diag_rad = rad * 0.7
        
        gen_size = 50.0
        
        for gx, gz in self.map_obj.gens:
            if abs(cx - gx) < (gen_size/2 + rad) and abs(cz - gz) < (gen_size/2 + rad):
                return True

        return False

    def get_nearby_generator(self, max_distance=60.0):
        if not self.generator_cache or not self.map_obj.gens:
            return None

        px, pz = self.posicion[0], self.posicion[2]
        for generator, (gx, gz) in zip(self.generator_cache, self.map_obj.gens):
            if generator.get("isFixed"):
                continue
            dist = math.sqrt((px - gx) ** 2 + (pz - gz) ** 2)
            if dist <= max_distance:
                return generator
        return None

    def send_fix_request(self, generator_id):
        if generator_id is None:
            return False
        try:
            response = requests.post(
                f"{self.base_url}/human/fix",
                json={"generatorId": generator_id},
                timeout=0.2
            )
            if response.status_code == 200:
                data = response.json()
                updated_state = data.get("state")
                if updated_state:
                    self.update_generator_cache(updated_state)
                    self.map_obj.update_generators_from_state(updated_state)
                return True
            else:
                try:
                    error_payload = response.json()
                    error_msg = error_payload.get("error")
                    if error_msg:
                        print(f"Unable to fix generator: {error_msg}")
                except:
                    pass
        except Exception as exc:
            print(f"Failed to reach generator endpoint: {exc}")
        return False

    def process_fixing(self):
        if not self.fix_input_active:
            self.is_fixing = False
            return

        generator = self.get_nearby_generator()
        if not generator:
            self.is_fixing = False
            return

        if self.frame_count - self.last_fix_frame < self.fix_cooldown_frames:
            return

        if self.send_fix_request(generator.get("id")):
            self.last_fix_frame = self.frame_count
            self.is_fixing = True
    
    def can_move(self, nueva_pos):
        celda_size = 50.0
        cx, cz = nueva_pos[0], nueva_pos[2]

        def check_collision_at_point(x, z):
            celda_x = int(round(x / celda_size)) + 7 
            celda_z = int(round(z / celda_size)) + 6
            if celda_z < 0 or celda_z >= self.mapa.shape[0]:
                return True
            if celda_x < 0 or celda_x >= self.mapa.shape[1]:
                return True

            if self.mapa[celda_z][celda_x] == 1:
                return True
            
            return False
        
        rad = self.bound_radio
        ang_rad = math.radians(self.angulo_personaje)
        c = math.cos(ang_rad)
        s = math.sin(ang_rad)
        
        diag_rad = rad * 0.7
        
        offsets_locales = [
            [0, rad],
            [0, -rad],
            [-rad, 0],
            [rad, 0],
            [-diag_rad, diag_rad],
            [diag_rad, diag_rad],
            [-diag_rad, -diag_rad],
            [diag_rad, -diag_rad]
        ]
        
        for ox_local, oz_local in offsets_locales:
            x_offset_mundo = (ox_local * c) + (oz_local * s)
            z_offset_mundo = (-ox_local * s) + (oz_local * c)

            px = cx + x_offset_mundo
            pz = cz + z_offset_mundo
            
            if check_collision_at_point(px, pz):
                return False
        
        if self.generator_close(nueva_pos):
            return False

        return True
    
    def update(self):
        if self.has_escaped:
            return

        self.frame_count += 1
            
        self.check_server_position()
        self.check_door_escape()
        
        if self.estado == "AVANZAR":
            rad = math.radians(self.angulo_personaje)
            nueva_pos = self.posicion + np.array([self.velocidad_avance * math.sin(rad), 0, self.velocidad_avance * math.cos(rad)])
            if self.can_move(nueva_pos):
                self.posicion = nueva_pos
                self.send_position_to_server()
            self.animation(1)
            
        elif self.estado == "RETROCEDER":
            rad = math.radians(self.angulo_personaje)
            nueva_pos = self.posicion + np.array([-self.velocidad_avance/2 * math.sin(rad), 0, -self.velocidad_avance/2 * math.cos(rad)])
            if self.can_move(nueva_pos):
                self.posicion = nueva_pos
                self.send_position_to_server()
            self.animation(0.5)
            
        elif self.estado == "AVANZAR_GIRAR_IZQ":
            self.angulo_personaje += self.velocidad_giro
            rad = math.radians(self.angulo_personaje)
            nueva_pos = self.posicion + np.array([self.velocidad_avance * math.sin(rad), 0, self.velocidad_avance * math.cos(rad)])
            if self.can_move(nueva_pos):
                self.posicion = nueva_pos
                self.send_position_to_server()
            self.animation(1) 

        elif self.estado == "AVANZAR_GIRAR_DER":
            self.angulo_personaje -= self.velocidad_giro
            rad = math.radians(self.angulo_personaje)
            nueva_pos = self.posicion + np.array([self.velocidad_avance * math.sin(rad), 0, self.velocidad_avance * math.cos(rad)])
            if self.can_move(nueva_pos):
                self.posicion = nueva_pos
                self.send_position_to_server()
            self.animation(1)
            
        elif self.estado == "RETROCEDER_GIRAR_DER":
            self.angulo_personaje -= self.velocidad_giro
            rad = math.radians(self.angulo_personaje)
            nueva_pos = self.posicion + np.array([-self.velocidad_avance/2 * math.sin(rad), 0, -self.velocidad_avance/2 * math.cos(rad)])
            if self.can_move(nueva_pos):
                self.posicion = nueva_pos
                self.send_position_to_server()
            self.animation(0.5)
            
        elif self.estado == "RETROCEDER_GIRAR_IZQ":
            self.angulo_personaje += self.velocidad_giro
            rad = math.radians(self.angulo_personaje)
            nueva_pos = self.posicion + np.array([-self.velocidad_avance/2 * math.sin(rad), 0, -self.velocidad_avance/2 * math.cos(rad)])
            if self.can_move(nueva_pos):
                self.posicion = nueva_pos
                self.send_position_to_server()
            self.animation(0.5)
            
        elif self.estado == "GIRAR_IZQ_ESTATICO":
            self.angulo_personaje += self.velocidad_giro
            self.reset()
            
        elif self.estado == "GIRAR_DER_ESTATICO":
            self.angulo_personaje -= self.velocidad_giro
            self.reset()
            
        elif self.estado == "REPOSO":
            self.reset()

        self.process_fixing()

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
