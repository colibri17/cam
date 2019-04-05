import os
import datetime
import zipfile
import threading
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
folder_id = '0B9DvLi_YjwDocWhTb1FvUzloQnM'


logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-10s) %(message)s',
                    )

def connect():
    credential_dir = os.path.join(os.getcwd(), '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir, 'credential2.json')
    credentials = ServiceAccountCredentials.from_json_keyfile_name(credential_path, scopes=SCOPES)
    http = credentials.authorize(httplib2.Http())
    service = build('drive', 'v3', http=http, cache_discovery=False)
    logging.debug('Connected!')
    return service

def recording(recording_end):
    recording_end.clear()
    logging.debug('Start recording')
    # Store the file
    os.system("ffmpeg -i rtsp://{user}:{pwd}@{url}:{port} -codec copy -f h264 -y -fs {dim} {full_name}".
              format(user=user, pwd=pwd, url=url, port=port, full_name=full_name, dim=dimMB * 1024 * 1024))
    recording_end.set()


def zipping(recording_end):
    """Wait for the event to be set before doing anything"""
    zipping_end.clear()
    logging.debug('Wait for the recording to end')
    event_is_set = recording_end.wait()
    logging.debug('Recording finished: %s', event_is_set)
    # Compress the file with zip
    zf = zipfile.ZipFile('%s.zip' % name, mode='w')
    zf.write(full_name, compress_type=zipfile.ZIP_DEFLATED)
    zf.close()
    zipping_end.set()


def storing(service, zipping_end):
    """Wait for the event to be set before doing anything"""
    logging.debug('Wait for the zipping to end')
    event_is_set = zipping_end.wait()
    logging.debug('Zipping finished: %s', event_is_set)
    file_metadata = {
      'name' : '%s.zip' % name,
      'parents': [ folder_id ]
    }

    media = MediaFileUpload('%s.zip' % name, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()

    logging.debug('File %s stored', file.get('id'))


# Connect to Google Drive platform
service = connect()

cont = 0

while cont < 2:

    print('cont')

    # Create an event
    recording_end = threading.Event()
    zipping_end = threading.Event()

    # Storing
    recording_th = threading.Thread(name='recording', target=recording, args=(recording_end,))
    recording_th.join()
    logging.debug('recording step ended!')
    # Zipping
    threading.Thread(name='zipping', target=zipping, args=(recording_end,)).start()
    # Google Drive
    threading.Thread(name='storing', target=storing, args=(service, zipping_end,)).start()

    recording_th.start()

    cont += 1



print 'Finished!'

#about = drive_service.about().get(fields="user, storageQuota").execute()
#limit = about['storageQuota']['limit']
#usage = about['storageQuota']['usage']
