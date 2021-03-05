import json
import datetime as dt


class Temperature(object):
    def __init__(self):
        self._hist = {"history": []}
        self._today = {
            "date": "2020-01-01",
            "temp": []
        }

    def get_today_avg(self):
        t_tot = 0
        t_cnt = 0
        for t in self._today["temp"]:
            t_tot += t
            t_cnt += 1
        if t_cnt > 0:
            return t_tot/t_cnt
        else:
            return 0

    def add_temp(self, t):
        self._today["temp"].append(t)
        avg = self.get_today_avg()
        found = False
        for hist in self._hist["history"]:
            if hist["date"] == self._today["date"]:
                hist["temp"] = avg
                found = True
        if not found:
            self._hist["history"].append({
                "date": self._today["date"],
                "temp": avg
            })
        self.save()

    def reset_temp(self):
        today = dt.date.today()
        self._today["date"] = str(today)
        self._today["temp"] = []

    def get_today(self):
        return self._today

    def save(self):
        f = open("temperature.json", "w")
        f.write(json.dumps(self._hist))
        f.close()
        f = open("today_temp.json", "w")
        f.write(json.dumps(self._today))
        f.close()

    def load(self):
        try:
            f = open("temperature.json", "r")
            self._hist = json.loads(f.read())
            f.close()
            f = open("today_temp.json", "r")
            self._today = json.loads(f.read())
            f.close()
        except FileNotFoundError:
            self.save()
