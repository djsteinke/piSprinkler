import threading

import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)


class Relay(object):
    def __init__(self, pin, callback):
        self._on = False
        self._pin = pin
        self._run_time = 30
        self._callback = callback
        GPIO.setup(self._pin, GPIO.OUT)
        GPIO.output(self._pin, GPIO.LOW)

    def set_pin(self, pin):
        self._pin = pin
        GPIO.setup(self._pin, GPIO.OUT)
        GPIO.output(self._pin, GPIO.LOW)

    def set_run_time(self, run_time):
        self._run_time = run_time

    def on(self):
        # TODO turn on
        self._on = True
        GPIO.output(self._pin, GPIO.HIGH)
        timer = threading.Timer(self._run_time, self.off)
        timer.start()

    def off(self):
        # TODO turn off
        self._on = False
        GPIO.output(self._pin, GPIO.LOW)
        if self._callback is not None:
            self._callback()

    def get_pin(self):
        return str(self._pin)
