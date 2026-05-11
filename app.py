import streamlit as st

st.set_page_config(
    page_title="ECG Biosensor Project | Shrimaan Rapuru",
    page_icon="🫀",
    layout="centered"
)

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .main {
        background-color: #0f1117;
    }

    .hero {
        text-align: center;
        padding: 3rem 1rem 2rem 1rem;
    }

    .badge {
        display: inline-block;
        background: linear-gradient(135deg, #ff4b4b22, #ff4b4b44);
        border: 1px solid #ff4b4b66;
        color: #ff4b4b;
        padding: 0.3rem 1rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 1.5rem;
    }

    .title {
        font-size: 2.8rem;
        font-weight: 700;
        color: #ffffff;
        line-height: 1.2;
        margin-bottom: 1rem;
    }

    .subtitle {
        font-size: 1.1rem;
        color: #8b8fa8;
        max-width: 520px;
        margin: 0 auto 2.5rem auto;
        line-height: 1.7;
    }

    .card {
        background: #1a1d2e;
        border: 1px solid #2a2d3e;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }

    .card-title {
        font-size: 0.75rem;
        font-weight: 600;
        color: #ff4b4b;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.5rem;
    }

    .card-body {
        font-size: 0.95rem;
        color: #c8cad8;
        line-height: 1.6;
    }

    .timeline {
        background: linear-gradient(135deg, #1a1d2e, #1e2235);
        border: 1px solid #2a2d3e;
        border-left: 3px solid #ff4b4b;
        border-radius: 0 12px 12px 0;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1rem;
    }

    .footer {
        text-align: center;
        padding: 2rem 0 1rem 0;
        color: #4a4d5e;
        font-size: 0.85rem;
    }

    .link {
        color: #ff4b4b;
        text-decoration: none;
    }

    .divider {
        border: none;
        border-top: 1px solid #2a2d3e;
        margin: 2rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Hero Section
st.markdown("""
<div class="hero">
    <div class="badge">🔬 Coming Summer 2026</div>
    <div class="title">ECG Biosensor<br>& Signal Analyzer</div>
    <div class="subtitle">
        A hardware-software project combining a custom-built ECG biosensor 
        with machine learning for real-time cardiac signal analysis and anomaly detection.
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# What I'm Building
st.markdown("### 🛠️ What I'm Building")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="card">
        <div class="card-title">Hardware</div>
        <div class="card-body">
            Custom ECG biosensor circuit with analog front-end, 
            signal conditioning, and microcontroller-based data acquisition.
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="card">
        <div class="card-title">Software & ML</div>
        <div class="card-body">
            Real-time signal processing pipeline with ML-based 
            anomaly detection and an interactive Streamlit dashboard.
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# Timeline
st.markdown("### 📅 Timeline")

st.markdown("""
<div class="timeline">
    <div class="card-title">Phase 1 — Hardware Design</div>
    <div class="card-body">Design and build ECG sensor circuit, test signal acquisition</div>
</div>
<div class="timeline">
    <div class="card-title">Phase 2 — Signal Processing</div>
    <div class="card-body">Build data pipeline, filter noise, extract features from ECG waveforms</div>
</div>
<div class="timeline">
    <div class="card-title">Phase 3 — ML Model</div>
    <div class="card-body">Train anomaly detection model on ECG signal data</div>
</div>
<div class="timeline">
    <div class="card-title">Phase 4 — Dashboard</div>
    <div class="card-body">Deploy interactive real-time visualization app — Summer 2026</div>
</div>
""", unsafe_allow_html=True)

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# About
st.markdown("### 👤 About Me")
st.markdown("""
<div class="card">
    <div class="card-body">
        I'm <strong style="color:#ffffff">Shrimaan Rapuru</strong>, a junior at The Early College at Guilford (4.0 GPA) 
        interested in embedded systems, signal processing, and building technology that works for people — not just in theory.<br><br>
        This project sits at the intersection of hardware and software — exactly where I want to work as an engineer.
        <br><br>
        <a class="link" href="https://us-ai-job-impact-predictor.streamlit.app/" target="_blank">🤖 US AI Job Impact Predictor</a> &nbsp;·&nbsp;
        <a class="link" href="https://scheduling-platform.streamlit.app/" target="_blank">📅 ODM Scheduling Platform</a> &nbsp;·&nbsp;
        <a class="link" href="https://linkedin.com/in/shrimaan-rapuru-439689329" target="_blank">LinkedIn</a> &nbsp;·&nbsp;
        <a class="link" href="https://github.com/shrimaan-rapuru" target="_blank">GitHub</a>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="footer">
    Built by Shrimaan Rapuru · Summer 2026
</div>
""", unsafe_allow_html=True)
