# Bibliotecas para o WEB e abrir o arquivo de imagem
from pathlib import Path
from traceback import print_exception

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image

# Funções internas
from processing import *
from extras import *
from kernels import *

import os
import io
import base64
import util
import hashlib

app = Flask(__name__)
CORS(app)

# ==========================================================
# Configurações
# ==========================================================

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True) # Cria a pasta automaticamente caso não exista
FILES = {} # Guarda o caminho físico associado a cada ID gerado

# Retorna o caminho da imagem associada ao ID.
def get_file_path(file_id):
    path = FILES.get(file_id)
    # Procurar arquivo na pasta, para evitar ter que refazer uploads durante testes
    if not path:
        store_path = os.path.join(UPLOAD_FOLDER, f"{file_id}.pgm", )
        if Path(store_path).exists(): path = store_path

    return path

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
    # Usar hash para evitar criar muitos arquivos repetidos durante testes
    output_id = util.sha256(matrix) #util.generate_id()
    filename = f"{output_id}.pgm"
    path = os.path.join(
        UPLOAD_FOLDER,
        filename
    )
    save_matrix_as_pgm(matrix, path)
    FILES[output_id] = path
    return output_id, path

def save_image(matrix, filename):
    path = os.path.join(UPLOAD_FOLDER, filename)
    save_matrix_as_pgm(matrix, path)
    return path

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

    # Usar hash para evitar criar muitos arquivos repetidos durante testes
    file_id = util.sha256(file.stream.read())
    file.stream.seek(0)
    # file_id = util.generate_id()

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
# PROCESSAMENTO DOS BLOCOS
# ==========================================================

# Recebimento e validação da imagem de entrada - Procura o arquivo da imagem, verifica se a imagem existe e carrega a imagem PGM como matriz para processamento posterior.
@app.route('/api/process', methods=['POST'])
def process_image():
    try:
        data: dict = request.get_json()
        block: str = data.get('block')
        params: dict = data.get('params', {})

        input_id: str = data.get('input_id')
        if not input_id:
            return jsonify({ 'error': 'Imagem de entrada não informada' }), 400

        path: str = get_file_path(input_id)
        if not path:
            return jsonify({ 'error': 'Imagem não encontrada' }), 404

        matrix = load_pgm_as_matrix(path)

        # BRILHO
        if block == "brightness":
            delta: int = params.get('delta', 30)
            result = apply_brightness(matrix, delta)

        # LIMIARIZAÇÃO
        elif block == "threshold":
            threshold: int = params.get('threshold', 128)
            result = apply_threshold(matrix, threshold)

        # CONVOLUÇÃO
        elif block == "convolution":
            preset: str = params.get('preset', 'mean')
            kernel = get_kernel(preset)
            result = apply_convolution(matrix, kernel)

        # MEDIANA
        elif block == "median":
            size: int = params.get('size', 3)
            if size % 2 == 0: size += 1 # Garante tamanho ímpar para a máscara

            result = apply_median(matrix, size)

        # COMPLEMENTO
        elif block == "complement":
            result = apply_complement(matrix)

        # HISTOGRAMA
        elif block == "histogram":
            histogram = calculate_histogram(matrix)
            return jsonify({ 'histogram': histogram })

        # MORFOLOGIA
        elif block == "morphology":
            operation: str = params.get('op', 'erosion')
            size: int = params.get('size', 3)
            elem: str = params.get('elem', 'square')
            # save_image(make_element(elem, size) * 255, f"elems/{elem}_{size}.pgm")

            result = apply_morphology(matrix, operation, elem, 3)

        # COMPLEMENTO
        elif block == "difference":
            input_b_id: str = params.get('input_b_id')
            if not input_b_id:
                return jsonify({ 'error': 'Imagem da entrada B não informada' }), 400

            path_b: str = get_file_path(input_b_id)
            if not path_b:
                return jsonify({ 'error': 'Imagem B não encontrada' }), 404

            matrix_b = load_pgm_as_matrix(path_b)

            if matrix.shape != matrix_b.shape:
                return jsonify({ 'error': 'As imagens não possuem as mesmas dimensões' }), 400

            result = apply_difference(matrix, matrix_b)

        else:
            return jsonify({ 'error': f'Bloco "{block}" não implementado' }), 400

        # SALVAR PGM
        output_id, _ = save_processed_image(result)
        preview = matrix_to_preview(result)
        width, height = get_image_info(result)

        return jsonify({
            'output_id': output_id,
            'width': width,
            'height': height,
            'preview': preview
        })
    except Exception as e:
        print_exception(e)
        return jsonify({ 'error': str(e) }), 500


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
