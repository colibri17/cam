import os
import datetime
import threading
import logging
import time

import httplib2
from apiclient.discovery import build
from apiclient.http import MediaFileUpload
from oauth2client.service_account import ServiceAccountCredentials

#patrizia.fiacchi11@gmail.com
#CAMinetto69

video_path = 'video/'

# Cam parameters
url = '192.168.1.97'
port = '554'
user = 'admin'
pwd = 'admin'

# Recording parameters
name = datetime.datetime.now().strftime('%Y%m%d_%H%M')
ext = 'mp4'
full_name = "{name}.{ext}".format(name=name, ext=ext)
duration = 30
dimMB = 20*1024*1024
compression = 26

# Local parameter
#localLim = 1024*1024*1024*100
localLim = 1024*1024*200

# Driver parameters
SCOPES = 'https://www.googleapis.com/auth/drive'
#driveLim = 1024*1024*1024*10
driveLim = 1024*1024*80
folder_id = '0B9DvLi_YjwDocWhTb1FvUzloQnM'
cred_name = 'credential.json'


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
    credential_path = os.path.join(credential_dir, cred_name)
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
    os.system("ffmpeg -i rtsp://{user}:{pwd}@{url}:{port} -vcodec libx264 -crf {compr} -acodec copy -y -f h264 -fs {dim} {full_name}".
              format(user=user, pwd=pwd, url=url, port=port, full_name=full_name, dim=dimMB, compr=compression))
    #os.system("ffmpeg -i rtsp://{user}:{pwd}@{url}:{port} -vcodec libx264 -crf {compr} -acodec copy -y -f h264 -t {dur} {full_name}".
    #          format(user=user, pwd=pwd, url=url, port=port, full_name=full_name, dur=duration, compr=compression))
    logging.debug('Recording ended')


def drive_usage():
    logging.debug('Checking drive usage')
    service = connect()
    about = service.about().get(fields="user, storageQuota").execute()
    #limit = int(about['storageQuota']['limit'])
    usage = int(about['storageQuota']['usage'])

    # Retrieve the items in Google drive
    results = service.files().list(pageSize=1000, fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])
    print items
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
        logging.debug('Drive limit: %s. Usage: %s', driveLim, usage)


def get_size_filename(start_path = '.'):
    total_size = 0
    files = []
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in [x for x in filenames if x.endswith(ext)]:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
            files.append(f)
    return total_size, files


def current_usage():
    logging.debug('Checking local usage')
    # Get the dimension of the folder and subfolders in which are stored the files
    total_size, files = get_size_filename(video_path)
    # Get the corresponding dates related to the file
    file_dates = [(datetime.datetime.strptime(name[:-4], '%Y%m%d_%H%M'), name) for name in files]
    # Order to delete the last one
    sorted_dates = sorted(file_dates, key=lambda x: x[0], reverse=True)
    # Delete the file if the total space is greater than the limit
    while total_size > localLim:
        # Delete the first element in the list
        to_delete = sorted_dates.pop()
        logging.debug('Delete %s from disk', str(to_delete[1]))
        # Delete
        os.remove(os.path.join(video_path, to_delete[1]))
        # Recompute the total size
        total_size, _ = get_size_filename(video_path)
    else:
        logging.debug('Local limit: %s. Usage: %s', localLim, total_size)


def storing(full_name, name):
    # Create a new connection
    service = connect()
    logging.debug('Start storing on Google Drive %s', name)
    # Define file properties
    file_metadata = {
      'name' : name,
      'parents': [ folder_id ]
    }

    media = MediaFileUpload(full_name, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    logging.debug('Storing ended')
    logging.debug('File %s stored', file.get('id'))


def drive(name, full_name):
    try:
        # Storing the file on Google Drive
        storing(full_name, name)
        # Check the usage of Google Drive and delete files if necessary
        drive_usage()
        # Check the usage locally
        current_usage()
    except IOError:
    # The file does not exist. This is because the camera did not record
        logging.debug('Error, the file does not exist')


cont = 0

while cont < 10:

    # Define the name to use when recording
    name = datetime.datetime.now().strftime('%Y%m%d_%H%M')
    full_name = "{path}{name}.{ext}".format(path=video_path, name=name, ext=ext)

    # Storing
    recording_th = threading.Thread(name='recording', target=recording)
    recording_th.start()
    recording_th.join()
    # Zipping and storing on google drive
    threading.Thread(name='flux', target=drive, args=(name, full_name,)).start()

    cont += 1
    print threading.enumerate()