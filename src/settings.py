import glob
import inspect
import json
import logging.config
import os
import shutil


def clean_dirs(dirs):
    for path in dirs:
        if os.path.exists(path):
            shutil.rmtree(path)
        if not os.path.exists(path):
            os.makedirs(path)


CURRENT_DIR = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
BASE_DIR = os.path.dirname(CURRENT_DIR)
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
BASE_VIDEO_DIR = os.path.join(BASE_DIR, 'video')
CONFIG_DIR = os.path.join(BASE_DIR, 'configs')
CONFIG_CAM_DIR = os.path.join(CONFIG_DIR, 'cams')
CONFIG_CREDENTIALS_DIR = os.path.join(CONFIG_DIR, 'credentials')
VIDEO_DIRS = []
for file in glob.glob(f'{CONFIG_CAM_DIR}/*.json'):
    with open(file) as data_file:
        data = json.load(data_file)
        VIDEO_DIRS.append(os.path.join(BASE_VIDEO_DIR, data['name']))

dirs_to_clean = [LOGS_DIR] + VIDEO_DIRS
clean_dirs(dirs_to_clean)

# Bandwidth
check_bdw = True
download_thhreshold = 3
sleep_time_high_bdw = 60
sleep_time_not_high_bdw = 60 * 5

# Schedule time
allowed_schedule = {0: ((0, 10), (21, 24)),
                    1: ((0, 10), (22, 24)),
                    2: ((0, 10), (22, 24)),
                    3: ((0, 10), (22, 24)),
                    4: ((0, 10), (22, 24)),
                    5: ((0, 10), (22, 24)),
                    6: ((0, 10), (22, 24)),
                    7: ((0, 10), (22, 24))}
sleep_time_not_allowed_time = 60

# Recording parameters
ext = 'mp4'
duration = 30
dimMB = 1 * 1024 * 1024
compression = 28

# Local parameter
localLim = 1024 * 1024 * 1024 * 20
# localLim = 1024*1024*200

# Driver parameters
scopes = 'https://www.googleapis.com/auth/drive'
# driveLim = 1024 * 1024 * 1024 * 4
driveLim = 1024 * 1024 * 100
cred_name = f'{CONFIG_CREDENTIALS_DIR}/credentials.json'
# cred_name = 'credentialMu.json'


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'simple',
            'stream': 'ext://sys.stdout'
        },
        'debug_file': {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'simple',
            'filename': os.path.join(LOGS_DIR, 'debug_logs.log'),
            'mode': 'w'
        },
        'permanent_debug_file': {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'simple',
            'filename': os.path.join(LOGS_DIR, 'permanent_debug_logs.log'),
            'mode': 'a'
        },
        'info_file': {
            'class': 'logging.FileHandler',
            'level': 'INFO',
            'formatter': 'simple',
            'filename': os.path.join(LOGS_DIR, 'info_logs.log'),
            'mode': 'w'
        },
    },
    'loggers': {
        'cam_recording': {
            'level': 'DEBUG',
            'handlers': ['console', 'debug_file', 'info_file', 'permanent_debug_file']
        }
    }
}

logging.config.dictConfig(LOGGING)