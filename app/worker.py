"""Single-writer bounded batches; failed sources are never deleted."""
import argparse
import json
import tempfile
import zipfile
from pathlib import Path
from app.drive import Drive
from app.main import run

def batch(drive, folders, limit=3, processor=run):
    if not 1 <= limit <= 10:
        raise ValueError('Batch limit must be 1 to 10')
    if len(set(folders.values())) != 4:
        raise ValueError('Four distinct folders are required')
    for folder in folders.values():
        if drive.get(folder)['mimeType'] != 'application/vnd.google-apps.folder':
            raise ValueError('Configured destination is not a folder')
    # Processing is resumed first after a cancelled runner. Actions concurrency is mandatory.
    pending = [(f,'Processing') for f in drive.list(folders['Processing'])]
    pending += [(f,'Inbox') for f in drive.list(folders['Inbox'])]
    results = []
    for item, location in pending[:limit]:
        file_id = item['id']
        with tempfile.TemporaryDirectory(prefix='dup-') as temp:
            root = Path(temp)
            try:
                if location == 'Inbox':
                    drive.move(file_id, folders['Inbox'], folders['Processing'])
                existing = [f for f in drive.list(folders['Finished']) if f['name'] == file_id+'.zip']
                if len(existing) == 1:
                    package = drive.get(existing[0]['id'])
                    props = package.get('appProperties', {})
                    checksum = drive.get(file_id).get('md5Checksum')
                    if props.get('dupVerified') != 'true' or not checksum or props.get('sourceChecksum') != checksum:
                        raise RuntimeError('Existing package provenance not verified')
                    drive.move(file_id, folders['Processing'], folders['Finished'])
                    results.append('recovered')
                    continue
                if existing:
                    raise ValueError('Duplicate finished packages')
                mime = item.get('mimeType','')
                suffix = {'image/jpeg':'.jpg','image/png':'.png','image/webp':'.webp'}.get(mime)
                if suffix is None:
                    raise ValueError('Unsupported source image format')
                image = root / ('source'+suffix)
                drive.download(file_id, image)
                from PIL import Image
                with Image.open(image) as source:
                    source.verify()
                out = root/'episode'
                status = processor(image, out)
                if status:
                    raise ValueError('Source or content QC blocked this episode')
                # Do not classify an upload/move interruption as a content failure.
            except Exception as exc:
                if not isinstance(exc, ValueError):
                    # API outages, upload interruptions and unexpected failures are retried on next batch.
                    raise
                # No source excerpts, secrets or provider exception text enter public Actions logs.
                report = root/'failure.json'
                report.write_text(json.dumps({'status':'failed','error_type':type(exc).__name__,
                    'recovery':'Inspect source, then move it back to Inbox to retry.'}), encoding='utf-8')
                archive = root/'failure.zip'
                with zipfile.ZipFile(archive,'w') as z:
                    z.write(report,'failure.json')
                    qc = root/'episode'/'qc.json'
                    if qc.exists():
                        z.write(qc,'qc.json')
                # Infrastructure errors retain Processing when delivery itself cannot complete.
                drive.upload_package(archive, folders['Failed'], file_id)
                drive.move(file_id, folders['Processing'], folders['Failed'])
                results.append('failed')
                continue
            drive.upload_package(out/'episode.zip', folders['Finished'], file_id)
            drive.move(file_id, folders['Processing'], folders['Finished'])
            results.append('finished')
    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='config/drive-folders.json')
    parser.add_argument('--limit', type=int, default=3)
    args = parser.parse_args()
    try:
        result = batch(Drive(), json.loads(Path(args.config).read_text()), args.limit)
        print(json.dumps({'processed':len(result),'finished':result.count('finished'), 'failed':result.count('failed')}))
        return 1 if 'failed' in result else 0
    except Exception as exc:
        print('Worker stopped: '+type(exc).__name__+'. Check credentials, folder access and Processing.')
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
