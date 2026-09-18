from pathlib import Path
from PIL import Image
import pytest
from app.worker import batch

FOLDERS = dict(Inbox='inbox', Processing='processing', Finished='finished', Failed='failed')
class FakeDrive:
    def __init__(self):
        self.location = 'inbox'
        self.uploads = []
    def get(self, id):
        return {'mimeType':'application/vnd.google-apps.folder'}
    def list(self, parent):
        return [{'id':'source', 'name':'page.png', 'mimeType':'image/png'}] if parent == self.location else []
    def move(self, id, source, dest):
        assert source == self.location
        self.location = dest
    def download(self, id, path):
        Image.new('RGB',(10,10)).save(path)
    def upload_package(self, path, parent, source):
        assert Path(path).is_file()
        self.uploads.append(parent)

def success(image, out):
    out.mkdir()
    (out/'episode.zip').write_bytes(b'test-package')
    return 0

def test_success_delivery_before_move():
    drive = FakeDrive()
    assert batch(drive,FOLDERS,processor=success) == ['finished']
    assert drive.location == 'finished'
    assert drive.uploads == ['finished']

def test_qc_failure_routes_to_failed():
    drive = FakeDrive()
    assert batch(drive,FOLDERS,processor=lambda *a:3) == ['failed']
    assert drive.location == 'failed'

def test_upload_outage_retains_processing():
    drive = FakeDrive()
    def fail(*a):
        raise RuntimeError('offline')
    drive.upload_package = fail
    with pytest.raises(RuntimeError):
        batch(drive,FOLDERS,processor=success)
    assert drive.location == 'processing'

def test_limit_validation():
    with pytest.raises(ValueError):
        batch(FakeDrive(),FOLDERS,limit=0)
