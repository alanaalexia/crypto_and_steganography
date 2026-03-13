# Chamber of Secrets 🔒📂

Chamber of Secrets is a full-stack web application designed to provide a dual-layer data protection system. By combining Hybrid Encryption and Image Steganography, the tool allows users to not only encrypt sensitive information but also hide it within media files, making it nearly impossible for unauthorized parties to detect.

## 🚀 Key Features
- Symmetric Encryption (AES-GCM): High-performance encryption used for processing large datasets (up to 500 MB) while ensuring data integrity.

- Asymmetric Encryption (RSA): Implemented for secure session key exchange, allowing safe communication between users.

- LSB Steganography (Least Significant Bit): A data-hiding technique for PNG files. The message is embedded into the least significant bits of the image pixels, keeping the carrier image visually identical to the original.

- Full-Stack Dashboard: A modern, intuitive interface for uploading, processing, and downloading encrypted or hidden data.

## 🛠️ Tech Stack
- Backend: Python with Flask;

- Security: cryptography library (AES-GCM and RSA implementations);

- Image Processing: Pillow (PIL) for pixel-level manipulation;

- Frontend: HTML5, Tailwind CSS and JavaScript.

## 🧠 Technical Architecture
### LSB Steganography
The LSB technique replaces the least significant bit of each color channel (RGB) with bits from the encrypted message. This ensures the data is distributed across the image so that any generated noise remains imperceptible to the human eye.

### Hybrid Encryption Model
To balance the security of RSA with the efficiency of AES, the project follows a hybrid approach:

- Raw data is encrypted using AES-GCM.

- The generated symmetric key is then encrypted with the recipient's RSA Public Key.

- The final package contains the encrypted payload and the protected key.

## 🔧 Installation & Setup
1. Clone the repository:

`git clone https://github.com/your-username/chamber-of-secrets.git
cd chamber-of-secrets`

2. Install dependencies:

`pip install -r requirements.txt`

3. Run the application:

`python app.py`

4. Access the app at `http://localhost:5000` in your browser.
