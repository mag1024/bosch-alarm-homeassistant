""" Support for Bosch Alarm Panel History as a sensor """

from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity

from homeassistant.const import EntityCategory

from .const import DOMAIN, HISTORY_ATTR

_LOGGER = logging.getLogger(__name__)

class PanelSensor(SensorEntity):
    def __init__(self, connection, observer):
        self._panel = connection.panel
        self._attr_has_entity_name = True
        self._attr_device_info = connection.device_info()
        self._observer = observer

    @property
    def should_poll(self): return False

    async def async_added_to_hass(self):
        self._observer.attach(self.schedule_update_ha_state)

    async def async_will_remove_from_hass(self):
        self._observer.detach(self.schedule_update_ha_state)

class PanelHistorySensor(PanelSensor):
    def __init__(self, connection):
        super().__init__(connection, connection.panel.history_observer)
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_unique_id = f'{connection.unique_id}_history'

    @property
    def icon(self): return "mdi:history"

    @property
    def state(self):
        events = self._panel.events
        if events:
            return str(events[-1])
        return "No events"

    @property
    def name(self): return f"History"

    @property
    def extra_state_attributes(self):
        events = self._panel.events
        return { HISTORY_ATTR + f'_{e.date}': e.message for e in events }

class PanelFaultsSensor(PanelSensor):
    def __init__(self, connection):
        super().__init__(connection, connection.panel.faults_observer)
        self._attr_unique_id = f'{connection.unique_id}_faults'

    @property
    def icon(self): return "mdi:alert-circle"

    @property
    def state(self):
        faults = self._panel.panel_faults
        return "\n".join(faults) if faults else "No faults"

    @property
    def name(self): return f"Faults"

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up a sensor for tracking panel history."""

    connection = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([PanelHistorySensor(connection), PanelFaultsSensor(connection)])

