import os
import datetime
import threading
import logging
import time
import json
import glob

import httplib2
from apiclient import errors
from apiclient.discovery import build
from apiclient.http import MediaFileUpload
from oauth2client.service_account import ServiceAccountCredentials

# os.chdir('C:\Users\Alberto\Documents\Alberto\Telecamera')
os.chdir('/home/alberto/Documenti/Personale/Progetti/Telecamera')
print os.getcwd()

# Recording parameters
ext = 'mp4'
duration = 30
dimMB = 20*1024*1024
compression = 28

# Local parameter
localLim = 1024*1024*1024*20
#localLim = 1024*1024*200

# Driver parameters
SCOPES = 'https://www.googleapis.com/auth/drive'
driveLim = 1024*1024*1024*4
#driveLim = 1024*1024*30
cred_name = 'credential.json'
#cred_name = 'credentialMu.json'

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

def recording(url, user, pwd, port, full_name, duration = False):
    logging.debug('Start recording %s', full_name)
    # Record the file with ffmpeg by using duration
    if duration:
        os.system("ffmpeg -i rtsp://{user}:{pwd}@{url}:{port} -vcodec libx264 -crf {compr} -acodec copy -y -f h264 -t {dur} {full_name}".
                  format(user=user, pwd=pwd, url=url, port=port, full_name=full_name, dur=duration, compr=compression))
    # Record the file with ffmpeg by using file size
    else:
        os.system("ffmpeg -i rtsp://{user}:{pwd}@{url}:{port} -vcodec libx264 -crf {compr} -acodec copy -y -f h264 -fs {dim} {full_name}".
                  format(user=user, pwd=pwd, url=url, port=port, full_name=full_name, dim=dimMB, compr=compression))
    logging.debug('Recording ended')


def drive_usage(folder_id):
    logging.debug('Checking drive usage')
    service = connect()
    # Retrieve the items in Google drive folder
    results = service.files().list(pageSize=1000, q="'%s' in parents" % folder_id, fields="nextPageToken, files(id, name, size)").execute()
    items = results.get('files', [])
    # Get the usage
    usage = sum([int(item['size']) for item in items])
    # Get the list of files
    names_id = [(item['name'], item['id']) for item in items if item['name'].endswith(ext)]
    # Order by the last one
    dates_id = [(datetime.datetime.strptime(name.split('_')[0], '%Y%m%d%H%M'), id) for (name, id) in names_id]
    sorted_dates_id = sorted(dates_id, key=lambda x: x[0], reverse=True)
    # Delete the last one up to the usage is below the fixed limit
    while usage > driveLim:
        # Delete the first element in the list
        to_delete = sorted_dates_id.pop()
        # Delete from Google Drive that ID
        logging.debug('Delete %s from Google Drive', str(to_delete[0]))
        service.files().delete(fileId=to_delete[1]).execute()
        # Update the usage
        results = service.files().list(pageSize=1000, q="'%s' in parents" % folder_id, fields="nextPageToken, files(id, name, size)").execute()
        items = results.get('files', [])
        usage = sum([int(item['size']) for item in items])
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


def local_usage():
    logging.debug('Checking local usage')
    # Get the dimension of the folder and subfolders in which are stored the files
    total_size, files = get_size_filename(video_path)
    # Get the corresponding dates related to the file
    file_dates = [(datetime.datetime.strptime(name.split('_')[0], '%Y%m%d%H%M'), name) for name in files]
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


def storing(full_name, name, folder_id):
    # Create a new connection
    service = connect()
    logging.debug('Start storing on Google Drive %s', name)
    # Define file properties
    file_metadata = {
      'name' : "%s.%s" % (name,ext),
      'parents': [ folder_id ]
    }

    media = MediaFileUpload(full_name, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    logging.debug('Storing ended')
    logging.debug('File %s stored', file.get('id'))


def drive(name, full_name, folder_id):
    try:
        # Storing the file on Google Drive
        storing(full_name, name, folder_id)
        # Check the usage of Google Drive and delete files if necessary
        drive_usage(folder_id)
        # Check the usage locally
        local_usage()
    except IOError:
    # The file does not exist. This is because the camera did not record
        logging.debug('Error, the file does not exist')


def start(url, user, pwd, port, cam_name, video_path, folder_id):

    cont = 0
    time.sleep(0)

    while True:

        # Define the name to use when recording
        name = "%s_%s" % (datetime.datetime.now().strftime('%Y%m%d%H%M'), cam_name)
        full_name = "{path}{name}.{ext}".format(path=video_path, name=name, ext=ext)

        # Storing
        recording_th = threading.Thread(name='cam%s_recording' % cam_name, target=recording, args=(url, user, pwd, port, full_name))
        recording_th.start()
        recording_th.join()
        # Zipping and storing on google drive
        threading.Thread(name='cam%s_flux' % cam_name, target=drive, args=(name, full_name, folder_id)).start()

        cont += 1

        print threading.enumerate()


if '__main__':

    # List files in cams folder
    for file in glob.glob('cams/*.json'):
        with open(file) as data_file:
            data = json.load(data_file)
            # Store cam parameters
            url = data['url']
            port = data['port']
            user = data['user']
            pwd = data['pwd']
            folder_id = data['folder_id']

            cam_name = url.split('.')[-1]
            video_path = 'video/%s/' % cam_name
            # video_path = 'video\\'

            # Start the thread to record
            threading.Thread(name='cam%s' % cam_name, target=start, args=(url, user, pwd, port, cam_name, video_path, folder_id)).start()

