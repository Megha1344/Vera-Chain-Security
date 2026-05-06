# Vera-Chain-Security
A decentralized anti-counterfeiting framework integrating Blockchain and AI to secure supply chains. Features a verification engine using OpenCV and Fuzzy Logic to cross-reference physical products with Digital Twins, ensuring a tamper-proof audit trail via Ethereum Smart Contracts.
VeraChain: Blockchain-Powered Brand Protection
VeraChain is a multimodal authentication platform designed to combat counterfeiting. It combines an immutable Blockchain Ledger with Computer Vision (OCR & Logo Detection) to ensure that products in the supply chain are authentic and verified.

🚀 Key Features
Manufacturer Onboarding (KYC): Secure verification for brands before they can register products.

Immutable Ledger: Every product is assigned a unique digital signature and stored in a tamper-proof blockchain.

Consumer Verification:

Live Camera OCR: Reads product IDs from physical labels in real-time.

Logo Detection: Uses OpenCV to match brand logos against a known database.

Multimodal Security: Uses both alphanumeric IDs and visual brand cues for dual-layer authentication.

🛠️ Tech Stack
Frontend: Streamlit (Multi-page App)

Blockchain: Custom Python implementation (vera_ledger)

Computer Vision: OpenCV, Pytesseract (OCR), PIL

Backend: Python 3.x

📂 Project Structure
Plaintext
├── home.py               # Main landing page
├── blockchain.py         # Blockchain core logic
├── requirements.txt      # Python dependencies
├── pages/
│   ├── 1_Manufacturer.py # KYC & Product registration
│   └── 2_Consumer.py     # Live verification portal
└── logos/                # Brand logo database for CV matching
⚙️ Setup & Installation
Clone the repository.

Install dependencies: pip install -r requirements.txt.

Ensure Tesseract OCR is installed on your local machine.

Run the app: streamlit run home.py.
