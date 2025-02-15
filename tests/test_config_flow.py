import pytest
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType, InvalidData
from custom_components.stateful_scenes import config_flow
from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.stateful_scenes.const import DOMAIN


async def test_config_flow_options(hass: HomeAssistant) -> None:
    """Test the config flow starts with a menu with manual and discover options."""
    # Check initial flow is a menu with two options
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["step_id"] == "user"
    assert result["type"] is FlowResultType.MENU
    assert result["menu_options"] == [
        "configure_internal_scenes",
        "select_external_scenes",
    ]

    # Check discover flow can be started
    discover_form_result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "configure_internal_scenes"}
    )
    assert discover_form_result["type"] is FlowResultType.FORM
    assert discover_form_result["step_id"] == "configure_internal_scenes"
    assert not discover_form_result["errors"]

    # Check manual flow can be started
    manual_form_result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "select_external_scenes"}
    )
    assert manual_form_result["type"] is FlowResultType.FORM
    assert manual_form_result["step_id"] == "select_external_scenes"
    assert manual_form_result["errors"]["base"] == "hub_not_found"
