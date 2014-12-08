""" Support for Hue lights. """
import logging

from datetime import timedelta

import homeassistant.util as util
from homeassistant.helpers import ToggleDevice
from homeassistant.const import ATTR_FRIENDLY_NAME, CONF_PLATFORM
from homeassistant.components.light import (
    ATTR_BRIGHTNESS, ATTR_HUE, ATTR_SATURATION, ATTR_KELVIN)


MIN_TIME_BETWEEN_SCANS = timedelta(seconds=10)
MIN_TIME_BETWEEN_FORCED_SCANS = timedelta(seconds=1)

# pylint: disable=unused-argument
def get_devices(hass, config):
    """ Gets the Hue lights. """
    logger = logging.getLogger(__name__)
    try:
        import homeassistant.external.lifx.lifx as lifx
    except ImportError:
        logger.exception("Error while importing dependency lifx.")

        return []

    lights = {}

    @util.Throttle(MIN_TIME_BETWEEN_SCANS, MIN_TIME_BETWEEN_FORCED_SCANS)
    def update_lights():
        """ Updates the lifx light objects with latest info from the bridge. """
        all_lights = lifx.get_lights()

        for light in all_lights:
            lights[light.addr] = LifxLight(light)

    update_lights()

    return list(lights.values())


class LifxLight(ToggleDevice):
    """
    Represents a Lifx light
    http://lifx.com

     """

    def __init__(self, lifxLightObj):
        self.light = lifxLightObj
        self.powered = self.light.power

    def get_name(self):
        """ Get the mame of the Hue light. """
        return self.light.bulb_label

    def turn_on(self, **kwargs):
        """ Turn the specified or all lights on. """
        command = {'on': True}

        self.light.set_power(command['on'])
        self.light.power = True


    def turn_off(self, **kwargs):
        """ Turn the specified or all lights off. """
        command = {'on': False}

        self.light.set_power(command['on'])
        self.light.power = False

    def is_on(self):
        """ True if device is on. """

        return self.light.power

    def get_state_attributes(self):
        """ Returns optional state attributes. """
        attr = {
            ATTR_FRIENDLY_NAME: self.get_name(),
            CONF_PLATFORM: "lifx",
            ATTR_HUE: self.light.hue,
            ATTR_SATURATION: self.light.saturation,
            ATTR_BRIGHTNESS: self.light.brightness,
            ATTR_KELVIN: self.light.kelvin,
            "Power": self.light.power,
            "Dim": self.light.dim
        }

        return attr

    def update(self):
        """ Synchronize state with bridge. """
        pass
