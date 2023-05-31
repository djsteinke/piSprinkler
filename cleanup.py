import firebase_admin
from firebase_admin import db

temperatureURL = "https://pitemperature-a22b2-default-rtdb.firebaseio.com"
databaseURL = "https://rn5notifications-default-rtdb.firebaseio.com/"
appKey = "sprinkler"

cred_obj = firebase_admin.credentials.Certificate("/home/pi/projects/firebaseKey.json")
default_app = firebase_admin.initialize_app(cred_obj, {
    'databaseURL': databaseURL
})

ref = db.reference(appKey)

child = ref.child('history')
child.delete()

child = ref.child('humidity')
child.delete()

child = ref.child('programs')
child.delete()

child = ref.child('setup')
child.delete()

child = ref.child('temperature')
child.delete()
