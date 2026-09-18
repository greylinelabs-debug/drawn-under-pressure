"""Deterministic, measured typography; never truncate source claims."""
from pathlib import Path
import os
from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1080, 1920
INK, PAPER, TEAL = '#202c38', '#fffaf0', '#007f82'

def font(size):
    candidates = [os.getenv('BOARD_FONT', ''), '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 'C:/Windows/Fonts/arial.ttf']
    for path in candidates:
        if path and Path(path).is_file():
            return ImageFont.truetype(path, size)
    raise RuntimeError('Install DejaVu Sans or set BOARD_FONT to a TrueType font')

def lines(text, face, width):
    result = []
    for paragraph in text.splitlines() or ['']:
        line = ''
        for word in paragraph.split():
            if face.getlength(word) > width:
                raise ValueError('Unbreakable text exceeds board width')
            trial = (line + ' ' + word).strip()
            if face.getlength(trial) > width:
                result.append(line)
                line = word
            else:
                line = trial
        result.append(line)
    return result

def board(topic, script, path, *, reveal=None, caption='', demo=False):
    from app.scene import revision
    revision(topic, script, path, reveal=reveal, caption=caption, demo=demo)
    return Path(path)
