import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from filters import full_pipeline
from scipy.signal import find_peaks

def plot_raw_vs_filtered(trial_num, fs=533):
    # Load data
    filepath = f'../results/experiment_1/resting_trial_{trial_num}.csv'
    df = pd.read_csv(filepath)
    raw = df['ecg_value'].values.astype(float)
    timestamps = df['timestamp'].values

    # Skip first 2 seconds
    skip = int(2 * fs)
    raw = raw[skip:]
    timestamps = timestamps[skip:]

    # Clip outliers
    raw = np.clip(raw, np.percentile(raw, 1), np.percentile(raw, 99))

    # Invert signal
    raw = -raw

    # Filter
    filtered = full_pipeline(raw, fs=fs)

    # Detect peaks
    min_distance = int(0.6 * fs)
    threshold = np.median(filtered) + 0.5 * np.std(filtered)
    peaks, _ = find_peaks(filtered, distance=min_distance, height=threshold)

    # Plot first 10 seconds
    samples = fs * 10
    t = timestamps[:samples]
    raw_plot = raw[:samples]
    filtered_plot = filtered[:samples]
    peaks_in_window = peaks[peaks < samples]

    fig, axes = plt.subplots(2, 1, figsize=(14, 8))

    # Raw signal
    axes[0].plot(t, raw_plot, color='gray', linewidth=0.8, label='Raw Signal')
    axes[0].set_title(f'Trial {trial_num} — Raw Signal (Unfiltered)')
    axes[0].set_ylabel('ADC Value')
    axes[0].grid(True)
    axes[0].legend()

    # Filtered signal with peaks
    axes[1].plot(t, filtered_plot, color='green', linewidth=0.8, label='Filtered Signal')
    if len(peaks_in_window) > 0:
        axes[1].plot(
            timestamps[peaks_in_window],
            filtered[peaks_in_window],
            'rv', markersize=10, label='R-peaks'
        )
    axes[1].set_title(f'Trial {trial_num} — Filtered Signal with R-Peak Detection')
    axes[1].set_ylabel('ADC Value')
    axes[1].set_xlabel('Time (seconds)')
    axes[1].grid(True)
    axes[1].legend()

    plt.suptitle(f'Resting Trial {trial_num} — Raw vs Filtered Comparison',
                fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(f'../results/experiment_1/raw_vs_filtered_trial_{trial_num}.png', dpi=150)
    print(f"Trial {trial_num} plot saved")
    plt.show()

def main():
    print("Generating raw vs filtered plots for all 5 trials...")
    for trial in range(1, 6):
        try:
            plot_raw_vs_filtered(trial)
            print(f"Trial {trial} complete")
        except Exception as e:
            print(f"Trial {trial} error: {e}")
    print("\nAll plots saved to results/experiment_1/")

if __name__ == "__main__":
    main()