from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/api/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400

    file = request.files['file']

    fid = str(uuid.uuid4())
    extension = os.path.splitext(file.filename)[1]

    filename = fid + extension
    path = os.path.join(UPLOAD_FOLDER, filename)

    file.save(path)

    return jsonify({
        'file_id': fid,
        'filename': filename
    })

if __name__ == '__main__':
    app.run(debug=True)