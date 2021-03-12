import json
import logging
import socket
import threading
import datetime as dt
from dateutil import parser

import RPi.GPIO as GPIO

from flask import Flask, request, jsonify, send_from_directory

from program import Program
from temperature import Temperature
from setup import Setup
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

t = Temperature()
s = Setup()
p_running = False


def check():
    global p_running
    for program in s.setup['programs']:
        next_date = parser.parse(program["nextRunTime"])
        logger.debug(f"check() now[{dt.datetime.now()}] next[{next_date}]")
        if next_date < dt.datetime.now() and not p_running:
            p = Program(s.setup["programs"][0], s.setup, t.hist, program_complete)
            p_running = True
            p.start()
            start_time = parser.parse(program["startTime"])
            next_date = dt.datetime.now()
            next_date += dt.timedelta(days=program["interval"])
            next_date = next_date.replace(hour=start_time.hour, minute=start_time.minute, second=0, microsecond=0)
            program["nextRunTime"] = str(next_date)
            logger.info(f"next run {next_date}")
            s.save()
    timer = threading.Timer(60, check)
    timer.start()


def program_complete():
    global p_running
    p_running = False


def get_temp_str(c):
    return f"{c:.1f}&deg;c" + f" [{get_f(c):.1f}&deg;f]"


def get_f(c):
    return c*1.8+32


@app.route('/relay/<pin_in>')
def relay_action(pin_in):
    logger.debug(f"relay[{pin_in}] action[ON] time[1]")

    # relay.set_pin(int(pin_in))
    action = "on"
    # if action == "on":
     #    relay.on()
    # else:
      #  relay.off()
    # pin_state = GPIO.input(pin)
    return jsonify(message="Success",
                   statusCode=200,
                   data=action), 200


@app.route('/getSetup')
def get_setup():
    return json.dumps({"setup": s.setup}), 200


@app.route('/update/<setup_type>', methods=['POST'])
def update(setup_type):
    if setup_type == "zones":
        z = request.json
        s.setup["zones"] = z
        s.save()

    return jsonify(message="Success",
                   statusCode=200,
                   data=setup_type), 200


@app.route("/setup/<action>")
def setup_cmd(action):
    if action == "load":
        s.load()
        s.save()
    return jsonify(message="Success",
                   statusCode=200,
                   data=action), 200


@app.route('/getTemp')
def get_temp():
    cond = get_temperature()
    cond_avg = t.get_today_avg()
    cond_max = t.get_today_max()
    ret = {
        "temp": cond[0],
        "humidity": cond[1],
        "avg_temp": cond_avg[0],
        "avg_humidity": cond_avg[1],
        "temp_max": cond_max[0],
        "temp_min": cond_max[1]
    }
    return ret, 200


@app.route('/getTempStr')
def get_temp_html():
    cond = get_temperature()
    cond_avg = t.get_today_avg()
    cond_max = t.get_today_max()
    ret = f"Temp: {get_temp_str(cond[0])} <br/>" + f"Humidity: {cond[1]:.0f}% <br/>"
    ret += f"Temp Avg: {get_temp_str(cond_avg[0])} <br/>" + f"Humidity Avg: {cond_avg[1]:.0f}% <br/>"
    ret += f"Temp Max: {get_temp_str(cond_max[0])} <br/>" + f"Temp Min: {get_temp_str(cond_max[1])}"
    return ret, 200


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')


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
    # s.load()
    check()
    t.start()
    # app.run(ssl_context='adhoc', host=host_name, port=1983)
    app.run(host=host_name, port=1983)
