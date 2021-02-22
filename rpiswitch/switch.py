import voluptuous as vol

from homeassistant.components.switch import SwitchEntity
from homeassistant.components.switch import PLATFORM_SCHEMA

from homeassistant.const import DEVICE_DEFAULT_NAME
import homeassistant.helpers.config_validation as cv

import board
import busio
import adafruit_ads1x15.ads1115 as ads1115
from adafruit_ads1x15.analog_in import AnalogIn
from datetime import datetime
import numpy as np
import math
import RPi.GPIO as GPIO

DEFAULT_VOLTAGE = 230
DEFAULT_SAMPLES = 100
DEFAULT_GAIN = 1
DEFAULT_PF = 1
DEFAULT_INVERT_LOGIC = False

CONF_PIN = "pin"
CONF_CHANNEL = "channel"
CONF_NAME = "name"
CONF_VOLTAGE = "voltage"
CONF_SAMPLES = "samples"
CONF_GAIN = "gain"
CONF_PF = "pf"
CONF_INVERT_LOGIC = "invert_logic"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_PIN): cv.positive_int,
        vol.Required(CONF_CHANNEL): vol.In([0, 1, 2, 3]),
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_VOLTAGE, default=DEFAULT_VOLTAGE): cv.positive_int,
        vol.Optional(CONF_SAMPLES, default=DEFAULT_SAMPLES): cv.positive_int,
        vol.Optional(CONF_GAIN, default=DEFAULT_GAIN): cv.positive_int,
        vol.Optional(CONF_PF, default=DEFAULT_PF): cv.positive_float,
        vol.Optional(CONF_INVERT_LOGIC, default=DEFAULT_INVERT_LOGIC): cv.boolean,
    }
)


def setup_platform(hass, config, add_devices, discovery_info=None):
    pin = config.get(CONF_PIN)
    channel = config.get(CONF_CHANNEL)
    name = config.get(CONF_NAME)
    voltage = config.get(CONF_VOLTAGE)
    samples = config.get(CONF_SAMPLES)
    gain = config.get(CONF_GAIN)
    pf = config.get(CONF_PF)
    invert_logic = config.get(CONF_INVERT_LOGIC)
    add_devices([RPiSwitch(pin, channel, name, voltage, samples, gain, pf, invert_logic)])


class RPiSwitch(SwitchEntity):
    def __init__(self, pin, channel, name, voltage, samples, gain, pf, invert_logic):
        self._pin = pin
        self._channel = channel
        self._name = name or DEVICE_DEFAULT_NAME
        self._voltage = voltage
        self._samples = samples
        self._gain = gain
        self._pf = pf
        self._invert_logic = invert_logic

        self._state = 0
        self._is_on = False

        self._current_rms = 0
        self._watt = 0

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self._pin, GPIO.OUT)

        self.update()

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        if self._invert_logic:
            GPIO.output(self._pin, GPIO.LOW)
        else:
            GPIO.output(self._pin, GPIO.HIGH)
        self.update()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        if self._invert_logic:
            GPIO.output(self._pin, GPIO.HIGH)
        else:
            GPIO.output(self._pin, GPIO.LOW)
        self.update()

    def update(self):
        if self._invert_logic:
            self._is_on = False if int(GPIO.input(self._pin)) == 1 else True
        else:
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
        return 0.0 if math.isnan(self._watt) else float("{:.0f}".format(self._watt))

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
