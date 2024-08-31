"""Support for Bosch Alarm Panel doors as locks"""

from __future__ import annotations

import logging
import re

from homeassistant.components.lock import (
    LockEntityFeature,
    LockEntity,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class PanelLockEntity(LockEntity):
    def __init__(self, id, panel_conn, door):
        self._observer = door.status_observer
        self._panel = panel_conn.panel
        self._attr_unique_id = f"{panel_conn.unique_id}_door_{id}"
        self._attr_device_info = panel_conn.device_info()
        self._attr_has_entity_name = True
        self._door = door
        self._door_id = id
        self._attr_supported_features = LockEntityFeature.OPEN

    @property
    def name(self):
        return self._door.name

    @property
    def is_open(self):
        return self._door.is_open()

    @property
    def is_locked(self):
        return self._door.is_locked()

    @property
    def available(self):
        return self._door.is_open() or self._door.is_locked()

    @property
    def should_poll(self):
        return False

    async def async_lock(self):
        await self._panel.door_relock(self._door_id)

    async def async_unlock(self):
        await self._panel.door_unlock(self._door_id)

    async def async_open(self):
        await self._panel.door_cycle(self._door_id)

    async def async_added_to_hass(self):
        self._observer.attach(self.schedule_update_ha_state)

    async def async_will_remove_from_hass(self):
        self._observer.detach(self.schedule_update_ha_state)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up binary sensors for alarm points and the connection status."""

    panel_conn = hass.data[DOMAIN][config_entry.entry_id]
    panel = panel_conn.panel

    def setup():
        async_add_entities(
            PanelLockEntity(id, panel_conn, door) for (id, door) in panel.doors.items()
        )

    panel_conn.on_connect.append(setup)
