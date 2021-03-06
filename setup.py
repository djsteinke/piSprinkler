import json

setup = {
    "zones": 5,
    "interval": 1,
    "startTime": "2000-01-01 06:30:00",
    "nextRunTime": "2020-01-01 06:30:00",
    "pins": [0, 1, 2, 3, 4],
    "programs": [
        {
            "nextRunTime": "2020-01-01 06:30:00",
            "steps": [
                {
                    "step": 1,
                    "zone": 3,
                    "time": [35, 40, 45, 50]
                },
                {
                    "step": 2,
                    "zone": 1,
                    "time": [35, 40, 45, 50]
                },
                {
                    "step": 3,
                    "zone": 4,
                    "time": [35, 40, 45, 50]
                },
                {
                    "step": 4,
                    "zone": 2,
                    "time": [35, 40, 45, 50]
                },
                {
                    "step": 5,
                    "zone": 5,
                    "time": [35, 40, 45, 50]
                }
            ]
        }
    ]
}


def save():
    f = open("setup.json", "w")
    f.write(json.dumps(setup))
    f.close()


def load():
    global setup
    try:
        f = open("setup.json", "r")
        setup = json.loads(f.read())
        f.close()
    except FileNotFoundError:
        save()


class Setup(object):
    def __init__(self):
        self._val = 1
