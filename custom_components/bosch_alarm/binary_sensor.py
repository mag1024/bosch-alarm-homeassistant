""" Support for Bosch Alarm Panel points as binary sensors """

from __future__ import annotations

import logging
import re

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)

from .const import DOMAIN
from .device import device_info_from_panel

_LOGGER = logging.getLogger(__name__)

def _guess_device_class(name):
    if re.search(r'\b(win(d)?(ow)?|wn)\b', name):
        return BinarySensorDeviceClass.WINDOW
    if re.search(r'\b(door|dr)\b', name):
        return BinarySensorDeviceClass.DOOR
    if re.search(r'\b(motion|md)\b', name):
        return BinarySensorDeviceClass.MOTION
    if re.search(r'\bco\b', name):
        return BinarySensorDeviceClass.CO
    if re.search(r'\bsmoke\b', name):
        return BinarySensorDeviceClass.SMOKE
    if re.search(r'\bglassbr(ea)?k\b', name):
        return BinarySensorDeviceClass.TAMPER
    return None

class PanelBinarySensor(BinarySensorEntity):
    def __init__(self, observer, unique_id, device_info):
        self._observer = observer
        self._unique_id = unique_id
        self._attr_has_entity_name = True
        self._attr_device_info = device_info

    @property
    def unique_id(self): return self._unique_id

    @property
    def should_poll(self): return False

    async def async_added_to_hass(self):
        self._observer.attach(self.schedule_update_ha_state)

    async def async_will_remove_from_hass(self):
        self._observer.detach(self.schedule_update_ha_state)

class PointSensor(PanelBinarySensor):
    def __init__(self, point, unique_id, device_info):
        PanelBinarySensor.__init__(
                self, point.status_observer, unique_id, device_info)
        self._point = point

    @property
    def name(self): return self._point.name

    @property
    def is_on(self): return self._point.is_open()

    @property
    def available(self):
        return self._point.is_open() or self._point.is_normal()

    @property
    def device_class(self):
        return _guess_device_class(self.name.lower())

class ConnectionStatusSensor(PanelBinarySensor):
    def __init__(self, panel, unique_id):
        PanelBinarySensor.__init__(
                self, panel.connection_status_observer, unique_id,
                device_info_from_panel(panel))
        self._panel = panel

    @property
    def name(self): return f"Connection Status"

    @property
    def is_on(self): return self._panel.connection_status()

    @property
    def device_class(self): return BinarySensorDeviceClass.CONNECTIVITY


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up binary sensors for alarm points and the connection status."""

    data = hass.data[DOMAIN][config_entry.entry_id]
    panel = data.panel

    async_add_entities(
            [ConnectionStatusSensor(
                panel, f'{panel.serial_number}_connection_status')])
    def setup():
        device_info = device_info_from_panel(panel)
        async_add_entities(
                PointSensor(point, f'{panel.serial_number}_point_{id}', device_info)
                    for (id, point) in panel.points.items())

    data.register_entity_setup(setup)
