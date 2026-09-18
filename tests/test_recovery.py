import hashlib
import pytest
from app.worker import batch
from tests.test_worker import FakeDrive, FOLDERS, success

class RecoveringDrive(FakeDrive):
    def __init__(self, *, valid=True, changed=False):
        super().__init__()
        self.location='processing'
        self.valid=valid
        self.changed=changed
    def list(self,parent):
        if parent=='finished':
            return [{'id':'package','name':'source.zip'}]
        return super().list(parent)
    def get(self,id):
        if id=='source':
            return {'md5Checksum':'new-source' if self.changed else 'original-source'}
        if id=='package':
            return {'md5Checksum':'uploaded-package', 'appProperties':{
                'sourceChecksum':'original-source','dupExpectedMD5':'uploaded-package' if self.valid else 'different-package'}}
        return super().get(id)

def test_complete_upload_recovers_before_final_marker():
    drive=RecoveringDrive()
    assert batch(drive,FOLDERS,processor=lambda *args:pytest.fail('must not regenerate'))==['recovered']
    assert drive.location=='finished'

@pytest.mark.parametrize('kwargs',[{'valid':False},{'changed':True}])
def test_bad_upload_or_changed_source_not_recovered(kwargs):
    drive=RecoveringDrive(**kwargs)
    with pytest.raises(RuntimeError):
        batch(drive,FOLDERS,processor=success)
    assert drive.location=='processing'

def test_worker_suppresses_source_output(capsys):
    def noisy(image,out):
        print('PRIVATE SOURCE EXCERPT')
        return success(image,out)
    batch(FakeDrive(),FOLDERS,processor=noisy)
    assert 'PRIVATE SOURCE EXCERPT' not in capsys.readouterr().out
