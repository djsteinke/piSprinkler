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

historyFB = ref.child('historyFB')

histories = historyFB.get()

hist_list = []

cnt = 0

for key in histories:
    value = histories[key]
    print(key, value)
    new_hist = [key, value['start']]
    if new_hist not in hist_list:
        hist_list.append(new_hist)
    else:
        #historyFB.child(key).remove()
        break
    #cnt += 1
    #if cnt > 1:
    #    break
