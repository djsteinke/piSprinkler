import re
from datetime import datetime
import threading

import firebase_admin
from firebase_admin import db
from firebase_admin.exceptions import FirebaseError
import logging
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
network_up = True
reset_stream = True
add_temp_list = []
set_value_list = []
setup = {}
current = {}
program_cb = None
loaded = [False, False]
setup_loaded = False
check_running = False
add_value_list = []


def ref_loaded():
    return loaded[0] and loaded[1]


"""
new_history_ref = new_history.child('history')
new_history_tmp = new_history_ref.push()
new_history_tmp.set(time_val)
"""


def add_value(path=None, val=None):
    if path is not None:
        add_value_list.append([path, val])
    if network_up:
        for new in list(add_value_list):
            try:
                new_path = ref.child(new[0])
                new_ref = new_path.push()
                new_ref.set(new[1])
                module_logger.debug("add_value() : " + new[0] + " value: " + str(new[1]))
            except Exception as e:
                module_logger.error("set_value() : " + new[0] + " value: " + str(new[1]) + " error: " + str(e))


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
            module_logger.debug('setup listener... ' + str(event.path))


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
        if action != 'none':
            if callable(program_cb):
                program_cb(action, current['programName'])
            db_current.child('action').set('none')


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


def set_value(path=None, value=None):
    if path is not None:
        set_value_list.append([path, value])

    if not network_up:
        module_logger.error("set_value() network down, try again later")
        threading.Timer(300, set_value).start()
        return
    else:
        for update in list(set_value_list):
            try:
                ref.child(update[0]).set(update[1])
                set_value_list.remove(update)
                module_logger.debug("set_value() : " + update[0] + " value: " + str(update[1]))
            except Exception as e:
                module_logger.error("set_value() : " + update[0] + " value: " + str(update[1]) + " error: " + str(e))


def set_next_run_time(prog_key=None, in_val=None):
    if prog_key is not None:
        next_run_time_list.append([prog_key, in_val])

    if not network_up:
        module_logger.error("set_next_run_time() network down, try again later")
        threading.Timer(300, set_next_run_time).start()
        return
    else:
        for update in list(next_run_time_list):
            try:
                child = f"programs/{update[0]}/nextRunTime"
                db_setup.child(child).set(update[1])
                next_run_time_list.remove(update)
            except Exception as e:
                module_logger.error("set_next_run_time() : " + update[0] + " value: " + str(update[1]) + " error: " + str(e))


def internet_on():
    global network_up, reset_stream
    try:
        requests.get("https://google.com")
        if not network_up:
            module_logger.debug('Network UP.')
        network_up = True
    except:
        if network_up:
            module_logger.error('Network DOWN!!!')
        network_up = False
        reset_stream = True


def check_listeners():
    global setup_stream, reset_stream, current_stream, check_running
    internet_on()
    if network_up and not check_running:
        check_running = True
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
        check_running = False
