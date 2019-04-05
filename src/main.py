import os
import datetime
import zipfile
import zlib
import logging

import httplib2
from apiclient.discovery import build
from apiclient.http import MediaFileUpload
from oauth2client.service_account import ServiceAccountCredentials

#patrizia.fiacchi11@gmail.com
#CAMinetto69

url = '192.168.1.97'
port = '554'
user = 'admin'
pwd = 'admin'

name = datetime.datetime.now().strftime('%Y%m%d_%H%M')
ext = 'mp4'
full_name = "{name}.{ext}".format(name=name, ext=ext)
duration = 60
dimMB = 1

SCOPES = 'https://www.googleapis.com/auth/drive'
driveLim = 1024*1024*10

logger = logging.basicConfig()

# Download the stream
#os.system("ffmpeg -i rtsp://admin:admin@192.168.1.97:554 -codec copy -f h264 output.mp4 &")
#os.system("ffmpeg -i rtsp://{user}:{pwd}@{url}:{port} -codec copy -f h264 -y -t {duration} {name}.mp4".
#          format(user=user, pwd=pwd, url=url, port=port, name=name, duration=duration))

# Store the file
os.system("ffmpeg -i rtsp://{user}:{pwd}@{url}:{port} -codec copy -f h264 -y -fs {dim} {full_name}".
          format(user=user, pwd=pwd, url=url, port=port, full_name=full_name, dim=dimMB*1024*1024))


# Compress the file with zip
zf = zipfile.ZipFile('%s.zip' % name, mode='w')
zf.write(full_name, compress_type=zipfile.ZIP_DEFLATED)
zf.close()

# Store the file in Google Drive
SCOPES = 'https://www.googleapis.com/auth/drive'
credential_dir = os.path.join(os.getcwd(), '.credentials')
if not os.path.exists(credential_dir):
    os.makedirs(credential_dir)
credential_path = os.path.join(credential_dir, 'credential2.json')
credentials = ServiceAccountCredentials.from_json_keyfile_name(credential_path, scopes=SCOPES)
http = credentials.authorize(httplib2.Http())
drive_service = build('drive', 'v3', http=http, cache_discovery=False)
print drive_service


folder_id = '0B9DvLi_YjwDocWhTb1FvUzloQnM'
file_metadata = {
  'name' : '%s.zip' % name,
  'parents': [ folder_id ]
}

media = MediaFileUpload('%s.zip' % name, resumable=True)
file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
print 'File ID: %s' % file.get('id')

print 'Finished!'

about = drive_service.about().get(fields="user, storageQuota").execute()
limit = about['storageQuota']['limit']
usage = about['storageQuota']['usage']
