#
# Basic distortion sound effect
# Tune the parameters for some twists and magic I guess
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

    # Apply the distortion effect
    distorted_samples = signal.distort(samples, power=0.5)

    # Save the filtered audio as mono / 16 bit / WAV PCM
    audio_file = wave.open('output.wav', 'wb')
    audio_file.setnchannels(1)
    audio_file.setsampwidth(2)  # 16-bit PCM
    audio_file.setframerate(sample_rate)
    audio_file.setnframes(len(distorted_samples))
    audio_file.writeframes(distorted_samples.astype(np.int16).tobytes())
    audio_file.close()
