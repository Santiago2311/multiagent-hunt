import sympy as sp

tx, ty, tz = sp.symbols('tx ty tz')
ox, oy, oz = sp.symbols('ox oy oz')  # offset
a, b, c = sp.symbols('a b c')
e = sp.symbols('e')  # escala

T_pos = sp.Matrix([
    [1, 0, 0, tx],
    [0, 1, 0, ty],
    [0, 0, 1, tz],
    [0, 0, 0, 1]
])

T_offset = sp.Matrix([
    [1, 0, 0, ox],
    [0, 1, 0, oy],
    [0, 0, 1, oz],
    [0, 0, 0, 1]
])

R_x_a = sp.Matrix([
    [1, 0, 0, 0],
    [0, sp.cos(a), -sp.sin(a), 0],
    [0, sp.sin(a), sp.cos(a), 0],
    [0, 0, 0, 1]
])

R_x_b = sp.Matrix([
    [1, 0, 0, 0],
    [0, sp.cos(b), -sp.sin(b), 0],
    [0, sp.sin(b), sp.cos(b), 0],
    [0, 0, 0, 1]
])

R_y = sp.Matrix([
    [sp.cos(c), 0, sp.sin(c), 0],
    [0, 1, 0, 0],
    [-sp.sin(c), 0, sp.cos(c), 0],
    [0, 0, 0, 1]
])

E_s = sp.Matrix([
    [e, 0, 0, 0],
    [0, e, 0, 0],
    [0, 0, e, 0],
    [0, 0, 0, 1]
])

M = T_pos * R_y * T_offset * R_x_a * E_s

def print_matrix_sym(M):
    rows = []
    for row in M.tolist():
        row_str = ", ".join([str(x) for x in row])
        rows.append(f"[{row_str}]")
    print(",\n".join(rows))

print_matrix_sym(M)

