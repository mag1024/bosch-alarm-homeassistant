"""The Bosch Alarm integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from homeassistant.const import (
    CONF_HOST,
    CONF_PORT,
    CONF_PASSWORD,
)

import asyncio
import logging
import bosch_alarm_mode2

from .const import (
    DOMAIN,
    CONF_ARMING_CODE,
    CONF_REQUIRE_ARMING_CODE
)

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.ALARM_CONTROL_PANEL]
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Bosch Alarm from a config entry."""

    arming_code = None
    if CONF_REQUIRE_ARMING_CODE in entry.options and entry.options[CONF_REQUIRE_ARMING_CODE] and CONF_ARMING_CODE in entry.options:
        arming_code = entry.options[CONF_ARMING_CODE] 
    panel = bosch_alarm_mode2.Panel(
            host=entry.data[CONF_HOST], port=entry.data[CONF_PORT],
            passcode=entry.data[CONF_PASSWORD], arming_code=arming_code)
    try:
        await panel.connect()
    except asyncio.exceptions.TimeoutError:
        _LOGGER.warning("Initial panel connection timed out...")
    except:
        logging.exception("Initial panel connection failed")

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = panel

    setup = lambda: hass.async_create_task(
            hass.config_entries.async_forward_entry_setups(entry, PLATFORMS))
    if panel.connection_status():
        setup()
    else:
        panel.connection_status_observer.attach(
                lambda: panel.connection_status() and setup())

    entry.async_on_unload(entry.add_update_listener(options_update_listener))
    return True

async def options_update_listener(
    hass: HomeAssistant, config_entry: ConfigEntry
):
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    await hass.data[DOMAIN][entry.entry_id].disconnect()
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await hass.data[DOMAIN][entry.entry_id].disconnect()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
