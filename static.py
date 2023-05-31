import logging
import os
import smbus
import time


bus = smbus.SMBus(1)
config = [0x08, 0x00]
fdir = os.path.abspath('/home/pi/projects/piSprinkler')
# fdir = os.path.abspath('C:/MyData/Program Files/PyCharm/pi_sprinkler')

module_logger = logging.getLogger('main.static')


def get_f_from_c(c):
    return c*1.8+32


def get_sensor_temp():
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
    return [round(temp_c, 2), round(humid, 1)]


def get_temperature():
    return get_sensor_temp()
