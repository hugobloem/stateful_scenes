import pytest
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType, InvalidData
from custom_components.stateful_scenes import config_flow
from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.stateful_scenes.const import (
    DOMAIN,
    CONF_SCENE_PATH,
    CONF_NUMBER_TOLERANCE,
    CONF_SCENE_ENTITY_ID,
    CONF_SCENE_ENTITIES,
    CONF_EXTERNAL_SCENE_ACTIVE,
)


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
    internal_form_result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "configure_internal_scenes"}
    )
    assert internal_form_result["type"] is FlowResultType.FORM
    assert internal_form_result["step_id"] == "configure_internal_scenes"
    assert not internal_form_result["errors"]

    # Check manual flow can be started
    external_form_result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "select_external_scenes"}
    )
    assert external_form_result["type"] is FlowResultType.FORM
    assert external_form_result["step_id"] == "select_external_scenes"
    assert external_form_result["errors"]["base"] == "hub_not_found"


async def test_configure_internal_scenes(hass: HomeAssistant) -> None:
    """Test the configure internal scenes step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "configure_internal_scenes"}
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "configure_internal_scenes"
    assert not result["errors"]

    # Simulate user input
    user_input = {
        CONF_SCENE_PATH: "config/scenes.yaml",
        CONF_NUMBER_TOLERANCE: 0.1,
    }
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Home Assistant Scenes"
    assert result["data"][CONF_SCENE_PATH] == "config/scenes.yaml"
    assert result["data"][CONF_NUMBER_TOLERANCE] == 0.1


async def test_select_external_scenes(hass: HomeAssistant) -> None:
    """Test the select external scenes step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "select_external_scenes"}
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "select_external_scenes"
    assert "errors" not in result

    # Simulate user input
    user_input = {
        CONF_SCENE_ENTITY_ID: "scene.living_room",
    }
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "configure_external_scene_entities"
    assert not result["errors"]


async def test_configure_external_scene_entities(hass: HomeAssistant) -> None:
    """Test the configure external scene entities step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "select_external_scenes"}
    )

    user_input = {
        CONF_SCENE_ENTITY_ID: "scene.living_room",
    }
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input
    )

    user_input = {
        CONF_SCENE_ENTITIES: ["light.living_room_light"],
    }
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "learn_external_scene"
    assert not result["errors"]


async def test_learn_external_scene(hass: HomeAssistant) -> None:
    """Test the learn external scene step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "select_external_scenes"}
    )

    user_input = {
        CONF_SCENE_ENTITY_ID: "scene.living_room",
    }
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input
    )

    user_input = {
        CONF_SCENE_ENTITIES: ["light.living_room_light"],
    }
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input
    )

    user_input = {
        CONF_EXTERNAL_SCENE_ACTIVE: True,
    }
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Living Room Scene"
    assert result["data"][CONF_SCENE_ENTITY_ID] == "scene.living_room"
    assert result["data"][CONF_SCENE_ENTITIES] == ["light.living_room_light"]
