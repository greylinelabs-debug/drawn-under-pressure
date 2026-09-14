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

def board(topic, script, path, *, reveal=None, caption=''):
    image = Image.new('RGB', (WIDTH, HEIGHT), PAPER)
    draw = ImageDraw.Draw(image)
    draw.text((60, 42), 'DRAWN UNDER PRESSURE', font=font(30), fill=TEAL)
    title = lines(topic, font(60), 960)
    if len(title) > 2:
        raise ValueError('Topic title too long')
    y = 110
    for line in title:
        draw.text((60, y), line, font=font(60), fill=INK)
        y += 74
    draw.line((60, y+14, 1020, y+10), fill=TEAL, width=7)
    y += 48
    sections = script.board_sections
    if not 1 <= len(sections) <= 8:
        raise ValueError('Board requires 1 to 8 sections')
    for index, section in enumerate(sections):
        heading = lines(section.heading, font(34), 930)
        body = [line for bullet in section.bullets for line in lines('- ' + bullet, font(30), 910)]
        height = len(heading)*44 + len(body)*39 + 28
        if y + height > 1530:
            raise ValueError('Board text overflows; shorten the script and repeat QC')
        if reveal is None or index < reveal:
            for line in heading:
                draw.text((60, y), line, font=font(34), fill=TEAL)
                y += 44
            for line in body:
                draw.text((80, y), line, font=font(30), fill=INK)
                y += 39
            y += 28
        else:
            y += height
    if caption:
        caption_lines = lines(caption, font(38), 920)
        if len(caption_lines) > 5:
            raise ValueError('Caption overflow')
        draw.rounded_rectangle((40, 1560, 1040, 1850), radius=20, fill=INK)
        for i, line in enumerate(caption_lines):
            draw.text((80, 1580+i*50), line, font=font(38), fill=PAPER)
    draw.text((60, 1870), 'PRIMARY FRCA  /  SOURCE-GROUNDED REVISION', font=font(22), fill=TEAL)
    image.save(path)
    return Path(path)
