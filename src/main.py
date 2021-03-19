import datetime
import glob
import json
import logging
import shlex
import subprocess
import threading
import time

import speedtest

import drive_manager
import local_manager
import settings

logger = logging.getLogger('cam_recording')
n_files = None


def bandwidth(high_bdw):
    s = speedtest.Speedtest()
    s.get_servers()
    s.get_best_server()
    s.download()
    s.upload()
    res = s.results.dict()
    download_mbs = round(res["download"] / (10 ** 6), 2)
    high_bdw[0] = (download_mbs / len(config_files)) >= settings.download_threshold


def unpack(data):
    return data['name'], data['url'], data['port'], data['user'], data['pwd'], data['folder_id']


def start(data):
    cam_name, url, port, user, pwd, folder_id = unpack(data)
    last_bdw_check = - float('inf')

    # Lists are mutable objects. Not
    # the most elegant way, but it works
    # to change the variable in thread
    high_bdw = [True]

    while True:
        video_name = "%s_%s" % (datetime.datetime.now().strftime('%Y%m%d%H%M'), cam_name)
        full_name = "{base_dir}/{cam_name}/{name}.{ext}".format(base_dir=settings.BASE_VIDEO_DIR,
                                                                cam_name=cam_name,
                                                                name=video_name,
                                                                ext=settings.ext)
        # If I am not the allowed time range, pass
        now = datetime.datetime.now()
        weekday = now.weekday()
        hour = now.hour

        allowed_hours = settings.allowed_schedule.get(weekday)
        if allowed_hours is not None and any(x <= hour <= y for x, y in allowed_hours):
            # If bandwidth is below a given threshold,
            # sleep for an higher time
            # Otherwise launch
            bdw_sleept = settings.sleep_time_high_bdw if high_bdw[0] else settings.sleep_time_not_high_bdw
            if settings.check_bdw and (time.time() - last_bdw_check) > bdw_sleept:
                bandwidth_th = threading.Thread(name='%s_above_th' % video_name,
                                                target=bandwidth,
                                                args=(high_bdw,))
                bandwidth_th.start()
                last_bdw_check = time.time()

            if high_bdw[0]:
                # Recording
                recording_th = threading.Thread(name='%s_recording' % video_name,
                                                target=recording,
                                                args=(url, user, pwd, port, full_name))
                recording_th.start()
                recording_th.join()

                # Drive saving and delete
                threading.Thread(name='%s_drive_storing' % video_name,
                                 target=store_and_delete,
                                 args=(video_name, cam_name, full_name, folder_id)).start()
            else:
                logger.info('Bandwidth below threshold, sleeping for %s seconds',
                            settings.sleep_time_not_high_bdw)
                time.sleep(settings.sleep_time_not_high_bdw)
        else:
            logger.info('Not allowed recording time, sleeping for %s seconds',
                        settings.sleep_time_not_allowed_time)
            time.sleep(settings.sleep_time_not_allowed_time)


def store_and_delete(video_name, cam_name, full_name, folder_id):
    drive_man = drive_manager.DriveManager()
    local_man = local_manager.LocalManager()
    try:
        # Storing the file on Google Drive
        drive_man.store(full_name, video_name, folder_id)
        # Check the usage of Google Drive and delete files if necessary
        drive_man.get_usage(folder_id)
        # Check the usage locally and delete files if necessary
        local_man.get_usage(cam_name)
    except IOError:
        # The file does not exist. This is because the camera did not record
        logger.debug('Error, the file does not exist')


def recording(url, user, pwd, port, full_name, duration=10):
    logger.info('Start to record file %s', full_name)
    # Recording the file with ffmpeg by using duration or dimension
    lasting = f"-t {duration}" if duration else f"-fs {settings.dimMB}"
    ffmpeg_cmd = 'ffmpeg -i rtsp://{user}:{pwd}@{url}:{port} -vcodec libx264 ' \
                 '-crf {compr} -acodec copy -y -f h264 {lasting} "{full_name}"'.format(user=user, pwd=pwd, url=url,
                                                                                       port=port,
                                                                                       full_name=full_name,
                                                                                       lasting=lasting,
                                                                                       compr=settings.compression)
    logger.info('Ffmpeg Command: %s', ffmpeg_cmd)
    subprocess.Popen(shlex.split(ffmpeg_cmd),
                     stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL).communicate()
    logger.debug('Recording ended')


if __name__ == '__main__':
    config_files = glob.glob(f'{settings.CONFIG_CAM_DIR}/97.json')
    for file in config_files:
        with open(file) as data_file:
            logger.info('Config file opened %s', file)
            threading.Thread(target=start, args=(json.load(data_file),)).start()
