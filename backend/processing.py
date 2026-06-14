import numpy as np


# ==========================================================
# BRILHO
# ==========================================================
# Ajusta o brilho somando um valor constante a todos os pixels da imagem. Os valores são limitados ao intervalo [0,255].
def apply_brightness(matrix, delta):
    height, width = matrix.shape
    result = np.zeros(
        (height, width),
        dtype=np.uint8
    )
    for y in range(height):
        for x in range(width):
            value = int(matrix[y][x]) + delta
            if value < 0:
                value = 0
            if value > 255:
                value = 255
            result[y][x] = value
    return result


# ==========================================================
# LIMIARIZAÇÃO
# ==========================================================
# Converte a imagem em binária - Pixels acima do limiar recebem 255. Pixels abaixo recebem 0.
def apply_threshold(matrix, threshold):
    height, width = matrix.shape
    result = np.zeros(
        (height, width),
        dtype=np.uint8
    )
    for y in range(height):
        for x in range(width):
            if matrix[y][x] >= threshold:
                result[y][x] = 255
            else:
                result[y][x] = 0
    return result


# ==========================================================
# CONVOLUÇÃO - Para cada pixel, a máscara percorre a vizinhança e calcula uma soma ponderada.
# ==========================================================
def apply_convolution(matrix, kernel):
    height, width = matrix.shape
    k_size = kernel.shape[0]
    offset = k_size // 2
    result = np.zeros(
        (height, width),
        dtype=np.uint8
    )
    for y in range(offset, height - offset):
        for x in range(offset, width - offset):
            value = 0.0
            for ky in range(k_size):
                for kx in range(k_size):
                    pixel = matrix[
                        y + ky - offset
                        ][
                        x + kx - offset
                        ]
                    weight = kernel[ky][kx]
                    value += pixel * weight
            value = round(value)
            if value < 0:
                value = 0
            if value > 255:
                value = 255
            result[y][x] = value
    return result


# ==========================================================
# FILTRO DA MEDIANA - Os pixels vizinhos são coletados, ordenados e o valor central é escolhido.
# ==========================================================
def apply_median(matrix, size):
    height, width = matrix.shape
    offset = size // 2
    result = np.zeros(
        (height, width),
        dtype=np.uint8
    )
    for y in range(offset, height - offset):
        for x in range(offset, width - offset):
            neighbors = []
            for ky in range(-offset, offset + 1):
                for kx in range(-offset, offset + 1):
                    neighbors.append(
                        int(
                            matrix[y + ky][x + kx]
                        )
                    )
            neighbors.sort()
            median_value = neighbors[
                len(neighbors) // 2
                ]
            result[y][x] = median_value
    return result
