import firebase_admin
from firebase_admin import db

databaseURL = "https://rn5notifications-default-rtdb.firebaseio.com/"
appKey = "sprinkler"

cred_obj = firebase_admin.credentials.Certificate("/home/pi/firebaseKey.json")
default_app = firebase_admin.initialize_app(cred_obj, {
    'databaseURL': databaseURL
})

ref = db.reference(appKey)

t = 0.0
h = 0


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
    child = f"setup/programs/{str(prog_key)}/nextRunTime"
    ref.child(child).set(in_val)
