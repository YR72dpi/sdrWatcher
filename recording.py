#!/usr/bin/env python3
import subprocess
import numpy as np
import wave
import time
import os
from config import *

def compute_magnitude(samples, sample_rate):
    """Calcule la magnitude du signal autour de 1750 Hz"""
    fft_vals = np.fft.fft(samples * np.hanning(len(samples)))
    fft_freqs = np.fft.fftfreq(len(samples), 1/sample_rate)
    idx = np.where((fft_freqs >= 1745) & (fft_freqs <= 1755))[0]
    return np.mean(np.abs(fft_vals[idx]))


def launchRecord(freq):
    """Enregistre la communication après le 1750 Hz"""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_raw = f"comm_{timestamp}.raw"
    output_wav = f"comm_{timestamp}.wav"

    cmd = [
        "rtl_fm",
        "-f", freq,
        "-M", "nfm",
        "-s", str(SAMPLE_RATE),
        "-g", str(GAIN),
        # "-l", str(SQUELCH)
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)

    history = []
    silence_count = 0

    print(f"{time.strftime('%H:%M:%S')} ⏺ Début enregistrement RAW")

    with open(output_raw, "wb") as f:
        try:
            while True:
                raw = proc.stdout.read(WINDOW_SIZE * 2)
                if len(raw) < WINDOW_SIZE * 2:
                    continue

                samples = np.frombuffer(raw, dtype=np.int16)
                f.write(raw)

                # Magnitude pour vérifier la fin de communication
                mag = compute_magnitude(samples, SAMPLE_RATE)
                history.append(mag)
                if len(history) > BLOCKS:
                    history.pop(0)
                avg_mag = np.mean(history)
                
                print(f"Magnitude : {avg_mag:.2f}")

                if THRESHOLD_SILENCE_MIN < avg_mag < THRESHOLD_SILENCE_MAX:
                    silence_count += 1
                    if silence_count > MAX_SILENCE_BLOCKS:
                        print(f"{time.strftime('%H:%M:%S')} ⏹ Fin de communication détectée")
                        proc.terminate()
                        proc.wait()
                        break
                else:
                    silence_count = 0

        except KeyboardInterrupt:
            print("Arrêt manuel")
        finally:
            proc.terminate()
            proc.wait()

    # Conversion RAW -> WAV
    print(f"{time.strftime('%H:%M:%S')} 🎵 Conversion RAW -> WAV : {output_wav}")
    with open(output_raw, "rb") as f:
        raw_data = f.read()
        samples = np.frombuffer(raw_data, dtype=np.int16)

    with wave.open(output_wav, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(samples.tobytes())

    # Supprimer le RAW
    os.remove(output_raw)
    print(f"{time.strftime('%H:%M:%S')} ✅ Enregistrement terminé : {output_wav}")
