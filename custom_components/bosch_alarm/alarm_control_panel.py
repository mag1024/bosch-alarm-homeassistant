""" Support for Bosch Alarm Panel """

from __future__ import annotations

import logging

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
)
import homeassistant.components.alarm_control_panel as alarm

from homeassistant.const import CONF_CODE
from homeassistant.helpers import config_validation, entity_platform
from homeassistant.helpers.config_validation import make_entity_service_schema
from homeassistant.util import dt

import voluptuous as vol
import datetime
from typing import Any

from .const import DOMAIN, DATETIME_ATTR
from .device import device_info_from_panel

_LOGGER = logging.getLogger(__name__)

READY_STATE_ATTR = 'ready_to_arm'
READY_STATE_NO = 'no'
READY_STATE_HOME = 'home'
READY_STATE_AWAY = 'away'
FAULTED_POINTS_ATTR = 'faulted_points'
ALARMS_ATTR = 'alarms'

SET_DATE_TIME_SERVICE_NAME = "set_date_time"
SET_DATE_TIME_SCHEMA = make_entity_service_schema({
    vol.Optional(DATETIME_ATTR): config_validation.datetime
})

class AreaAlarmControlPanel(AlarmControlPanelEntity):
    def __init__(self, panel, arming_code, area_id, area, unique_id):
        self._panel = panel
        self._area_id = area_id
        self._area = area
        self._unique_id = unique_id
        self._arming_code = arming_code
        self._attr_device_info = device_info_from_panel(panel)
    
    @property
    def code_format(self) -> alarm.CodeFormat | None:
        """Return one or more digits/characters."""
        if self._arming_code is None: 
            return None
        if self._arming_code.isnumeric():
            return alarm.CodeFormat.NUMBER
        return alarm.CodeFormat.TEXT
    @property
    def unique_id(self): return self._unique_id

    @property
    def should_poll(self): return False

    @property
    def name(self): return self._area.name

    @property
    def state(self):
        if self._area.is_triggered(): return 'triggered'
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
    
    def _arming_code_correct(self, code) -> bool:
        return code == self._arming_code

    async def async_alarm_disarm(self, code=None) -> None:
        if self._arming_code_correct(code): 
            await self._panel.area_disarm(self._area_id)
    async def async_alarm_arm_home(self, code=None) -> None:
        if self._arming_code_correct(code): 
            await self._panel.area_arm_part(self._area_id)
    async def async_alarm_arm_away(self, code=None) -> None:
        if self._arming_code_correct(code): 
            await self._panel.area_arm_all(self._area_id)

    @property
    def extra_state_attributes(self):
        ready_state = READY_STATE_NO
        if self._area.all_ready: ready_state = READY_STATE_AWAY
        elif self._area.part_ready: ready_state = READY_STATE_HOME
        return { READY_STATE_ATTR: ready_state,
                 FAULTED_POINTS_ATTR: self._area.faults,
                 ALARMS_ATTR: "\n".join(self._area.alarms) }

    async def async_added_to_hass(self):
        self._area.status_observer.attach(self.schedule_update_ha_state)
        self._area.alarm_observer.attach(self.schedule_update_ha_state)
        self._area.ready_observer.attach(self.schedule_update_ha_state)

    async def async_will_remove_from_hass(self):
        self._area.status_observer.detach(self.schedule_update_ha_state)
        self._area.alarm_observer.detach(self.schedule_update_ha_state)
        self._area.ready_observer.detach(self.schedule_update_ha_state)

    async def set_panel_date(self, **kwargs: Any):
        value: datetime = kwargs.get(DATETIME_ATTR, dt.now())
        await self._panel.set_panel_date(value)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up control panels for each area."""
    panel = hass.data[DOMAIN][config_entry.entry_id]

    arming_code = config_entry.options.get(CONF_CODE, None)
    async_add_entities(
            AreaAlarmControlPanel(panel, arming_code, id, area, f'{panel.serial_number}_area_{id}')
                for (id, area) in panel.areas.items())

    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(SET_DATE_TIME_SERVICE_NAME, SET_DATE_TIME_SCHEMA, "set_panel_date")

