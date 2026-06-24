# ❤️ ECG Biosensor Platform

A low-cost, real-time ECG signal acquisition and analysis platform built from a SparkFun AD8232 and an Arduino Uno R4 Minima — designed, validated, and documented as an independent engineering research project.

> Built a $90.78 ECG biosensing platform that achieved 96.3% R-peak detection accuracy and identified a heart-rate-dependent performance limitation through multi-subject validation.

**🔗 Live Dashboard:** [ecg-biosensor.streamlit.app](https://ecg-biosensor.streamlit.app)
**📄 Manuscript:** Submitted to *Oxford Journal of Student Scholarship* (2026)

![ECG Biosensor Dashboard](./assets/dashboard_screenshot.png)

---

## Project Gallery

| | |
|---|---|
| **System Block Diagram** | **PCB Layout (KiCad, Rev A)** |
| ![Block Diagram](./assets/block_diagram.png) | ![PCB Layout](./assets/pcb_layout.png) |
| **Raw vs. Filtered Signal** | **Validation Against Apple Watch Series 8** |
| ![Signal Pipeline](./assets/signal_pipeline.png) | ![Validation Results](./assets/validation_results.png) |

---

## Overview

Standard clinical ECG systems cost $1,000–$10,000, placing cardiac monitoring out of reach for many people and resource-limited healthcare settings. This project investigates whether consumer-grade hardware, combined with carefully engineered signal processing, can produce physiologically meaningful cardiac metrics at a fraction of that cost.

**Total hardware cost: $90.78**

| Metric | Result |
|---|---|
| R-peak detection accuracy | 96.3% (N=5 trials) |
| Validated sampling rate | 533.3 Hz |
| Apple Watch agreement (stable conditions) | MAPE 3.51–4.10% |
| Apple Watch agreement (combined, N=25) | r=0.762, MAPE=9.30% |
| Subjects | N=6, 30 resting trials |

---

## Key Finding

The platform's accuracy is **strongly heart-rate-dependent**: subjects with resting heart rates above 90 BPM achieved sub-4.5% error against an Apple Watch Series 8 reference, while subjects below 85 BPM saw error rates exceed 16%. This pattern is consistent with a fixed amplitude threshold (`median + 0.5 × SD`) becoming more susceptible to baseline drift as the interval between true R-peaks grows — and it directly motivates the adaptive threshold work planned for Phase 2.

---

## System Architecture

```
Electrodes (Ag/AgCl)
        │
        ▼
  AD8232 Analog Front-End  ──►  Arduino Uno R4 Minima (14-bit ADC, 533.3 Hz)
        │                              │
        │                       USB Serial (115200 baud)
        ▼                              ▼
  Right-Leg Drive Circuit       Python Signal Pipeline
                                       │
                         ┌─────────────┼─────────────┐
                         ▼             ▼             ▼
                  Butterworth      IIR Notch     R-peak Detection
                  Bandpass         Filter        (adaptive threshold)
                  (0.5–40 Hz)      (60 Hz)              │
                         └─────────────┼─────────────┘
                                       ▼
                            HRV Metrics (SDNN, RMSSD)
                                       │
                                       ▼
                          Streamlit Real-Time Dashboard
```

---

## Repository Structure

```
ecg-biosensor/
├── dashboard/          Streamlit application (live ECG dashboard, CSV playback)
├── docs/               Block diagram, additional documentation
├── experiments/        Protocols for all three structured experiments
├── firmware/           Arduino acquisition code
├── hardware/           KiCad PCB + schematics, Gerber fabrication files
├── report/             Research manuscript and technical report
├── results/            Raw and processed ECG data, all subjects/trials
├── signal_processing/  Filter, peak-detection, and HRV scripts
├── LICENSE
└── README.md
```

---

## Hardware

| Component | Part | Cost |
|---|---|---|
| ECG analog front-end | SparkFun AD8232 (SEN-12650) | $24.41 |
| Microcontroller | Arduino Uno R4 Minima | $19.99 |
| Electrodes | Ag/AgCl, 100-pack | $15.30 |
| Electrode cable | CAB-12970 | $9.60 |
| Misc. (breadboard, headers, prep pads) | — | $21.48 |
| **Total** | | **$90.78** |

A custom 2-layer PCB (140 × 56.5 mm, FR-4, LeadFree HASL) was designed in KiCad following the AD8232 datasheet reference design. Fabrication files were submitted to JLCPCB; boards were received June 13, 2026. Assembly and Phase 2 validation are in progress. See [`hardware/`](./hardware) for the schematic, PCB layout, and Gerber files.

---

## Signal Processing Pipeline

1. **Bandpass filter** — 4th-order Butterworth, 0.5–40 Hz, zero-phase (`scipy.signal.filtfilt`)
2. **Notch filter** — IIR notch at 60 Hz (Q=30) to reject powerline interference
3. **R-peak detection** — adaptive amplitude threshold (`median + 0.5 × SD`), minimum 319-sample inter-peak distance
4. **HRV computation** — SDNN and RMSSD from the resulting RR-interval series

See [`signal_processing/`](./signal_processing) for the full implementation.

---

## Experiments

| # | Title | Protocol |
|---|---|---|
| 1 | Resting vs. Exercise vs. Recovery | 5 resting trials + 3 exercise blocks (Subject 2) |
| 2 | Electrode Placement Robustness | 4 placement conditions × 3 trials (Subject 2) |
| 3 | Filter Algorithm Comparison | 3 algorithms × 5 trials (Subject 2) |

Full protocols and results are in [`experiments/`](./experiments) and [`results/`](./results).

---

## Validation

BPM measurements were validated against simultaneous Apple Watch Series 8 recordings across 25 paired readings from five subjects. Apple Watch was selected as an accessible consumer benchmark rather than a clinical gold standard — agreement results should be interpreted as comparative consumer-device performance, not clinical validation.

| Subject | Avg Apple Watch BPM | Mean Bias | MAPE |
|---|---|---|---|
| 2 | 97.4 | +1.0 | 3.87% |
| 3 | 93.8 | +1.0 | 4.10% |
| 4 | 97.0 | +2.6 | 3.51% |
| 5 | 72.0 | +12.0 | 16.72% |
| 6 | 80.2 | +14.6 | 18.28% |

---

## Future Work

- Adaptive, time-decaying threshold envelope to correct the heart-rate-dependent bias
- PCB assembly and Phase 2 experimental validation
- Extended multi-subject study (N ≥ 20)
- Benchmarking against a clinical-grade ECG or Holter monitor
- Bluetooth wireless data acquisition

---

## Phase 2 — Hardware Assembly (In Progress)

Custom PCB (Rev A) received from JLCPCB on June 13, 2026.

| Bare PCB | Shipment Packaging |
|---|---|
| ![PCB](./hardware/pcb_renders/board_photo.png) | ![Packaging](./hardware/pcb_renders/board_arrival.png) |

Assembly and Phase 2 validation against the breadboard prototype are in progress.

---

## Running the Dashboard Locally

```bash
git clone https://github.com/shrimaan-rapuru/ECG-BIOSENSOR.git
cd ECG-BIOSENSOR/dashboard
pip install -r requirements.txt
streamlit run ecg_dashboard_demo.py
```

The hosted version at [ecg-biosensor.streamlit.app](https://ecg-biosensor.streamlit.app) runs in CSV playback mode and requires no hardware.

---

## Ethics Statement

This platform is intended solely for educational and engineering research purposes. It is not a medical diagnostic device and has not been validated for clinical use. All participants were anonymized as Subjects 2–7; no identifying health data is disclosed. Participation was voluntary with informed consent obtained prior to data collection.

---

## Author

**Shrimaan Rapuru**
The Early College at Guilford, Greensboro, NC

## License

MIT License — see [LICENSE](./LICENSE) for details.
