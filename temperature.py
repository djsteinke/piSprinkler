import json
import datetime as dt
import logging

from dateutil import parser
import threading

from static import get_temperature
from properties import temp_refresh_interval

module_logger = logging.getLogger('main.program')


class Temperature(object):
    def __init__(self):
        self._today = {
            "date": "2020-01-01 00:00:00",
            "temp": [],
            "humidity": [],
            "temp_max": 0,
            "temp_min": 0
        }
        self._hist = {"history": []}
        self._date = dt.date.today()
        self.load()

    def get_today_avg(self):
        t_tot = 0
        t_cnt = 0
        avg = [0.0, 0.0]
        for t in self._today["temp"]:
            t_tot += t
            t_cnt += 1
        if t_cnt > 0:
            avg[0] = round(t_tot/t_cnt, 2)
        else:
            avg[0] = 0
        h_tot = 0
        h_cnt = 0
        for h in self._today["humidity"]:
            h_tot += h
            h_cnt += 1
        if h_cnt > 0:
            avg[1] = round(h_tot/h_cnt, 1)
        else:
            avg[1] = 0
        return avg

    def add_temp(self):
        c = get_temperature()
        module_logger.debug(f"add_temp() temp[{c[0]}] humidity[{c[1]}]")
        self._today["temp"].append(c[0])
        self._today["humidity"].append(c[1])
        avg = self.get_today_avg()
        if self._today["temp_max"] == 0 or self._today["temp_max"] < c[0]:
            self._today["temp_max"] = c[0]
        if self._today["temp_min"] == 0 or self._today["temp_min"] > c[0]:
            self._today["temp_min"] = c[0]
        found = False
        for hist in self._hist["history"]:
            if hist["dt"] == self._today["date"]:
                hist["tAvg"] = avg[0]
                hist["hAvg"] = avg[1]
                if self._today["temp_max"] == 0 or self._today["temp_max"] < c[0]:
                    hist["tMax"] = c[0]
                if self._today["temp_min"] == 0 or self._today["temp_min"] > c[0]:
                    hist["tMin"] = c[0]
                run_time = dt.datetime.now()
                run_time = run_time.replace(microsecond=0)
                new_temp = {
                    "time": str(run_time),
                    "t": c[0],
                    "h": c[1]
                }
                hist['history'].append(new_temp)
                found = True
                break
        if not found:
            run_time = dt.datetime.now()
            run_time = run_time.replace(microsecond=0)
            self._hist["history"].append({
                "dt": self._today["date"],
                "tAvg": avg[0],
                "hAvg": avg[1],
                "tMax": c[0],
                "tMin": c[0],
                "history": [
                    {
                        "time": str(run_time),
                        "t": c[0],
                        "h": c[1]
                    }
                ]
            })
        self.save()

    def reset_today(self):
        today = dt.date.today()
        self._today["date"] = str(today)
        self._today["temp"] = []
        self._today["humidity"] = []
        self._today["temp_min"] = 0
        self._today["temp_max"] = 0

    def get_today(self):
        return self._today

    def get_today_max(self):
        return [self._today["temp_max"], self._today["temp_min"]]

    def save(self):
        f = open("t.json", "w")
        f.write(json.dumps(self._hist, indent=4))
        f.close()
        f = open("today_t.json", "w")
        f.write(json.dumps(self._today, indent=4))
        f.close()

    def load(self):
        try:
            tmp = open("t.json", "r")
            self._hist = json.loads(tmp.read())
            tmp.close()
            td = open("today_t.json", "r")
            self._today = json.loads(td.read())
            td.close()
            self._date = parser.parse(self._today["date"]).date()
        except FileNotFoundError:
            self.save()

    def start(self):
        timer = threading.Timer(10, self.record)
        timer.start()

    def record(self):
        if dt.date.today() != self._date:
            self.reset_today()
            self._date = dt.date.today()
        self.add_temp()
        timer = threading.Timer(temp_refresh_interval, self.record)
        timer.start()

    @property
    def hist(self):
        return self._hist

