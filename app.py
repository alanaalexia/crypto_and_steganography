import os
import time
import re
from flask import Flask, render_template, request, send_file, jsonify
from crypt_engine import CryptoEngine
from stego_engine import StegoEngine
from cryptography.hazmat.primitives import serialization

app = Flask(__name__)

# Configurações de Upload
# Aumentamos o limite para 600MB para garantir que o teste de 500MB passe sem erro
app.config['MAX_CONTENT_LENGTH'] = 600 * 1024 * 1024 
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Instância dos motores
engine = CryptoEngine()
stego_engine = StegoEngine()

# --- UTILITÁRIOS PARA CHAVES RSA ---

def strip_pem(pem_string):
    """Remove os delimitadores -----BEGIN...----- e quebras de linha."""
    return re.sub(r'-----.*?-----|\s+', '', pem_string)

def wrap_pem(clean_text, is_private=True):
    """Reconstrói o formato PEM que a biblioteca cryptography exige."""
    tag = "PRIVATE KEY" if is_private else "PUBLIC KEY"
    return f"-----BEGIN {tag}-----\n{clean_text}\n-----END {tag}-----"

# --- ROTAS PRINCIPAIS ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_keys', methods=['GET'])
def generate_keys():
    """Gera um par de chaves e envia apenas o conteúdo Base64 para o front."""
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
    action = request.form.get('action') # 'encrypt' ou 'decrypt'
    method = request.form.get('method') # 'symmetric' ou 'asymmetric'
    file = request.files.get('file')
    
    if not file:
        return jsonify({'status': 'error', 'message': 'Selecione um arquivo'}), 400

    input_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(input_path)
    
    # --- LÓGICA DE NOMES DE ARQUIVO (Limpeza de .enc) ---
    if action == 'decrypt':
        # Pegamos o nome do arquivo enviado (ex: imagem.png.enc)
        filename = file.filename
        
        # Se ele terminar em .enc, removemos essa extensão
        if filename.lower().endswith('.enc'):
            nome_original = filename[:-4] # Remove os últimos 4 caracteres (.enc)
        else:
            nome_original = filename
            
        # O arquivo final será salvo como dec_imagem.png
        output_path = os.path.join(UPLOAD_FOLDER, f"dec_{nome_original}")
    else:
        # Na criptografia, apenas adicionamos o .enc ao final
        output_path = input_path + ".enc"

    try:
        duration = 0
        
        # 1. MODO SIMÉTRICO (AES)
        if method == 'symmetric':
            password = request.form.get('password')
            if not password:
                return jsonify({'status': 'error', 'message': 'Senha não fornecida'}), 400
            
            if action == 'encrypt':
                duration = engine.encrypt_symmetric(input_path, output_path, password)
            else:
                duration = engine.decrypt_symmetric(input_path, output_path, password)
        
        # 2. MODO ASSIMÉTRICO (RSA)
        else:
            key_text = request.form.get('key_text', '').strip()
            if not key_text:
                return jsonify({'status': 'error', 'message': 'Cole a chave PEM no campo'}), 400
            
            if action == 'encrypt':
                # O usuário pode colar a Pública OU a Privada para criptografar
                # Tentamos carregar como Pública primeiro
                try:
                    pem = wrap_pem(key_text, is_private=False)
                    key_obj = serialization.load_pem_public_key(pem.encode())
                except:
                    # Se falhar, tenta carregar como Privada e extrai a Pública dela
                    pem = wrap_pem(key_text, is_private=True)
                    key_obj = serialization.load_pem_private_key(pem.encode(), password=None).public_key()
                
                duration = engine.encrypt_asymmetric(input_path, output_path, key_obj)
            
            else:
                # Na decriptografia, a Privada é obrigatória
                pem = wrap_pem(key_text, is_private=True)
                key_obj = engine.load_private_key(pem.encode())
                duration = engine.decrypt_asymmetric(input_path, output_path, key_obj)

        return jsonify({
            'status': 'success',
            'time': f"{duration:.4f}s",
            'download_url': f"/download/{os.path.basename(output_path)}"
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': f"Falha: {str(e)}"}), 500

@app.route('/steganography', methods=['POST'])
def steganography():
    action = request.form.get('action')
    image_file = request.files.get('image')
    
    if not image_file:
        return jsonify({'status': 'error', 'message': 'Imagem carrier não selecionada'}), 400

    img_path = os.path.join(UPLOAD_FOLDER, image_file.filename)
    image_file.save(img_path)

    try:
        if action == 'hide':
            secret_file = request.files.get('file_to_hide')
            hide_path = os.path.join(UPLOAD_FOLDER, secret_file.filename)
            secret_file.save(hide_path)
            
            output_name = f"stego_{os.path.splitext(image_file.filename)[0]}.png"
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
    return send_file(os.path.join(UPLOAD_FOLDER, filename), as_attachment=True)

if __name__ == '__main__':
    # Rode com debug=True para reiniciar o servidor ao salvar arquivos
    app.run(debug=True)