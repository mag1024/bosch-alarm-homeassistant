"""The Bosch Alarm integration."""

from __future__ import annotations

import logging

import bosch_alarm_mode2

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_MODEL,
    CONF_PASSWORD,
    CONF_PORT,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import CONF_INSTALLER_CODE, CONF_USER_CODE, DOMAIN
from .device import PanelConnection

PLATFORMS: list[Platform] = [
    Platform.ALARM_CONTROL_PANEL,
    Platform.BINARY_SENSOR,
    Platform.LOCK,
    Platform.SENSOR,
    Platform.SWITCH,
]
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Bosch Alarm from a config entry."""
    panel = bosch_alarm_mode2.Panel(
        host=entry.data[CONF_HOST],
        port=entry.data[CONF_PORT],
        automation_code=entry.data.get(CONF_PASSWORD, None),
        installer_or_user_code=entry.data.get(
            CONF_INSTALLER_CODE, entry.data.get(CONF_USER_CODE, None)
        ),
    )

    # The config flow sets the entries unique id to the serial number if available
    # If the panel doesn't expose it's serial number, use the entry id as a unique id instead.
    unique_id = entry.unique_id or entry.entry_id

    panel_conn = PanelConnection(panel, unique_id, entry.data[CONF_MODEL])

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = panel_conn

    entry.async_on_unload(entry.add_update_listener(options_update_listener))

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    )
    entry.async_create_background_task(hass, panel.connect(), "panel_connection")
    return True


async def options_update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)
    new = {**config_entry.data}
    if config_entry.version == 1:
        # Solution panels previously put the user code in the password field
        # But now its in the user code field
        if "Solution" in config_entry.title:
            new[CONF_USER_CODE] = new[CONF_PASSWORD]
            new.pop(CONF_PASSWORD)

    if config_entry.version < 3:
        model = config_entry.title.replace("Bosch ", "")

        # Remove old devices using the panel model as an identifier
        device_registry = dr.async_get(hass)
        for device_entry in dr.async_entries_for_config_entry(
            device_registry, config_entry.entry_id
        ):
            if (DOMAIN, model) in device_entry.identifiers:
                device_registry.async_remove_device(device_entry.id)

        # The config flow sets the entries title to the panel's model
        new[CONF_MODEL] = model

        config_entry.version = 3
        hass.config_entries.async_update_entry(config_entry, data=new)

    _LOGGER.debug("Migration to version %s successful", config_entry.version)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await hass.data[DOMAIN][entry.entry_id].disconnect()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
