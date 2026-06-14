# ==========================================================
# Funções Auxiliares
# ==========================================================
import hashlib
import uuid

# Gera um identificador único para cada imagem.
def generate_id():
    return str(uuid.uuid4())

# Gera um hash sha 256.
def sha256(e):
    sha = hashlib.sha256()
    sha.update(e)
    return sha.hexdigest()
