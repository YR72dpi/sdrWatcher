#!/usr/bin/env python3
import subprocess
import numpy as np
import time
from recording import launchRecord
from config import *

# =======================
# Fonctions
# =======================
def launch_rtl_fm(freq, sample_rate, gain, squelch):
    """Lance rtl_fm et retourne le processus"""
    cmd = [
        "rtl_fm",
        "-f", freq,
        "-M", "nfm",
        "-s", str(sample_rate),
        "-g", str(gain),
        "-l", str(squelch)
    ]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE)


def read_samples(proc, window_size):
    """Lit WINDOW_SIZE échantillons depuis rtl_fm"""
    raw = proc.stdout.read(window_size * 2)
    if len(raw) < window_size * 2:
        return None
    return np.frombuffer(raw, dtype=np.int16)


def compute_magnitude(samples, sample_rate):
    """Calcule la magnitude du signal autour de 1750 Hz"""
    fft_vals = np.fft.fft(samples * np.hanning(len(samples)))
    fft_freqs = np.fft.fftfreq(len(samples), 1/sample_rate)
    idx = np.where((fft_freqs >= 1745) & (fft_freqs <= 1755))[0]
    return np.mean(np.abs(fft_vals[idx]))


def detect_tone(history, magnitude, threshold, blocks):
    """Ajoute la magnitude à l'historique et vérifie le seuil lissé"""
    history.append(magnitude)
    if len(history) > blocks:
        history.pop(0)
    return np.mean(history) > threshold

def stopListening(proc):
    proc.terminate()
    proc.wait()

def main():
    proc = launch_rtl_fm(FREQ, SAMPLE_RATE, GAIN, SQUELCH)
    history = []
    keep_waiting = True

    try:
        while True:
            samples = read_samples(proc, WINDOW_SIZE)
            if samples is None:
                continue

            magnitude = compute_magnitude(samples, SAMPLE_RATE)
            if magnitude > 0:
                print(f"~~ Fréquence active {magnitude}~~")
                
            if detect_tone(history, magnitude, THRESHOLD, BLOCKS):
                print(f"{time.strftime('%H:%M:%S')} 🔔 Ton 1750 Hz détecté !")
                stopListening(proc)
                launchRecord(FREQ)
                main()


    except KeyboardInterrupt:
        print("Arrêt manuel")
        stopListening(proc)

    finally:
        stopListening(proc)


if __name__ == "__main__":
    main()
