"""The Bosch Alarm integration."""

from __future__ import annotations

import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry

from homeassistant.const import (
    CONF_HOST,
    CONF_PORT,
    CONF_PASSWORD
)

import bosch_alarm_mode2

from .device import BoschPanel

from .const import DOMAIN, CONF_INSTALLER_CODE, CONF_USER_CODE

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.ALARM_CONTROL_PANEL, Platform.SENSOR,
                             Platform.SWITCH]
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Bosch Alarm from a config entry."""
    panel = bosch_alarm_mode2.Panel(
            host=entry.data[CONF_HOST], port=entry.data[CONF_PORT],
            automation_code=entry.data.get(CONF_PASSWORD, None),
            installer_or_user_code=entry.data.get(CONF_INSTALLER_CODE, entry.data.get(CONF_USER_CODE, None)))

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = BoschPanel(panel)

    # We store the serial number as the unique id
    # If the panel doesn't expose it's serial number, use the entry id as a unique id instead.
    panel.serial_number = entry.unique_id or entry.entry_id

    # We use the panels model as the entries title
    panel.model = entry.title.replace("Bosch ","")

    # Remove old devices using the panel model as an identifier
    dr = device_registry.async_get(hass)
    for device_entry in device_registry.async_entries_for_config_entry(dr, entry.entry_id):
        if (DOMAIN, panel.model) in device_entry.identifiers:
            dr.async_remove_device(device_entry.id)

    entry.async_on_unload(entry.add_update_listener(options_update_listener))

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(entry, PLATFORMS))

    entry.async_create_background_task(hass, panel.connect(), "connection")

    return True

async def options_update_listener(
    hass: HomeAssistant, config_entry: ConfigEntry
):
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)

async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)
    if config_entry.version == 1:
        new = {**config_entry.data}
        # Solution panels previously put the user code in the password field
        # But now its in the user code field
        if "Solution" in config_entry.title:
            new[CONF_USER_CODE] = new[CONF_PASSWORD]
            new.pop(CONF_PASSWORD)

        config_entry.version = 2
        hass.config_entries.async_update_entry(config_entry, data=new)

    _LOGGER.debug("Migration to version %s successful", config_entry.version)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await hass.data[DOMAIN][entry.entry_id].disconnect()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
