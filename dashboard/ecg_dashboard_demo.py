import streamlit as st
import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt, iirnotch, find_peaks
import plotly.graph_objects as go

st.set_page_config(
    page_title="ECG Biosensor Platform Demo",
    page_icon="❤️",
    layout="wide"
)

st.markdown("""
<style>
    .bpm-display { font-size: 72px; font-weight: bold; color: #e74c3c; text-align: center; }
    .hrv-display { font-size: 38px; font-weight: bold; color: #2ecc71; text-align: center; }
    .metric-label { font-size: 16px; color: #888888; text-align: center; }
    .disclaimer { font-size: 13px; color: #cc0000; text-align: center; font-style: italic; }
</style>
""", unsafe_allow_html=True)

def butter_bandpass(data, lowcut=0.5, highcut=40.0, fs=533, order=4):
    nyq = 0.5 * fs
    b, a = butter(order, [lowcut/nyq, highcut/nyq], btype='band')
    return filtfilt(b, a, data)

def notch_filter(data, freq=60.0, fs=533, Q=30):
    nyq = 0.5 * fs
    b, a = iirnotch(freq/nyq, Q)
    return filtfilt(b, a, data)

def full_pipeline(data, fs=533):
    return notch_filter(butter_bandpass(data, fs=fs), fs=fs)

def detect_peaks(filtered, fs=533):
    if len(filtered) < int(fs * 2):
        return np.array([])
    peaks, _ = find_peaks(filtered,
                          distance=int(0.6 * fs),
                          height=np.median(filtered) + 0.5 * np.std(filtered))
    return peaks

def calculate_bpm(peaks, fs=533):
    if len(peaks) < 2:
        return 0.0
    return round(60 / np.mean(np.diff(peaks) / fs), 1)

def calculate_hrv(peaks, fs=533):
    if len(peaks) < 3:
        return 0.0, 0.0
    rr = np.diff(peaks) / fs * 1000
    return round(np.std(rr), 2), round(np.sqrt(np.mean(np.diff(rr)**2)), 2)

@st.cache_data
def load_ecg_data():
    url = "https://raw.githubusercontent.com/shrimaan-rapuru/ECG-BIOSENSOR/master/results/experiment_1/resting_trial_3.csv"
    try:
        df = pd.read_csv(url)
        raw = df['ecg_value'].values.astype(float)
        timestamps = df['timestamp'].values
        skip = int(2 * 533)
        raw = raw[skip:]
        timestamps = np.arange(len(raw)) / 533.0
        raw = np.clip(raw, np.percentile(raw, 1), np.percentile(raw, 99))
        return -raw, timestamps
    except Exception as e:
        st.error(f"Could not load data: {e}")
        return None, None

# ── SIDEBAR ──
st.sidebar.title("⚙️ Settings")
st.sidebar.markdown("**Demo Mode** — CSV Playback")
st.sidebar.markdown("*Resting Trial 3, Subject 2*")
st.sidebar.markdown("---")
window_size = st.sidebar.slider("Display Window (seconds)", 5, 28, 10)
show_raw = st.sidebar.checkbox("Show Raw Signal", value=False)
st.sidebar.markdown("---")
st.sidebar.markdown("**Filter Settings:**")
st.sidebar.markdown("- Butterworth Bandpass: 0.5-40 Hz")
st.sidebar.markdown("- IIR Notch: 60 Hz (Q=30)")
st.sidebar.markdown("- Order: 4 | Zero-phase (filtfilt)")
st.sidebar.markdown("---")
st.sidebar.markdown("**Hardware:**")
st.sidebar.markdown("- SparkFun AD8232")
st.sidebar.markdown("- Arduino Uno R4 Minima")
st.sidebar.markdown("- fs = 533.3 Hz (validated)")

# ── TITLE ──
st.title("❤️ Real-Time ECG Biosensor Platform")
st.markdown("**Low-Cost ECG Signal Acquisition & HRV Analysis | CSV Playback Demo**")
st.markdown("*Subject 2 | Resting Trial 3 | fs = 533.3 Hz | Butterworth Bandpass 0.5–40 Hz + IIR Notch 60 Hz*")

# ── LOAD DATA ──
raw, timestamps = load_ecg_data()
if raw is None:
    st.error("Could not load ECG data.")
    st.stop()

fs = 533
filtered = full_pipeline(raw, fs=fs)
peaks = detect_peaks(filtered, fs=fs)
bpm = calculate_bpm(peaks, fs=fs)
sdnn, rmssd = calculate_hrv(peaks, fs=fs)
total_samples = len(filtered)
samples_per_window = int(fs * window_size)

# ── METRICS ──
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown('<p class="metric-label">Heart Rate</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="bpm-display" style="color:{"#e74c3c" if bpm > 100 else "#2ecc71"}">{bpm}</p>', unsafe_allow_html=True)
    st.markdown('<p class="metric-label">BPM</p>', unsafe_allow_html=True)
with col2:
    st.markdown('<p class="metric-label">SDNN</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="hrv-display">{sdnn}</p>', unsafe_allow_html=True)
    st.markdown('<p class="metric-label">ms</p>', unsafe_allow_html=True)
with col3:
    st.markdown('<p class="metric-label">RMSSD</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="hrv-display">{rmssd}</p>', unsafe_allow_html=True)
    st.markdown('<p class="metric-label">ms</p>', unsafe_allow_html=True)
with col4:
    st.markdown('<p class="metric-label">Peaks Detected</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="hrv-display">{len(peaks)}</p>', unsafe_allow_html=True)
    st.markdown('<p class="metric-label">total</p>', unsafe_allow_html=True)

st.markdown("---")

# ── STATIC WAVEFORM (no blinking) ──
st.subheader("📈 ECG Waveform")

# Slider to scrub through the signal manually
position = st.slider(
    "Scrub through signal",
    min_value=0,
    max_value=max(0, total_samples - samples_per_window),
    value=0,
    step=int(fs * 0.5),
    format="%d samples"
)

start = position
end = min(start + samples_per_window, total_samples)

disp_filtered = filtered[start:end]
disp_times = timestamps[start:end]
disp_raw = raw[start:end]
peaks_in_window = peaks[(peaks >= start) & (peaks < end)] - start

fig = go.Figure()
if show_raw:
    raw_norm = (disp_raw - np.mean(disp_raw)) / (np.std(disp_raw) + 1e-8) * np.std(disp_filtered)
    fig.add_trace(go.Scatter(x=disp_times, y=raw_norm, mode='lines',
                             name='Raw Signal', line=dict(color='gray', width=1), opacity=0.5))
fig.add_trace(go.Scatter(x=disp_times, y=disp_filtered, mode='lines',
                         name='Filtered ECG', line=dict(color='#2ecc71', width=1.5)))
if len(peaks_in_window) > 0:
    fig.add_trace(go.Scatter(
        x=disp_times[peaks_in_window],
        y=disp_filtered[peaks_in_window],
        mode='markers', name='R-peaks',
        marker=dict(color='red', size=10, symbol='triangle-down')
    ))
fig.update_layout(
    height=380, showlegend=True,
    xaxis_title="Time (seconds)", yaxis_title="ADC Value",
    plot_bgcolor='#0e1117', paper_bgcolor='#0e1117',
    font=dict(color='white'),
    xaxis=dict(gridcolor='#333333'), yaxis=dict(gridcolor='#333333'),
    legend=dict(bgcolor='#1e2130', bordercolor='#333333'),
    margin=dict(l=60, r=20, t=20, b=60)
)
st.plotly_chart(fig, use_container_width=True)
st.progress(min(int((start / total_samples) * 100), 100))

st.markdown("---")

# ── FULL SIGNAL VIEW ──
with st.expander("📉 View Full Signal"):
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=timestamps, y=filtered, mode='lines',
        name='Full ECG', line=dict(color='#2ecc71', width=0.8)
    ))
    if len(peaks) > 0:
        fig2.add_trace(go.Scatter(
            x=timestamps[peaks], y=filtered[peaks],
            mode='markers', name='R-peaks',
            marker=dict(color='red', size=6, symbol='triangle-down')
        ))
    fig2.update_layout(
        height=250, showlegend=True,
        xaxis_title="Time (seconds)", yaxis_title="ADC Value",
        plot_bgcolor='#0e1117', paper_bgcolor='#0e1117',
        font=dict(color='white'),
        xaxis=dict(gridcolor='#333333'), yaxis=dict(gridcolor='#333333'),
        margin=dict(l=60, r=20, t=10, b=40)
    )
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# ── VALIDATION ──
st.subheader("📊 Validation Results")
col_v1, col_v2, col_v3 = st.columns(3)
with col_v1:
    st.metric("R-peak Accuracy", "96.3%", "N=5 trials")
with col_v2:
    st.metric("Apple Watch Agreement", "r = 0.893", "N=15 readings")
with col_v3:
    st.metric("MAPE (stable conditions)", "3.69%", "Subjects 2 & 4")

st.markdown("---")
st.markdown("""
<div style='text-align:center;color:gray;font-size:12px;'>
ECG Biosensor Platform — Shrimaan Rapuru | The Early College at Guilford | Summer 2026<br>
4th-order Butterworth Bandpass (0.5-40Hz) + IIR Notch (60Hz) | fs = 533.3Hz (validated)<br>
<a href='https://github.com/shrimaan-rapuru/ECG-BIOSENSOR' target='_blank'>github.com/shrimaan-rapuru/ECG-BIOSENSOR</a>
</div><br>
<p class="disclaimer">Not a medical device. For educational and research purposes only.</p>
""", unsafe_allow_html=True)
