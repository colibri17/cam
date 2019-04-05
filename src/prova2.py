

import os
import datetime
import zipfile
import threading
import logging

import httplib2
from apiclient.discovery import build
from apiclient.http import MediaFileUpload
from oauth2client.service_account import ServiceAccountCredentials
from apiclient import errors

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
dimMB = 20

SCOPES = 'https://www.googleapis.com/auth/drive'
#driveLim = 1024*1024*1024*10
driveLim = 1024*1024*200

# Logger
logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-10s) %(message)s',
                    )


def connect():
    logging.debug('Connecting')
    credential_dir = os.path.join(os.getcwd(), '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir, 'credential.json')
    credentials = ServiceAccountCredentials.from_json_keyfile_name(credential_path, scopes=SCOPES)
    http = credentials.authorize(httplib2.Http())
    service = build('drive', 'v3', http=http, cache_discovery=False)
    logging.debug('Connected!')
    return service

service = connect()
about = service.about().get(fields="user, storageQuota").execute()
limit = int(about['storageQuota']['limit'])
usage = int(about['storageQuota']['usage'])
print about
print limit
print usage

# Retrieve the items in Google drive
results = service.files().list(pageSize=1000, fields="nextPageToken, files(id, name)").execute()
items = results.get('files', [])
print items
# Get the list of files
names_id = [(item['name'], item['id']) for item in items]
for el in names_id:
    try:
        service.files().delete(fileId=el[1]).execute()
    except errors.HttpError:
        print 'error'
print js

# Order by the last one
dates_id = [(datetime.datetime.strptime(name[:-4], '%Y%m%d_%H%M'), id) for (name, id) in names_id]
sorted_dates_id = sorted(dates_id, key = lambda x: x[0], reverse = True)
# Delete the last one up to the usage is below the fixed limit
print sorted_dates_id
while usage > driveLim:
    # Delete the first element in the list
    to_delete = sorted_dates_id.pop()
    # Delete from Google Drive that ID
    logging.debug('Delete %s from Google Drive', str(to_delete[0]))
    service.files().delete(fileId=to_delete[1]).execute()

    about = service.about().get(fields="user, storageQuota").execute()
    usage = int(about['storageQuota']['usage'])