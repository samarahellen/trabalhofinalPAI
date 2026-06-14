import numpy as np

def make_element(shape: str, size: int) -> np.ndarray:
    if size % 2 == 0: raise ValueError("O tamanho do elemento deve ser impar")

    element = np.zeros((size, size), dtype=np.uint8)
    center = size // 2

    # Quadrado sólido
    if shape == "square":
        element[:, :] = 1

    # Cruz
    elif shape == "cross":
        element[center, :] = 1 # Barra horizontal
        element[:, center] = 1 # Barra vertical

    # Barra vertical
    elif shape == "vertical":
        element[:, center] = 1

    # Barra horizontal
    elif shape == "horizontal":
        element[center, :] = 1

    # Diagonal para baixo \
    elif shape == "diagonal_down":
        for k in range(size):
            element[k, k] = 1

    # Diagonal para cima /
    elif shape == "diagonal_up":
        for k in range(size):
            element[size - 1 - k, k] = 1

    # Formato de X
    elif shape == "x":
        for k in range(size):
            element[k, k] = 1
            element[size - 1 - k, k] = 1

    # Circulo sólido
    elif shape == "circle":
        element[:, :] = make_circle(size)[:, :]

    # Diamante
    elif shape == "diamond":
        for i in range(size):
            for j in range(size):
                # Distancia L1
                if abs(i - center) + abs(j - center) <= center:
                    element[i, j] = 1

    else:
        raise ValueError(f"Elemento estruturante desconhecido '{shape}'")

    return element

# Usar o algoritmo de Bresenham para o círculo
# Gerar círculos melhores para o elemento estruturante
def make_circle(size):
    if size % 2 == 0: raise ValueError("O tamanho do círculo deve ser impar")

    result = np.zeros((size, size), dtype=bool)

    # Raio do círculo
    r = (size - 1) // 2

    # --- Octante de Bresenham (x ≥ y ≥ 0, começando do topo do círculo) ---
    # Variável de decisão: err

    x, y = r, 0

    # Valor inicial para variante x=r, y=0
    # O algoritmo padrão usa 3 - 2 * r, mas -4 está sendo usado por gerar círculos de melhor circularidade aparente
    err = -4

    # Guardar valores lara a linha
    row_x = np.zeros(r + 1, dtype=int)

    while x >= y:
        row_x[y] = x              # octante: limite de x neste offset de y
        row_x[x] = y              # octante simétrico

        if err > 0:
            err += 4 * (y - x) + 10
            x -= 1
        else:
            err += 4 * y + 6
        y += 1

    # Preencher or circulo
    cx = cy = r
    col_idx = np.arange(size)

    for dy in range(r + 1):
        half_w = row_x[dy]
        mask = (col_idx >= cx - half_w) & (col_idx <= cx + half_w)
        result[cy - dy, :] = mask   # upper half (including centre row)
        result[cy + dy, :] = mask   # lower half

    return result
