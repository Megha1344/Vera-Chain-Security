import streamlit as st
import pandas as pd
from blockchain import vera_ledger
import datetime
import random
import hashlib

st.set_page_config(page_title="VeraChain", layout="wide", page_icon="🛡️")

# Professional Dark Theme
st.markdown("""
<style>
    .stApp { background-color: #0a0f1c; color: #e0e0ff; }
    .stButton>button { background: linear-gradient(90deg, #0066ff, #00ccff); color: white; border-radius: 10px; font-weight: bold; height: 3em; }
    .success { color: #00ff9d; }
    .kyc-box { background-color: #1a2338; padding: 20px; border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

# Session State
if 'kyc_completed' not in st.session_state:
    st.session_state.kyc_completed = False
if 'company_name' not in st.session_state:
    st.session_state.company_name = None
if 'manufacturer_id' not in st.session_state:
    st.session_state.manufacturer_id = None
if 'is_demo_user' not in st.session_state:
    st.session_state.is_demo_user = False

st.title("🛡️ VeraChain - Manufacturer Onboarding & Portal")
st.markdown("**Supply Chain Integrity & Brand Protection using Blockchain + Computer Vision**")

# ==================== KYC ONBOARDING SCREEN ====================
if not st.session_state.kyc_completed:
    st.subheader("Step 1: Manufacturer KYC / KYB Verification")
    st.info("Only manufacturers who complete KYC can register products on the immutable blockchain.")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("#### I am a Manufacturer")
        with st.form("kyc_form"):
            st.markdown('<div class="kyc-box">', unsafe_allow_html=True)

            company_name = st.text_input("Company / Brand Name *", placeholder="e.g., Rolex India Pvt Ltd")
            gstin = st.text_input("GSTIN *", placeholder="29AAACC1234B1Z5")
            pan = st.text_input("PAN Number *", placeholder="AAACC1234B")
            director_name = st.text_input("Authorized Director / Signatory Name")
            email = st.text_input("Official Company Email")

            st.markdown("**Upload KYC Documents** (simulated)")
            uploaded = st.file_uploader("GST Certificate, PAN Card, Incorporation Certificate, etc.",
                                        type=["pdf", "jpg", "png"], accept_multiple_files=True)

            submit_kyc = st.form_submit_button("Submit KYC for Verification")

            if submit_kyc:
                if company_name and gstin and pan:
                    st.session_state.company_name = company_name
                    st.session_state.manufacturer_id = hashlib.sha256(company_name.encode()).hexdigest()[:12].upper()
                    st.session_state.kyc_completed = True
                    st.success(f"✅ KYC Successfully Verified for **{company_name}**!")
                    st.rerun()
                else:
                    st.error("Please fill all mandatory fields (Company Name, GSTIN, PAN)")

            st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown("#### Demo / Testing Mode")
        st.info("Not a manufacturer? Use this for quick demonstration.")

        demo_name = st.text_input("Enter your name / role", value="SaiTejasvi")

        if st.button("🎯 Give me Demo Exception → Skip KYC"):
            st.session_state.company_name = f"DEMO - {demo_name}"
            st.session_state.manufacturer_id = "DEMO-" + hashlib.sha256(demo_name.encode()).hexdigest()[:8].upper()
            st.session_state.kyc_completed = True
            st.session_state.is_demo_user = True
            st.success(f"✅ Demo access granted as **{st.session_state.company_name}**")
            st.rerun()

    st.caption(
        "In real production: KYC documents would be verified against official government portals + manual approval.")
    st.stop()  # Stop until KYC or Demo is completed

# ==================== MAIN PRODUCT PORTAL (After KYC) ====================
status = "✅ KYC Approved" if not st.session_state.is_demo_user else "🧪 Demo Mode (KYC Bypassed)"
st.success(
    f"{status} | Company: **{st.session_state.company_name}** | Manufacturer ID: {st.session_state.manufacturer_id}")

st.markdown("### Product Registration Portal (Blockchain Extension)")

tab1, tab2, tab3 = st.tabs(["Register Products", "Live Ledger", "Analytics & Security"])

with tab1:
    st.subheader("Register Authentic Products")

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🚀 Load 50 Realistic Sample Products"):
            sample_products = []
            base_brand = st.session_state.company_name.split()[
                0] if "DEMO" not in st.session_state.company_name else "Rolex"
            brands = [base_brand, "Cipla", "Apple", "Nike", "Samsung", "Pfizer", "Omega"]
            categories = ["Luxury", "Pharma", "Electronics", "Apparel"]

            for i in range(50):
                brand = random.choice(brands)
                cat = random.choice(categories)
                pid = f"{brand.upper()}-{random.randint(1000, 9999)}-{random.choice(['V', 'X', 'B'])}{random.randint(2025, 2027)}"
                signature = hashlib.sha256(
                    f"{pid}{st.session_state.manufacturer_id}{datetime.datetime.now()}".encode()).hexdigest()[:16]

                sample_products.append({
                    'product_id': pid,
                    'manufacturer': brand,
                    'category': cat,
                    'mfg_date': str(datetime.date.today()),
                    'registered_by': st.session_state.company_name,
                    'manufacturer_id': st.session_state.manufacturer_id,
                    'digital_signature': signature
                })

            prev_hash = vera_ledger.chain[-1]['hash'] if vera_ledger.chain else '0'
            vera_ledger.create_block(sample_products, prev_hash)
            st.success(f"✅ 50 sample products registered with digital signatures!")
            st.rerun()

    with col_b:
        with st.form("single_product"):
            pid = st.text_input("Product ID", placeholder="ROLEX-V2026").strip().upper()
            brand = st.text_input("Brand Name", value=st.session_state.company_name.split()[
                0] if not st.session_state.is_demo_user else "Rolex")
            category = st.selectbox("Category", ["Luxury", "Pharma", "Electronics", "Apparel"])
            mfg_date = st.date_input("Manufacturing Date", datetime.date.today())

            if st.form_submit_button("Register on Blockchain"):
                if pid and brand:
                    signature = hashlib.sha256(
                        f"{pid}{st.session_state.manufacturer_id}{datetime.datetime.now()}".encode()).hexdigest()[:16]
                    product = {
                        'product_id': pid,
                        'manufacturer': brand,
                        'category': category,
                        'mfg_date': str(mfg_date),
                        'registered_by': st.session_state.company_name,
                        'manufacturer_id': st.session_state.manufacturer_id,
                        'digital_signature': signature
                    }
                    prev_hash = vera_ledger.chain[-1]['hash'] if vera_ledger.chain else '0'
                    vera_ledger.create_block([product], prev_hash)
                    st.success(f"✅ {pid} registered successfully!")

with tab2:
    st.subheader("🔗 Live Blockchain Ledger")
    if st.button("Validate Blockchain Integrity"):
        if vera_ledger.validate_chain():
            st.success("✅ Blockchain is intact and tamper-proof!")
        else:
            st.error("❌ Chain validation failed!")

    vera_ledger.load_from_db()
    if vera_ledger.chain:
        data = []
        for block in reversed(vera_ledger.chain):
            for p in block.get('products', []):
                data.append({
                    "Timestamp": block['timestamp'],
                    "Product ID": p.get('product_id'),
                    "Brand": p.get('manufacturer'),
                    "Category": p.get('category'),
                    "Mfg Date": p.get('mfg_date'),
                    "Registered By": p.get('registered_by'),
                    "Manufacturer ID": p.get('manufacturer_id'),
                    "Digital Signature": p.get('digital_signature', '')[:12] + "..."
                })
        st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)

        with st.expander("👨‍💻 View Raw JSON (Technical Proof)"):
            st.json(vera_ledger.chain)
    else:
        st.info("No products registered yet.")

with tab3:
    st.subheader("Analytics & Security")
    total_products = sum(len(block.get('products', [])) for block in vera_ledger.chain)
    st.metric("Total Products Registered", total_products)
    st.metric("Blocks in Ledger", len(vera_ledger.chain))
    st.metric("Mock Verifications", random.randint(680, 3850))

    st.markdown("#### Security Features")
    st.write("• Full KYC / KYB Verification")
    st.write("• Digital Signature on every product")
    st.write("• Immutable Blockchain with hash linking")
    st.write("• Complete audit trail")
    st.caption("**Roadmap**: Real Polygon blockchain integration with ECDSA signatures using Web3.py")

st.caption("VeraChain • Multimodal Authentication (CV + Blockchain) • SeedBrains 2026")
