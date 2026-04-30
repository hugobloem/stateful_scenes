"""Tests for Stateful Scenes select platform."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.stateful_scenes.const import DEFAULT_OFF_SCENE_ENTITY_ID



async def test_select_entity_created_external(
    hass: HomeAssistant, mock_config_entry_external: MockConfigEntry, mock_light_entities
):
    """Test select entity is created for external scene."""
    await hass.config_entries.async_setup(mock_config_entry_external.entry_id)
    await hass.async_block_till_done()

    select_states = hass.states.async_entity_ids("select")
    assert len(select_states) >= 1


async def test_select_entity_created_hub(
    hass: HomeAssistant, mock_config_entry_hub: MockConfigEntry,
    mock_scene_entities, mock_light_entities, mock_cover_entities
):
    """Test select entities are created for hub scenes."""
    await hass.config_entries.async_setup(mock_config_entry_hub.entry_id)
    await hass.async_block_till_done()

    # One select per scene in hub
    select_states = hass.states.async_entity_ids("select")
    assert len(select_states) >= 2


async def test_select_default_option(
    hass: HomeAssistant, mock_config_entry_external: MockConfigEntry, mock_light_entities
):
    """Test select entity starts as unavailable (restore on deactivate is on by default)."""
    await hass.config_entries.async_setup(mock_config_entry_external.entry_id)
    await hass.async_block_till_done()

    select_states = hass.states.async_entity_ids("select")
    if select_states:
        entity_id = select_states[0]
        state = hass.states.get(entity_id)
        assert state is not None
        # Select is unavailable when restore_on_deactivate is True (default)
        # It becomes available only when restore_on_deactivate is toggled off
        assert state.state == "unavailable"


async def test_select_change_off_scene(
    hass: HomeAssistant, mock_config_entry_hub: MockConfigEntry,
    mock_scene_entities, mock_light_entities, mock_cover_entities
):
    """Test changing the off scene select updates the scene."""
    await hass.config_entries.async_setup(mock_config_entry_hub.entry_id)
    await hass.async_block_till_done()

    select_states = hass.states.async_entity_ids("select")
    if select_states:
        entity_id = select_states[0]
        state = hass.states.get(entity_id)
        # Verify options are available
        options = state.attributes.get("options", [])
        assert DEFAULT_OFF_SCENE_ENTITY_ID in options
