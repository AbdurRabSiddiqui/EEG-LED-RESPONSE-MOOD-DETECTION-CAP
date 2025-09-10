## Mood Cap: Real‑Time EEG Mood Detection with LED Feedback

A wearable system that reads EEG signals with an OpenBCI Cyton board, classifies the user’s mental state (Calm, Stressed, Focused) in real time using Python, and visualizes the result on a WS2812B LED strip driven by an Arduino Nano.

### 1) Introduction

The goal of this project is to design and build a wearable "Mood Cap" that detects a user’s mental state through EEG signals and displays the result via an LED strip. Using the OpenBCI Cyton board, a Python program, and an Arduino Nano, the system streams brain activity, performs basic signal processing and classification, and provides immediate visual feedback.

Objectives achieved:

- Acquire EEG data through non‑invasive electrodes
- Process and classify the signals into distinct mood states
- Calibrate per user to reduce ambiguity
- Provide real‑time visual feedback through an LED strip
- Integrate into a functional, wearable prototype

### 2) Hardware Setup

- OpenBCI Cyton board with six electrodes:
  - 1 reference on earlobe, 1 ground on forehead
  - 4 acquisition electrodes: 2 on the forehead, 2 above the ears (10–20 alignment)
- Laptop running the Python classifier
- Arduino Nano controlling a WS2812B LED strip mounted to the cap
- Safety helmet’s adjustable inner suspension used for electrode stability and LED mounting
- Cyton battery and Arduino placed in a small enclosure; laptop for control

LED mapping:

- Color coding on Arduino: Blue = Calm, Red = Stressed, Green = Focused, White = idle/no data

### 3) Software Overview

This repo contains:

- `livecyton.py` — Python real‑time EEG processing and mood classification, sends result over serial
- `sketch_jul16a.ino` — Arduino sketch to receive mood labels and drive the LED strip via FastLED

Python key features:

- Live stream from Cyton via BrainFlow
- 10‑second calibration to build user‑specific baseline
- Per‑second analysis window with band‑pass filtering and bandpower features (alpha/beta)
- Simple rules relative to baseline for Calm/Focused/Stressed
- Majority vote across channels; result sent to Arduino

Arduino key features:

- Receives newline‑terminated labels over serial
- Maps mood label to solid LED color
- Fallback to White if no updates received within 2 seconds

### 4) Python Code Logic (Explained)

The Python pipeline in `livecyton.py`:

1. Configuration

   - `channel_count = 2` (first two EEG channels analyzed)
   - `sampling_rate = 250`, `window_duration = 1s`, `baseline_window = 10s`
   - `arduino_port`, `arduino_baudrate` for serial to Arduino
   - `cyton_port`, `board_id` for BrainFlow/Cyton

2. Signal Processing Helpers

   - `bandpass_filter(signal, fs, low=1.0, high=50.0)`
     - 4th‑order Butterworth band‑pass (1–50 Hz) with `filtfilt` to remove phase distortion
   - `compute_band_power(signal, fs, band)`
     - Welch PSD; integrates power in a frequency band using `np.trapz`
   - `detect_mood(alpha, beta, base_alpha, base_beta)`
     - Compute ratios vs baseline: `alpha_ratio = alpha/base_alpha`, `beta_ratio = beta/base_beta`
     - Rules:
       - If `beta_ratio > 1.5` and `beta > alpha` → `FOCUSED`
       - Else if `alpha_ratio > 1.5` and `alpha > beta` → `CALM`
       - Else → `STRESSED`

3. Session Setup

   - Initialize BrainFlow with `cyton_port` and start stream
   - Open serial connection to Arduino and wait 2s for reset

4. Baseline (Calibration) — 10 seconds

   - Every `window_duration` (1s), pull latest `window_size` samples
   - For each of the first `channel_count` EEG channels:
     - Filter: band‑pass 1–50 Hz
     - Compute band powers: alpha (8–13 Hz), beta (13–30 Hz)
   - Average all alpha and beta values across the calibration window to form `baseline_alpha` and `baseline_beta`

5. Real‑Time Loop (every second)

   - Pull latest 1‑second buffer from Cyton
   - For each analyzed channel:
     - Filter → compute alpha/beta powers → classify with `detect_mood`
   - Majority vote across channels for the second’s label
   - Print label to console and send newline‑terminated label to Arduino over serial

6. Shutdown & Safety
   - Gracefully stop BrainFlow stream and close serial on KeyboardInterrupt or error

Trade‑offs/Notes:

- The rule‑based classifier is intentionally simple and interpretable; it is not a medical device
- Baseline ratioing mitigates inter‑subject variability but is sensitive to electrode placement and artifacts
- Filtering 1–50 Hz removes DC drift and high‑frequency noise; consider notch filtering (50/60 Hz) if needed

### 5) Arduino Logic (Explained)

The Arduino sketch (`sketch_jul16a.ino`) uses FastLED:

- On setup: initialize Serial (115200), FastLED, set default color to White
- Loop:
  - When a line is available on Serial, read and normalize the label (`CALM`, `FOCUSED`, `STRESSED`)
  - Call `showMood` to map to color: Blue/Green/Red respectively; unknown → Purple
  - If no new label arrives for `TIMEOUT_MS` (2s), revert LEDs to White to indicate idle/no data

### 6) Getting Started

Prerequisites

- Python 3.9+
- OpenBCI Cyton board
- Arduino Nano (or compatible) + WS2812B LED strip
- Python packages: `numpy`, `scipy`, `brainflow`, `pyserial`
- Arduino libraries: `FastLED`

Install Python dependencies

```bash
pip install numpy scipy brainflow pyserial
# or
pip3 install numpy scipy brainflow pyserial
```

Note: BrainFlow may require platform‑specific setup (drivers/permissions). Refer to BrainFlow docs for your OS.

Flash the Arduino

1. Open `sketch_jul16a.ino` in Arduino IDE
2. Install the FastLED library (Library Manager)
3. Set the correct board and port
4. Upload

Configure serial ports in Python

- Edit `livecyton.py`:
  - `arduino_port = '/dev/...'` (your Arduino serial port)
  - `cyton_port = '/dev/...'` (your Cyton serial port)

Run the Python script

```bash
python livecyton.py
```

Expected behavior

- First ~10 seconds: building baseline (keep still, relax face to reduce EMG)
- Then per‑second labels print in the terminal and LEDs change color accordingly

### 7) Parameters You Can Tweak

- Python (`livecyton.py`):
  - `channel_count` — number of EEG channels analyzed (defaults to 2)
  - `sampling_rate`, `window_duration`, `baseline_window` — timing and buffer sizes
  - Filter band: 1–50 Hz; bandpower bands: alpha (8–13), beta (13–30)
  - Detection thresholds in `detect_mood` (e.g., ratio > 1.5)
- Arduino (`sketch_jul16a.ino`):
  - `NUM_LEDS`, `BRIGHTNESS`, `LED_PIN` (default D6), `TIMEOUT_MS`

### 8) Results

The final system processes EEG in real time, uses a 10‑second calibration to stabilize classification, and drives a smooth LED response. The helmet insert provides stable electrode contact; the LED strip offers intuitive visual feedback.

### 9) Future Improvements (since hardware is already avaible)

- Expand beyond mood detection: sleep staging, attention tracking, epilepsy event detection
- Dedicated app (desktop/mobile) with per‑electrode visualization (e.g., 3D brain model)
- Advanced ML models for multi‑class emotional states
- Wireless comms, more channels, robust artifact rejection (blink/muscle)
- Configurable notch filter; automated channel quality checks

### 10) Safety & Disclaimer

- This project is for research/education; not a medical device nor diagnostic tool
- Ensure proper electrode hygiene and safe battery/insulation practices

### 11) Repository Structure

```
.
├─ livecyton.py        # Real‑time EEG processing & classification (Python)
├─ sketch_jul16a.ino   # Arduino + FastLED visualization
└─ README.md           # Documentation
```

### 12) License

This project is released under the MIT License. See `LICENSE` for details.
# EEG-LED-RESPONSE-MOOD-DETECTION-CAP
