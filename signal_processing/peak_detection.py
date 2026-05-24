import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from filters import full_pipeline
import matplotlib.pyplot as plt

def detect_r_peaks(filtered_signal, fs=533):
    min_distance = int(0.6 * fs)
    threshold = np.median(filtered_signal) + 0.5 * np.std(filtered_signal)
    peaks, _ = find_peaks(filtered_signal, distance=min_distance, height=threshold)
    return peaks

def calculate_bpm(peaks, fs=533):
    if len(peaks) < 2:
        return 0
    rr_intervals = np.diff(peaks) / fs
    return round(60 / np.mean(rr_intervals), 1)

def compute_hrv(peaks, fs=533):
    if len(peaks) < 3:
        return None
    rr = np.diff(peaks) / fs * 1000
    return {'SDNN_ms': round(np.std(rr), 2), 'RMSSD_ms': round(np.sqrt(np.mean(np.diff(rr)**2)), 2), 'mean_RR_ms': round(np.mean(rr), 2), 'num_beats': len(peaks)}
def plot_single_beat(filtered, peaks, timestamps, fs=533):
    if len(peaks) < 3:
        return
    center_peak = peaks[len(peaks)//2]
    start = center_peak - int(0.3 * fs)
    end = center_peak + int(0.5 * fs)
    if start < 0 or end > len(filtered):
        return
    t = timestamps[start:end]
    f = filtered[start:end]
    t_relative = t - t[0]
    r_peak_time = t_relative[int(0.3 * fs)]
    plt.figure(figsize=(10, 5))
    plt.plot(t_relative, f, color='blue', linewidth=1.5)
    plt.axvline(x=r_peak_time, color='red', linestyle='--', alpha=0.5, label='R-peak')
    plt.annotate('R', xy=(r_peak_time, f[int(0.3*fs)]),
                xytext=(r_peak_time+0.02, f[int(0.3*fs)]+10),
                fontsize=12, color='red')
    plt.title('Single Heartbeat — PQRST Wave Analysis')
    plt.xlabel('Time (seconds)')
    plt.ylabel('ADC Value')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('../results/experiment_1/single_beat_pqrst.png', dpi=150)
    print("Single beat plot saved to results/experiment_1/single_beat_pqrst.png")
    plt.show()
def main():
    df = pd.read_csv('../results/experiment_1/exercise_trial_1.csv')
    raw = df['ecg_value'].values.astype(float)
    timestamps = df['timestamp'].values
    fs = 533
    skip_samples = int(2 * fs)
    raw = raw[skip_samples:]
    timestamps = timestamps[skip_samples:]
    raw = np.clip(raw, np.percentile(raw, 1), np.percentile(raw, 99))
    raw = -raw  # Invert signal — electrode polarity reversed
    raw = np.clip(raw, np.percentile(raw, 1), np.percentile(raw, 99))
    filtered = full_pipeline(raw, fs=fs)
    print(f"Min: {filtered.min():.3f} Max: {filtered.max():.3f} Std: {filtered.std():.3f}")
    peaks = detect_r_peaks(filtered, fs=fs)
    bpm = calculate_bpm(peaks, fs=fs)
    hrv = compute_hrv(peaks, fs=fs)
    print(f"Peaks: {len(peaks)} BPM: {bpm}")
    if hrv:
        print(f"SDNN: {hrv['SDNN_ms']}ms RMSSD: {hrv['RMSSD_ms']}ms")
    samples = fs * 10
    t = timestamps[:samples]
    f = filtered[:samples]
    peaks_in_window = peaks[peaks < samples]
    plt.figure(figsize=(14, 5))
    plt.plot(t, f, color='green', linewidth=0.8, label='Filtered ECG')
    if len(peaks_in_window) > 0:
        plt.plot(timestamps[peaks_in_window], filtered[peaks_in_window], 'rv', markersize=10, label='R-peaks')
    plt.title(f'BPM: {bpm}')
    plt.xlabel('Time (seconds)')
    plt.ylabel('ADC Value')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('../results/experiment_1/peak_detection.png', dpi=150)
    print("\nPlot saved to results/experiment_1/peak_detection.png")
    plt.show()
    plot_single_beat(filtered, peaks, timestamps, fs=fs)

if __name__ == "__main__":
    main()
