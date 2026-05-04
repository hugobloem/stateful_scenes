"""Tests for Stateful Scenes config flow."""

from __future__ import annotations

import os

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.stateful_scenes.const import (
    CONF_DEBOUNCE_TIME,
    CONF_ENABLE_DISCOVERY,
    CONF_EXTERNAL_SCENE_ACTIVE,
    CONF_IGNORE_UNAVAILABLE,
    CONF_NUMBER_TOLERANCE,
    CONF_RESTORE_STATES_ON_DEACTIVATE,
    CONF_SCENE_ENTITIES,
    CONF_SCENE_PATH,
    CONF_TRANSITION_TIME,
    DOMAIN,
)

from .const import MOCK_EXTERNAL_SCENE_DATA, MOCK_HUB_DATA, SCENES_YAML_CONTENT


async def test_user_step_shows_menu(hass: HomeAssistant):
    """Test user step shows a menu with internal/external options."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == FlowResultType.MENU
    assert "configure_internal_scenes" in result["menu_options"]
    assert "select_external_scenes" in result["menu_options"]


async def test_configure_internal_scenes_success(hass: HomeAssistant):
    """Test configuring internal scenes with valid path creates entry."""
    # Write scenes file
    scenes_path = os.path.join(hass.config.config_dir, "scenes.yaml")
    with open(scenes_path, "w") as f:
        f.write(SCENES_YAML_CONTENT)

    # Set up scene entities so Hub can resolve entity_ids
    hass.states.async_set(
        "scene.test_scene_1",
        "scening",
        {"friendly_name": "Test Scene 1", "id": "1001"},
    )
    hass.states.async_set(
        "scene.test_scene_2",
        "scening",
        {"friendly_name": "Test Scene 2", "id": "1002"},
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "configure_internal_scenes"},
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "configure_internal_scenes"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_SCENE_PATH: "scenes.yaml",
            CONF_NUMBER_TOLERANCE: 1,
            CONF_RESTORE_STATES_ON_DEACTIVATE: False,
            CONF_TRANSITION_TIME: 1.0,
            CONF_DEBOUNCE_TIME: 0.0,
            CONF_IGNORE_UNAVAILABLE: False,
            CONF_ENABLE_DISCOVERY: False,
        },
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Home Assistant Scenes"
    assert result["data"][CONF_SCENE_PATH] == "scenes.yaml"
    assert result["data"]["hub"] is True


async def test_configure_internal_scenes_yaml_not_found(hass: HomeAssistant):
    """Test configuring with non-existent file shows error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "configure_internal_scenes"},
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_SCENE_PATH: "nonexistent.yaml",
            CONF_NUMBER_TOLERANCE: 1,
            CONF_RESTORE_STATES_ON_DEACTIVATE: False,
            CONF_TRANSITION_TIME: 1.0,
            CONF_DEBOUNCE_TIME: 0.0,
            CONF_IGNORE_UNAVAILABLE: False,
            CONF_ENABLE_DISCOVERY: False,
        },
    )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "yaml_not_found"}


async def test_configure_internal_scenes_invalid_yaml(hass: HomeAssistant):
    """Test configuring with invalid YAML shows error."""
    path = os.path.join(hass.config.config_dir, "bad.yaml")
    with open(path, "w") as f:
        f.write("{{{{invalid yaml: [}")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "configure_internal_scenes"},
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_SCENE_PATH: "bad.yaml",
            CONF_NUMBER_TOLERANCE: 1,
            CONF_RESTORE_STATES_ON_DEACTIVATE: False,
            CONF_TRANSITION_TIME: 1.0,
            CONF_DEBOUNCE_TIME: 0.0,
            CONF_IGNORE_UNAVAILABLE: False,
            CONF_ENABLE_DISCOVERY: False,
        },
    )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_yaml"}


async def test_select_external_scenes_step(
    hass: HomeAssistant, mock_config_entry_hub, mock_scene_entities
):
    """Test external scene selection step shows entity selector."""
    # Set up the hub first
    await hass.config_entries.async_setup(mock_config_entry_hub.entry_id)
    await hass.async_block_till_done()

    # Add an external scene entity
    hass.states.async_set(
        "scene.external_scene",
        "scening",
        {"friendly_name": "External Scene"},
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "select_external_scenes"},
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "select_external_scenes"


async def test_integration_discovery_step(hass: HomeAssistant):
    """Test integration discovery creates a flow."""
    discovery_data = {
        "entity_id": "scene.hue_scene",
        "device_id": "hue_device_123",
    }

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_INTEGRATION_DISCOVERY},
        data=discovery_data,
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "configure_external_scene_entities"


async def test_reconfigure_hub_shows_form(
    hass: HomeAssistant, mock_config_entry_hub: MockConfigEntry, mock_scene_entities
):
    """Test reconfigure step for hub entry shows form with current values."""
    await hass.config_entries.async_setup(mock_config_entry_hub.entry_id)
    await hass.async_block_till_done()

    result = await mock_config_entry_hub.start_reconfigure_flow(hass)

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "reconfigure_hub"


async def test_reconfigure_hub_updates_entry(
    hass: HomeAssistant, mock_config_entry_hub: MockConfigEntry, mock_scene_entities
):
    """Test reconfigure hub with valid input updates the config entry."""
    await hass.config_entries.async_setup(mock_config_entry_hub.entry_id)
    await hass.async_block_till_done()

    result = await mock_config_entry_hub.start_reconfigure_flow(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_SCENE_PATH: "scenes.yaml",
            CONF_NUMBER_TOLERANCE: 5,
            CONF_RESTORE_STATES_ON_DEACTIVATE: True,
            CONF_TRANSITION_TIME: 2.0,
            CONF_DEBOUNCE_TIME: 0.5,
            CONF_IGNORE_UNAVAILABLE: True,
            CONF_ENABLE_DISCOVERY: True,
        },
    )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"

    # Verify the entry was updated
    assert mock_config_entry_hub.data[CONF_NUMBER_TOLERANCE] == 5
    assert mock_config_entry_hub.data[CONF_RESTORE_STATES_ON_DEACTIVATE] is True
    assert mock_config_entry_hub.data[CONF_TRANSITION_TIME] == 2.0
    assert mock_config_entry_hub.data[CONF_DEBOUNCE_TIME] == 0.5
    assert mock_config_entry_hub.data[CONF_IGNORE_UNAVAILABLE] is True
    assert mock_config_entry_hub.data[CONF_ENABLE_DISCOVERY] is True


async def test_reconfigure_hub_invalid_yaml(
    hass: HomeAssistant, mock_config_entry_hub: MockConfigEntry, mock_scene_entities
):
    """Test reconfigure hub with invalid YAML shows error."""
    await hass.config_entries.async_setup(mock_config_entry_hub.entry_id)
    await hass.async_block_till_done()

    result = await mock_config_entry_hub.start_reconfigure_flow(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_SCENE_PATH: "nonexistent.yaml",
            CONF_NUMBER_TOLERANCE: 1,
            CONF_RESTORE_STATES_ON_DEACTIVATE: False,
            CONF_TRANSITION_TIME: 1.0,
            CONF_DEBOUNCE_TIME: 0.0,
            CONF_IGNORE_UNAVAILABLE: False,
            CONF_ENABLE_DISCOVERY: False,
        },
    )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "yaml_not_found"}


async def test_reconfigure_external_shows_form(
    hass: HomeAssistant,
    mock_config_entry_external: MockConfigEntry,
    mock_light_entities,
):
    """Test reconfigure step for external scene entry shows form."""
    await hass.config_entries.async_setup(mock_config_entry_external.entry_id)
    await hass.async_block_till_done()

    result = await mock_config_entry_external.start_reconfigure_flow(hass)

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "reconfigure_external"


async def test_reconfigure_external_updates_settings(
    hass: HomeAssistant,
    mock_config_entry_external: MockConfigEntry,
    mock_light_entities,
):
    """Test reconfigure external with same entities updates settings only."""
    await hass.config_entries.async_setup(mock_config_entry_external.entry_id)
    await hass.async_block_till_done()

    result = await mock_config_entry_external.start_reconfigure_flow(hass)

    # Submit with same entities (unchanged) - should update directly
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NUMBER_TOLERANCE: 3,
            CONF_RESTORE_STATES_ON_DEACTIVATE: True,
            CONF_TRANSITION_TIME: 1.5,
            CONF_DEBOUNCE_TIME: 0.3,
            CONF_IGNORE_UNAVAILABLE: True,
            CONF_SCENE_ENTITIES: ["light.living_room", "light.bedroom"],
        },
    )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"

    # Verify the entry was updated
    assert mock_config_entry_external.data[CONF_NUMBER_TOLERANCE] == 3
    assert mock_config_entry_external.data[CONF_RESTORE_STATES_ON_DEACTIVATE] is True
    assert mock_config_entry_external.data[CONF_TRANSITION_TIME] == 1.5
    assert mock_config_entry_external.data[CONF_DEBOUNCE_TIME] == 0.3
    assert mock_config_entry_external.data[CONF_IGNORE_UNAVAILABLE] is True


async def test_reconfigure_external_change_entities(
    hass: HomeAssistant,
    mock_config_entry_external: MockConfigEntry,
    mock_light_entities,
    service_calls,
):
    """Test reconfigure external with changed entities triggers re-learn."""
    await hass.config_entries.async_setup(mock_config_entry_external.entry_id)
    await hass.async_block_till_done()

    # Set up the scene entity for the turn_on call
    hass.states.async_set(
        "scene.external_test",
        "scening",
        {"friendly_name": "External Scene"},
    )

    result = await mock_config_entry_external.start_reconfigure_flow(hass)

    # Submit with different entities - should go to learn step
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NUMBER_TOLERANCE: 1,
            CONF_RESTORE_STATES_ON_DEACTIVATE: False,
            CONF_TRANSITION_TIME: 1.0,
            CONF_DEBOUNCE_TIME: 0.0,
            CONF_IGNORE_UNAVAILABLE: False,
            CONF_SCENE_ENTITIES: ["light.living_room"],  # removed bedroom
        },
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "reconfigure_external_learn"

    # Confirm the scene is active
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_EXTERNAL_SCENE_ACTIVE: True},
    )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"

    # Verify entities were re-learned (only living_room now)
    assert "light.living_room" in mock_config_entry_external.data["entities"]
    assert "light.bedroom" not in mock_config_entry_external.data["entities"]
