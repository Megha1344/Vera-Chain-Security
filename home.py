import streamlit as st

st.set_page_config(
    page_title="VeraChain",
    page_icon="🛡️",
    layout="wide"
)

# Dark Theme
st.markdown("""
<style>
    .stApp { background-color: #0a0f1c; color: #e0e0ff; }
    .big-title { font-size: 4.8rem; font-weight: bold; text-align: center; margin-bottom: 0.5rem; }
    .subtitle { font-size: 1.6rem; text-align: center; color: #88aaff; margin-bottom: 3rem; }
    .card {
        background-color: #1a2338;
        padding: 2.5rem;
        border-radius: 16px;
        text-align: center;
        transition: transform 0.3s;
    }
    .card:hover { transform: scale(1.05); }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="big-title">🛡️ VERA CHAIN</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Veracity + Blockchain = Trust You Can Verify</p>', unsafe_allow_html=True)

st.markdown("### Choose Your Role")

col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🏭 Manufacturer Portal")
    st.write("KYC Verification • Product Registration • Immutable Ledger")
    if st.button("🚀 Go to Manufacturer Portal", use_container_width=True, type="primary"):
        st.switch_page("pages/1_Manufacturer.py")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🔍 Consumer Portal")
    st.write("Live Camera • Photo Upload • Logo Detection • Blockchain Check")
    if st.button("🔍 Go to Consumer Portal", use_container_width=True, type="primary"):
        st.switch_page("pages/2_Consumer.py")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")
st.caption("VeraChain • Multimodal Authentication (Computer Vision + Blockchain) • SeedBrains 2026")
