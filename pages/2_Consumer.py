import streamlit as st
import cv2
import numpy as np
from PIL import Image
import time
import os
import pytesseract
import shutil
from blockchain import vera_ledger
from difflib import get_close_matches

# ====================== TESSERACT CLOUD FIX ======================
# Automatically find the Tesseract path on the Streamlit Linux server
tesseract_path = shutil.which("tesseract")

if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
else:
    # Fallback for local Windows testing (only if not on cloud)
    windows_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    if os.path.exists(windows_path):
        pytesseract.pytesseract.tesseract_cmd = windows_path
    else:
        st.error("Tesseract not found. Ensure 'packages.txt' exists on GitHub with 'tesseract-ocr'.")

st.set_page_config(page_title="VeraChain Consumer", layout="wide", page_icon="🔍")

# Professional Dark Theme
st.markdown("""
<style>
    .stApp { background-color: #0a0f1c; color: #e0e0ff; }
    .success-text { color: #00ff9d; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("🔍 VeraChain - Consumer Authenticity Checker")
st.markdown("**Verify products using ID, Photo, Live Camera, or Logo Detection**")

# ====================== LOGO SETUP ======================
LOGO_DIR = "logos"
known_logos = {}

if os.path.exists(LOGO_DIR):
    loaded = []
    for file in os.listdir(LOGO_DIR):
        if file.lower().endswith((".png", ".jpg", ".jpeg")):
            brand = file.split(".")[0].upper().replace("_LOGO", "")
            path = os.path.join(LOGO_DIR, file)
            # Use IMREAD_COLOR then convert to match templates better
            img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            if img is not None:
                known_logos[brand] = img
                loaded.append(brand)
    if loaded:
        st.sidebar.success(f"✅ Loaded {len(loaded)} logos: {loaded}")
else:
    st.sidebar.error("❌ 'logos' folder not found!")

# OCR Preprocessing
def preprocess_ocr(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Simple thresholding works better for digital camera shots
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh

# Logo Detection
def detect_logo(image):
    if not known_logos:
        return None, 0.0
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    best_brand = None
    best_score = 0.0
    for brand, template in known_logos.items():
        try:
            # Resize template to match a portion of the screen
            res = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(res)
            if max_val > best_score:
                best_score = max_val
                best_brand = brand
        except:
            continue
    return best_brand, best_score

# Method Selection
method = st.sidebar.radio("Verification Method",
                          ["Live Camera", "Upload Photo", "Type Product ID"])

# ====================== LIVE CAMERA ======================
if method == "Live Camera":
    st.subheader("📹 Live Camera Scan")
    img_file = st.camera_input("Take a photo of the product ID or Logo")

    if img_file:
        pil_img = Image.open(img_file)
        img = np.array(pil_img)
        img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        
        with st.spinner("Analyzing scan..."):
            # 1. OCR Search
            processed = preprocess_ocr(img_bgr)
            text = pytesseract.image_to_string(processed, config='--oem 3 --psm 11')
            words = [w.strip().upper() for w in text.split() if len(w.strip()) >= 4]

            # 2. Blockchain Lookup
            vera_ledger.load_from_db()
            all_ids = []
            for block in vera_ledger.chain:
                for p in block.get('products', []):
                    all_ids.append(p.get('product_id', '').upper())

            found_match = False
            for word in words:
                match = get_close_matches(word, all_ids, n=1, cutoff=0.6)
                if match:
                    prod = vera_ledger.verify_id(match[0])
                    st.success(f"✅ **AUTHENTIC PRODUCT FOUND**")
                    st.json(prod)
                    found_match = True
                    break
            
            # 3. Logo Lookup
            logo, score = detect_logo(img_bgr)
            if logo and score > 0.4:
                st.info(f"🖼️ **Logo Detected:** {logo} ({int(score*100)}% Confidence)")

            if not found_match and (not logo or score < 0.4):
                st.warning("No matching product or logo found in this frame.")

# ====================== UPLOAD PHOTO ======================
elif method == "Upload Photo":
    st.subheader("🖼️ Upload Product Photo")
    uploaded = st.file_uploader("Choose image", type=["jpg", "jpeg", "png"])

    if uploaded:
        pil_img = Image.open(uploaded)
        st.image(pil_img, caption="Uploaded Image", width=400)
        
        if st.button("🔍 Run Verification"):
            img = np.array(pil_img.convert('RGB'))
            img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

            # OCR Process
            processed = preprocess_ocr(img_bgr)
            text = pytesseract.image_to_string(processed)
            
            # Blockchain Verify
            vera_ledger.load_from_db()
            # (Similar logic to camera for verification...)
            st.write(f"Detected Text: {text}")
            
            logo, score = detect_logo(img_bgr)
            if logo and score > 0.4:
                st.success(f"Verified Brand Logo: {logo}")

# ====================== MANUAL ID ======================
else:
    st.subheader("⌨️ Manual Product ID Check")
    pid = st.text_input("Enter Product ID")
    if st.button("Verify Now"):
        vera_ledger.load_from_db()
        result = vera_ledger.verify_id(pid.strip().upper())
        if result:
            st.success(f"✅ Authentic: Verified by {result.get('manufacturer')}")
            st.table(result)
        else:
            st.error("❌ Not Found: This product ID is not registered on VeraChain.")

st.caption("VeraChain Consumer Portal • SeedBrains 2026")
