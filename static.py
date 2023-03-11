import logging
import os

import requests

import properties
import smbus
import time

bus = smbus.SMBus(1)
config = [0x08, 0x00]
fdir = os.path.abspath('/home/pi/projects/piSprinkler')
# fdir = os.path.abspath('C:/MyData/Program Files/PyCharm/pi_sprinkler')

module_logger = logging.getLogger('main.static')


class ExternalSystemError(Exception):
    pass


def get_f_from_c(c):
    return c*1.8+32


def get_logging_level():
    if properties.log_debug:
        return logging.DEBUG
    elif properties.log_info:
        return logging.INFO
    elif properties.log_warning:
        return logging.WARNING
    else:
        return logging.ERROR


def get_sensor_temp():
    cnt = 0
    while cnt < 12:
        try:
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
        except:
            cnt += 1
            time.sleep(5)
    return [-1, -1]


def get_temperature():
    """
    try:
        x = requests.get('http://192.168.0.140:31000/getTemp', timeout=10)
        if not x.ok:
            raise ExternalSystemError(f'Response Error: {x.status_code} - {x.reason}')
        msg = x.json()
        if msg['humidity'] < 0:
            raise ExternalSystemError('Client Error: Sensor not connected.')
        return [msg['temp'], msg['humidity']]
    except requests.exceptions.HTTPError as err:
        log_msg = f"Http Error: {err}"
    except requests.exceptions.ConnectionError as err:
        log_msg = f"Error Connecting: {err}"
    except requests.exceptions.Timeout as err:
        log_msg = f"Timeout Error: {err}"
    except requests.exceptions.RequestException as err:
        log_msg = f"Request Error: {err}"
    except ExternalSystemError as err:
        log_msg = err
    module_logger.debug(log_msg)
    """
    return get_sensor_temp()
