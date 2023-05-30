""" Support for Bosch Alarm Panel History as a sensor """

from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorEntity
)
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

HISTORY_ATTR = 'history'
HISTORY_ID_ATTR = 'history_id'

class PanelHistorySensor(SensorEntity, RestoreEntity):
    def __init__(self, panel, unique_id):
        self._panel = panel
        self._observer = panel.history_observer
        self._unique_id = unique_id

    @property
    def unique_id(self): return self._unique_id

    @property
    def should_poll(self): return False

    @property
    def name(self): return f"{self._panel.model} History"

    @property
    def extra_state_attributes(self):
        return { HISTORY_ATTR: "\n".join(self._panel.history), HISTORY_ID_ATTR: self._panel.last_history_id }
    
    async def async_added_to_hass(self):
        self._observer.attach(self.async_schedule_update_ha_state)
        state = await self.async_get_last_state()
        history = []
        start_id = 0
        if state:
            state = state.as_dict()
            if HISTORY_ID_ATTR in state:
                start_id = state[HISTORY_ID_ATTR]
                history = state[HISTORY_ATTR].split("\n")
        await self._panel.load_history(start_id, history)

    async def async_will_remove_from_hass(self):
        self._observer.detach(self.async_schedule_update_ha_state)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up a sensor for tracking panel history."""

    panel = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(
            [PanelHistorySensor(
                panel, f'{panel.serial_number}_history')])

