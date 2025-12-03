import numpy as np
import requests
from OpenGL.GL import *
from objloader import OBJ

mat = [[1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1],
       [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1],
       [1, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 1],
       [1, 0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1, 1],
       [1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1],
       [1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 0, 0, 1],
       [1, 0, 1, 1, 1, 0, 0, 0, 1, 1, 0, 0, 1],
       [1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1],
       [1, 1, 0, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1],
       [1, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1],
       [1, 0, 1, 1, 1, 1, 0, 0, 0, 1, 1, 0, 1],
       [1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1],
       [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]]

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

CELL_SIZE = 50.0
GRID_CENTER_COL = 8  # 1-indexed column center of the maze
GRID_CENTER_ROW = 7  # 1-indexed row center of the maze
DEFAULT_BASE_URL = "http://localhost:8000"


class Mapa:
    def __init__(self, texture_wall=None, base_url=DEFAULT_BASE_URL):
        generador = OBJ("model/generador.obj", swapyz=True)

        self.generador = generador
        self.centro = (6, 7)
        self.num_generadores = 3
        self.posiciones = np.random.choice(
            len(genpos), self.num_generadores, replace=False)
        self.mat = np.array(mat)
        self.texture_wall = texture_wall
        self.base_url = base_url

        self.gens = []  # world-space generator positions for collision checks
        self.generator_state = []  # last known generator state from the server

        self._apply_local_generators()
        self.sync_generators_from_server()

    def grid_to_world(self, grid_x, grid_y):
        world_x = (grid_x - GRID_CENTER_COL) * CELL_SIZE
        world_z = (grid_y - GRID_CENTER_ROW) * CELL_SIZE
        return world_x, world_z

    def draw_cube(self, size=1.0):
        hs = size / 2.0
        glBegin(GL_QUADS)

        glTexCoord2f(0.0, 0.0)
        glVertex3f(-hs, -hs, hs)
        glTexCoord2f(1.0, 0.0)
        glVertex3f(hs, -hs, hs)
        glTexCoord2f(1.0, 1.0)
        glVertex3f(hs, hs, hs)
        glTexCoord2f(0.0, 1.0)
        glVertex3f(-hs, hs, hs)

        glTexCoord2f(0.0, 0.0)
        glVertex3f(-hs, -hs, -hs)
        glTexCoord2f(0.0, 1.0)
        glVertex3f(-hs, hs, -hs)
        glTexCoord2f(1.0, 1.0)
        glVertex3f(hs, hs, -hs)
        glTexCoord2f(1.0, 0.0)
        glVertex3f(hs, -hs, -hs)

        glTexCoord2f(0.0, 0.0)
        glVertex3f(-hs, -hs, -hs)
        glTexCoord2f(1.0, 0.0)
        glVertex3f(-hs, -hs, hs)
        glTexCoord2f(1.0, 1.0)
        glVertex3f(-hs, hs, hs)
        glTexCoord2f(0.0, 1.0)
        glVertex3f(-hs, hs, -hs)

        glTexCoord2f(0.0, 0.0)
        glVertex3f(hs, -hs, -hs)
        glTexCoord2f(0.0, 1.0)
        glVertex3f(hs, hs, -hs)
        glTexCoord2f(1.0, 1.0)
        glVertex3f(hs, hs, hs)
        glTexCoord2f(1.0, 0.0)
        glVertex3f(hs, -hs, hs)

        glTexCoord2f(0.0, 0.0)
        glVertex3f(-hs, hs, -hs)
        glTexCoord2f(0.0, 1.0)
        glVertex3f(-hs, hs, hs)
        glTexCoord2f(1.0, 1.0)
        glVertex3f(hs, hs, hs)
        glTexCoord2f(1.0, 0.0)
        glVertex3f(hs, hs, -hs)

        glTexCoord2f(0.0, 0.0)
        glVertex3f(-hs, -hs, -hs)
        glTexCoord2f(1.0, 0.0)
        glVertex3f(hs, -hs, -hs)
        glTexCoord2f(1.0, 1.0)
        glVertex3f(hs, -hs, hs)
        glTexCoord2f(0.0, 1.0)
        glVertex3f(-hs, -hs, hs)
        glEnd()

    def draw(self):
        if self.texture_wall:
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, self.texture_wall)
            glColor3f(1.0, 1.0, 1.0)
        else:
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

        if self.texture_wall:
            glDisable(GL_TEXTURE_2D)

        for idx, (gx, gz) in enumerate(self.gens):
            glPushMatrix()
            glTranslatef(gx, 0.0, gz)
            glScalef(5.0, 6.0, 5.0)
            glBindTexture(GL_TEXTURE_2D, 0)

            is_fixed = False
            if idx < len(self.generator_state):
                is_fixed = self.generator_state[idx].get("isFixed", False)

            if is_fixed:
                glColor3f(0.4, 0.9, 0.4)
            else:
                glColor3f(0.9, 0.45, 0.2)

            self.generador.render()
            glPopMatrix()

        glColor3f(1.0, 1.0, 1.0)

    def _apply_local_generators(self):
        self.gens[:] = []
        local_state = []
        for idx in self.posiciones:
            r, c = genpos[idx]
            x = (c - self.centro[1]) * CELL_SIZE
            z = (r - self.centro[0]) * CELL_SIZE
            self.gens.append([x, z])
            local_state.append({
                "id": None,
                "pos": [c + 1, r + 1],
                "isFixed": False,
                "timeToFix": 0
            })
        self.generator_state = local_state

    def _apply_server_generators(self, generators):
        ordered_generators = sorted(
            (gen for gen in generators if gen.get("pos")),
            key=lambda gen: gen.get("id", 0)
        )

        new_positions = []
        for generator in ordered_generators:
            pos = generator.get("pos", [])
            if len(pos) != 2:
                continue
            world_x, world_z = self.grid_to_world(pos[0], pos[1])
            new_positions.append([world_x, world_z])

        if new_positions:
            self.gens[:] = new_positions
            self.generator_state = [{
                "id": gen.get("id"),
                "pos": list(gen.get("pos", [])),
                "isFixed": gen.get("isFixed", False),
                "timeToFix": gen.get("timeToFix", 0)
            } for gen in ordered_generators]

    def update_generators_from_state(self, state):
        if not state:
            return False
        generators = state.get("generators", [])
        if not generators:
            return False
        self._apply_server_generators(generators)
        return True

    def sync_generators_from_server(self):
        try:
            response = requests.get(f"{self.base_url}/state", timeout=0.2)
            if response.status_code == 200:
                state = response.json()
                return self.update_generators_from_state(state)
        except requests.RequestException:
            pass
        return False
