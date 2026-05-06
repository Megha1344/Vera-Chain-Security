import streamlit as st
import cv2
import numpy as np
from PIL import Image
import time
import os
from blockchain import vera_ledger
from difflib import get_close_matches
import pytesseract  # ← This was missing!

import shutil
import os

# Automatically find the Tesseract path on the Streamlit Linux server
tesseract_path = shutil.which("tesseract")

if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
else:
    st.error("Tesseract binary not found. Please ensure packages.txt contains tesseract-ocr")
# Set Tesseract path (VERY IMPORTANT for Windows)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

st.set_page_config(page_title="VeraChain Consumer", layout="wide", page_icon="🔍")

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
            img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            if img is not None:
                known_logos[brand] = img
                loaded.append(brand)
    if loaded:
        st.sidebar.success(f"✅ Loaded {len(loaded)} logos: {loaded}")
    else:
        st.sidebar.warning("Logos folder found but no valid images.")
else:
    st.sidebar.error("❌ 'logos' folder not found! Create it and add rolex_logo.png, apple_logo.png, etc.")


# OCR Preprocessing
def preprocess_ocr(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    smoothed = cv2.bilateralFilter(gray, 9, 75, 75)
    thresh = cv2.adaptiveThreshold(smoothed, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, 31, 10)
    upscaled = cv2.resize(thresh, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    closed = cv2.morphologyEx(upscaled, cv2.MORPH_CLOSE, kernel)
    return cv2.bitwise_not(closed)


# Logo Detection
def detect_logo(image):
    if not known_logos:
        return None, 0.0
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    best_brand = None
    best_score = 0.0
    for brand, template in known_logos.items():
        try:
            result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)
            if max_val > best_score and max_val > 0.5:
                best_score = max_val
                best_brand = brand
        except:
            continue
    return best_brand, best_score


# Method Selection
method = st.sidebar.radio("Verification Method",
                          ["Live Camera", "Upload Photo", "Type Product ID"])

# ====================== LIVE CAMERA (Fixed Version) ======================
if method == "Live Camera":
    st.subheader("📹 Live Camera - Point at ID or Logo")

    start_cam = st.checkbox("Start Live Camera", value=False)

    if start_cam:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            st.error("❌ Cannot access camera. Make sure camera is not used by another app.")
        else:
            frame_win = st.empty()
            result_win = st.empty()

            while start_cam:
                ret, frame = cap.read()
                if not ret:
                    st.error("Failed to capture frame")
                    break

                # Display live feed
                frame_win.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), channels="RGB", use_column_width=True)

                # Process every 2 seconds
                if int(time.time()) % 2 == 0:
                    processed = preprocess_ocr(frame)
                    text = pytesseract.image_to_string(processed, config='--oem 3 --psm 11')
                    ids = [w.strip() for w in text.split() if len(w.strip()) >= 4]

                    vera_ledger.load_from_db()
                    id_map = {"".join(filter(str.isalnum, p.get('product_id', '').upper())): p
                              for block in vera_ledger.chain for p in block.get('products', [])}

                    results = []
                    for rid in ids:
                        norm = "".join(filter(str.isalnum, rid.upper()))
                        m = get_close_matches(norm, list(id_map.keys()), n=1, cutoff=0.35)
                        if m:
                            p = id_map[m[0]]
                            results.append(f"✅ {p['product_id']} : AUTHENTIC ({p.get('manufacturer', '')})")

                    logo, score = detect_logo(frame)
                    if logo and score > 0.55:
                        results.append(f"🖼️ Logo Detected: **{logo}** (Confidence: {score:.2f})")

                    if results:
                        result_win.markdown("### 🔍 Result\n" + "\n".join(results))
                    else:
                        result_win.info("Scanning... Point camera clearly at handwritten ID or logo")

                time.sleep(0.1)

            cap.release()

# ====================== UPLOAD PHOTO ======================
elif method == "Upload Photo":
    st.subheader("🖼️ Upload Photo of Product / Logo / Handwritten ID")
    uploaded = st.file_uploader("Choose image", type=["jpg", "jpeg", "png"])

    if uploaded:
        pil_img = Image.open(uploaded)
        st.image(pil_img, use_column_width=True)

        if st.button("🔍 Analyze Image"):
            with st.spinner("Processing OCR + Logo Detection..."):
                img = np.array(pil_img.convert('RGB'))
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

                processed = preprocess_ocr(img)
                text = pytesseract.image_to_string(processed, config='--oem 3 --psm 11')
                detected_ids = [w.strip() for w in text.split() if len(w.strip()) >= 4]

                vera_ledger.load_from_db()
                id_map = {"".join(filter(str.isalnum, p.get('product_id', '').upper())): p
                          for block in vera_ledger.chain for p in block.get('products', [])}

                results = []
                for d in detected_ids:
                    norm = "".join(filter(str.isalnum, d.upper()))
                    m = get_close_matches(norm, list(id_map.keys()), n=1, cutoff=0.35)
                    if m:
                        p = id_map[m[0]]
                        results.append(f"✅ **{p['product_id']}**: AUTHENTIC ({p.get('manufacturer', '')})")

                logo, score = detect_logo(img)
                if logo and score > 0.5:
                    results.append(f"🖼️ **Logo Match**: {logo} (Confidence: {score:.2f})")

                if results:
                    st.success("Verification Results")
                    for r in results:
                        st.markdown(r)
                else:
                    st.warning("No clear Product ID or logo detected.")

# ====================== MANUAL ======================
else:
    st.subheader("⌨️ Manual Product ID Check")
    pid = st.text_input("Enter Product ID (e.g. ROLEX-V2026)")
    if st.button("Check Authenticity"):
        if pid:
            prod = vera_ledger.verify_id(pid.strip().upper())
            if prod:
                st.success(f"✅ AUTHENTIC - {prod.get('manufacturer', '')}")
            else:
                st.error(f"❌ Product **{pid}** not found")
        else:
            st.warning("Please enter Product ID")

st.caption("VeraChain Consumer Portal • OCR + Logo Detection + Blockchain • SeedBrains 2026")
