import json
import logging
import socket
import threading
import datetime as dt
from dateutil import parser

import RPi.GPIO as GPIO

from flask import Flask, request, jsonify, send_from_directory

from properties import port, ip
from program import Program
from temperature import Temperature
from setup import Setup
from static import get_logging_level, get_temperature, get_sensor_temp
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
p = Program(None, None, None, None)
p_running = False

delay = "2021-01-01 00:00:01"


def check():
    global p_running, p
    delay_date = parser.parse(s.setup['delay'])
    for program in s.setup['programs']:
        next_date = parser.parse(program["nextRunTime"])
        if next_date < dt.datetime.now() and not p_running:
            interval = 1
            if next_date >= delay_date:
                interval = program["interval"]
                p = Program(program, s.setup, t.hist, program_complete)
                if program['active']:
                    p_running = True
                    p.start()
            start_time = parser.parse(program["startTime"])
            next_date = dt.datetime.now()
            next_date += dt.timedelta(days=interval)
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
    return c * 1.8 + 32


@app.route('/delay/<action>', defaults={'days': 0})
@app.route('/delay/<action>/<days>')
def set_delay(action, days):
    global delay
    d = int(days)
    ret = {"type": "delay",
           "response": {
                "action": action,
                "status": "",
                "date": ""}}
    if action == 'set':
        d = d + 1
        delay_date = dt.datetime.now()
        delay_date += dt.timedelta(days=d)
        delay_date = delay_date.replace(hour=0, minute=0, second=0, microsecond=0)
        delay = str(delay_date)
        s.setup['delay'] = delay
        s.save()
        ret['response']['date'] = delay
        ret['response']['status'] = 'success'
    elif action == "cancel":
        delay_date = dt.datetime.now()
        delay_date = delay_date.replace(hour=0, minute=0, second=0, microsecond=0)
        delay = str(delay_date)
        s.setup['delay'] = delay
        s.save()
        ret['response']['date'] = delay
        ret['response']['status'] = 'success'
    else:
        ret['response']['status'] = f'error: invalid action type[{action}]'
    return ret, 200


@app.route('/program/<action>', defaults={'name': ""})
@app.route('/program/<action>/<name>')
def run_program(action, name):
    global p_running, s, p
    ret = {"type": "program",
           "response": {
                "action": action,
                "name": name,
                "status": ""}}
    if action == "run":
        for program in s.setup['programs']:
            if program['name'] == name:
                logger.debug(f"runProgram({name})")
                p = Program(program, s.setup, t.hist, program_complete)
                p.start()
                ret['response']['status'] = "success"
                return ret, 200
    elif action == "cancel":
        if p.running:
            p.cancel()
            ret['response']['status'] = "success"
            return ret, 200
    ret['response']['status'] = f"error: program[{name}] does not exist or no program running"
    return ret, 200


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


@app.route('/getProgramStatus')
def get_program_status():
    ret = {"type": "programStatus",
           "response": {
               "status": "success",
               "name": None,
               "step": None,
               "time": None,
               "runTime": None,
               "delay": ""}}
    if p.p is not None:
        ret['response']['name'] = p.p['name']
        ret['response']['step'] = p.step
        ret['response']['time'] = p.step_time
        ret['response']['runTime'] = p.run_time
    else:
        delay_date = parser.parse(delay)
        if delay_date > dt.datetime.now():
            ret['response']['delay'] = delay
    return ret, 200


@app.route('/getSetup')
def get_setup():
    return {"type": "setup",
            "response": {
                "setup": s.setup}}, 200


@app.route('/update/<setup_type>', methods=['POST'])
def update(setup_type):
    ret = {"type": "update",
           "response": {
               "type": setup_type,
               "status": "success"}}
    if setup_type == "zones":
        val = request.json
        s.setup["zones"] = val
        s.save()
        logger.debug("update zones \n" + json.dumps(s.setup["zones"]))
    elif setup_type == "programs":
        val = request.json
        s.setup["programs"] = val
        s.save()
    return ret, 200


@app.route("/setup/<action>")
def setup_cmd(action):
    if action == "load":
        s.load()
        s.save()
    return jsonify(message="Success",
                   statusCode=200,
                   data=action), 200


@app.route('/getSensorTemp')
def get_s_temp():
    cond = get_sensor_temp()
    ret = {"temp": cond[0],
           "humidity": cond[1],
           "temp_f": get_f(cond[0])}
    return ret, 200


@app.route('/getTemp', defaults={'days': 0})
@app.route('/getTemp/<days>')
def get_temp(days):
    global p
    if days == 0:
        cond = get_temperature()
        cond_avg = t.get_today_avg()
        cond_max = t.get_today_max()
        ret = {"type": "temp",
               "response": {
                   "temp": cond[0],
                   "humidity": cond[1],
                   "avgTemp": cond_avg[0],
                   "avgHumidity": cond_avg[1],
                   "tempMax": cond_max[0],
                   "tempMin": cond_max[1],
                   "program": {"name": None,
                               "step": None,
                               "time": None,
                               "runTime": None,
                               "delay": ""}
               }
               }
        if p.p is not None and p.running:
            ret['response']['program']['name'] = p.p['name']
            ret['response']['program']['step'] = p.step
            ret['response']['program']['time'] = p.run_time
            ret['response']['program']['runTime'] = p.step_time

        delay_date = parser.parse(delay)
        if delay_date > dt.datetime.now():
            ret['response']['program']['delay'] = delay
        return ret, 200
    else:
        today = dt.date.today()
        i = 0
        ret = {"type": "history",
               "response": {"history": []}}
        while i < int(days):
            for hist in t.hist['history']:
                if hist['dt'] == str(today):
                    ret['response']['history'].append(hist)
                    break
            i += 1
            today -= dt.timedelta(days=1)
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
    try:
        stream = os.popen('hostname -I')
        host_name = stream.read().strip()
    except all:
        host_name = ip
    logger.info("machine host_name[" + host_name + "]")
    check()
    t.start()
    app.run(host=host_name, port=port)
