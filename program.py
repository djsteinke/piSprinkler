import logging

from relay import Relay
import datetime as dt
from static import watering_times, average_temps

module_logger = logging.getLogger('main.program')


class ProgramWithEvents(object):
    callback = None

    def on_complete(self, callback):
        self.callback = callback

    def complete(self):
        if self.callback is not None:
            self.callback(self)


class Program(ProgramWithEvents):
    def __init__(self, p, z, t):
        self._p = p
        self._z = z
        self._t = t
        self._step = 1

    def start(self):
        module_logger.debug("Program.start()")
        self.run_step()

    def run_step(self):
        print(f"run_step() {self._step} of {len(self._z)}")
        if self._step > len(self._p["steps"]):
            self.complete()
        else:
            for step in self._p["steps"]:
                if step["step"] == self._step:
                    zone = step["zone"]
                    pin = 0
                    head = -1
                    for z in self._z:
                        if z["zone"] == zone:
                            pin = z["pin"]
                            head = z["type"]
                            break
                    if pin > 0:
                        r = Relay(pin, self.run_step)
                        t = self.det_run_time(head)
                        print(f"zone[{zone}] head[{head}] pin[{pin}] time[{t}]")
                        if t > 0:
                            r.set_run_time(int(t))
                            r.on()
        self._step += 1

    def det_run_time(self, h):
        date = dt.datetime.today()
        month = dt.date.today().month - 1
        month = 6
        date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        date -= dt.timedelta(days=1)
        act_temp = 0
        act_cnt = 0
        for day in self._t["history"]:
            if day["date"] == str(date):
                act_temp += day["temp"]
                act_cnt += 1
                break
        date -= dt.timedelta(days=1)
        for day in self._t["history"]:
            if day["date"] == str(date):
                act_temp += day["temp"]
                act_cnt += 1
                break
        if act_cnt == 0:
            return 0
        else:
            avg_temp = act_temp/act_cnt
        per_temp = 1
        if average_temps[month] > 0:
            per_temp = avg_temp/average_temps[month]
        print(f"{avg_temp} {average_temps[month]} {watering_times[h][month]}")
        return watering_times[h][month]*per_temp
