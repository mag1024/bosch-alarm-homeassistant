""" Support for Bosch Alarm Panel History as a sensor """

from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity

from homeassistant.const import EntityCategory

from .const import DOMAIN, HISTORY_ATTR

from .device import device_info_from_panel

_LOGGER = logging.getLogger(__name__)

class PanelHistorySensor(SensorEntity):
    def __init__(self, panel):
        self._panel = panel
        self._attr_device_info = device_info_from_panel(panel)
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def icon(self): return "mdi:history"

    @property
    def unique_id(self): return f'{self._panel.serial_number}_history'

    @property
    def should_poll(self): return False

    @property
    def state(self):
        events = self._panel.events
        if events:
            return str(events[-1])
        return "No events"

    @property
    def name(self): return f"{self._panel.model} History"

    @property
    def extra_state_attributes(self):
        events = self._panel.events
        return { HISTORY_ATTR + f'_{e.date}': e.message for e in events }
    
    async def async_added_to_hass(self):
        self._panel.history_observer.attach(self.schedule_update_ha_state)

    async def async_will_remove_from_hass(self):
        self._panel.history_observer.detach(self.schedule_update_ha_state)
class PanelFaultsSensor(SensorEntity):
    def __init__(self, panel):
        self._panel = panel
        self._attr_device_info = device_info_from_panel(panel)

    @property
    def icon(self): return "mdi:alert-circle"

    @property
    def unique_id(self): return f'{self._panel.serial_number}_faults'

    @property
    def should_poll(self): return False

    @property
    def state(self):
        faults = self._panel.panel_faults
        return "\n".join(faults) if faults else "No faults"

    @property
    def name(self): return f"{self._panel.model} Faults"
    
    async def async_added_to_hass(self):
        self._panel.faults_observer.attach(self.schedule_update_ha_state)

    async def async_will_remove_from_hass(self):
        self._panel.faults_observer.detach(self.schedule_update_ha_state)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up a sensor for tracking panel history."""

    panel = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([PanelHistorySensor(panel), PanelFaultsSensor(panel)])

