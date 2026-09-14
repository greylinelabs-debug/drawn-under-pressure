"""Offline free default, with an injectable speech-provider interface."""
from pathlib import Path
from typing import Protocol
import shutil
import subprocess
import wave

class SpeechProvider(Protocol):
    def speak(self, text: str, role: str, path: Path) -> None: ...

class EspeakSpeech:
    def __init__(self, executable='espeak-ng', words_per_minute=175):
        self.executable = shutil.which(executable)
        if not self.executable:
            raise RuntimeError('Install espeak-ng (free offline speech engine)')
        self.rate = words_per_minute

    def speak(self, text, role, path):
        subprocess.run([self.executable, '-v', 'en-gb', '-s', str(self.rate),
                        '-p', '35' if role == 'examiner' else '55',
                        '-w', str(path), '--stdin'], input=text, text=True,
                       check=True, capture_output=True, timeout=120)
        if duration(path) <= 0:
            raise ValueError('TTS returned empty audio')

def duration(path):
    with wave.open(str(path), 'rb') as audio:
        return audio.getnframes() / audio.getframerate()

def silence(path, seconds):
    with wave.open(str(path), 'wb') as audio:
        audio.setparams((1, 2, 22050, 0, 'NONE', 'not compressed'))
        audio.writeframes(b'\0\0' * round(seconds * 22050))
