from crypt_engine import CryptoEngine
import os

engine = CryptoEngine()

def create_dummy_file(name, size_mb):
    with open(name, "wb") as f:
        f.write(os.urandom(size_mb * 1024 * 1024))

# 1. Criar arquivos de teste
print("Gerando arquivos de teste (isso pode demorar um pouco)...")
create_dummy_file("test_1mb.bin", 1)
create_dummy_file("test_500mb.bin", 500)

# 2. Teste Simétrico (Exemplo)
password_short = "12345678"
password_long = "a" * 128

print("\n--- TESTE SIMÉTRICO (AES) ---")
for p in [password_short, password_long]:
    for size in ["1mb", "500mb"]:
        t = engine.encrypt_symmetric(f"test_{size}.bin", f"enc_{size}.bin", p)
        print(f"Arquivo: {size} | Senha: {len(p)} chars | Tempo: {t:.4f}s")

# Limpeza
# os.remove("test_1mb.bin") ...