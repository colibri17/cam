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
check_bdw = False
bdw_threshold = 3
sleep_time_high_bdw = 60
sleep_time_not_high_bdw = 60 * 5

# Schedule time
allowed_schedule = {0: (("00:00", "09:59"), ("22:00", "23:59")),
                    1: (("00:00", "09:59"), ("22:00", "23:59")),
                    2: (("00:00", "19:59"), ("22:00", "23:59")),
                    3: (("00:00", "09:59"), ("22:00", "23:59")),
                    4: (("00:00", "09:59"), ("22:00", "23:59")),
                    5: (("00:00", "09:45"), ("22:00", "23:59")),
                    6: (("00:00", "09:59"), ("22:00", "23:59"))}
sleep_time_not_allowed_time = 60

# Recording parameters
ext = 'mp4'
dimMB = 1 * 1024 * 1024
compression = 28

# Local parameter
localLim = 1024 * 1024 * 1024 * 1
driveLim = 1024 * 1024 * 500

# Driver parameters
scopes = 'https://www.googleapis.com/auth/drive'
cred_name = f'{CONFIG_CREDENTIALS_DIR}/credentials.json'


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(asctime)s - %(threadName)s - %(levelname)s - %(message)s'
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
