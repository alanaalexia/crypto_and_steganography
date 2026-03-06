from PIL import Image
import os

class StegoEngine:
    def hide_data(self, image_path, data_path, output_path):
        """Esconde os bits de um arquivo nos bits menos significativos (LSB) de uma imagem."""
        img = Image.open(image_path).convert('RGB')
        
        # Lê o arquivo que será escondido
        with open(data_path, 'rb') as f:
            data = f.read()

        # Precisamos saber o tamanho do arquivo para conseguir extrair depois
        # Usamos 4 bytes (32 bits) para guardar o tamanho do arquivo
        data_len = len(data).to_bytes(4, byteorder='big')
        payload = data_len + data
        
        # Converte o payload (tamanho + dados) em uma lista de bits
        bits = []
        for byte in payload:
            for i in range(8):
                bits.append((byte >> (7 - i)) & 1)

        pixels = list(img.getdata())
        
        # Verificação crítica: a imagem tem pixels suficientes? (3 bits por pixel: R, G, B)
        if len(bits) > len(pixels) * 3:
            raise ValueError(f"Imagem insuficiente! Precisa de {len(bits)} bits, mas só tem {len(pixels)*3}.")

        new_pixels = []
        bit_idx = 0
        
        for pixel in pixels:
            new_pixel = list(pixel)
            for color_idx in range(3): # R, G, B
                if bit_idx < len(bits):
                    # Zera o último bit (& ~1) e coloca o bit da mensagem (| bits[bit_idx])
                    new_pixel[color_idx] = (new_pixel[color_idx] & ~1) | bits[bit_idx]
                    bit_idx += 1
            new_pixels.append(tuple(new_pixel))

        # Salva a nova imagem (deve ser PNG para não perder dados por compressão)
        img.putdata(new_pixels)
        img.save(output_path, "PNG")

    def reveal_data(self, image_path, output_data_path):
        """Extrai os bits escondidos de uma imagem LSB."""
        img = Image.open(image_path).convert('RGB')
        pixels = list(img.getdata())
        
        bits = []
        for pixel in pixels:
            for color_idx in range(3):
                bits.append(pixel[color_idx] & 1)
        
        # Converter os bits de volta para bytes
        all_bytes = bytearray()
        for i in range(0, len(bits), 8):
            if i + 8 > len(bits): break
            byte = 0
            for bit in bits[i:i+8]:
                byte = (byte << 1) | bit
            all_bytes.append(byte)
        
        # Recupera o tamanho do arquivo original (primeiros 4 bytes)
        data_len = int.from_bytes(all_bytes[:4], byteorder='big')
        actual_data = all_bytes[4:4+data_len]
        
        with open(output_data_path, 'wb') as f:
            f.write(actual_data)