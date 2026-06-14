import numpy as np

# ==========================================================
# MÁSCARAS DE CONVOLUÇÃO
# ==========================================================
# Retorna a máscara selecionada pelo usuário.
def get_kernel(preset: str) -> np.ndarray:
    if preset == "mean":
        return np.ones((3, 3), dtype=float) / 9.0

    elif preset == "laplacian":
        return np.array([
            [0, -1, 0],
            [-1, 4, -1],
            [0, -1, 0]
        ], dtype=float)

    elif preset == "sharpen":
        return np.array([
            [0, -1, 0],
            [-1, 5, -1],
            [0, -1, 0]
        ], dtype=float)

    elif preset == "sobel_x":
        return np.array([
            [-1, 0, 1],
            [-2, 0, 2],
            [-1, 0, 1]
        ], dtype=float)

    elif preset == "sobel_y":
        return np.array([
            [-1, -2, -1],
            [0, 0, 0],
            [1, 2, 1]
        ], dtype=float)

    elif preset == "custom": # Máscara padrão
        return np.array([
            [0, -1, 0],
            [-1, 5, -1],
            [0, -1, 0]
        ], dtype=float)

    # fallback
    return np.ones((3, 3), dtype=float) / 9.0
