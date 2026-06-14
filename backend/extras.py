import numpy as np

from morphology import *
from structural_elements import make_element


# ==========================================================
# COMPLEMENTO DA IMAGEM
# ==========================================================
def apply_complement(matrix):
    height, width = matrix.shape

    result = np.zeros(
        (height, width),
        dtype=np.uint8
    )

    for y in range(height):
        for x in range(width):
            result[y][x] = 255 - int(matrix[y][x])

    return result


# ==========================================================
# HISTOGRAMA
# ==========================================================
def calculate_histogram(matrix):

    histogram = []

    # cria 256 posições manualmente
    for i in range(256):
        histogram.append(0)

    height, width = matrix.shape

    for y in range(height):
        for x in range(width):

            pixel = int(
                matrix[y][x]
            )

            histogram[pixel] += 1

    return histogram


# ==========================================================
# MORFOLOGIA
# ==========================================================
def apply_morphology(matrix, op: str, elem: str, size: int):
    element = make_element(elem, size)

    if op == "erosion":
        result = apply_erosion(matrix, element)

    elif op == "dilation":
        result = apply_dilation(matrix, element)

    elif op == "opening":
        result = apply_opening(matrix, element)

    elif op == "closing":
        result = apply_closing(matrix, element)

    else:
        raise ValueError(f'Operação "{op}" desconhecida')

    return result


# ==========================================================
# DIFERENÇA
# ==========================================================
def apply_difference(matrix_a, matrix_b):
    height, width = matrix_a.shape

    result = np.zeros(matrix_a.shape, dtype=np.uint8)
    for y in range(height):
        for x in range(width):
            pixel_a = matrix_a[y, x]
            pixel_b = matrix_b[y, x]
            pixel_max = max(pixel_a, pixel_b)
            pixel_min = min(pixel_a, pixel_b)
            diff = pixel_max - pixel_min
            if diff > pixel_max:
                raise ValueError(f"Integer overflow x={x}, y={y}, a={pixel_a}, b={pixel_b}, max={pixel_max}, min={pixel_min}")

            result[y, x] = diff

    return result
