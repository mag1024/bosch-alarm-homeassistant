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
    CONF_INSTALLER_CODE,
    CONF_USER_CODE
)
_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=7700): cv.positive_int
    }
)

STEP_AUTH_DATA_SCHEMA_SOLUTION = vol.Schema(
    {
        vol.Required(CONF_USER_CODE): str,
    }
)

STEP_AUTH_DATA_SCHEMA_AMAX = vol.Schema(
    {
        vol.Required(CONF_INSTALLER_CODE): str,
        vol.Required(CONF_PASSWORD): str,
    }
)

STEP_AUTH_DATA_SCHEMA_BG = vol.Schema(
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

async def try_connect(hass: HomeAssistant, data: dict[str, Any], load_selector: int=0):
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    panel = Panel(host=data[CONF_HOST], port=data[CONF_PORT],
                  automation_code=data.get(CONF_PASSWORD, None), 
                  installer_or_user_code=data.get(CONF_INSTALLER_CODE, data.get(CONF_USER_CODE, None)))

    try:
        await panel.connect(load_selector)
    except (PermissionError, ValueError) as err:
        _LOGGER.exception(err)
        raise RuntimeError("invalid_auth")
    except (OSError, ConnectionRefusedError, ssl.SSLError, asyncio.exceptions.TimeoutError) as err:
        _LOGGER.exception(err)
        raise RuntimeError("cannot_connect")
    except Exception as err:  # pylint: disable=broad-except
        _LOGGER.exception(err)
        raise RuntimeError("unknown")
    finally:
        await panel.disconnect()

    return (panel.model, panel.serial_number)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Bosch Alarm."""

    VERSION = 2
    entry: config_entries.ConfigEntry | None = None
    data: dict[str, Any] | None = None
    model: str | None = None

    @staticmethod
    @config_entries.callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )
        try:
            # Use load_selector = 0 to fetch the panel model without authentication. 
            (model, _) = await try_connect(self.hass, user_input, 0)
            self.model = model
            self.data = user_input
            return await self.async_step_auth()
        except RuntimeError as ex:
            _LOGGER.info(user_input)
            return self.async_show_form(
                step_id="user", data_schema=self.add_suggested_values_to_schema(
                    STEP_USER_DATA_SCHEMA, user_input
                ), errors={"base": ex.args}
            )
    async def async_step_auth(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the auth step."""
        if "Solution" in self.model:
            schema = STEP_AUTH_DATA_SCHEMA_SOLUTION
        elif "AMAX" in self.model:
            schema = STEP_AUTH_DATA_SCHEMA_AMAX
        else:
            schema = STEP_AUTH_DATA_SCHEMA_BG

        if user_input is None:
            return self.async_show_form(
                step_id="auth", data_schema=schema
            )
        self.data.update(user_input)
        try:
            (model, serial_number) = await try_connect(self.hass, self.data, Panel.LOAD_EXTENDED_INFO)
            await self.async_set_unique_id(serial_number)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="Bosch %s" % model, data=self.data)
        except RuntimeError as ex:
            return self.async_show_form(
                step_id="auth", data_schema=self.add_suggested_values_to_schema(
                    schema, user_input
                ), errors={"base": ex.args}
            )

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
