import voluptuous as vol

from homeassistant.components.switch import SwitchEntity
from homeassistant.components.switch import PLATFORM_SCHEMA

from homeassistant.const import DEVICE_DEFAULT_NAME
import homeassistant.helpers.config_validation as cv

import RPi.GPIO as GPIO

DEFAULT_INVERT_LOGIC = False

CONF_PIN = "pin"
CONF_NAME = "name"
CONF_INVERT_LOGIC = "invert_logic"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_PIN): cv.positive_int,
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_INVERT_LOGIC, default=DEFAULT_INVERT_LOGIC): cv.boolean,
    }
)


def setup_platform(hass, config, add_devices, discovery_info=None):
    pin = config.get(CONF_PIN)
    name = config.get(CONF_NAME)
    invert_logic = config.get(CONF_INVERT_LOGIC)
    add_devices([RPiSwitch(pin, name, invert_logic)])


class RPiSwitch(SwitchEntity):
    def __init__(self, pin, name, invert_logic):
        self._pin = pin
        self._name = name or DEVICE_DEFAULT_NAME
        self._invert_logic = invert_logic

        self._is_on = False

        self._busy = False

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
