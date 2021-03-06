import json
import datetime as dt
import threading

from static import get_temperature


class Temperature(object):
    def __init__(self):
        self._today = {}
        self._hist = {}
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
            avg[0] = t_tot/t_cnt
        else:
            avg[0] = 0
        h_tot = 0
        h_cnt = 0
        for h in self._today["humidity"]:
            h_tot += h
            h_cnt += 1
        if h_cnt > 0:
            avg[1] = h_tot/h_cnt
        else:
            avg[1] = 0
        return avg

    def add_temp(self):
        c = get_temperature()
        self._today["temp"].append(c[0])
        self._today["humidity"].append(c[1])
        avg = self.get_today_avg()
        found = False
        for hist in self._hist["history"]:
            if hist["date"] == self._today["date"]:
                hist["temp"] = avg[0]
                hist["humidity"] = avg[1]
                found = True
        if not found:
            self._hist["history"].append({
                "date": self._today["date"],
                "temp": avg[0],
                "humidity": avg[1]
            })
        self.save()

    def reset_today(self):
        today = dt.date.today()
        self._today["date"] = str(today)
        self._today["temp"] = []

    def get_today(self):
        return self._today

    def save(self):
        f = open("t.json", "w")
        f.write(json.dumps(self._hist))
        f.close()
        f = open("today_t.json", "w")
        f.write(json.dumps(self._today))
        f.close()

    def load(self):
        try:
            tmp = open("t.json", "r")
            self._hist = json.loads(tmp.read())
            tmp.close()
            td = open("today_t.json", "r")
            self._today = json.loads(td.read())
            td.close()
        except FileNotFoundError:
            self.save()

    def start(self):
        timer = threading.Timer(1800, self.record)
        timer.start()

    def record(self):
        if dt.date.today() != self._date:
            self.reset_today()
            self._date = dt.date.today()
        self.add_temp()
        timer = threading.Timer(1800, self.record)
        timer.start()

