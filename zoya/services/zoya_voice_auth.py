import os
import numpy as np
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(dotenv_path=BASE_DIR / ".env")

# Pitch ranges
# Male fundamental frequency: 85 - 155 Hz
# Female fundamental frequency: 165 - 255 Hz
UNEEB_PITCH_MIN = 80
UNEEB_PITCH_MAX = 165
STABILITY_THRESHOLD = 5 # Need 5 consecutive frames of stranger voice to alert

class VoiceAnalyzer:
    def __init__(self, sample_rate=48000, buffer_duration_ms=500):
        self.sample_rate = sample_rate
        self.buffer_size = int(sample_rate * (buffer_duration_ms / 1000))
        self.audio_buffer = np.zeros(self.buffer_size, dtype=np.int16)
        self.stranger_count = 0
        self.is_stranger_detected = False

    def add_frames(self, frames: bytes):
        """Add new PCM frames to the rolling buffer."""
        new_data = np.frombuffer(frames, dtype=np.int16)
        if len(new_data) > self.buffer_size:
            new_data = new_data[-self.buffer_size:]
        
        # Roll buffer and append
        self.audio_buffer = np.roll(self.audio_buffer, -len(new_data))
        self.audio_buffer[-len(new_data):] = new_data

    def get_pitch(self) -> float:
        """Calculate pitch from the current buffer using Autocorrelation."""
        try:
            # Check for silence/low energy (RMS)
            rms = np.sqrt(np.mean(self.audio_buffer.astype(np.float32)**2))
            if rms < 300: # Threshold for 'actual' speech vs background noise
                return 0.0

            # Pre-processing: Remove DC
            samples = self.audio_buffer.astype(np.float32) - np.mean(self.audio_buffer)
            
            # Autocorrelation
            corr = np.correlate(samples, samples, mode='full')
            corr = corr[len(corr)//2:]

            # Peak detection in human voice range (80Hz - 800Hz)
            # Min lag = sr / max_freq = 48000 / 800 = 60
            # Max lag = sr / min_freq = 48000 / 70 = 685
            min_lag = 60
            max_lag = 700
            
            if len(corr) < max_lag: return 0.0
            
            search_region = corr[min_lag:max_lag]
            peak_lag = np.argmax(search_region) + min_lag
            
            pitch = self.sample_rate / peak_lag
            return pitch
        except Exception:
            return 0.0

    def analyze_identity(self) -> str:
        """
        Analyze current buffer and return 'UNEEB', 'STRANGER', or 'SILENCE'.
        """
        pitch = self.get_pitch()
        
        if pitch == 0:
            return "SILENCE"
        
        is_uneeb = UNEEB_PITCH_MIN <= pitch <= UNEEB_PITCH_MAX
        
        # Debug Logging for Terminal (Commented out to prevent flood)
        # status = "UNEBB" if is_uneeb else "STRANGER"
        # print(f"[VOICE] Pitch: {pitch:.1f}Hz | Detect: {status}")

        if not is_uneeb:
            self.stranger_count += 1
        else:
            self.stranger_count = 0
            self.is_stranger_detected = False

        if self.stranger_count >= STABILITY_THRESHOLD:
            self.is_stranger_detected = True
            return "STRANGER"
            
        return "UNEEB"

def is_uneeeb_voice(pitch: float) -> bool:
    """Helper for simple checks."""
    if pitch == 0: return True
    return UNEEB_PITCH_MIN <= pitch <= UNEEB_PITCH_MAX
