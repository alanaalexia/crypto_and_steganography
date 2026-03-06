from flask import Flask, render_template, request, send_file, jsonify
from crypt_engine import CryptoEngine
import os
import time
from stego_engine import StegoEngine # Certifique-se que o arquivo stego_engine.py existe

app = Flask(__name__)
engine = CryptoEngine()
stego_engine = StegoEngine()

# Pastas para salvar os arquivos temporários
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/crypt_action', methods=['POST'])
def crypt_action():
    action = request.form['action'] # 'encrypt' ou 'decrypt'
    method = request.form['method']
    file = request.files['file']
    password = request.form['password']
    
    input_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(input_path)
    if action == 'decrypt':
        # os.path.splitext separa 'caminho/foto.png.enc' em ('caminho/foto.png', '.enc')
        root, ext = os.path.splitext(input_path)
    
        if ext == '.enc':
        # Se era .enc, o 'root' já é o nome original (ex: foto.png)
        # Vamos adicionar 'dec_' no início do nome do arquivo
            path_dir = os.path.dirname(root)
            name_only = os.path.basename(root)
            output_path = os.path.join(path_dir, "dec_" + name_only)
        else:
            # Caso o arquivo não tenha .enc por algum motivo
            output_path = input_path + ".decrypted"
    else:
        output_path = input_path + ".enc"

    try:
        if method == 'symmetric':
            if action == 'encrypt':
                duration = engine.encrypt_symmetric(input_path, output_path, password)
            else:
                duration = engine.decrypt_symmetric(input_path, output_path, password)
        else:
            # Assimétrica (Para simplificar o trabalho, geramos as chaves globalmente ou simulamos)
            # Em um cenário real, você carregaria sua chave privada para decifrar.
            priv_key, pub_key = engine.generate_rsa_keys() 
            if action == 'encrypt':
                duration = engine.encrypt_asymmetric(input_path, output_path, pub_key)
            else:
                # Nota: Aqui você precisaria da chave privada gerada no momento do encrypt.
                # Para o teste do professor, você pode gerar o par e manter na memória.
                duration = engine.decrypt_asymmetric(input_path, output_path, priv_key)

        return jsonify({
            'status': 'success',
            'time': f"{duration:.4f}s",
            'download_url': f"/download/{os.path.basename(output_path)}"
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
@app.route('/download/<filename>')
def download(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)

@app.route('/crypt_action', methods=['POST'])
def crypt_action():
    action = request.form['action']
    method = request.form['method']
    file = request.files['file']
    
    input_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(input_path)
    
    # Lógica de nomes de arquivo que você já fez
    if action == 'decrypt':
        output_path = input_path.replace('.enc', '')
        output_path = os.path.join(os.path.dirname(output_path), "dec_" + os.path.basename(output_path))
    else:
        output_path = input_path + ".enc"

    try:
        if method == 'symmetric':
            password = request.form['password']
            if action == 'encrypt':
                duration = engine.encrypt_symmetric(input_path, output_path, password)
            else:
                duration = engine.decrypt_symmetric(input_path, output_path, password)
        
        else: # ASSIMÉTRICO
            if action == 'encrypt':
                # Gera as chaves e envia a PRIVADA para o usuário salvar
                priv, pub = engine.generate_rsa_keys()
                priv_pem, pub_pem = engine.export_keys_to_strings(priv, pub)
                
                duration = engine.encrypt_asymmetric(input_path, output_path, pub)
                
                # Criamos um arquivo TXT temporário com a chave privada para o usuário baixar
                key_filename = "MINHA_CHAVE_PRIVADA.txt"
                with open(os.path.join(UPLOAD_FOLDER, key_filename), "wb") as f:
                    f.write(priv_pem)

                return jsonify({
                    'status': 'success',
                    'time': f"{duration:.4f}s",
                    'download_url': f"/download/{os.path.basename(output_path)}",
                    'key_url': f"/download/{key_filename}" # Envia a chave junto!
                })
            
            else: # DECRYPT ASYMMETRIC
                # O usuário precisa subir o arquivo da chave privada
                key_file = request.files['key_file']
                priv_key = engine.load_private_key(key_file.read())
                duration = engine.decrypt_asymmetric(input_path, output_path, priv_key)

        return jsonify({
            'status': 'success',
            'time': f"{duration:.4f}s",
            'download_url': f"/download/{os.path.basename(output_path)}"
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/steganography', methods=['POST'])
def steganography():
    action = request.form['action'] # 'hide' ou 'reveal'
    image = request.files['image']
    
    img_path = os.path.join(UPLOAD_FOLDER, image.filename)
    image.save(img_path)
    output_path = os.path.join(UPLOAD_FOLDER, "stego_" + image.filename)

    try:
        start_time = time.perf_counter()
        if action == 'hide':
            file_to_hide = request.files['file_to_hide']
            hide_path = os.path.join(UPLOAD_FOLDER, file_to_hide.filename)
            file_to_hide.save(hide_path)
            
            stego_engine.hide_data(img_path, hide_path, output_path)
            duration = time.perf_counter() - start_time
            return jsonify({
                'status': 'success',
                'time': f"{duration:.4f}s",
                'download_url': f"/download/{os.path.basename(output_path)}"
            })
        else:
            # Revelar
            result_path = os.path.join(UPLOAD_FOLDER, "revealed_data.bin")
            stego_engine.reveal_data(img_path, result_path)
            duration = time.perf_counter() - start_time
            return jsonify({
                'status': 'success',
                'time': f"{duration:.4f}s",
                'download_url': f"/download/revealed_data.bin"
            })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
    