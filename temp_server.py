import threading

import smbus
import time
import socket

from flask import Flask, jsonify

app = Flask(__name__)
bus = smbus.SMBus(1)
config = [0x08, 0x00]
host_name = "192.168.0.140"
port = 31000
temperature = 0.0
humidity = 0.0


def get_temperature():
    global temperature, humidity
    bus.write_i2c_block_data(0x38, 0xE1, config)
    byt = bus.read_byte(0x38)
    measure_cmd = [0x33, 0x00]
    bus.write_i2c_block_data(0x38, 0xAC, measure_cmd)
    time.sleep(0.5)
    data = bus.read_i2c_block_data(0x38, 0x00)
    temp_raw = ((data[3] & 0x0F) << 16) | (data[4] << 8) | data[5]
    temp_c = ((temp_raw*200) / 1048576) - 50
    humid_raw = ((data[1] << 16) | (data[2] << 8) | data[3]) >> 4
    humid = humid_raw * 100 / 1048576
    temperature = round(temp_c, 2)
    humidity = round(humid, 1)
    threading.Timer(30, get_temperature)


@app.route('/getTemp')
def relay_action():
    global temperature, humidity
    return jsonify(t=temperature,
                   h=humidity), 200


if __name__ == '__main__':
    host_name = socket.gethostbyname(socket.gethostname())
    print(host_name + "[" + host_name[0: 3] + "]")
    if host_name[0: 3] == "127":
        host_name = "192.168.0.140"
    elif host_name[0: 3] == "192":
        val = 1
    else:
        host_name = "localhost"
    get_temperature()
    app.run(host=host_name, port=port)
