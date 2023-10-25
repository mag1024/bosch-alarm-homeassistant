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
import homeassistant.helpers.config_validation as cv

from homeassistant.const import (
    CONF_HOST,
    CONF_PORT,
    CONF_PASSWORD,
    CONF_CODE
)

from bosch_alarm_mode2 import Panel

from .const import (
    DOMAIN,
    CONF_INSTALLER_CODE
)
_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=7700): cv.positive_int,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_INSTALLER_CODE): str,
    }
)

STEP_CODE_AUTH_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_INSTALLER_CODE): str,
    }
)

STEP_AUTOMATION_AUTH_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PASSWORD): str,
    }
)

STEP_INIT_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional(
            CONF_CODE
        ): str
    }
)

async def try_connect(hass: HomeAssistant, data: dict[str, Any]):
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    panel = Panel(host=data[CONF_HOST], port=data[CONF_PORT],
                  automation_code=data[CONF_PASSWORD], installer_code=data.get(CONF_INSTALLER_CODE, None)) 
    errors = {}

    try:
        await panel.connect(Panel.LOAD_BASIC_INFO)
    except (PermissionError, ValueError):
        errors["base"] = "invalid_auth"
    except (OSError, ConnectionRefusedError, ssl.SSLError, asyncio.exceptions.TimeoutError):
        errors["base"] = "cannot_connect"
    except Exception:  # pylint: disable=broad-except
        _LOGGER.exception("Unexpected exception")
        errors["base"] = "unknown"
    finally:
        await panel.disconnect()
    
    if errors:
        raise Exception(errors)
    
    return (panel.model, panel.serial_number)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Bosch Alarm."""

    VERSION = 1
    entry: config_entries.ConfigEntry | None = None

    @staticmethod
    @config_entries.callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if "entry_id" in self.context:
            entry = self.hass.config_entries.async_get_entry(
                self.context["entry_id"]
            )
            if user_input is None:
                user_input = entry.data
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )
        try:
            (model, serial_number) = await try_connect(self.hass, user_input)
            if "entry_id" in self.context:
                entry = self.hass.config_entries.async_get_entry(
                    self.context["entry_id"]
                )
                self.hass.config_entries.async_update_entry(entry, data=user_input)
                await self.hass.config_entries.async_reload(entry.entry_id)
                return self.async_abort(reason="reauth_successful")
            else:
                await self.async_set_unique_id(serial_number)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="Bosch %s" % model, data=user_input)
        except Exception as ex:
            return self.async_show_form(
                step_id="user", data_schema=self.add_suggested_values_to_schema(
                    STEP_USER_DATA_SCHEMA, user_input
                ), errors=ex.args
            )

    async def async_step_reauth(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
       return await self.async_step_user(user_input)

class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                STEP_INIT_DATA_SCHEMA, self.config_entry.options
            )
        )
