"""Sentence-timed burned captions and progressive board assembly."""
import json
import re
import shutil
import subprocess
from pathlib import Path
from app.render import board
from app.tts import EspeakSpeech, duration, silence

def executable():
    found = shutil.which('ffmpeg')
    if found:
        return found
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()

def command(args):
    subprocess.run([executable(), '-hide_banner', '-loglevel', 'error', '-nostdin', *args],
                   check=True, capture_output=True, timeout=600)

def stamp(seconds):
    ms = round(seconds*1000)
    return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'

def assemble(topic, script, out, provider=None):
    provider = provider or EspeakSpeech()
    scratch = out / 'media'
    scratch.mkdir()
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', script.formal_answer.strip())
    segments = [('examiner', script.examiner_question, 0),
                ('pause', script.pause_screen_top+'\n'+script.pause_screen_bottom, 0),
                ('candidate', script.memory_line, 1)]
    segments += [('candidate', sentence, min(len(script.board_sections), 1+i*len(script.board_sections)//max(1,len(sentences)-1))) for i,sentence in enumerate(sentences)]
    timeline, cursor = [], 0.0
    for i,(role,text,reveal) in enumerate(segments):
        wav = scratch / f'{i:03}.wav'
        if role == 'pause':
            silence(wav, 4)
        else:
            provider.speak(text, role, wav)
        seconds = duration(wav)
        timeline.append(dict(text=text, role=role, start=cursor, end=cursor+seconds))
        cursor += seconds
        board(topic, script, scratch / f'{i:03}.png', reveal=reveal, caption=text)
    hold = max(3.0, 45.0-cursor)
    if cursor + hold > 60:
        raise ValueError('Narration exceeds 60 seconds; shorten script and repeat QC')
    i = len(segments)
    silence(scratch / f'{i:03}.wav', hold)
    board(topic, script, scratch / f'{i:03}.png')
    for i in range(len(segments)+1):
        command(['-y', '-loop','1','-framerate','25','-i',str(scratch/f'{i:03}.png'),
                 '-i',str(scratch/f'{i:03}.wav'),'-c:v','libx264','-preset','ultrafast',
                 '-tune','stillimage','-pix_fmt','yuv420p','-c:a','aac','-ar','48000',
                 '-ac','1','-t',str(duration(scratch/f'{i:03}.wav')), str(scratch/f'{i:03}.mp4')])
    concat = scratch / 'concat.txt'
    concat.write_text(''.join(f"file '{i:03}.mp4'\n" for i in range(len(segments)+1)), encoding='utf-8')
    command(['-y','-f','concat','-safe','1','-i',str(concat),'-c','copy','-movflags','+faststart',str(out/'video.mp4')])
    command(['-i',str(out/'video.mp4'),'-f','null','-'])
    probe = subprocess.run([executable(), '-hide_banner', '-i', str(out/'video.mp4')], capture_output=True, text=True, timeout=30)
    match = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', probe.stderr)
    if not match or '1080x1920' not in probe.stderr or 'Audio: aac' not in probe.stderr:
        raise ValueError('Encoded media validation failed')
    h,m,s = map(float,match.groups())
    encoded_seconds = h*3600 + m*60 + s
    if not 44.9 <= encoded_seconds <= 60.2 or abs(encoded_seconds - cursor - hold) > 0.3:
        raise ValueError('Encoded duration differs from narration timeline')
    (out/'captions.srt').write_text('\n\n'.join(f"{i+1}\n{stamp(s['start'])} --> {stamp(s['end'])}\n{s['text']}" for i,s in enumerate(timeline))+'\n', encoding='utf-8')
    (out/'timeline.json').write_text(json.dumps(timeline, indent=2), encoding='utf-8')
    return cursor + hold
