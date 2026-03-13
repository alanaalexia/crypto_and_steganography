import os
import time
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding

class CryptoEngine:
    def __init__(self):
        self.chunk_size = 64 * 1024  # 64KB por vez para não estourar a RAM

    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Transforma qualquer senha (8 ou 128 chars) em uma chave de 32 bytes."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return kdf.derive(password.encode())

    # --- CRIPTOGRAFIA SIMÉTRICA (AES-GCM) ---
    def encrypt_symmetric(self, input_path, output_path, password):
        start_time = time.perf_counter()
        salt = os.urandom(16)
        nonce = os.urandom(12)
        key = self._derive_key(password, salt)
        aesgcm = AESGCM(key)

        with open(input_path, 'rb') as f_in, open(output_path, 'wb') as f_out:
            f_out.write(salt)   # 16 bytes
            f_out.write(nonce)  # 12 bytes
            
            while True:
                # 1. Tenta ler um pedaço do arquivo
                chunk = f_in.read(self.chunk_size)
                
                # 2. Se o resultado for vazio, significa que o arquivo acabou
                if not chunk:
                    break 
                    
                # 3. Se chegou aqui, há dados para criptografar
                # No AES-GCM, o chunk cifrado terá a tag de autenticação embutida
                encrypted_chunk = aesgcm.encrypt(nonce, chunk, None)
                
                # 4. Grava o pedaço trancado no novo arquivo
                f_out.write(encrypted_chunk)
        
        return time.perf_counter() - start_time

    # --- CRIPTOGRAFIA ASSIMÉTRICA (RSA HÍBRIDA) ---
    # Nota: RSA não cifra 500MB diretamente. Ciframos o arquivo com AES 
    # e ciframos a chave AES com RSA.

    def generate_rsa_keys(self):
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()
        return private_key, public_key

    def encrypt_asymmetric(self, input_path, output_path, public_key):
        start_time = time.perf_counter()
        
        # 1. Gerar uma chave simétrica temporária
        session_key = AESGCM.generate_key(bit_length=256)
        aesgcm = AESGCM(session_key)
        nonce = os.urandom(12)

        # 2. Cifrar a chave de sessão com RSA
        encrypted_session_key = public_key.encrypt(
            session_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        # 3. Cifrar o arquivo com a chave de sessão (AES)
        with open(input_path, 'rb') as f_in, open(output_path, 'wb') as f_out:
            # Guardamos o tamanho da chave RSA cifrada para saber onde ler depois
            f_out.write(len(encrypted_session_key).to_bytes(4, 'big'))
            f_out.write(encrypted_session_key)
            f_out.write(nonce)

            while chunk := f_in.read(self.chunk_size):
                f_out.write(aesgcm.encrypt(nonce, chunk, None))

        return time.perf_counter() - start_time
    
    # --- DECRIPTOGRAFIA SIMÉTRICA ---
    def decrypt_symmetric(self, input_path, output_path, password):
        start_time = time.perf_counter()
        with open(input_path, 'rb') as f_in, open(output_path, 'wb') as f_out:
            salt = f_in.read(16)
            nonce = f_in.read(12)
            key = self._derive_key(password, salt)
            aesgcm = AESGCM(key)
            
            while chunk := f_in.read(self.chunk_size + 16): # +16 bytes da tag GCM
                decrypted_chunk = aesgcm.decrypt(nonce, chunk, None)
                f_out.write(decrypted_chunk)
        
        return time.perf_counter() - start_time

    # --- DECRIPTOGRAFIA ASSIMÉTRICA (HÍBRIDA) ---
    def decrypt_asymmetric(self, input_path, output_path, private_key):
        start_time = time.perf_counter()
        with open(input_path, 'rb') as f_in, open(output_path, 'wb') as f_out:
            # Lê o tamanho da chave RSA, a chave e o nonce
            key_len = int.from_bytes(f_in.read(4), 'big')
            encrypted_session_key = f_in.read(key_len)
            nonce = f_in.read(12)

            # Decifra a chave de sessão com a Privada RSA
            session_key = private_key.decrypt(
                encrypted_session_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            aesgcm = AESGCM(session_key)

            while chunk := f_in.read(self.chunk_size + 16):
                f_out.write(aesgcm.decrypt(nonce, chunk, None))

        return time.perf_counter() - start_time
    
    def load_private_key(self, pem_data: bytes):
        """Converte o texto do .txt/pem de volta para um objeto RSA."""
        return serialization.load_pem_private_key(
            pem_data,
            password=None,
        )

    def export_keys_to_strings(self, private_key, public_key):
        """Transforma os objetos de chave em texto para você salvar no .txt."""
        priv_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        pub_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return priv_pem, pub_pem