import re
from datetime import datetime
import threading

import firebase_admin
from firebase_admin import db
from firebase_admin.exceptions import FirebaseError
import logging
import datetime as dt
from time import sleep
import requests

module_logger = logging.getLogger('main.firebase_db')

temperatureURL = "https://pitemperature-a22b2-default-rtdb.firebaseio.com"
databaseURL = "https://rn5notifications-default-rtdb.firebaseio.com/"
appKey = "sprinkler"

cred_obj = firebase_admin.credentials.Certificate("/home/pi/projects/firebaseKey.json")
default_app = firebase_admin.initialize_app(cred_obj, {
    'databaseURL': databaseURL
})

ref = db.reference(appKey)

db_setup = ref.child('setupFB')
db_current = ref.child('currentFB')


t = 0.0
h = 0
t_start = 48*60*60

setup_stream = None
current_stream = None
timer = 0
network_up = True
reset_stream = True
add_temp_list = []
setup = {}
current = {}
delay = dt.datetime.now()
average_temps = []
watering_times = []
program_cb = None
loaded = [False, False]


def ref_loaded():
    return loaded[0] and loaded[1]


def add_temp(day_val_in, time_val_in=None):
    module_logger.debug("add_temp() " + str(time_val_in))
    add_temp_list.append([day_val_in, time_val_in])
    if network_up:
        for vals in list(add_temp_list):
            try:
                day_val, time_val = vals
                if ref.child('history').order_by_key().limit_to_last(1).get():
                    snapshot = ref.child('history').order_by_key().limit_to_last(1).get()
                    # module_logger.debug('snapshot exists')
                    found = False
                    for key, val in snapshot.items():
                        today = dt.date.today()
                        last_history = val
                        # last_history_ref = ref.child('history/' + key)
                        # last_history = last_history_ref.get()
                        if last_history['dt'] == str(today):
                            module_logger.debug('date found : ' + last_history['dt'] + " : " + key)
                            hist_ref = ref.child('history/' + key)
                            hist_ref.update(day_val)
                            new_history = hist_ref.child("history").push()
                            new_history.set(time_val)
                            found = True
                    if not found:
                        # module_logger.debug('date not found. add day.')
                        history_ref = ref.child('history')
                        new_history = history_ref.push()
                        new_history.set(day_val)
                        if time_val is not None:
                            new_history_tmp = new_history.child('history').push()
                            new_history_tmp.set(time_val)
                else:
                    module_logger.debug('snapshot does not exist')
                    try:
                        history_ref = ref.child('history')
                        new_history = history_ref.push()
                        new_history.set(day_val)
                        if time_val is not None:
                            new_history_ref = new_history.child('history')
                            new_history_tmp = new_history_ref.push()
                            new_history_tmp.set(time_val)
                    except Exception as e:
                        module_logger.error("add_temp() " + str(e))
                add_temp_list.remove(vals)
            except Exception as e:
                module_logger.debug("Add temp failed while updating. Try again.", str(e))


def programs_listener(event):
    if event.data:
        module_logger.debug('path: ' + str(event.path))
        module_logger.debug('eventType: ' + str(event.event_type))
        module_logger.debug('programs listener... ' + str(event.data))


def zones_listener(event):
    if event.data:
        module_logger.debug('zones listener... ' + str(event.data))


setup_loaded = False


def setup_listener(event):
    global setup, setup_loaded
    if event.data:
        if str(event.path) == "/":
            setup = event.data
            loaded[0] = True
        else:
            path = re.sub(r'^/', '', str(event.path))
            setup[path] = event.data
        if not setup_loaded:
            module_logger.debug("setup loaded: ")
            module_logger.debug(setup)
            setup_loaded = True
        else:
            module_logger.debug('setup listener...')


def current_listener(event):
    global current
    if event.data:
        module_logger.debug("current_listener() path: " + str(event.path) + " data: " + str(event.data))
        if str(event.path) == "/":
            current = event.data
            loaded[1] = True
        else:
            path = re.sub(r'^/', '', str(event.path))
            current[path] = event.data
        action = current['action'] if current['action'] else 'none'
        if action == 'stop':
            if callable(program_cb):
                program_cb('cancel', None)
            db_current.child('action').set('none')
            return
        elif action == 'start':
            if current['programName'] and current['programName'] != 'none':
                if callable(program_cb):
                    program_cb('start', current['programName'])


def get_temp_history():
    fromTime = datetime.now().timestamp() - t_start  # 48hrs
    url = temperatureURL + f'/history.json?orderBy="dt"&startAt={int(fromTime)}'
    x = requests.get(url)
    if x.status_code != 200:
        module_logger.error("get_temp_history() : " + str(x.status_code))
    return x.json()


temp_in_val = None
humid_in_val = None
next_run_time_list = []


def set_temperature(in_val=None):
    global t, temp_in_val
    if in_val is not None:
        temp_in_val = in_val
    try:
        if network_up:
            if in_val != t and temp_in_val is not None:
                ref.child('temperature').set(temp_in_val)
                t = temp_in_val
            temp_in_val = None
        else:
            raise Exception("Network Down. Wait to update.")
    except:
        threading.Timer(300, set_temperature).start()


def set_humidity(in_val=humid_in_val):
    global h, humid_in_val
    if in_val is not None:
        humid_in_val = in_val
    try:
        if network_up:
            if in_val != h and humid_in_val is not None:
                ref.child('humidity').set(humid_in_val)
                h = humid_in_val
            humid_in_val = None
        else:
            raise Exception("Network Down. Wait to update.")
    except:
        threading.Timer(300, set_humidity).start()


def set_next_run_time(prog_key=None, in_val=None):
    if prog_key is not None:
        next_run_time_list.append([prog_key, in_val])
    try:
        if network_up:
            for update in list(next_run_time_list):
                child = f"programs/{update[0]}/nextRunTime"
                db_setup.child(child).set(update[1])
                next_run_time_list.remove(update)
        else:
            raise Exception("network down. try again later.")
    except:
        module_logger.error("error in updating program, nextRunTime", str(next_run_time_list))
        threading.Timer(300, set_next_run_time).start()


def internet_on():
    global network_up, reset_stream
    while True:
        try:
            requests.get("https://google.com")
            if not network_up:
                module_logger.debug('Network UP.')
            network_up = True
            return network_up
        except:
            if network_up:
                module_logger.error('Network DOWN!!!')
            network_up = False
            reset_stream = True
        sleep(15)


def start_listeners():
    global timer, setup_stream, reset_stream, current_stream
    while True:
        if internet_on():
            if reset_stream:
                try:
                    current_stream.close()
                except:
                    pass
                try:
                    setup_stream.close()
                    module_logger.debug('streams closed...')
                except:
                    module_logger.debug('no streams to close...')
                    pass
                try:
                    setup_stream = db_setup.listen(setup_listener)
                    sleep(5)
                    current_stream = db_current.listen(current_listener)
                    module_logger.debug('streams open...')
                    reset_stream = False
                except FirebaseError:
                    module_logger.error('failed to start listeners... ')
                    reset_stream = True
        sleep(15)
