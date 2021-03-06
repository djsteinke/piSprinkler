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

temperature = Temperature()


def check():
    print("check()")
    next_date = parser.parse(setup["nextRunTime"])
    conditions = get_temperature()
    if dt.date.today() > parser.parse(temperature.get_today()["date"]).date():
        temperature.reset_temp()
    temperature.add_temp(conditions[0])
    print(temperature.get_today_avg())
    if next_date < dt.datetime.now():
        # TODO start
        start_time = parser.parse(setup["startTime"])
        next_date = dt.datetime.now()
        next_date += dt.timedelta(days=setup["interval"])
        next_date = next_date.replace(hour=start_time.hour, minute=start_time.minute, second=0, microsecond=0)
        setup["nextRunTime"] = str(next_date)
        save()
        print(next_date)
    print(json.dumps(setup))
    timer = threading.Timer(60, check)
    timer.start()


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


@app.route('/getTemp')
def get_temp():
    cond = get_temperature()
    ret = {
        "temp": f"{cond[0]:0.1f}",
        "humidity": f"{cond[1]:0.0f}",
        "avg_temp": temperature.get_today()
    }
    return json.dumps(ret)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')


if __name__ == '__main__':
    host_name = socket.gethostbyname(socket.gethostname())
    logger.info("machine host_name[" + host_name + "]")
    print(host_name + "[" + host_name[0: 3] + "]")
    if host_name[0: 3] == "192" or host_name[0: 3] == "127":
        host_name = "192.168.0.152"
    else:
        host_name = "localhost"
    logger.info("app host_name[" + host_name + "]")
    load()
    check()

    # app.run(ssl_context='adhoc', host=host_name, port=1983)
    app.run(host=host_name, port=1983)
