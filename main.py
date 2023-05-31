import logging
import threading
import datetime as dt
import traceback
from time import sleep

import RPi.GPIO as GPIO

from programFB import ProgramFB
import firebase_db

logger = logging.getLogger('main')
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh = logging.FileHandler('/home/pi/projects/piSprinkler/log.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

degree_sign = u"\N{DEGREE SIGN}"

p = ProgramFB(None, None, None)
p_running = False

delay = dt.datetime.now()
check_fb_interval = 60
last_check_fb = dt.datetime.now()


def get_timestamp(val):
    return val if val < 9000000000 else val / 1000


def check_delay():
    global delay
    delay = dt.datetime.fromtimestamp(get_timestamp(firebase_db.current['delay']))


def check_program(now, program):
    global p_running, p
    next_date = dt.datetime.fromtimestamp(get_timestamp(program['nextRunTime']))
    if next_date < now and not p_running:
        interval = 1
        if next_date >= delay:
            interval = program["interval"]
            tempHistory = firebase_db.get_temp_history()
            p = ProgramFB(program, tempHistory, program_complete)
            if program['active']:
                p_running = True
                p.start()
        start_time = dt.datetime.fromtimestamp(get_timestamp(program["startTime"]))
        logger.debug(f"start_time : {str(start_time)}")
        next_date = now
        next_date += dt.timedelta(days=interval)
        next_date = next_date.replace(hour=start_time.hour, minute=start_time.minute, second=0, microsecond=0)
        program["nextRunTime"] = next_date.timestamp()
        firebase_db.set_next_run_time(program["name"], next_date.timestamp() * 1000)
        logger.info(f"{program['name']} : next run {next_date}")


def check_fb(now):
    global p_running, p, last_check_fb
    if now.timestamp() - last_check_fb.timestamp() >= check_fb_interval:
        try:
            logger.debug(".")
            if firebase_db.ref_loaded():
                check_delay()
                for key in firebase_db.setup['programs']:
                    program = firebase_db.setup['programs'][key]
                    check_program(now, program)
        except Exception:
            logger.error("check_fb()" + traceback.format_exc())
        last_check_fb = now


def program_complete():
    global p_running
    p_running = False


def run(action, key):
    global p, p_running
    logger.debug("run() action: " + action + " key: " + key + " running: " + str(p_running))
    if action == 'cancel' and p_running:
        p.cancel()
        p_running = False
        logger.debug("run() stopped")
    elif action == 'start':
        program = firebase_db.setup['programs'][key]
        if program is not None:
            if p_running:
                p.cancel()
                p_running = False
                sleep(3)
            p_running = True
            tempHistory = firebase_db.get_temp_history()
            p = ProgramFB(program, tempHistory, program_complete)
            threading.Timer(1, p.start).start()
            logger.debug("run() started")


if __name__ == '__main__':
    firebase_db.program_cb = run
    while True:
        try:
            dt_now = dt.datetime.now()
            threading.Thread(target=firebase_db.check_listeners, args=()).start()
            threading.Thread(target=check_fb, args=(dt_now,)).start()
        except Exception:
            logger.error(traceback.format_exc())
        sleep(15)
