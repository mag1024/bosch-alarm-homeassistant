""" Support for Bosch Alarm Panel """

from __future__ import annotations

import logging

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
)

from .const import (
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

READY_STATE_ATTR = 'ready_to_arm'
READY_STATE_NO = 'no'
READY_STATE_HOME = 'home'
READY_STATE_AWAY = 'away'
FAULTED_POINTS_ATTR = 'faulted_points'

class AreaAlarmControlPanel(AlarmControlPanelEntity):
    def __init__(self, panel, area_id, area, unique_id):
        self._panel = panel
        self._area_id = area_id
        self._area = area
        self._unique_id = unique_id

    @property
    def unique_id(self): return self._unique_id

    @property
    def should_poll(self): return False

    @property
    def name(self): return self._area.name

    @property
    def state(self):
        if self._area.is_disarmed(): return 'disarmed'
        if self._area.is_arming(): return 'arming'
        if self._area.is_pending(): return 'pending'
        if self._area.is_part_armed(): return 'armed_home'
        if self._area.is_all_armed(): return 'armed_away'
        return None

    @property
    def supported_features(self) -> int:
        return (
            AlarmControlPanelEntityFeature.ARM_HOME
            | AlarmControlPanelEntityFeature.ARM_AWAY
        )

    async def async_alarm_disarm(self, code=None) -> None:
        await self._panel.area_disarm(self._area_id)
    async def async_alarm_arm_home(self, code=None) -> None:
        await self._panel.area_arm_part(self._area_id)
    async def async_alarm_arm_away(self, code=None) -> None:
        await self._panel.area_arm_all(self._area_id)

    @property
    def extra_state_attributes(self):
        ready_state = READY_STATE_NO
        if self._area.all_ready: ready_state = READY_STATE_AWAY
        elif self._area.part_ready: ready_state = READY_STATE_HOME
        return { READY_STATE_ATTR: ready_state,
                 FAULTED_POINTS_ATTR: self._area.faults }

    async def async_added_to_hass(self):
        self._area.status_observer.attach(self.async_schedule_update_ha_state)
        self._area.ready_observer.attach(self.async_schedule_update_ha_state)

    async def async_will_remove_from_hass(self):
        self._area.status_observer.detach(self.async_schedule_update_ha_state)
        self._area.ready_observer.detach(self.async_schedule_update_ha_state)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up control panels for each area."""

    panel = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(
            AreaAlarmControlPanel(panel, id, area, f'{panel.serial_number}_area_{id}')
                for (id, area) in panel.areas.items())

