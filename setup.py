import json

setup_msg = {
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
    "interval": 1,
    "startTime": "2000-01-01 06:30:00",
    "nextRunTime": "2021-03-05 06:30:00",
    "programs": [
        {
            "nextRunTime": "2020-01-01 06:30:00",
            "steps": [
                {
                    "step": 1,
                    "zone": 3,
                    "time": [
                        35,
                        40,
                        45,
                        50
                    ]
                },
                {
                    "step": 2,
                    "zone": 1,
                    "time": [
                        35,
                        40,
                        45,
                        50
                    ]
                },
                {
                    "step": 3,
                    "zone": 4,
                    "time": [
                        35,
                        40,
                        45,
                        50
                    ]
                },
                {
                    "step": 4,
                    "zone": 2,
                    "time": [
                        35,
                        40,
                        45,
                        50
                    ]
                },
                {
                    "step": 5,
                    "zone": 5,
                    "time": [
                        35,
                        40,
                        45,
                        50
                    ]
                }
            ]
        }
    ]
}


class Setup(object):
    def __init__(self):
        global setup_msg
        self._setup = setup_msg
        try:
            f = open("setup.json", "r")
            self._setup = json.loads(f.read())
            f.close()
        except FileNotFoundError:
            self.save()

    def save(self):
        f = open("setup.json", "w")
        f.write(json.dumps(self._setup, indent=4))
        f.close()

    def load(self):
        try:
            f = open("setup.json", "r")
            self._setup = json.loads(f.read())
            f.close()
        except FileNotFoundError:
            self.save()

    @property
    def setup(self):
        return self._setup
