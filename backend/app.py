from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid

app = Flask(__name__)
CORS(app)

# Pasta onde os arquivos enviados serão armazenados
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Recebe um arquivo do frontend e salva no servidor
@app.route('/api/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    file = request.files['file']

    # Gera um ID único para evitar conflitos de nomes
    fid = str(uuid.uuid4())
    extension = os.path.splitext(file.filename)[1]
    filename = fid + extension
    path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(path)

    # Retorna os dados necessários para o frontend identificar o arquivo
    return jsonify({
        'file_id': fid,
        'filename': filename
    })

# Inicia a API Flask em modo de desenvolvimento
if __name__ == '__main__':
    app.run(debug=True)
