from app.demo import demo_script
from app.scene import card
from app.render import board
from app.video import spoken_chunks, pad_to_frame
from app.tts import silence, duration
from PIL import Image
import pytest

def test_caption_chunks_preserve_every_word():
    text='Give 0.5 mg/kg/min only if the supplied source explicitly states that regimen. '+('A long but exact qualification follows. '*12)
    chunks=spoken_chunks(text)
    assert ' '.join(chunks) == ' '.join(text.split())
    assert all(len(chunk)<=120 for chunk in chunks)

def test_audio_padding_aligns_frames(tmp_path):
    path=tmp_path/'sample.wav'
    silence(path,1.013)
    padded=pad_to_frame(path)
    assert padded==1.04
    assert abs(duration(path)-padded)<0.0001

@pytest.mark.parametrize('kind',['examiner','pause','hook'])
def test_scene_cards(tmp_path,kind):
    path=tmp_path/'card.png'
    script=demo_script()
    card('Style demonstration',script,path,kind=kind,text=script.examiner_question,demo=True)
    assert Image.open(path).size==(1080,1920)

def test_full_six_panel_board(tmp_path):
    script=demo_script()
    path=tmp_path/'board.png'
    board('The viva, drawn clearly.',script,path,demo=True)
    assert Image.open(path).size==(1080,1920)

def test_scene_overflow_is_rejected(tmp_path):
    with pytest.raises(ValueError,match='overflows'):
        card('Demo',demo_script(),tmp_path/'card.png',kind='hook',text='Long sentence. '*200)
