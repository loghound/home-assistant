"""
homeassistant.components.tellstick_sensor
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Shows sensor values from tellstick sensors.

Possible config keys:

outside_air_temp=1|0
inside_temp=1|0
attic_temp=1|0
fan_speed=1|0
fan_cfm=1|0
room_name="name of room"

ip_addr=192.168.1.24

"""
import logging

from collections import namedtuple
import requests
import re

import homeassistant.util as util
from homeassistant.const import ATTR_FRIENDLY_NAME, ATTR_UNIT_OF_MEASUREMENT


# The domain of your component. Should be equal to the name of your component
DOMAIN = "whole_house_fan"

# List of component names (string) your component depends upon
# If you are setting up a group but not using a group for anything,
# don't depend on group
DEPENDENCIES = []

ENTITY_ID_FORMAT = DOMAIN + '.{}'

DatatypeDescription = namedtuple("DatatypeDescription", ['name', 'unit'])


def setup(hass, config):
    """ Register services or listen for events that your component needs. """

    logger = logging.getLogger(__name__)

    fan = WholeHouseFan(config[DOMAIN]['ipaddr'])

    sensor_value_datatypes = [
        "OA_TEMP",
        "INSIDE_TEMP",
        "ATTIC_TEMP"
        "FAN_SPEED"
    ]

    sensor_value_descriptions = {
        "OA_TEMP":
            DatatypeDescription(
                'Outside Temp', u"\u00B0" + "F"),
        "ATTIC_TEMP":
            DatatypeDescription(
                'Attic Temp', u"\u00B0" + "F"),
        "INSIDE_TEMP":
            DatatypeDescription(
                config[DOMAIN]['room_name'] or 'Inside Temp', u"\u00B0" + "F"),
        "FAN_SPEED":
            DatatypeDescription(
                'Fan Speed', ""),


    }

    def update_sensor_value_state(sensor_name, sensor_value):
        """ Update the state of a sensor value """

        sensor_value_description = \
            sensor_value_descriptions[sensor_name]

        sensor_value_name = '{}'.format(
            sensor_value_description.name)

        entity_id = ENTITY_ID_FORMAT.format(
            util.slugify(sensor_value_name))

        state = sensor_value

        state_attr = {
            ATTR_FRIENDLY_NAME: sensor_value_name,
            ATTR_UNIT_OF_MEASUREMENT: sensor_value_description.unit
        }

        hass.states.set(entity_id, state, state_attr)


    # pylint: disable=unused-argument
    def update_sensors_state(time):
        """ Update the state of all sensors """
        fan.update_fan_data()
        update_sensor_value_state("OA_TEMP", fan.oa_temp())
        update_sensor_value_state("INSIDE_TEMP", fan.inside_temp())
        update_sensor_value_state("ATTIC_TEMP", fan.attic_temp())
        update_sensor_value_state("FAN_SPEED", "{} ({} CFM)".format(fan.fan_speed(), fan.fan_cfm()))

    update_sensors_state(None)

    hass.track_time_change(update_sensors_state, second=[0, 30])

    return True


# from http://blog.airscapefans.com/archives/gen-2-controls-api
#
# ————–Example of xml data ——————
#
# fanspd<fanspd>0</fanspd>
# doorinprocess<doorinprocess>0</doorinprocess>
# timeremaining<timeremaining>0</timeremaining>
# macaddr<macaddr>60:CB:FB:99:99:0A</macaddr>
# ipaddr<ipaddr>192.168.0.20</ipaddr>
# model<model>2.5eWHF</model>
# softver: <softver>2.14.1</softver>
# interlock1:<interlock1>0</interlock1>
# interlock2: <interlock2>0</interlock2>
# cfm: <cfm>0</cfm>
# power: <power>0</power>
# inside:<house_temp>72</house_temp>
# <DNS1>192.168.0.1</DNS1>
# attic: <attic_temp>92</attic_temp>
# OA: <oa_temp>81</oa_temp>
# server response: <server_response>Posted
# OK<br/></server_response>
# DIP Switches: <DIPS>00000</DIPS>
# Remote Switch:<switch2>1111</switch2>
# Setpoint:<Setpoint>0</Setpoint>
#
# ——————————————————–
class WholeHouseFan:
    def __init__(self, ipaddr):
        self.ipaddr = ipaddr
        self.update_fan_data()

    def update_fan_data(self):
        self.results = requests.get("http://{}/fanspd.cgi".format(self.ipaddr)).text

    def _get_value(self, value):
        ret = re.search('{}>(.*)</{}'.format(value, value), self.results).group(1)
        return ret

    def model(self):
        ret = self._get_value("model")
        return ret

    def oa_temp(self):
        ret = self._get_value("oa_temp")
        return ret

    def inside_temp(self):
        ret = self._get_value("house_temp")
        return ret

    def attic_temp(self):
        ret = self._get_value("attic_temp")
        return ret

    def fan_speed(self):
        ret = self._get_value("fanspd")
        return ret

    def fan_cfm(self):
        ret = self._get_value("cfm")
        return ret

