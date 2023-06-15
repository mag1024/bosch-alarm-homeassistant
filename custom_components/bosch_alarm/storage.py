"""Helpers for History data stored in HA storage."""

from __future__ import annotations

import logging
from typing import Any, TypedDict, NamedTuple

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.storage import Store

from .const import DOMAIN, HISTORY

HISTORY_STORAGE_KEY = HISTORY
HISTORY_STORAGE_VERSION = 1
HISTORY_SAVE_DELAY = 10
_LOGGER = logging.getLogger(__name__)


class HistoryEvent(NamedTuple):
    event_id: int
    event: str


class StorageLayout(TypedDict):

    pairings: dict[str, list[HistoryEvent]]


class HistoryStorage:

    def __init__(self, hass: HomeAssistant) -> None:
        """Create a new history store."""
        self.hass = hass
        self.store = Store[StorageLayout](
            hass, HISTORY_STORAGE_VERSION, HISTORY_STORAGE_KEY
        )
        self.storage_data: dict[str, list[HistoryEvent]] = {}

    async def async_initialize(self) -> None:
        """Get the history data."""
        if not (raw_storage := await self.store.async_load()):
            # There is no history events yet
            return

        self.storage_data = raw_storage.get("history", {})

    def get_events(self, entry_id: str) -> list[HistoryEvent]:
        """Get history data."""
        return self.storage_data.get(entry_id) or []

    @callback
    def async_create_or_update_map(
        self, entry_id: str, events: list[HistoryEvent]
    ) -> list[HistoryEvent]:
        self.storage_data[entry_id] = events
        self._async_schedule_save()
        return events

    @callback
    def async_delete_map(self, entry_id: str) -> None:
        if entry_id in self.storage_data:
            self.storage_data.pop(entry_id)
            self._async_schedule_save()

    @callback
    def _async_schedule_save(self) -> None:
        self.store.async_delay_save(self._data_to_save, HISTORY_SAVE_DELAY)

    @callback
    def _data_to_save(self) -> StorageLayout:
        """Return history events to store in a file."""
        return StorageLayout(history=self.storage_data)


async def async_get_entity_storage(hass: HomeAssistant) -> HistoryStorage:
    """Get entity storage."""
    if HISTORY in hass.data:
        map_storage: HistoryStorage = hass.data[HISTORY]
        return map_storage
    map_storage = hass.data[HISTORY] = HistoryStorage(hass)
    await map_storage.async_initialize()
    return map_storage
