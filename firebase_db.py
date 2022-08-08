import firebase_admin
from firebase_admin import db
from firebase_admin.exceptions import FirebaseError
import logging


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


def add_temp_today(val):
    module_logger.debug('add_temp_today()')
    module_logger.debug(val)
    history = ref.child('history').order_by_key().limit_to_last(1).get()
    module_logger.debug(history)
    new_history = history[0].child('history').push()
    new_history.set(val)


def add_day(val):
    module_logger.debug('add_day()')
    module_logger.debug(val)
    history = db.reference(appKey + "/history")
    new_history = history.push()
    new_history.set(val)


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
