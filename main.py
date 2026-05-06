import requests, cv2, numpy as np, pytesseract, time, os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from difflib import get_close_matches
from blockchain import vera_ledger

# --- 1. CONFIGURATION ---
TWILIO_SID = 'ACb91d89859c616b445d8c9a24167327f1'
TWILIO_AUTH_TOKEN = 'cc13067bcb056d47f229fc958a49908b'
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

app = Flask(__name__)


def normalize(text):
    return "".join(filter(str.isalnum, text.upper()))


@app.route("/whatsapp", methods=['POST'])
def whatsapp_reply():
    print("\n--- INITIATING HUMAN-CENTRIC SCAN ---")
    vera_ledger.load_from_db()
    resp = MessagingResponse()

    num_media = int(request.values.get('NumMedia', 0))
    detected_ids = []

    if num_media > 0:
        image_url = request.values.get('MediaUrl0')
        time.sleep(3)
        try:
            # Download and Decode
            img_data = requests.get(image_url, auth=(TWILIO_SID, TWILIO_AUTH_TOKEN)).content
            nparr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # --- STEP A: NOISE REDUCTION ---
            # Bilateral filter removes paper grain but keeps handwriting edges sharp
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            smoothed = cv2.bilateralFilter(gray, 9, 75, 75)

            # --- STEP B: ADAPTIVE EDGE DETECTION ---
            # This finds the 'outline' of your writing, ignoring flat horizontal lines
            thresh = cv2.adaptiveThreshold(smoothed, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                           cv2.THRESH_BINARY_INV, 31, 10)

            # --- STEP C: DYNAMIC UPSCALING ---
            # We triple the size so Tesseract can see small 'touch points' clearly
            upscaled = cv2.resize(thresh, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)

            # --- STEP D: LIGHT MORPHOLOGY ---
            # We close small gaps in the ink strokes (fixes the 'broken letter' issue)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            closed = cv2.morphologyEx(upscaled, cv2.MORPH_CLOSE, kernel)

            # Final Inversion for Tesseract
            final_img = cv2.bitwise_not(closed)
            cv2.imwrite("multi_scan_debug.png", final_img)

            # --- STEP E: AGGRESSIVE OCR ---
            # PSM 11: Sparse text (finds IDs even if they are scattered or messy)
            # OEM 3: Default OCR + LSTM (AI mode)
            custom_config = r'--oem 3 --psm 11'
            raw_data = pytesseract.image_to_string(final_img, config=custom_config)

            # Extract everything that looks like a word
            detected_ids = [w.strip() for w in raw_data.split() if len(w.strip()) >= 4]
            print(f"DEBUG: Scanned Chunks: {detected_ids}")

        except Exception as e:
            print(f"ERROR: {e}")
            return str(resp.message("⚠️ Processing error. Please try again."))
    else:
        detected_ids = [request.values.get('Body', '').strip()]

    # --- BLOCKCHAIN VERIFICATION ---
    id_map = {normalize(p['product_id']): p['product_id'] for block in vera_ledger.chain for p in block['products']}
    all_normalized_ids = list(id_map.keys())

    results = []
    for raw_id in detected_ids:
        norm_id = normalize(raw_id)
        if not norm_id: continue

        # 0.35 cutoff is very forgiving for messy handwriting
        matches = get_close_matches(norm_id, all_normalized_ids, n=1, cutoff=0.35)

        if matches:
            original_id = id_map[matches[0]]
            p_data = vera_ledger.verify_id(original_id)
            results.append(f"✅ {original_id}: AUTHENTIC ({p_data['manufacturer']})")
        else:
            if len(raw_id) > 5:
                results.append(f"❌ {raw_id}: NOT RECOGNIZED")

    # Format Output
    if not results:
        reply = "🛡️ VERA-CHAIN REPORT:\n\nNo valid IDs found. Please ensure the lighting is even."
    else:
        reply = "🛡️ VERA-CHAIN BATCH REPORT:\n\n" + "\n".join(list(set(results)))

    resp.message(reply)
    return str(resp)


if __name__ == "__main__":
    app.run(port=5000, debug=False)
