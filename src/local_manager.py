import logging
import os
import datetime
import settings

logger = logging.getLogger('cam_recording')


class LocalManager:

    def __init__(self):
        pass

    def store(self):
        pass

    def get_size_filename(self, start_path='.'):
        total_size = 0
        files = []
        for dirpath, dirnames, filenames in os.walk(start_path):
            for f in [x for x in filenames if x.endswith(settings.ext)]:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
                files.append(f)
        return total_size, files

    def delete_former_files(self, cam_name):
        """
        Delet files from local storage if we
        overcome the allowed threshold
        :param cam_name:
        :return:
        """
        video_path = "{base_dir}/{cam_name}".format(base_dir=settings.BASE_VIDEO_DIR, cam_name=cam_name)
        logger.debug('Checking local usage')
        total_size, files = self.get_size_filename(video_path)
        file_dates = [(datetime.datetime.strptime(name.split('_')[0], '%Y%m%d%H%M'), name) for name in files]
        sorted_dates = sorted(file_dates, key=lambda x: x[0], reverse=True)
        while total_size > settings.localLim:
            to_delete = sorted_dates.pop()
            logger.debug('Delete %s from disk', str(to_delete[1]))
            os.remove(os.path.join(video_path, to_delete[1]))
            total_size, _ = self.get_size_filename(video_path)
        else:
            logger.debug('Local limit: %s. Usage: %s', settings.localLim, total_size)
