import json
import os

from static import fdir

setup_msg = {
    "average_temps": [32.0, 28.0, 35.1, 49.1, 51.6, 65.6, 75.7, 75.4, 69.3, 43.7, 36.2, 33.7],
    "watering_times": [
        [0, 0, 0, 0, 12, 17, 18, 14, 11, 0, 0, 0],
        [0, 0, 0, 0, 30, 43, 45, 34, 28, 0, 0, 0]
    ],
    "zones": [
        {
            "zone": 1,
            "type": 1,
            "pin": 1
        },
        {
            "zone": 2,
            "type": 1,
            "pin": 1
        },
        {
            "zone": 3,
            "type": 1,
            "pin": 1
        },
        {
            "zone": 4,
            "type": 0,
            "pin": 1
        },
        {
            "zone": 5,
            "type": 1,
            "pin": 1
        }
    ],
    "programs": [
        {
            "nextRunTime": "2020-01-01 06:30:00",
            "startTime": "2000-01-01 06:30:00",
            "interval": 1,
            "steps": [
                {
                    "step": 1,
                    "zone": 3
                },
                {
                    "step": 2,
                    "zone": 1
                },
                {
                    "step": 3,
                    "zone": 4
                },
                {
                    "step": 4,
                    "zone": 2
                },
                {
                    "step": 5,
                    "zone": 5
                }
            ]
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
        except FileNotFoundError:
            self.save()

    def save(self):
        global f_setup
        f = open(f_setup, "w")
        f.write(json.dumps(self._setup, indent=4))
        f.close()

    def load(self):
        global f_setup
        try:
            f = open(f_setup, "r")
            self._setup = json.loads(f.read())
            f.close()
        except FileNotFoundError:
            self.save()

    @property
    def setup(self):
        return self._setup
