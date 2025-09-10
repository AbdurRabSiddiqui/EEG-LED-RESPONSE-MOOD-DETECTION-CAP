import time
from collections import Counter
import numpy as np
from scipy.signal import butter, filtfilt, welch
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
import serial

#CONFIG
channel_count = 2
sampling_rate = 250
window_duration = 1  # seconds
window_size = sampling_rate * window_duration
baseline_window = 10  # seconds to build baseline

arduino_port = '/dev/cu.usbmodem48CA432DA9D82'  # update to your Arduino port
arduino_baudrate = 115200

cyton_port = '/dev/cu.usbserial-DQ007UJG'  # update to your Cyton port
board_id = BoardIds.CYTON_BOARD.value

#SIGNAL PROCESSING
def bandpass_filter(signal, fs, low=1.0, high=50.0, order=4):
    b, a = butter(order, [low / (fs / 2), high / (fs / 2)], btype='band')
    return filtfilt(b, a, signal)

def compute_band_power(signal, fs, band):
    fmin, fmax = band
    freqs, psd = welch(signal, fs=fs, nperseg=256)
    idx = np.logical_and(freqs >= fmin, freqs <= fmax)
    return np.trapz(psd[idx], freqs[idx])

def detect_mood(alpha, beta, base_alpha, base_beta):
    # Relative change to baseline
    alpha_ratio = alpha / (base_alpha + 1e-6)
    beta_ratio = beta / (base_beta + 1e-6)

    if beta_ratio > 1.5 and beta > alpha:
        return 'FOCUSED'  # high beta, could be muscle contraction or concentration
    elif alpha_ratio > 1.5 and alpha > beta:
        return 'CALM'
    else:
        return 'STRESSED'

#SETUP
params = BrainFlowInputParams()
params.serial_port = cyton_port
board = BoardShim(board_id, params)

arduino = serial.Serial(arduino_port, arduino_baudrate)
time.sleep(2)  # allow Arduino to reset

try:
    board.prepare_session()
    board.start_stream()
    print("Building baseline for {} seconds...".format(baseline_window))

    alpha_values = []
    beta_values = []

    # Collect baseline
    start_time = time.time()
    while time.time() - start_time < baseline_window:
        time.sleep(window_duration)
        data = board.get_current_board_data(window_size)
        eeg_channels = BoardShim.get_eeg_channels(board_id)

        for ch_index in range(channel_count):
            raw_segment = data[eeg_channels[ch_index]]
            filtered = bandpass_filter(raw_segment, sampling_rate)
            alpha_values.append(compute_band_power(filtered, sampling_rate, (8, 13)))
            beta_values.append(compute_band_power(filtered, sampling_rate, (13, 30)))

    baseline_alpha = np.mean(alpha_values)
    baseline_beta = np.mean(beta_values)

    print("Baseline set: alpha={:.3f}, beta={:.3f}".format(baseline_alpha, baseline_beta))
    print("\nMood Detection Per Second:\n")

    #MAIN LOOP
    while True:
        time.sleep(window_duration)
        data = board.get_current_board_data(window_size)
        eeg_channels = BoardShim.get_eeg_channels(board_id)

        second_moods = []
        for ch_index in range(channel_count):
            raw_segment = data[eeg_channels[ch_index]]
            filtered = bandpass_filter(raw_segment, sampling_rate)
            alpha = compute_band_power(filtered, sampling_rate, (8, 13))
            beta = compute_band_power(filtered, sampling_rate, (13, 30))
            mood = detect_mood(alpha, beta, baseline_alpha, baseline_beta)
            second_moods.append(mood)

        common_mood = Counter(second_moods).most_common(1)[0][0]
        print(common_mood)

        # Send mood to Arduino
        arduino.write((common_mood + '\n').encode())

except KeyboardInterrupt:
    print("\nStopping mood detection...")

except Exception as e:
    print("Error:", e)

finally:
    try:
        board.stop_stream()
        board.release_session()
    except:
        pass
    arduino.close()
