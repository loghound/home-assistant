""" Supports scanning a OpenWRT router. """
import logging
import json
from datetime import timedelta
import re
import threading
import requests

import homeassistant as ha
import homeassistant.util as util
from homeassistant.components.device_tracker import DOMAIN

# Return cached results if last scan was less then this time ago
MIN_TIME_BETWEEN_SCANS = timedelta(seconds=5)

_LOGGER = logging.getLogger(__name__)


# pylint: disable=unused-argument
def get_scanner(hass, config):
    """ Validates config and returns a Luci scanner. """
    if not util.validate_config(config,
                                {DOMAIN: [ha.CONF_HOST, ha.CONF_USERNAME,
                                          ha.CONF_PASSWORD]},
                                _LOGGER):
        return None

    scanner = LuciDeviceScanner(config[DOMAIN])

    return scanner if scanner.success_init else None


# pylint: disable=too-many-instance-attributes
class LuciDeviceScanner(object):
    """ This class queries a wireless router running OpenWrt firmware
    for connected devices. Adapted from Tomato scanner.

    # opkg install luci-mod-rpc
    for this to work on the router.

    The API is described here:
    http://luci.subsignal.org/trac/wiki/Documentation/JsonRpcHowTo

    (Currently, we do only wifi iwscan, and no DHCP lease access.)
    """

    def __init__(self, config):
        host = config[ha.CONF_HOST]
        username, password = config[ha.CONF_USERNAME], config[ha.CONF_PASSWORD]

        self.parse_api_pattern = re.compile(r"(?P<param>\w*) = (?P<value>.*);")

        self.lock = threading.Lock()

        self.last_results = {}

        self.token = _get_token(host, username, password)
        self.host = host

        self.mac2name = None
        self.success_init = self.token is not None

    def scan_devices(self):
        """ Scans for new devices and return a
            list containing found device ids. """

        self._update_info()

        return self.last_results

    def get_device_name(self, device):
        """ Returns the name of the given device or None if we don't know. """

        with self.lock:
            if self.mac2name is None:
                url = 'http://{}/cgi-bin/luci/rpc/uci'.format(self.host)
                result = _req_json_rpc(url, 'get_all', 'dhcp',
                                       params={'auth': self.token})
                if result:
                    hosts = [x for x in result.values()
                             if x['.type'] == 'host' and
                             'mac' in x and 'name' in x]
                    mac2name_list = [(x['mac'], x['name']) for x in hosts]
                    self.mac2name = dict(mac2name_list)
                else:
                    # Error, handled in the _req_json_rpc
                    return
            return self.mac2name.get(device, None)

    @util.Throttle(MIN_TIME_BETWEEN_SCANS)
    def _update_info(self):
        """ Ensures the information from the Luci router is up to date.
            Returns boolean if scanning successful. """
        if not self.success_init:
            return False

        with self.lock:
            _LOGGER.info("Checking ARP")

            url = 'http://{}/cgi-bin/luci/rpc/sys'.format(self.host)
            result = _req_json_rpc(url, 'net.arptable',
                                   params={'auth': self.token})
            if result:
                self.last_results = [x['HW address'] for x in result]

                return True

            return False


def _req_json_rpc(url, method, *args, **kwargs):
    """ Perform one JSON RPC operation. """
    data = json.dumps({'method': method, 'params': args})
    try:
        res = requests.post(url, data=data, timeout=5, **kwargs)
    except requests.exceptions.Timeout:
        _LOGGER.exception("Connection to the router timed out")
        return
    if res.status_code == 200:
        try:
            result = res.json()
        except ValueError:
            # If json decoder could not parse the response
            _LOGGER.exception("Failed to parse response from luci")
            return
        try:
            return result['result']
        except KeyError:
            _LOGGER.exception("No result in response from luci")
            return
    elif res.status_code == 401:
        # Authentication error
        _LOGGER.exception(
            "Failed to authenticate, "
            "please check your username and password")
        return
    else:
        _LOGGER.error("Invalid response from luci: %s", res)


def _get_token(host, username, password):
    """ Get authentication token for the given host+username+password """
    url = 'http://{}/cgi-bin/luci/rpc/auth'.format(host)
    return _req_json_rpc(url, 'login', username, password)
