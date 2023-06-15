""" Support for Bosch Alarm Panel History as a sensor """

from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorEntity
)

from homeassistant.const import EntityCategory

from .const import (
    DOMAIN,
)
from .device import device_info_from_panel

_LOGGER = logging.getLogger(__name__)

HISTORY_ATTR = 'history'
HISTORY_ID_ATTR = 'history_id'

class PanelHistorySensor(SensorEntity):
    def __init__(self, panel, unique_id):
        self._panel = panel
        self._observer = panel.history_observer
        self._unique_id = unique_id
        self._attr_device_info = device_info_from_panel(panel)
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def icon(self): return "mdi:history"

    @property
    def unique_id(self): return self._unique_id

    @property
    def should_poll(self): return False

    @property
    def state(self): return len(self._panel.history)

    @property
    def name(self): return f"{self._panel.model} History"

    @property
    def extra_state_attributes(self):
        history = self._panel.history
        return { HISTORY_ATTR: "\n".join(x[1] for x in history)}
    
    async def async_added_to_hass(self):
        self._observer.attach(self.schedule_update_ha_state)

    async def async_will_remove_from_hass(self):
        self._observer.detach(self.schedule_update_ha_state)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up a sensor for tracking panel history."""

    panel = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(
            [PanelHistorySensor(
                panel, f'{panel.serial_number}_history')])

