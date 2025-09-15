#!/usr/bin/env python3
import subprocess
import numpy as np
import time

# Paramètres
FREQ = "147.90500M"
SAMPLE_RATE = 22050
WINDOW_SIZE = 2048
GAIN = 32.8
BLOCKS_PER_SECOND = SAMPLE_RATE // WINDOW_SIZE  # approx. number of FFT blocks per second
SQUELSH = 20

def compute_magnitude(samples, sample_rate):
    fft_vals = np.fft.fft(samples * np.hanning(len(samples)))
    fft_freqs = np.fft.fftfreq(len(samples), 1/sample_rate)
    idx = np.where((fft_freqs >= 1745) & (fft_freqs <= 1755))[0]
    return np.mean(np.abs(fft_vals[idx]))

# Lancer rtl_fm
cmd = [
    "rtl_fm",
    "-f", FREQ,
    "-M", "nfm",
    "-s", str(SAMPLE_RATE),
    "-g", str(GAIN),
    #"-l", str(SQUELSH)
]
proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)

try:
    while True:
        mags = []
        for _ in range(BLOCKS_PER_SECOND):
            raw = proc.stdout.read(WINDOW_SIZE * 2)
            if len(raw) < WINDOW_SIZE * 2:
                continue
            samples = np.frombuffer(raw, dtype=np.int16)
            mags.append(compute_magnitude(samples, SAMPLE_RATE))
        avg_mag = np.mean(mags)
        print(f"{time.strftime('%H:%M:%S')} | Magnitude 1750Hz: {avg_mag:.2f}")

except KeyboardInterrupt:
    print("\nArrêt manuel")
    proc.terminate()
    proc.wait()
