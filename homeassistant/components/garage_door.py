"""
homeassistant.components.garage_door
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Shows (and controls) state of garage door via wink hub

"""
import logging

from collections import namedtuple
import homeassistant.components.hubs.pywink.pywink  as pywink


import homeassistant.util as util
from homeassistant.const import ATTR_FRIENDLY_NAME, ATTR_UNIT_OF_MEASUREMENT


# The domain of your component. Should be equal to the name of your component
DOMAIN = "garage_door"

# List of component names (string) your component depends upon
# If you are setting up a group but not using a group for anything,
# don't depend on group
DEPENDENCIES = []

ENTITY_ID_FORMAT = DOMAIN + '.{}'

DatatypeDescription = namedtuple("DatatypeDescription", ['name', 'unit'])


def setup(hass, config):
    """ Register services or listen for events that your component needs. """

    logger = logging.getLogger(__name__)

    doors=pywink.get_garage_doors()[0]

    sensor_value_datatypes = [
        "GARAGE_DOOR",
    ]

    sensor_value_descriptions = {
        "GARAGE_DOOR":
            DatatypeDescription(
                'Garage Door', ""),
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
        update_sensor_value_state("GARAGE_DOOR", "Open" if doors.state() else "Closed")


    update_sensors_state(None)

    hass.track_time_change(update_sensors_state, second=[0, 30])

    return True


