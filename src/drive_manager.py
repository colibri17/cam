import datetime
import logging

import httplib2
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from oauth2client.service_account import ServiceAccountCredentials

import settings

logger = logging.getLogger('cam_recording')


class DriveManager:

    def __init__(self):
        pass

    def connect(self):
        logger.debug('Connecting')
        credentials = ServiceAccountCredentials.from_json_keyfile_name(settings.cred_name, scopes=settings.scopes)
        http = credentials.authorize(httplib2.Http())
        service = build('drive', 'v3', http=http, cache_discovery=False)
        logger.debug('Connected on Google Drive!')
        return service

    def store(self, full_name, name, folder_id):
        service = self.connect()
        logger.debug('Start storing on Google Drive %s', name)
        file_metadata = {
            'name': "%s.%s" % (name, settings.ext),
            'parents': [folder_id]
        }
        media = MediaFileUpload(full_name, resumable=True)
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        logger.debug('Storing ended')
        logger.debug('File %s stored', file.get('id'))

    def get_usage(self, folder_id):
        logger.debug('Checking drive usage')
        service = self.connect()
        # Retrieve the items in Google drive folder
        results = service.files().list(pageSize=1000, q="'%s' in parents" % folder_id,
                                       fields="nextPageToken, files(id, name, size)").execute()
        items = results.get('files', [])
        # Get the usage
        usage = sum([int(item['size']) for item in items])
        # Get the list of files
        names_id = [(item['name'], item['id']) for item in items if item['name'].endswith(settings.ext)]
        # Order by the last one
        dates_id = [(datetime.datetime.strptime(name.split('_')[0], '%Y%m%d%H%M'), id) for (name, id) in names_id]
        sorted_dates_id = sorted(dates_id, key=lambda x: x[0], reverse=True)
        # Delete the last one up to the usage is below the fixed limit
        while usage > settings.driveLim:
            # Delete the first element in the list
            to_delete = sorted_dates_id.pop()
            # Delete from Google Drive that ID
            logger.debug('Delete %s from Google Drive', str(to_delete[0]))
            service.files().delete(fileId=to_delete[1]).execute()
            # Update the usage
            results = service.files().list(pageSize=1000, q="'%s' in parents" % folder_id,
                                           fields="nextPageToken, files(id, name, size)").execute()
            items = results.get('files', [])
            usage = sum([int(item['size']) for item in items])
        else:
            logger.debug('Drive limit: %s. Usage: %s', settings.driveLim, usage)
