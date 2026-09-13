"""Drive adapter. OAuth credentials are supplied only through the environment."""
import io
import json
import os
import re
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

def identifier(value):
    if not re.fullmatch(r'[A-Za-z0-9_-]+', value):
        raise ValueError('Invalid Drive identifier')
    return value

class Drive:
    def __init__(self, service=None):
        if service is None:
            raw = os.getenv('GOOGLE_DRIVE_OAUTH_JSON')
            if not raw:
                raise RuntimeError('GOOGLE_DRIVE_OAUTH_JSON is required for unattended Drive access')
            credentials = Credentials.from_authorized_user_info(json.loads(raw))
            service = build('drive','v3',credentials=credentials,cache_discovery=False)
        self.service = service

    def get(self, file_id):
        return self.service.files().get(fileId=identifier(file_id), fields='id,name,mimeType,size,parents,md5Checksum,appProperties', supportsAllDrives=True).execute(num_retries=3)

    def list(self, parent):
        token = None
        result = []
        while True:
            page = self.service.files().list(q=f"'{identifier(parent)}' in parents and trashed = false",
                fields='nextPageToken,files(id,name,mimeType,size,parents,md5Checksum)', pageToken=token,
                pageSize=100, supportsAllDrives=True, includeItemsFromAllDrives=True).execute(num_retries=3)
            result.extend(page.get('files', []))
            token = page.get('nextPageToken')
            if not token:
                return result

    def move(self, file_id, source, destination):
        current = self.get(file_id)
        if source not in current.get('parents', []):
            raise ValueError('Source has moved; refusing stale operation')
        self.service.files().update(fileId=file_id, addParents=identifier(destination),
            removeParents=identifier(source), fields='id,parents', supportsAllDrives=True).execute(num_retries=3)
        if destination not in self.get(file_id).get('parents', []):
            raise RuntimeError('Drive move verification failed')

    def download(self, file_id, path):
        metadata = self.get(file_id)
        if not metadata.get('mimeType','').startswith('image/') or int(metadata.get('size',0)) > 20*1024*1024:
            raise ValueError('Only source images up to 20 MiB are accepted')
        with Path(path).open('wb') as handle:
            download = MediaIoBaseDownload(handle, self.service.files().get_media(fileId=file_id), chunksize=1024*1024)
            done = False
            while not done:
                _, done = download.next_chunk(num_retries=3)
                if handle.tell() > 20*1024*1024:
                    raise ValueError('Source exceeds size limit')

    def upload_package(self, path, parent, source_id):
        # Stable name enables recovery if upload succeeded but the final source move failed.
        name = identifier(source_id) + '.zip'
        matches = [f for f in self.list(parent) if f['name'] == name]
        if len(matches) > 1:
            raise RuntimeError('Duplicate output packages require review')
        if matches:
            metadata = self.get(matches[0]['id'])
            import hashlib
            if metadata.get('md5Checksum') != hashlib.md5(Path(path).read_bytes()).hexdigest():
                raise RuntimeError('Existing package differs; retain Processing for recovery')
            return matches[0]['id']
        request = self.service.files().create(body={'name':name,'parents':[parent]},
            media_body=MediaFileUpload(str(path), mimetype='application/zip', resumable=True),
            fields='id', supportsAllDrives=True)
        response = None
        while response is None:
            _, response = request.next_chunk(num_retries=3)
        import hashlib
        metadata = self.get(response['id'])
        if metadata.get('md5Checksum') != hashlib.md5(Path(path).read_bytes()).hexdigest():
            raise RuntimeError('Uploaded package checksum mismatch')
        self.service.files().update(fileId=response['id'], body={'appProperties':{
            'dupVerified':'true', 'sourceChecksum':self.get(source_id).get('md5Checksum','')}},
            fields='id', supportsAllDrives=True).execute(num_retries=3)
        return response['id']
