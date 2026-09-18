import json
import os
import shutil
from pathlib import Path
import pytest
from app.models import SourcePage, DrugTopic, GroundedFact, ScriptPackage, BoardSection, ModelQCReview
from app.qc import SourceGroundingQC, find_novel_numeric_unit_claims
from app.render import board
from app.tts import silence
from app.package import render_package, digest

@pytest.fixture
def episode():
    text = 'This is a synthetic layout fixture. It contains no clinical advice.'
    source = SourcePage(topic='Pipeline demonstration', topic_type='drug', source_text=text, source_quality='good')
    topic = DrugTopic(topic=source.topic, classification=[GroundedFact(value=text, evidence=text)])
    script = ScriptPackage(examiner_question='Right then, doctor. Tell me about this demonstration.',
        pause_screen_top='PAUSE THE VIDEO', pause_screen_bottom='THINK LIKE THE CANDIDATE',
        memory_line='A board with nothing to prescribe.', formal_answer=text,
        board_sections=[BoardSection(heading='Synthetic demonstration', bullets=[text]),
                        BoardSection(heading='Pipeline', bullets=['Board, speech, captions and private delivery.'])])
    return source, topic, script

class Approve:
    def generate(self, *args):
        return ModelQCReview(supported=True)

def test_deterministic_board(tmp_path, episode):
    _, topic, script = episode
    board(topic.topic, script, tmp_path/'a.png')
    board(topic.topic, script, tmp_path/'b.png')
    assert digest(tmp_path/'a.png') == digest(tmp_path/'b.png')

def test_overflow_blocks(tmp_path, episode):
    _, topic, script = episode
    script.board_sections[0].bullets = ['Repeated long source text. '*500]
    with pytest.raises(ValueError, match='overflows'):
        board(topic.topic, script, tmp_path/'a.png')

@pytest.mark.parametrize('source,claim', [('5 mg/kg/min','5 mg/kg/h'),('10%','20%'),('2–4 mg','2–6 mg'),('0.5 mg','5 mg')])
def test_numeric_variants(source, claim):
    assert find_novel_numeric_unit_claims(source, claim)

def test_board_numeric_claim_blocks(episode):
    source, topic, script = episode
    script.board_sections[0].bullets = ['Give 999 mg']
    assert SourceGroundingQC(Approve()).review(source,topic,script).status == 'blocked_qc'

def test_evidence_blocks(episode):
    source, topic, script = episode
    topic.classification[0].evidence = 'Invented quote'
    assert SourceGroundingQC(Approve()).review(source,topic,script).status == 'blocked_qc'

def test_caution_blocks_without_model(episode):
    source, topic, script = episode
    source.source_quality = 'usable_with_caution'
    assert SourceGroundingQC(Approve()).review(source,topic,script).status == 'blocked_source_quality'

def test_blocked_package_creates_no_video(tmp_path, episode):
    source, topic, script = episode
    qc = SourceGroundingQC(Approve()).review(source,topic,script)
    qc.status = 'blocked_qc'
    with pytest.raises(ValueError):
        render_package(source,topic,script,qc,tmp_path)
    assert not (tmp_path/'video.mp4').exists()

class SilentTestSpeech:
    def speak(self, text, role, path):
        silence(path, 2)

@pytest.mark.skipif(os.getenv('RUN_MEDIA_TESTS') != '1', reason='Explicit FFmpeg integration test')
def test_full_package(tmp_path, episode):
    source, topic, script = episode
    qc = SourceGroundingQC(Approve()).review(source,topic,script)
    for name, obj in [('source',source),('topic',topic),('script',script),('qc',qc)]:
        (tmp_path/(name+'.json')).write_text(obj.model_dump_json(), encoding='utf-8')
    result = render_package(source,topic,script,qc,tmp_path,SilentTestSpeech())
    assert 45 <= result['duration_seconds'] <= 60
    assert (tmp_path/'episode.zip').stat().st_size > 10000
    assert all(digest(tmp_path/name) == sha for name,sha in result['files'].items())

@pytest.mark.skipif(not shutil.which('espeak-ng'), reason='eSpeak NG not installed locally; required in Linux CI')
def test_real_free_speech(tmp_path):
    from app.tts import EspeakSpeech, duration
    EspeakSpeech().speak('This is a voice test.', 'examiner', tmp_path/'voice.wav')
    assert duration(tmp_path/'voice.wav') > 0
