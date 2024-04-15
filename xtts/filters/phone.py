#
# Basic phone sound effect
# Cuts <300Hz, >3kHz
#

import numpy as np
import wave
from scipy import signal


def filter(audio_path: str):
    # Read the audio file
    audio_file = wave.open(audio_path, 'rb')
    sample_rate = audio_file.getframerate()
    num_frames = audio_file.getnframes()
    samples = np.frombuffer(audio_file.readframes(num_frames), dtype=np.int16)
    audio_file.close()

    # Phones typically cut outside the range [300,3k]Hz
    # Here we define the filter
    low = 300 / (0.5 * sample_rate)
    high = 3000 / (0.5 * sample_rate)
    b, a = signal.butter(4, [low, high], btype='band')

    # Apply the filter
    filtered_samples = signal.lfilter(b, a, samples)

    # Save the filtered audio as mono / 16 bit / WAV PCM
    audio_file = wave.open('output.wav', 'wb')
    audio_file.setnchannels(1)
    audio_file.setsampwidth(2)  # 16-bit PCM
    audio_file.setframerate(sample_rate)
    audio_file.setnframes(len(filtered_samples))
    audio_file.writeframes(filtered_samples.astype(np.int16).tobytes())
    audio_file.close()
