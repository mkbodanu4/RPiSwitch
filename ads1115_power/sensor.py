import voluptuous as vol

from homeassistant.helpers.entity import Entity
from homeassistant.components.sensor import PLATFORM_SCHEMA

from homeassistant.const import DEVICE_DEFAULT_NAME
import homeassistant.helpers.config_validation as cv

import math
from .measure_power import measure

DEFAULT_VOLTAGE = 230
DEFAULT_SAMPLES = 100
DEFAULT_GAIN = 1
DEFAULT_PF = 1

CONF_CHANNEL = "channel"
CONF_NAME = "name"
CONF_VOLTAGE = "voltage"
CONF_SAMPLES = "samples"
CONF_GAIN = "gain"
CONF_PF = "pf"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_CHANNEL): vol.In([0, 1, 2, 3]),
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_VOLTAGE, default=DEFAULT_VOLTAGE): cv.positive_int,
        vol.Optional(CONF_SAMPLES, default=DEFAULT_SAMPLES): cv.positive_int,
        vol.Optional(CONF_GAIN, default=DEFAULT_GAIN): cv.positive_int,
        vol.Optional(CONF_PF, default=DEFAULT_PF): cv.positive_float,
    }
)


def setup_platform(hass, config, add_devices, discovery_info=None):
    channel = config.get(CONF_CHANNEL)
    name = config.get(CONF_NAME)
    voltage = config.get(CONF_VOLTAGE)
    samples = config.get(CONF_SAMPLES)
    gain = config.get(CONF_GAIN)
    pf = config.get(CONF_PF)
    add_devices([ADS1115_Power(channel, name, voltage, samples, gain, pf)])


class ADS1115_Power(Entity):
    def __init__(self, channel, name, voltage, samples, gain, pf):
        self._channel = channel
        self._name = name or DEVICE_DEFAULT_NAME
        self._voltage = voltage
        self._samples = samples
        self._gain = gain
        self._pf = pf

        self._watt = 0
        self.update()

    def update(self):
        self._watt = measure(self._channel, self._samples, self._gain, self._voltage, self._pf)

    @property
    def unit_of_measurement(self):
        return 'W'

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return 0.0 if math.isnan(self._watt) else float("{:.0f}".format(self._watt))

    @property
    def should_poll(self):
        return True
