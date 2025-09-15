#!/usr/bin/env python3
import subprocess
import numpy as np
import time
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import *


# Paramètres
DURATION = 5  # secondes pour mesurer le bruit ambiant

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
    "-g", str(GAIN)
]
proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)

magnitudes = []
start_time = time.time()

try:
    while time.time() - start_time < DURATION:
        raw = proc.stdout.read(WINDOW_SIZE * 2)
        if len(raw) < WINDOW_SIZE * 2:
            continue
        samples = np.frombuffer(raw, dtype=np.int16)
        mag = compute_magnitude(samples, SAMPLE_RATE)
        magnitudes.append(mag)

except KeyboardInterrupt:
    print("Arrêt manuel")

finally:
    proc.terminate()
    proc.wait()

# Calcul du seuil ambiant
avg_noise = np.mean(magnitudes)
std_noise = np.std(magnitudes)
threshold_estimate = avg_noise + 3 * std_noise  # seuil = bruit moyen + 3 sigma
# Min et max
min_mag = np.min(magnitudes)
max_mag = np.max(magnitudes)

print(f"📊 Magnitude moyenne bruit: {avg_noise:.2f}")
print(f"📊 Écart-type bruit: {std_noise:.2f}")
print(f"✅ Seuil recommandé: {threshold_estimate:.2f}")
print(f"📉 Magnitude minimale bruit: {min_mag:.2f}")
print(f"📈 Magnitude maximale bruit: {max_mag:.2f}")