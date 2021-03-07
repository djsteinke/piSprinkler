import json
import logging
import socket
import threading
import datetime as dt
from dateutil import parser

import RPi.GPIO as GPIO

from flask import Flask, request, jsonify, send_from_directory

from temperature import Temperature
from setup import setup, save, load
from relay import Relay
from static import get_logging_level, get_temperature
import os

degree_sign = u"\N{DEGREE SIGN}"

app = Flask(__name__)

# create logger with 'spam_application'
logger = logging.getLogger('main')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('log.log')
fh.setLevel(get_logging_level())
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

relay = Relay(0)

zones = [Relay(0), Relay(1), Relay(1), Relay(1), Relay(1)]

t = Temperature()


def check():
    next_date = parser.parse(setup["nextRunTime"])
    logger.debug(f"check() now[{dt.datetime.now()}] next[{next_date}]")
    if next_date < dt.datetime.now():
        # TODO start
        start_time = parser.parse(setup["startTime"])
        next_date = dt.datetime.now()
        next_date += dt.timedelta(days=setup["interval"])
        next_date = next_date.replace(hour=start_time.hour, minute=start_time.minute, second=0, microsecond=0)
        setup["nextRunTime"] = str(next_date)
        save()
        logger.info(next_date)
    timer = threading.Timer(60, check)
    timer.start()


def get_temp_str(c):
    return f"{c:.1f}c" + f" [{get_f(c):.1f}f]"


def get_f(c):
    return c*1.8+32


@app.route('/relay/<pin_in>')
def relay_action(pin_in):
    logger.debug(f"relay[{pin_in}] action[ON] time[1]")
    relay.set_pin(int(pin_in))
    action = "on"
    if action == "on":
        relay.on()
    else:
        relay.off()
    # pin_state = GPIO.input(pin)
    return jsonify(message="Success",
                   statusCode=200,
                   data=action), 200


@app.route("/setup/<action>")
def setup_cmd(action):
    if action == "load":
        load()


@app.route('/getTemp')
def get_temp():
    cond = get_temperature()
    cond_avg = t.get_today_avg()
    ret = {
        "temp": get_temp_str(cond[0]),
        "humidity": f"{cond[1]:.0f}%",
        "avg_temp": get_temp_str(cond_avg[0]),
        "avg_humidity": f"{cond_avg[1]:.0f}%"
    }
    return


@app.route('/getTempStr')
def get_temp_str():
    cond = get_temperature()
    cond_avg = t.get_today_avg()
    ret = f"temp: {get_temp_str(cond[0])} \n" + f"humidity: {cond[1]:.0f}% \n"
    ret += f"avg_temp: {get_temp_str(cond_avg[0])} \n" + f"avg_humidity: {cond_avg[1]:.0f}%"
    return ret


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')


if __name__ == '__main__':
    host_name = socket.gethostbyname(socket.gethostname())
    logger.info("machine host_name[" + host_name + "]")
    print(host_name + "[" + host_name[0: 3] + "]")
    if host_name[0: 3] == "127":
        host_name = "192.168.0.152"
    elif host_name[0: 3] == "192":
        val = 1
    else:
        host_name = "localhost"
    logger.info("app host_name[" + host_name + "]")
    load()
    check()
    t.start()
    # app.run(ssl_context='adhoc', host=host_name, port=1983)
    app.run(host=host_name, port=1983)
