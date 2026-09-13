import hashlib
import json
import zipfile
from pathlib import Path
from app.render import board
from app.video import assemble

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def render_package(source, topic, script, qc, out, provider=None):
    if (qc.status != 'ready_for_render' or not qc.model_supported or
        qc.numeric_or_unit_issues or qc.unsupported_or_distorted_claims or
        source.source_quality != 'good'):
        raise ValueError('Rendering requires a clean source and passing QC')
    board(topic.topic, script, out/'board.png')
    seconds = assemble(topic.topic, script, out, provider)
    (out/'script.txt').write_text('\n\n'.join([script.examiner_question, script.pause_screen_top,
        script.pause_screen_bottom, script.memory_line, script.formal_answer]), encoding='utf-8')
    names = ['board.png','video.mp4','script.txt','captions.srt','timeline.json','source.json','topic.json','script.json','qc.json']
    manifest = {'schema_version': 1, 'status': 'rendered', 'duration_seconds': seconds,
                'files': {name:digest(out/name) for name in names}}
    (out/'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    with zipfile.ZipFile(out/'episode.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for name in names + ['manifest.json']:
            archive.write(out/name, name)
    return manifest
