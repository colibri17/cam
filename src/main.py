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


def bandwidth(high_bdw):
    s = speedtest.Speedtest()
    s.get_servers()
    s.get_best_server()
    s.download()
    s.upload()
    res = s.results.dict()
    download_mbs = round(res["download"] / (10 ** 6), 2)
    high_bdw[0] = (download_mbs / len(config_cam_files)) >= settings.bdw_threshold


def unpack(data):
    return data['name'], data['url'], data['port'], data['user'], data['pwd'], data['folder_id']


def main(data):
    name, url, port, user, pwd, folder_id = unpack(data)
    last_bdw_check = - float('inf')

    # Lists are mutable objects. So, I can interact with
    # the thread by using this. Not
    # the most elegant way, but it works
    # to change the variable in thread
    high_bdw = [True]

    while True:
        recording_short_name = "%s_%s" % (datetime.datetime.now().strftime('%Y%m%d%H%M'), name)
        recording_full_name = "{base_dir}/{cam_name}/{name}.{ext}".format(base_dir=settings.BASE_VIDEO_DIR,
                                                                          cam_name=name,
                                                                          name=recording_short_name,
                                                                          ext=settings.ext)
        # If I am not the allowed time range, pass
        now = datetime.datetime.now()
        weekday = now.weekday()
        hour_minutes = now.strftime('%H:%M')
        allowed_times = settings.allowed_schedule.get(weekday)
        if allowed_times is not None and any(x <= hour_minutes <= y for x, y in allowed_times):
            # If bandwidth is below a given threshold,
            # sleep for an higher time
            # Otherwise launch
            bdw_sleept = settings.sleep_time_high_bdw if high_bdw[0] else settings.sleep_time_not_high_bdw
            if settings.check_bdw and (time.time() - last_bdw_check) > bdw_sleept:
                bandwidth_th = threading.Thread(name='%s_above_th' % recording_short_name,
                                                target=bandwidth,
                                                args=(high_bdw,))
                bandwidth_th.start()
                last_bdw_check = time.time()

            if high_bdw[0]:
                # Recording
                recording_th = threading.Thread(name='%s_recording' % recording_short_name,
                                                target=record,
                                                args=(url, user, pwd, port, recording_full_name))
                recording_th.start()
                recording_th.join()

                # Drive saving and delete
                threading.Thread(name='%s_drive_storing' % recording_short_name,
                                 target=store,
                                 args=(recording_short_name, name, recording_full_name, folder_id)).start()
            else:
                logger.info('Bandwidth below threshold, sleeping for %s seconds',
                            settings.sleep_time_not_high_bdw)
                time.sleep(settings.sleep_time_not_high_bdw)
        else:
            logger.info('Not allowed recording time, sleeping for %s seconds',
                        settings.sleep_time_not_allowed_time)
            time.sleep(settings.sleep_time_not_allowed_time)


def store(video_name, cam_name, full_name, folder_id):
    try:
        drive_man.store(full_name, video_name, folder_id)
        drive_man.delete_former_files(folder_id)
        logger.info('full_name %s', full_name)
        local_man.delete_former_files(cam_name)
    except IOError as e:
        logger.warning('Error %s', e)


def record(url, user, pwd, port, full_name):
    logger.info('Start to record on file %s', full_name)
    ffmpeg_cmd = 'ffmpeg -i rtsp://{user}:{pwd}@{url}:{port} -vcodec libx264 ' \
                 '-crf {compr} -acodec copy -y -f h264 -fs {dim} "{full_name}"'.format(user=user, pwd=pwd, url=url,
                                                                                       port=port,
                                                                                       full_name=full_name,
                                                                                       dim=settings.dimMB,
                                                                                       compr=settings.compression)
    logger.info('Ffmpeg Command: %s', ffmpeg_cmd)
    subprocess.Popen(shlex.split(ffmpeg_cmd), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).communicate()
    logger.debug('Recording ended')


if __name__ == '__main__':
    config_cam_files = glob.glob(f'{settings.CONFIG_CAM_DIR}/*.json')

    drive_man = drive_manager.DriveManager()
    local_man = local_manager.LocalManager()

    for file in config_cam_files:
        with open(file) as data_file:
            logger.info('Config file opened %s', file)
            threading.Thread(target=main, args=(json.load(data_file),)).start()
