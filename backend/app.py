from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image

import os
import io
import uuid
import base64
import numpy as np

app = Flask(__name__)
CORS(app)

# ==========================================================
# Configurações
# ==========================================================

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True) # Cria a pasta automaticamente caso não exista
FILES = {} # Guarda o caminho físico associado a cada ID gerado

# ==========================================================
# Funções Auxiliares
# ==========================================================

# Gera um identificador único para cada imagem.
def generate_id(): 
    return str(uuid.uuid4())

# Retorna o caminho da imagem associada ao ID.
def get_file_path(file_id):
    return FILES.get(file_id)

# Salva uma matriz de pixels em formato PGM.
def save_matrix_as_pgm(matrix, path):
    img = Image.fromarray(
        matrix.astype(np.uint8),
        mode='L'
    )
    img.save(path)

# Carrega uma imagem PGM e converte para matriz.
def load_pgm_as_matrix(path):
    img = Image.open(path)
    img = img.convert("L")  # garante escala de cinza
    return np.array(img, dtype=np.uint8)

# Converte uma matriz para PNG em Base64 - O frontend usa esse Base64 para exibir a miniatura da imagem.
def matrix_to_preview(matrix):
    img = Image.fromarray(
        matrix.astype(np.uint8),
        mode='L'
    )
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(
        buffer.getvalue()
    ).decode("utf-8")

# Salva uma imagem processada e registra seu ID -  Retorna: output_id e caminho
def save_processed_image(matrix):
    output_id = generate_id()
    filename = f"{output_id}.pgm"
    path = os.path.join(
        UPLOAD_FOLDER,
        filename
    )
    save_matrix_as_pgm(matrix, path)
    FILES[output_id] = path
    return output_id, path

# Retorna largura e altura da matriz, necessários para algumas das operações.
def get_image_info(matrix):
    height, width = matrix.shape
    return width, height


# ==========================================================
# CARREGAR PGM - UPLOAD
# ==========================================================

@app.route('/api/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({
            'error': 'Nenhum arquivo enviado'
        }), 400
    file = request.files['file']
    if not file.filename.lower().endswith('.pgm'): # Aceita apenas PGM
        return jsonify({
            'error': 'Apenas arquivos .pgm são permitidos'
        }), 400
    file_id = generate_id()
    filename = f"{file_id}.pgm"
    path = os.path.join(
        UPLOAD_FOLDER,
        filename
    )
    file.save(path)
    FILES[file_id] = path
    try:
        matrix = load_pgm_as_matrix(path)
        width, height = get_image_info(matrix)
        preview = matrix_to_preview(matrix)
        return jsonify({
            'file_id': file_id,
            'filename': filename,
            'width': width,
            'height': height,
            'preview': preview
        })
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

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

#     Converte a imagem em binária - Pixels acima do limiar recebem 255; Pixels abaixo recebem 0.
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
# MÁSCARAS DE CONVOLUÇÃO
# ==========================================================

# Retorna a máscara selecionada pelo usuário.
def get_kernel(preset):
    if preset == "mean":
        return np.array([
            [1, 1, 1],
            [1, 1, 1],
            [1, 1, 1]
        ], dtype=float) / 9.0

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
    return np.array([
        [1,1,1],
        [1,1,1],
        [1,1,1]
    ], dtype=float) / 9.0

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
# FILTRO DA MEDIANA - Os pixels vizinhos são coletados,ordenados e o valor central é escolhido.
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
# PROCESSAMENTO DOS BLOCOS
# ==========================================================

# Recebimento e validação da imagem de entrada - Procura o arquivo da imagem, verifica se a imagem existe e carrega a imagem PGM como matriz para processamento posterior.
@app.route('/api/process', methods=['POST'])
def process_image():
    try:
        data = request.get_json()
        block = data.get('block')
        input_id = data.get('input_id')
        params = data.get('params', {})
        if not input_id:
            return jsonify({
                'error': 'Imagem de entrada não informada'
            }), 400
        path = get_file_path(input_id)
        if not path:
            return jsonify({
                'error': 'Imagem não encontrada'
            }), 404
        matrix = load_pgm_as_matrix(path)

        # BRILHO
        if block == "brightness":
            delta = int(
                params.get('delta', 30)
            )
            result = apply_brightness(
                matrix,
                delta
            )

        # LIMIARIZAÇÃO
        elif block == "threshold":
            threshold = int(
                params.get('threshold', 128)
            )
            result = apply_threshold(
                matrix,
                threshold
            )

        # CONVOLUÇÃO
        elif block == "convolution":

            preset = params.get(
                'preset',
                'mean'
            )

            kernel = get_kernel(
                preset
            )

            result = apply_convolution(
                matrix,
                kernel
            )

        # MEDIANA
        elif block == "median":
            size = int(
                params.get('size', 3)
            )
            if size % 2 == 0: # Garante tamanho ímpar para a máscara
                size += 1
            result = apply_median(
                matrix,
                size
            )

        # COMPLEMENTO
        elif block == "complement":

            result = apply_complement(
                matrix
            )

        # HISTOGRAMA
        elif block == "histogram":

            histogram = calculate_histogram(
                matrix
            )

            return jsonify({
                'histogram': histogram
            })

        else:
            return jsonify({
                'error': f'Bloco "{block}" não implementado'
            }), 400

        # SALVAR PGM
        output_id, _ = save_processed_image(
            result
        )
        preview = matrix_to_preview(
            result
        )
        width, height = get_image_info(
            result
        )
        return jsonify({
            'output_id': output_id,
            'width': width,
            'height': height,
            'preview': preview
        })
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

# DOWNLOAD
@app.route('/api/download/<file_id>')
def download(file_id):
    path = get_file_path(file_id)
    if not path:
        return jsonify({
            'error': 'Arquivo não encontrado'
        }), 404
    return send_file(
        path,
        as_attachment=True,
        download_name=f'{file_id}.pgm',
        mimetype='image/x-portable-graymap'
    )

# INICIALIZAÇÃO
if __name__ == '__main__':
    print()
    print('=' * 50)
    print('PSE-Image Backend')
    print('Servidor iniciado em:')
    print('http://127.0.0.1:5000')
    print('=' * 50)
    print()
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
