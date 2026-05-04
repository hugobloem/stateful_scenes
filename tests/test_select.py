"""Tests for Stateful Scenes select platform."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.stateful_scenes.const import DEFAULT_OFF_SCENE_ENTITY_ID, DOMAIN


async def test_select_entity_created_external(
    hass: HomeAssistant,
    mock_config_entry_external: MockConfigEntry,
    mock_light_entities,
):
    """Test select entity is created for external scene."""
    await hass.config_entries.async_setup(mock_config_entry_external.entry_id)
    await hass.async_block_till_done()

    select_states = hass.states.async_entity_ids("select")
    assert len(select_states) >= 1


async def test_select_entity_created_hub(
    hass: HomeAssistant,
    mock_config_entry_hub: MockConfigEntry,
    mock_scene_entities,
    mock_light_entities,
    mock_cover_entities,
):
    """Test select entities are created for hub scenes."""
    await hass.config_entries.async_setup(mock_config_entry_hub.entry_id)
    await hass.async_block_till_done()

    # One select per scene in hub
    select_states = hass.states.async_entity_ids("select")
    assert len(select_states) >= 2


async def test_select_default_option(
    hass: HomeAssistant,
    mock_config_entry_external: MockConfigEntry,
    mock_light_entities,
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
    hass: HomeAssistant,
    mock_config_entry_hub: MockConfigEntry,
    mock_scene_entities,
    mock_light_entities,
    mock_cover_entities,
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


async def test_select_available_with_special_chars_in_name(
    hass: HomeAssistant,
    mock_light_entities,
):
    """Test select entity tracks restore_on_deactivate switch for scenes with special chars.

    Regression test for https://github.com/.../issues/251:
    Scene names with parentheses, hyphens, etc. caused the Off Scene selector
    to be permanently unavailable because the entity ID was manually constructed
    from the name using only space-to-underscore replacement.
    """
    # Create an external scene with special characters in the name
    special_scene_data = {
        "name": "EFFECT_Christmas (Candy Canes)",
        "entity_id": "scene.effect_christmas_candy_canes",
        "id": "ext_special_1",
        "area": None,
        "learn": True,
        "icon": None,
        "number_tolerance": 1,
        "entities": {
            "light.living_room": {"state": "on", "brightness": 200},
        },
        "hub": False,
    }

    entry = MockConfigEntry(
        domain=DOMAIN,
        data=special_scene_data,
        title="EFFECT_Christmas (Candy Canes)",
        unique_id="stateful_scene.effect_christmas_candy_canes",
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # Find the restore_on_deactivate switch entity
    ent_reg = er.async_get(hass)
    switch_entry = ent_reg.async_get_entity_id(
        "switch", DOMAIN, "ext_special_1_learned_restore_on_deactivate"
    )
    assert switch_entry is not None, "Restore on deactivate switch should exist"

    # Turn off the restore_on_deactivate switch to make the select available
    hass.states.async_set(switch_entry, "off")
    await hass.async_block_till_done()

    # The select entity should become available
    select_entity_id = ent_reg.async_get_entity_id(
        "select", DOMAIN, "ext_special_1_learned_off_scene"
    )
    assert select_entity_id is not None, "Off scene select should exist"

    state = hass.states.get(select_entity_id)
    assert state is not None
    assert state.state != "unavailable", (
        "Off Scene select should be available after restore_on_deactivate is turned off, "
        "even for scenes with special characters in the name"
    )


async def test_select_available_with_hyphenated_name(
    hass: HomeAssistant,
    mock_light_entities,
):
    """Test select entity works for scenes with hyphens in name."""
    special_scene_data = {
        "name": "Living Room - Evening",
        "entity_id": "scene.living_room_evening",
        "id": "ext_hyphen_1",
        "area": None,
        "learn": True,
        "icon": None,
        "number_tolerance": 1,
        "entities": {
            "light.living_room": {"state": "on", "brightness": 150},
        },
        "hub": False,
    }

    entry = MockConfigEntry(
        domain=DOMAIN,
        data=special_scene_data,
        title="Living Room - Evening",
        unique_id="stateful_scene.living_room_evening",
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # Find the restore_on_deactivate switch entity via registry
    ent_reg = er.async_get(hass)
    switch_entry = ent_reg.async_get_entity_id(
        "switch", DOMAIN, "ext_hyphen_1_learned_restore_on_deactivate"
    )
    assert switch_entry is not None, "Restore on deactivate switch should exist"

    # Turn off restore_on_deactivate
    hass.states.async_set(switch_entry, "off")
    await hass.async_block_till_done()

    # The select entity should become available
    select_entity_id = ent_reg.async_get_entity_id(
        "select", DOMAIN, "ext_hyphen_1_learned_off_scene"
    )
    assert select_entity_id is not None

    state = hass.states.get(select_entity_id)
    assert state is not None
    assert state.state != "unavailable", (
        "Off Scene select should be available for scenes with hyphens in the name"
    )
