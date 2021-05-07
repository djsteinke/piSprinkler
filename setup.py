import json
import logging
import os

from static import fdir

module_logger = logging.getLogger('main.setup')

setup_msg = {
    "average_temps": [32.0, 28.0, 35.1, 49.1, 51.6, 65.6, 75.7, 75.4, 69.3, 43.7, 36.2, 33.7],
    "watering_times": [
        [0, 0, 0, 0, 12, 17, 18, 14, 11, 0, 0, 0],
        [0, 0, 0, 0, 30, 43, 45, 34, 28, 0, 0, 0],
        [0, 0, 0, 0, 24, 35, 36, 27, 23, 0, 0, 0]
    ],
    "zones": [],
    "programs": [
        {
            "name": "value",
            "nextRunTime": "2020-01-01 06:30:00",
            "startTime": "2000-01-01 06:30:00",
            "interval": 1,
            "active": True,
            "steps": []
        }
    ]
}

f_setup = os.path.join(fdir, 'setup.json')


class Setup(object):
    def __init__(self):
        global setup_msg
        global f_setup
        self._setup = setup_msg
        try:
            f = open(f_setup, "r")
            self._setup = json.loads(f.read())
            f.close()
            module_logger.debug('Setup(exists)')
        except FileNotFoundError:
            self.save()
            module_logger.debug('Setup(FileNotFound)')

    def save(self):
        global f_setup
        f = open(f_setup, "w")
        f.write(json.dumps(self._setup, indent=4))
        f.close()
        module_logger.debug('save()')

    def load(self):
        global f_setup
        try:
            f = open(f_setup, "r")
            self._setup = json.loads(f.read())
            f.close()
            module_logger.debug('load(exists)')
        except FileNotFoundError:
            self.save()
            module_logger.debug('load(FileNotFound)')

    @property
    def setup(self):
        return self._setup
