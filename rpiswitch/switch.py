from homeassistant.components.switch import SwitchEntity

import board
import busio
import adafruit_ads1x15.ads1115 as ads1115
from adafruit_ads1x15.analog_in import AnalogIn
from datetime import datetime
import numpy as np
import math
import RPi.GPIO as GPIO


def setup_platform(hass, config, add_devices, discovery_info=None):
    pin = config.get('pin')
    channel = config.get('channel')
    name = config.get('name')
    voltage = config.get('voltage')
    samples = config.get('samples')
    gain = config.get('gain')
    pf = config.get('pf')
    add_devices([RPiSwitch(pin, channel, name, voltage, samples, gain, pf)])


class RPiSwitch(SwitchEntity):
    def __init__(self, pin, channel, name, voltage, samples, gain, pf):
        self._pin = pin
        self._channel = channel
        self._name = name
        self._voltage = voltage
        self._samples = samples
        self._gain = gain
        self._pf = pf

        self._state = 0
        self._is_on = False

        self._current_rms = 0
        self._watt = 0

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self._pin, GPIO.OUT)

        self.update()

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        GPIO.output(self._pin, GPIO.HIGH)
        self.update()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        GPIO.output(self._pin, GPIO.LOW)
        self.update()

    def update(self):
        self._is_on = True if int(GPIO.input(self._pin)) == 1 else False

        i2c = busio.I2C(board.SCL, board.SDA)
        ads = ads1115.ADS1115(i2c)
        ads.gain = 1
        ads.mode = ads1115.Mode.CONTINUOUS

        start = datetime.now().timestamp()
        currents = []
        times = []
        while len(currents) < self._samples:
            channel_data = AnalogIn(ads, int(self._channel))
            currents.append((channel_data.voltage / 200) * 1000)
            times.append(datetime.now().timestamp() - start)

        currents = np.array(currents)
        self._current_rms = np.sqrt(np.mean(currents ** 2))
        self._watt = (self._current_rms * 230) * self._pf

    @property
    def current_power_w(self):
        return 0.0 if math.isnan(self._watt) else float("{:.2f}".format(self._watt))

    @property
    def unit_of_measurement(self):
        return 'W'

    @property
    def device_class(self):
        return 'switch'

    @property
    def is_on(self):
        return self._is_on

    @property
    def name(self):
        return self._name

    @property
    def should_poll(self):
        return True
