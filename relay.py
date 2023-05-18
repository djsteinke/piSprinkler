import logging
import threading

import RPi.GPIO as GPIO
import logging

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

module_logger = logging.getLogger('main.relay')


class Relay(object):
    def __init__(self, pin, callback):
        self._on = False
        self._pin = pin
        self._run_time = 0
        self._wait = 0
        self._callback = callback
        GPIO.setup(self._pin, GPIO.OUT)
        if GPIO.input(self._pin) == 0:
            self._gpio_on = GPIO.HIGH
            self._gpio_off = GPIO.LOW
        else:
            self._gpio_on = GPIO.LOW
            self._gpio_off = GPIO.HIGH

        GPIO.output(self._pin, self._gpio_off)

    def __str__(self):
        return f"Pin: {str(self._pin)} On: {str(self._on)} RunTime: {str(self._run_time)} Wait: {str(self._wait)} GPIO: " \
               f"{'HIGH' if self._gpio_on == GPIO.HIGH else 'LOW'}"

    def set_pin(self, pin):
        self._pin = pin
        GPIO.setup(self._pin, GPIO.OUT)
        if GPIO.input(self._pin) == 0:
            self._gpio_on = GPIO.HIGH
            self._gpio_off = GPIO.LOW
        else:
            self._gpio_on = GPIO.LOW
            self._gpio_off = GPIO.HIGH
        GPIO.output(self._pin, self._gpio_off)

    def set_run_time(self, run_time):
        self._run_time = run_time

    def set_wait(self, wait):
        self._wait = wait

    def on(self):
        module_logger.debug("on() - " + self.__str__())
        self._on = True
        GPIO.output(self._pin, self._gpio_on)
        if self._run_time > 0:
            timer = threading.Timer(self._run_time, self.off)
            timer.start()

    def force_off(self):
        module_logger.debug("force_off() - " + self.__str__())
        self._wait = 0
        self.off()

    def off(self):
        GPIO.output(self._pin, self._gpio_off)
        self._on = False
        if self._callback is not None:
            timer = threading.Timer(self._wait, self._callback)
            timer.start()
        module_logger.debug("off() - " + self.__str__())

    def get_pin(self):
        return str(self._pin)
