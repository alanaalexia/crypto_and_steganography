from PIL import Image
import os

class StegoEngine:
    def hide_data(self, image_path, data_path, output_path):
        """Esconde os bits de um arquivo nos bits menos significativos (LSB) de uma imagem."""
        # Abre a imagem e garante que está em modo RGB
        img = Image.open(image_path).convert('RGB')
        
        # Lê o arquivo binário que será escondido
        with open(data_path, 'rb') as f:
            data = f.read()

        # Adiciona o tamanho do arquivo nos primeiros 4 bytes (32 bits)
        data_len = len(data).to_bytes(4, byteorder='big')
        payload = data_len + data
        
        # Converte bytes para uma lista de bits (0 e 1)
        bits = []
        for byte in payload:
            for i in range(8):
                bits.append((byte >> (7 - i)) & 1)

        pixels = list(img.getdata())
        
        # Verifica se a imagem tem pixels suficientes (3 canais por pixel: R, G, B)
        if len(bits) > len(pixels) * 3:
            raise ValueError(f"Imagem insuficiente! Precisa de {len(bits)} bits, mas só tem {len(pixels)*3}.")

        new_pixels = []
        bit_idx = 0
        
        for pixel in pixels:
            new_pixel = list(pixel)
            for color_idx in range(3): # R, G, B
                if bit_idx < len(bits):
                    # Altera apenas o Bit Menos Significativo (LSB)
                    new_pixel[color_idx] = (new_pixel[color_idx] & ~1) | bits[bit_idx]
                    bit_idx += 1
            new_pixels.append(tuple(new_pixel))

        # Salva em PNG para evitar compressão com perda de dados
        img.putdata(new_pixels)
        img.save(output_path, "PNG")

    def reveal_data(self, image_path, output_data_path):
        """Extrai os bits escondidos de uma imagem LSB."""
        img = Image.open(image_path).convert('RGB')
        pixels = list(img.getdata())
        
        # Coleta todos os bits LSB da imagem
        bits = []
        for pixel in pixels:
            for color_idx in range(3):
                bits.append(pixel[color_idx] & 1)
        
        # Converte bits de volta para bytes
        all_bytes = bytearray()
        for i in range(0, len(bits), 8):
            if i + 8 > len(bits): break
            byte = 0
            for bit in bits[i:i+8]:
                byte = (byte << 1) | bit
            all_bytes.append(byte)
        
        if len(all_bytes) < 4:
            raise ValueError("Imagem muito pequena para conter dados.")

        # Lê os primeiros 4 bytes para saber o tamanho do arquivo escondido
        data_len = int.from_bytes(all_bytes[:4], byteorder='big')
        
        # Extrai exatamente a quantidade de bytes necessária
        actual_data = all_bytes[4:4+data_len]
        
        with open(output_data_path, 'wb') as f:
            f.write(actual_data)