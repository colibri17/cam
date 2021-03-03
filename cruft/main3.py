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

# Cam parameters
url = '192.168.1.97'
port = '554'
user = 'admin'
pwd = 'admin'

# Recording parameters
name = datetime.datetime.now().strftime('%Y%m%d_%H%M')
ext = 'mp4'
full_name = "{name}.{ext}".format(name=name, ext=ext)
duration = 60
dimMB = 20

# Compression parameters

# Driver parameters
SCOPES = 'https://www.googleapis.com/auth/drive'
driveLim = 1024*1024*1024*10
folder_id = '0B9DvLi_YjwDocWhTb1FvUzloQnM'


# Logger
logging.basicConfig(level=logging.DEBUG,
                    format='(%(asctime)s %(threadName)-10s) %(message)s',
                    datefmt='%m/%d/%Y %H:%M:%S'
                    )


def connect():
    logging.debug('Connecting')
    # Define the directory where the credentials are stored
    credential_dir = os.path.join(os.getcwd(), '.credentials')
    # Get the path of the credentials
    credential_path = os.path.join(credential_dir, 'credential2.json')
    # Create the credential object
    credentials = ServiceAccountCredentials.from_json_keyfile_name(credential_path, scopes=SCOPES)
    # Authenticate
    http = credentials.authorize(httplib2.Http())
    # Create the service
    service = build('drive', 'v3', http=http, cache_discovery=False)
    logging.debug('Connected!')
    return service

def recording():
    logging.debug('Start recording %s', full_name)
    # Record the file with ffmpeg
    #os.system("ffmpeg -i rtsp://{user}:{pwd}@{url}:{port} -codec copy -f h264 -y -fs {dim} {full_name}".
    #          format(user=user, pwd=pwd, url=url, port=port, full_name=full_name, dim=dimMB*1024*1024))
    os.system("ffmpeg -i rtsp://{user}:{pwd}@{url}:{port} -vcodec libx264 -crf 26 -acodec copy -y -f h264 -t {dur} {full_name}".
              format(user=user, pwd=pwd, url=url, port=port, full_name=full_name, dur=duration))
    logging.debug('Recording ended')


def zipping(name, full_name):
    # Compress the file with zip
    logging.debug('Start zipping')
    zf = zipfile.ZipFile('%s.zip' % name, mode='w')
    zf.write(full_name, compress_type=zipfile.ZIP_DEFLATED)
    zf.close()
    logging.debug('Zipping ended')


def usage():
    logging.debug('Checking usage')
    service = connect()
    about = service.about().get(fields="user, storageQuota").execute()
    #limit = int(about['storageQuota']['limit'])
    usage = int(about['storageQuota']['usage'])

    # Retrieve the items in Google drive
    results = service.files().list(pageSize=1000, fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])
    # Get the list of files
    names_id = [(item['name'], item['id']) for item in items if item['name'].endswith(ext)]
    # Order by the last one
    dates_id = [(datetime.datetime.strptime(name[:-4], '%Y%m%d_%H%M'), id) for (name, id) in names_id]
    sorted_dates_id = sorted(dates_id, key=lambda x: x[0], reverse=True)
    # Delete the last one up to the usage is below the fixed limit
    while usage > driveLim:
        # Delete the first element in the list
        to_delete = sorted_dates_id.pop()
        # Delete from Google Drive that ID
        logging.debug('Delete %s from Google Drive', str(to_delete[0]))
        service.files().delete(fileId=to_delete[1]).execute()
        # Recompute the usage
        about = service.about().get(fields="user, storageQuota").execute()
        usage = int(about['storageQuota']['usage'])
    else:
        logging.debug('No files deleted. There is still space!')


def storing(name):
    # Create a new connection
    service = connect()
    logging.debug('Start storing on Google Drive %s', '%s.zip' % name)
    file_metadata = {
      'name' : '%s.zip' % name,
      'parents': [ folder_id ]
    }

    media = MediaFileUpload('%s.zip' % name, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    logging.debug('Storing ended')
    logging.debug('File %s stored', file.get('id'))


def drive(name, full_name):
    # Zipping the file
    zipping(name, full_name)
    # Storing the file on Google Drive
    storing(name)
    # Check the usage of Google Drive and delete files if necessary
    usage()


cont = 0

while cont < 10:

    # Define the name to use when recording
    name = datetime.datetime.now().strftime('%Y%m%d_%H%M')
    full_name = "{name}.{ext}".format(name=name, ext=ext)

    # Storing
    recording_th = threading.Thread(name='recording', target=recording)
    recording_th.start()
    recording_th.join()
    print js
    # Zipping and storing on google drive
    threading.Thread(name='zipping_storing', target=drive, args=(name, full_name,)).start()

    cont += 1
    print threading.enumerate()