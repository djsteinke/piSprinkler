import firebase_admin
from firebase_admin import db
from firebase_admin.exceptions import FirebaseError
import logging
import datetime as dt


module_logger = logging.getLogger('main.firebase_db')

databaseURL = "https://rn5notifications-default-rtdb.firebaseio.com/"
appKey = "sprinkler"

cred_obj = firebase_admin.credentials.Certificate("/home/pi/firebaseKey.json")
default_app = firebase_admin.initialize_app(cred_obj, {
    'databaseURL': databaseURL
})

ref = db.reference(appKey)

db_programs = ref.child('setup/programs')

t = 0.0
h = 0


def add_temp(day_val, time_val=None):
    module_logger.debug(time_val)
    if ref.child('history').get():
        snapshot = ref.child('history').order_by_key().limit_to_last(1).get()
        module_logger.debug('snapshot exists')
        found = False
        for key, val in snapshot.items():
            today = dt.date.today()
            last_history_ref = ref.child('history/' + key)
            last_history = last_history_ref.get()
            module_logger.debug(key + " : " + last_history['dt'])
            if last_history['dt'] == str(today):
                module_logger.debug('date found' + key)
                last_history_ref.update(day_val)
                history_ref = last_history_ref.child("history")
                new_history = history_ref.push()
                new_history.set(time_val)
                found = True
        if not found:
            module_logger.debug('date not found. add day.')
            history_ref = ref.child('history')
            new_history = history_ref.push()
            new_history.set(day_val)
            if time_val is not None:
                new_history_ref = new_history.child('history')
                new_history_tmp = new_history_ref.push()
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
            module_logger.error(str(e))


def programs_listener(event):
    module_logger.debug('firebase listener...')
    if event.data:
        # TODO : Load programs
        module_logger.debug("PROGRAMS: ")
        module_logger.debug(db_programs.get())


def set_temperature(in_val):
    global t
    if in_val != t:
        ref.child('temperature').set(in_val)
        t = in_val


def set_humidity(in_val):
    global h
    if in_val != h:
        ref.child('humidity').set(in_val)
        h = in_val


def set_next_run_time(prog_key, in_val):
    try:
        child = f"setup/programs/{str(prog_key)}/nextRunTime"
        ref.child(child).set(in_val)
    except Exception as e:
        module_logger.error(str(e))


def start_programs_listener():
    try:
        module_logger.debug("Starting Programs Listener")
        db_programs.listen(programs_listener)
    except FirebaseError:
        module_logger.error('failed to start listener... trying again.')
        start_programs_listener()
