""" Support for Bosch Alarm Panel """

from __future__ import annotations

import logging

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
)
import homeassistant.components.alarm_control_panel as alarm
from homeassistant.helpers.restore_state import RestoreEntity

from homeassistant.const import (
    CONF_CODE
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
HISTORY_ATTR = 'history'
HISTORY_ID_ATTR = 'history_id'
ALARMS_ATTR = 'alarms'

class AreaAlarmControlPanel(AlarmControlPanelEntity, RestoreEntity):
    def __init__(self, panel, arming_code, area_id, area, unique_id):
        self._panel = panel
        self._area_id = area_id
        self._area = area
        self._unique_id = unique_id
        self._arming_code = arming_code
    
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
        if self.code_format == alarm.CodeFormat.NUMBER:
            return int(code) == self._arming_code

        if self.code_format == alarm.CodeFormat.TEXT:
            return code == self._arming_code

        return True

    async def async_alarm_disarm(self, code=0) -> None:
        if self._arming_code_correct(code): 
            await self._panel.area_disarm(self._area_id)
    async def async_alarm_arm_home(self, code=0) -> None:
        if self._arming_code_correct(code): 
            await self._panel.area_arm_part(self._area_id)
    async def async_alarm_arm_away(self, code=0) -> None:
        if self._arming_code_correct(code): 
            await self._panel.area_arm_all(self._area_id)

    @property
    def extra_state_attributes(self):
        ready_state = READY_STATE_NO
        if self._area.all_ready: ready_state = READY_STATE_AWAY
        elif self._area.part_ready: ready_state = READY_STATE_HOME
        return { READY_STATE_ATTR: ready_state,
                 FAULTED_POINTS_ATTR: self._area.faults,
                 HISTORY_ATTR: "\n".join(self._area.history),
                 HISTORY_ID_ATTR: self._area.last_history_event,
                 ALARMS_ATTR: "\n".join(self._area.alarms) }
    
    async def _async_update_ha_state(self):
        await self.async_schedule_update_ha_state()
        await self.async_write_ha_state()

    async def async_added_to_hass(self):
        self._area.status_observer.attach(self._async_update_ha_state)
        self._area.alarm_observer.attach(self._async_update_ha_state)
        self._area.ready_observer.attach(self._async_update_ha_state)
        self._area.history_observer.attach(self._async_update_ha_state)
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
        self._area.status_observer.detach(self._async_update_ha_state)
        self._area.alarm_observer.detach(self._async_update_ha_state)
        self._area.ready_observer.detach(self._async_update_ha_state)
        self._area.history_observer.detach(self._async_update_ha_state)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up control panels for each area."""

    panel = hass.data[DOMAIN][config_entry.entry_id]

    arming_code = config_entry.options.get(CONF_CODE, None)
    async_add_entities(
            AreaAlarmControlPanel(panel, arming_code, id, area, f'{panel.serial_number}_area_{id}')
                for (id, area) in panel.areas.items())

