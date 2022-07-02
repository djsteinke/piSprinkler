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
        ref.child('temperature').update(in_val)
        t = in_val


def set_humidity(in_val):
    global t
    if in_val != t:
        ref.child('humidity').update(in_val)
        t = in_val
