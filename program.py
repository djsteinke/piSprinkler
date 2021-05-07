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
        self._step = 0
        self._run_time = 0.0
        self._time = 0.0
        self._running = False

    def start(self):
        module_logger.debug("start()")
        self.run_step()

    def stop(self):
        module_logger.debug("stop()")
        if self._r is not None:
            self._step = -1
            self._r.off()

    def run_step(self):
        self._running = False
        self._time = 0
        self._run_time = 0
        if self._step < 0 or self._step >= len(self._p["steps"]):
            if self._step < 0:
                module_logger.debug("cancelled()")
            else:
                module_logger.debug("complete()")
            self._r = None
            if self._callback is not None:
                self._callback()
        else:
            log_msg = f"run_step() [{self._step+1} of {len(self._p['steps'])}]"
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
                            t = step['time']*60
                        else:
                            t = self.det_run_time(step['percent']/100.0, head)
                            t = t*12.0/(28.0/self._p['interval'])
                        log_msg += f" zone[{zone}] head[{head}] pin[{pin}] time[{t:.1f}]"
                        if t > 0:
                            self._running = True
                            run = False
                            self._time = 0
                            self._run_time = t
                            self._r.set_run_time(int(t))
                            self._r.set_wait(step['wait']*60)
                            self._r.on()
                            timer = threading.Timer(60, self.set_run_time)
                            timer.start()
                        else:
                            run = True
            module_logger.debug(log_msg)
            self._step += 1
            if run:
                self.run_step()

    def set_run_time(self):
        if self._running:
            self._time += 1
            timer = threading.Timer(60, self.set_run_time)
            timer.start()

    def det_run_time(self, p, h):
        # h = step["type"]
        # p = step["percent"]/100.0
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
            avg_temp = act_temp/act_cnt
        per_temp = 1.0
        if self._s['average_temps'][month] > 0:
            per_temp = get_f_from_c(avg_temp)/self._s['average_temps'][month]
        return self._s['watering_times'][h][month]*per_temp*60.0*p

    @property
    def p(self):
        return self._p

    @property
    def step(self):
        return self._step

    @property
    def time(self):
        return self._time

    @property
    def run_time(self):
        return self._run_time

    @property
    def running(self):
        return self._running
