from typing import Callable

import numpy as np

def apply_erosion(matrix, elem):
    return _apply(matrix, elem, 255, min)

def apply_dilation(matrix, elem):
    return _apply(matrix, elem, 0, max)


def apply_opening(matrix, elem):
    return apply_erosion(apply_dilation(matrix, elem), elem)


def apply_closing(matrix, elem):
    return apply_dilation(apply_erosion(matrix, elem), elem)


# Uma função de morfologia com as partes que diferem abstraídas
# O teste de qual o valor entre os pixels no elemento que devem permanecer (maior ou menor valor) é definido pela variável "test"
# init_val é o valor inicial para o teste, 255 para min, 0 para max
def _apply(matrix: np.ndarray, elem: np.ndarray, init_val: int, test: Callable[[int, int], int]):
    height, width = matrix.shape
    elem_h, elem_w = elem.shape

    # Achar o pondo de âncora do elemento estruturante
    anchor_y, anchor_x = elem_h // 2, elem_w // 2

    # Criar imagem final com zeros em todos os pixels
    result = np.zeros((height, width), dtype=np.uint8)

    # Calcular o valor limite para sair do loop mais cedo quando possível
    limit = 255 - init_val

    for y in range(height):
        for x in range(width):
            current_val = init_val

            for elem_y in range(elem_h):
                for elem_x in range(elem_w):
                    # Não realizar operação em pontos do elemento que possuem o valor 0
                    if elem[elem_y, elem_x] == 0: continue

                    pixel_y = y + (elem_y - anchor_y)
                    pixel_x = x + (elem_x - anchor_x)

                    if pixel_y < 0 or pixel_y >= height or pixel_x < 0 or pixel_x >= width:
                        pixel_val = 0  # Pixel fora da imagem, tratar como padding de 0
                    else:
                        # Ler o valor do pixel
                        pixel_val = matrix[pixel_y, pixel_x]

                    # Comparar o valor do pixel com o atual, escolhendo o maior ou menor, dependendo da operação
                    current_val = test(pixel_val, current_val)

                    # Terminar teste do pixel mais cedo se der o valor limite
                    if current_val == limit: break
                if current_val == limit: break

            # Salvar valor na imagem final
            result[y, x] = current_val

    return result
