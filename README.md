🔐 CryptoStegano-PySuite
A high-performance web application built with Python (Flask) for advanced cryptographic operations and image steganography. This suite is designed to handle large-scale data (up to 500MB) and analyze the performance of various security algorithms.

🚀 Features
1. Symmetric Encryption (AES-256-GCM)
Variable Key Lengths: Supports 8 to 128-character keys using PBKDF2HMAC (Password-Based Key Derivation Function 2) to normalize any input into a secure 256-bit key.

Streaming Architecture: Uses a chunk-based processing method (64KB blocks) to ensure files as large as 500MB can be encrypted without crashing the system's RAM.

Authenticated Encryption: Uses GCM (Galois/Counter Mode) to ensure data integrity and authenticity.

2. Asymmetric Encryption (RSA-4096)
Hybrid Cryptography: To handle files of 500MB (which exceed standard RSA block limits), the system generates a random AES session key to encrypt the file, then wraps that key with the recipient's RSA Public Key.

Security: Implements PKCS1v15 padding for maximum compatibility and security.

3. Image Steganography (LSB)
LSB Technique: Hides encrypted payloads within the Least Significant Bits of a PNG image's pixels.

Payload Capacity: Includes a pre-flight check to verify if the carrier image has enough pixels to store the requested file (crucial for the 1MB vs 500MB test cases).

🛠️ Tech Stack
Backend: Python 3.x, Flask.

Security: cryptography library (Hazmat layer for high performance).

Image Processing: Pillow (PIL) for pixel manipulation.

Frontend: HTML5, JavaScript (ES6), Tailwind CSS for a modern UI.

📊 Benchmarking & Analysis (Requirement C)
The application includes a testing module to generate the data required for the final report. Tests are conducted on:

File Sizes: 1 MB and 500 MB.

Key Lengths: 8 characters and 128 characters.

Repetitions: Each test is executed 3 times to calculate the average execution time.

Expected Technical Findings:
Key Length Impact: You will notice that the execution time for an 8-char key vs. a 128-char key is nearly identical, as the KDF overhead is constant regardless of the file size.

Memory Management: By using Python's open(file, 'rb') with chunks, the memory footprint stays low (approx. 50-100MB) even when processing a 500MB file.

📂 Project Structure
Plaintext
├── app.py              # Flask Backend & API Routes
├── logic/
│   ├── symmetric.py    # AES-GCM implementation
│   ├── asymmetric.py   # RSA Hybrid implementation
│   └── steganography.py# LSB Image logic
├── templates/          # HTML Frontend
├── static/             # CSS/JS files
├── tests/              # Scripts to generate 1MB/500MB dummy files
└── README.md
⚙️ Setup & Installation
Clone the repository:

Bash
git clone https://github.com/your-username/CryptoStegano-PySuite.git
cd CryptoStegano-PySuite
Create a Virtual Environment:

Bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
Install Dependencies:

Bash
pip install flask cryptography Pillow
Run the Application:

Bash
python app.py
Access the UI at http://127.0.0.1:5000