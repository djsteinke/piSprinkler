import logging
import threading

from relay import Relay
import datetime as dt
from static import get_f_from_c

module_logger = logging.getLogger('main.program')


class Program(object):
    def __init__(self, p, s, t, callback):
        self._p = p
        self._s = s
        self._t = t
        self._r = None
        self._callback = callback
        self._step_cnt = 0
        self._step = 0
        self._step_time = 0
        self._run_time = 0
        self._running = False
        self._timer = None

    def start(self):
        module_logger.debug("start()")
        self._step_cnt = len(self._p["steps"])
        self._running = True
        self.run_step()

    def cancel(self):
        module_logger.debug("cancel()")
        self._running = False
        if self._r is not None:
            self._r.off()

    def stop(self):
        module_logger.debug("stop()")
        self._running = False
        self._r = None
        self._step = 0
        self._step_cnt = 0
        if self._callback is not None:
            self._callback()

    def run_step(self):
        self._step += 1
        self._step_time = 0
        self._run_time = 0
        if self._timer is not None:
            self._timer.cancel()
        if not self._running or self._step >= self._step_cnt:
            self.stop()
        else:
            log_msg = f"run_step() [{self._step + 1} of {self._step_cnt}]"
            run = True
            for step in self._p['steps']:
                if step['step'] == self._step:
                    head = -1
                    pin = 0
                    zone = step['zone']
                    for z in self._s['zones']:
                        if z['zone'] == zone:
                            pin = z['pin']
                            head = z['type']
                            break
                    if pin > 0 and head >= 0:
                        self._r = Relay(pin, self.run_step)
                        if step['time'] > 0:
                            t = step['time'] * 60
                        else:
                            t = self.det_run_time(step['percent'] / 100.0, head)
                            t = t * 12.0 / (28.0 / self._p['interval'])
                        log_msg += f" zone[{zone}] head[{head}] pin[{pin}] time[{t:.1f}]"
                        if t > 0:
                            run = False
                            self._step_time = int(t)
                            self._r.set_run_time(int(t))
                            w = 3
                            if step['wait'] > 0:
                                w = step['wait'] * 60
                            self._r.set_wait(w)
                            self._r.on()
                            self._timer = threading.Timer(60, self.set_run_time)
                            self._timer.start()
                        else:
                            run = True
            module_logger.debug(log_msg)
            self._step += 1
            if run:
                self.run_step()

    def set_run_time(self):
        if self._running:
            self._run_time += 1
            self._timer = threading.Timer(60, self.set_run_time)
            self._timer.start()

    def det_run_time(self, p, h):
        date = dt.datetime.today()
        month = dt.date.today().month - 1
        date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        date -= dt.timedelta(days=1)
        act_temp = 0
        act_cnt = 0
        for day in self._t["history"]:
            if day["dt"] == str(date.date()):
                act_temp += day["tAvg"]
                act_cnt += 1.0
                break
        date -= dt.timedelta(days=1)
        for day in self._t["history"]:
            if day["dt"] == str(date.date()):
                act_temp += day["tAvg"]
                act_cnt += 1.0
                break
        if act_cnt == 0:
            module_logger.debug("det_run_time() temp history not found.")
            return 0
        else:
            avg_temp = act_temp / act_cnt
        per_temp = 1.0
        if self._s['average_temps'][month] > 0:
            per_temp = get_f_from_c(avg_temp) / self._s['average_temps'][month]
        return self._s['watering_times'][h][month] * per_temp * 60.0 * p

    @property
    def p(self):
        return self._p

    @property
    def step(self):
        return self._step

    @property
    def step_cnt(self):
        return self._step_cnt

    @property
    def step_time(self):
        return self._step_time

    @property
    def run_time(self):
        return self._run_time

    @property
    def running(self):
        return self._running
