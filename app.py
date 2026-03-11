import os
import time
import re
from flask import Flask, render_template, request, send_file, jsonify
from crypt_engine import CryptoEngine
from stego_engine import StegoEngine
from cryptography.hazmat.primitives import serialization
from werkzeug.utils import secure_filename

app = Flask(__name__)

# --- CONFIGURAÇÕES ---
app.config['MAX_CONTENT_LENGTH'] = 600 * 1024 * 1024 
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

engine = CryptoEngine()
stego_engine = StegoEngine()

# --- UTILITÁRIOS ---

def strip_pem(pem_string):
    return re.sub(r'-----.*?-----|\s+', '', pem_string)

def wrap_pem(clean_text, is_private=True):
    tag = "PRIVATE KEY" if is_private else "PUBLIC KEY"
    return f"-----BEGIN {tag}-----\n{clean_text}\n-----END {tag}-----"

# --- ROTAS ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_keys', methods=['GET'])
def generate_keys():
    try:
        priv, pub = engine.generate_rsa_keys()
        priv_pem, pub_pem = engine.export_keys_to_strings(priv, pub)
        return jsonify({
            'status': 'success',
            'private_key': strip_pem(priv_pem.decode('utf-8')),
            'public_key': strip_pem(pub_pem.decode('utf-8'))
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/crypt_action', methods=['POST'])
def crypt_action():
    action = request.form.get('action') 
    method = request.form.get('method')
    file = request.files.get('file')
    
    if not file or file.filename == '':
        return jsonify({'status': 'error', 'message': 'Selecione um arquivo'}), 400

    # 1. Sanitiza o nome original
    raw_filename = secure_filename(file.filename)
    input_path = os.path.join(UPLOAD_FOLDER, raw_filename)
    file.save(input_path)
    
    # 2. LÓGICA DE PREFIXO (CORRIGIDA)
    # Removemos qualquer ".enc" existente no nome para evitar "enc_arquivo.txt.enc"
    base_name = raw_filename.replace('.enc', '')
    
    if action == 'encrypt':
        output_name = f"enc_{base_name}"
    else:
        # Se for decriptar, remove o prefixo 'enc_' se ele existir
        if base_name.startswith('enc_'):
            output_name = f"dec_{base_name[4:]}"
        else:
            output_name = f"dec_{base_name}"

    output_path = os.path.join(UPLOAD_FOLDER, output_name)

    try:
        duration = 0
        if method == 'symmetric':
            password = request.form.get('password')
            if not password:
                return jsonify({'status': 'error', 'message': 'Senha não fornecida'}), 400
            
            if action == 'encrypt':
                duration = engine.encrypt_symmetric(input_path, output_path, password)
            else:
                duration = engine.decrypt_symmetric(input_path, output_path, password)
        
        else:
            key_text = request.form.get('key_text', '').strip()
            if not key_text:
                return jsonify({'status': 'error', 'message': 'Chave PEM ausente'}), 400
            
            if action == 'encrypt':
                try:
                    pem = wrap_pem(key_text, is_private=False)
                    key_obj = serialization.load_pem_public_key(pem.encode())
                except:
                    pem = wrap_pem(key_text, is_private=True)
                    key_obj = serialization.load_pem_private_key(pem.encode(), password=None).public_key()
                
                duration = engine.encrypt_asymmetric(input_path, output_path, key_obj)
            else:
                pem = wrap_pem(key_text, is_private=True)
                key_obj = engine.load_private_key(pem.encode())
                duration = engine.decrypt_asymmetric(input_path, output_path, key_obj)

        return jsonify({
            'status': 'success',
            'time': f"{duration:.4f}s",
            'download_url': f"/download/{output_name}"
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/steganography', methods=['POST'])
def steganography():
    action = request.form.get('action')
    image_file = request.files.get('image')
    
    if not image_file:
        return jsonify({'status': 'error', 'message': 'Imagem não selecionada'}), 400

    img_name = secure_filename(image_file.filename)
    img_path = os.path.join(UPLOAD_FOLDER, img_name)
    image_file.save(img_path)

    try:
        if action == 'hide':
            secret_file = request.files.get('file_to_hide')
            secret_name = secure_filename(secret_file.filename)
            hide_path = os.path.join(UPLOAD_FOLDER, secret_name)
            secret_file.save(hide_path)
            
            output_name = f"stego_{os.path.splitext(img_name)[0]}.png"
            output_path = os.path.join(UPLOAD_FOLDER, output_name)

            start = time.perf_counter()
            stego_engine.hide_data(img_path, hide_path, output_path)
            duration = time.perf_counter() - start
        else:
            output_name = "revelado_resultado.bin"
            output_path = os.path.join(UPLOAD_FOLDER, output_name)
            
            start = time.perf_counter()
            stego_engine.reveal_data(img_path, output_path)
            duration = time.perf_counter() - start
        
        return jsonify({
            'status': 'success',
            'time': f"{duration:.4f}s",
            'download_url': f"/download/{output_name}"
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/download/<filename>')
def download(filename):
    # Garante que o download use o nome exato gerado
    return send_file(os.path.join(UPLOAD_FOLDER, filename), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)