"""Tests for the bosch_alarm config flow."""

from unittest.mock import MagicMock, patch

import pytest
import asyncio

from homeassistant import config_entries
from homeassistant.const import (
    CONF_HOST,
    CONF_PORT,
    CONF_PASSWORD,
    CONF_CODE,
    CONF_MODEL,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.components.bosch_alarm.const import (
    DOMAIN,
    CONF_INSTALLER_CODE,
    CONF_USER_CODE,
)

from bosch_alarm_mode2 import Panel

from tests.common import MockConfigEntry


async def test_form_user_solution(hass: HomeAssistant) -> None:
    """Test we get the form."""

    async def connect(self, load_selector):
        self.model = "Solution 3000"

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] is None
    with (
        patch("bosch_alarm_mode2.panel.Panel.connect", connect),
        patch(
            "homeassistant.components.bosch_alarm.async_setup_entry",
            return_value=True,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "1.1.1.1", CONF_PORT: 7700},
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "auth"
        assert result["errors"] is None
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USER_CODE: "1234"},
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["title"] == "Bosch Solution 3000"
        assert result["data"] == {
            CONF_HOST: "1.1.1.1",
            CONF_PORT: 7700,
            CONF_USER_CODE: "1234",
            CONF_MODEL: "Solution 3000",
        }


async def test_form_user_amax(hass: HomeAssistant) -> None:
    """Test we get the form."""

    async def connect(self, load_selector):
        self.model = "AMAX 3000"

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] is None
    with (
        patch("bosch_alarm_mode2.panel.Panel.connect", connect),
        patch(
            "homeassistant.components.bosch_alarm.async_setup_entry",
            return_value=True,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "1.1.1.1", CONF_PORT: 7700},
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "auth"
        assert result["errors"] is None
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_INSTALLER_CODE: "1234", CONF_PASSWORD: "1234567890"},
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["title"] == "Bosch AMAX 3000"
        assert result["data"] == {
            CONF_HOST: "1.1.1.1",
            CONF_PORT: 7700,
            CONF_INSTALLER_CODE: "1234",
            CONF_PASSWORD: "1234567890",
            CONF_MODEL: "AMAX 3000",
        }


async def test_form_user_bg(hass: HomeAssistant) -> None:
    """Test we get the form."""

    async def connect(self, load_selector):
        self.model = "B5512 (US1B)"

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] is None
    with (
        patch("bosch_alarm_mode2.panel.Panel.connect", connect),
        patch(
            "homeassistant.components.bosch_alarm.async_setup_entry",
            return_value=True,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "1.1.1.1", CONF_PORT: 7700},
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "auth"
        assert result["errors"] is None
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PASSWORD: "1234567890"},
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["title"] == "Bosch B5512 (US1B)"
        assert result["data"] == {
            CONF_HOST: "1.1.1.1",
            CONF_PORT: 7700,
            CONF_PASSWORD: "1234567890",
            CONF_MODEL: "B5512 (US1B)",
        }


async def test_form_invalid_auth(hass: HomeAssistant) -> None:
    """Test we get the form."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] is None
    with (
        patch("bosch_alarm_mode2.panel.Panel.connect", side_effect=PermissionError()),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "1.1.1.1", CONF_PORT: 7700},
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {"base": "invalid_auth"}


async def test_form_cant_connect(hass: HomeAssistant) -> None:
    """Test we get the form."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] is None
    with (
        patch(
            "bosch_alarm_mode2.panel.Panel.connect",
            side_effect=asyncio.exceptions.TimeoutError(),
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "1.1.1.1", CONF_PORT: 7700},
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {"base": "cannot_connect"}


async def test_options_flow(hass: HomeAssistant) -> None:
    """Test the options flow for SkyConnect."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "1.1.1.1",
            CONF_PORT: 7700,
            CONF_INSTALLER_CODE: "1234",
            CONF_PASSWORD: "1234567890",
            CONF_MODEL: "AMAX 3000",
        },
        version=1,
        minor_version=2,
    )
    config_entry.add_to_hass(hass)

    with (
        patch("bosch_alarm_mode2.panel.Panel.connect", None),
        patch(
            "homeassistant.components.bosch_alarm.async_setup_entry",
            return_value=True,
        ),
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)

    # First step is confirmation
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_CODE: "1234"},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"] is True

    assert config_entry.options == {CONF_CODE: "1234"}
