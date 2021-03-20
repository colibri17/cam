import datetime
import logging

import httplib2
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from oauth2client.service_account import ServiceAccountCredentials

import settings

logger = logging.getLogger('cam_recording')


class DriveManager:

    def __init__(self):
        pass

    def connect(self):
        """
        Connect to Google drive
        :return: None
        """
        logger.debug('Connecting')
        credentials = ServiceAccountCredentials.from_json_keyfile_name(settings.cred_name, scopes=settings.scopes)
        http = credentials.authorize(httplib2.Http(timeout=300))
        service = build('drive', 'v3', http=http, cache_discovery=False)
        logger.debug('Connected on Google Drive!')
        return service

    def store(self, full_name, short_name, folder_id):
        """
        Store the recording on google drive
        :param full_name: full name of recording, containing the full path
        :param short_name: short name of recording, containing just the name
        :param folder_id: id-folder on Google drive where storing the recordings
        :return: None
        """
        service = self.connect()
        logger.debug('Start storing on Google Drive %s', short_name)
        file_metadata = {
            'name': "%s.%s" % (short_name, settings.ext),
            'parents': [folder_id]
        }
        media = MediaFileUpload(full_name, resumable=True)
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute(num_retries=4)
        logger.debug('Storing ended')
        logger.debug('File %s stored', file.get('id'))

    def delete_former_files(self, folder_id):
        """
        Delete oldest file from Google Drive if we exceeded the
        allowed threshold
        :param folder_id: id-folder on Google drive used to store the recordings
        :return:
        """
        service = self.connect()
        logger.debug('Checking drive usage')
        results = service.files().list(pageSize=1000, q="'%s' in parents" % folder_id,
                                       fields="nextPageToken, files(id, name, size)").execute()
        items = results.get('files', [])
        usage = sum([int(item['size']) for item in items])
        names_id = [(item['name'], item['id']) for item in items if item['name'].endswith(settings.ext)]
        dates_id = [(datetime.datetime.strptime(name.split('_')[0], '%Y%m%d%H%M'), id) for (name, id) in names_id]
        sorted_dates_id = sorted(dates_id, key=lambda x: x[0], reverse=True)
        while usage > settings.driveLim:
            to_delete = sorted_dates_id.pop()
            logger.debug('Delete %s from Google Drive', str(to_delete[0]))
            try:
                # Another thread might have deleted the file
                service.files().delete(fileId=to_delete[1]).execute()
            except HttpError as e:
                logger.warning("Error %s", e)
            results = service.files().list(pageSize=1000, q="'%s' in parents" % folder_id,
                                           fields="nextPageToken, files(id, name, size)").execute()
            items = results.get('files', [])
            usage = sum([int(item['size']) for item in items])
        else:
            logger.debug('Drive limit: %s. Usage: %s', settings.driveLim, usage)
