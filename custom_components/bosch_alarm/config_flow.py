"""Config flow for Bosch Alarm integration."""
from __future__ import annotations

import logging
import ssl
import asyncio
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from homeassistant.const import (
    CONF_HOST,
    CONF_PORT,
    CONF_PASSWORD,
)

from bosch_alarm_mode2 import Panel

from .const import (
    DOMAIN,
)
_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT): int,
        vol.Required(CONF_PASSWORD): str,
    }
)

async def try_connect(hass: HomeAssistant, data: dict[str, Any]):
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    panel = Panel(host=data[CONF_HOST], port=data[CONF_PORT],
                  passcode=data[CONF_PASSWORD],legacymode=False)
    try:
        await panel.connect(Panel.LOAD_BASIC_INFO)
    finally:
        await panel.disconnect()

    # Return info that you want to store in the config entry.
    return (panel.model, panel.serial_number)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Bosch Alarm."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            (model, serial_number) = await try_connect(self.hass, user_input)
            await self.async_set_unique_id(serial_number)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="Bosch %s" % model, data=user_input)
        except (OSError, ConnectionRefusedError, ssl.SSLError, asyncio.exceptions.TimeoutError):
            errors["base"] = "cannot_connect"
        except PermissionError:
            errors["base"] = "invalid_auth"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
