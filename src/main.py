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

download_th = 3


def bandwidth():
    s = speedtest.Speedtest()
    s.get_servers()
    s.get_best_server()
    s.download()
    s.upload()
    res = s.results.dict()

    download_mbs = round(res["download"] / (10 ** 6), 2)
    upload_mbs = round(res["upload"] / (10 ** 6), 2)
    print('done', download_mbs, upload_mbs)
    if download_mbs < download_th:
        above_th = False
    else:
        print('above threshodl!!')
        above_th = True


def unpack(data):
    return data['name'], data['url'], data['port'], data['user'], data['pwd'], data['folder_id']


def start(data):
    cam_name, url, port, user, pwd, folder_id = unpack(data)

    above_th = False
    last_exec = - float('inf')

    while True:

        video_name = "%s_%s" % (datetime.datetime.now().strftime('%Y%m%d%H%M'), cam_name)
        full_name = "{base_dir}/{cam_name}/{name}.{ext}".format(base_dir=settings.BASE_VIDEO_DIR,
                                                                cam_name=cam_name,
                                                                name=video_name,
                                                                ext=settings.ext)

        # If I am not in the allowed time range, pass
        now = datetime.datetime.now()
        # If bandwith is below a given threshold, pass
        if not above_th:
            last_threshold = 60
        else:
            last_threshold = 60 * 5
        print('last threshold', last_threshold)
        if settings.check_bandwidth and (time.time() - last_exec) > last_threshold:
            print('executing bandwidth')
            bandwidth_th = threading.Thread(name='%s_above_th' % video_name, target=bandwidth)
            bandwidth_th.start()
            print('result', above_th)
            last_exec = time.time()

        if above_th:
            # Recording
            recording_th = threading.Thread(name='%s_locally_recording' % video_name, target=recording,
                                            args=(url, user, pwd, port, full_name))
            recording_th.start()
            recording_th.join()

            # Drive saving and delete
            threading.Thread(name='%s_drive_storing' % video_name, target=store_and_delete,
                             args=(video_name, cam_name, full_name, folder_id)).start()
        else:
            logger.info('Below bandwidth threshold, sleeping')
            time.sleep(60)


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


def recording(url, user, pwd, port, full_name, duration=False):
    logger.info('Start to record file %s', full_name)
    # Record the file with ffmpeg by using duration
    if duration:
        ffmpeg_cmd = 'ffmpeg -i rtsp://{user}:{pwd}@{url}:{port} -vcodec libx264 ' \
                     '-crf {compr} -acodec copy -y -f h264 -t {dur} "{full_name}"'.format(user=user, pwd=pwd, url=url,
                                                                                          port=port,
                                                                                          full_name=full_name,
                                                                                          dur=duration,
                                                                                          compr=settings.compression)
        logger.info('Ffmpeg Command: %s', ffmpeg_cmd)
    # Record the file with ffmpeg by using file size
    else:
        ffmpeg_cmd = 'ffmpeg -i rtsp://{user}:{pwd}@{url}:{port} -vcodec libx264 ' \
                     '-crf {compr} -acodec copy -y -f h264 -fs {dim} "{full_name}"'.format(user=user, pwd=pwd, url=url,
                                                                                           port=port,
                                                                                           full_name=full_name,
                                                                                           dim=settings.dimMB,
                                                                                           compr=settings.compression)
        logger.info('Ffmpeg Command: %s', ffmpeg_cmd)
    subprocess.Popen(shlex.split(ffmpeg_cmd), stdout=subprocess.PIPE).communicate()
    logger.debug('Recording ended')


if __name__ == '__main__':
    for file in glob.glob(f'{settings.CONFIG_CAM_DIR}/229.json'):
        with open(file) as data_file:
            logger.info('Config file opened %s', file)
            threading.Thread(target=start, args=(json.load(data_file),)).start()
