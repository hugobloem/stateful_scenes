"""Tests for Stateful Scenes number platform."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.stateful_scenes.const import DOMAIN


async def test_number_entities_created(
    hass: HomeAssistant,
    mock_config_entry_external: MockConfigEntry,
    mock_light_entities,
):
    """Test number entities are created for scene."""
    await hass.config_entries.async_setup(mock_config_entry_external.entry_id)
    await hass.async_block_till_done()

    # Each scene creates: TransitionNumber, DebounceTime, Tolerance
    number_states = hass.states.async_entity_ids("number")
    assert len(number_states) >= 3


async def test_transition_number_set_value(
    hass: HomeAssistant,
    mock_config_entry_external: MockConfigEntry,
    mock_light_entities,
):
    """Test setting transition time via number entity."""
    await hass.config_entries.async_setup(mock_config_entry_external.entry_id)
    await hass.async_block_till_done()

    transition_numbers = [
        eid for eid in hass.states.async_entity_ids("number") if "transition" in eid
    ]

    if transition_numbers:
        entity_id = transition_numbers[0]
        await hass.services.async_call(
            "number", "set_value", {"entity_id": entity_id, "value": 5.0}, blocking=True
        )
        await hass.async_block_till_done()

        scene = hass.data[DOMAIN][mock_config_entry_external.entry_id]
        assert scene.transition_time == 5.0


async def test_debounce_number_set_value(
    hass: HomeAssistant,
    mock_config_entry_external: MockConfigEntry,
    mock_light_entities,
):
    """Test setting debounce time via number entity."""
    await hass.config_entries.async_setup(mock_config_entry_external.entry_id)
    await hass.async_block_till_done()

    debounce_numbers = [
        eid for eid in hass.states.async_entity_ids("number") if "debounce" in eid
    ]

    if debounce_numbers:
        entity_id = debounce_numbers[0]
        await hass.services.async_call(
            "number", "set_value", {"entity_id": entity_id, "value": 2.5}, blocking=True
        )
        await hass.async_block_till_done()

        scene = hass.data[DOMAIN][mock_config_entry_external.entry_id]
        assert scene.debounce_time == 2.5


async def test_tolerance_number_set_value(
    hass: HomeAssistant,
    mock_config_entry_external: MockConfigEntry,
    mock_light_entities,
):
    """Test setting tolerance via number entity."""
    await hass.config_entries.async_setup(mock_config_entry_external.entry_id)
    await hass.async_block_till_done()

    tolerance_numbers = [
        eid for eid in hass.states.async_entity_ids("number") if "tolerance" in eid
    ]

    if tolerance_numbers:
        entity_id = tolerance_numbers[0]
        await hass.services.async_call(
            "number", "set_value", {"entity_id": entity_id, "value": 5}, blocking=True
        )
        await hass.async_block_till_done()

        scene = hass.data[DOMAIN][mock_config_entry_external.entry_id]
        assert scene.number_tolerance == 5


async def test_transition_number_range(
    hass: HomeAssistant,
    mock_config_entry_external: MockConfigEntry,
    mock_light_entities,
):
    """Test transition number entity has correct range."""
    await hass.config_entries.async_setup(mock_config_entry_external.entry_id)
    await hass.async_block_till_done()

    transition_numbers = [
        eid for eid in hass.states.async_entity_ids("number") if "transition" in eid
    ]

    if transition_numbers:
        entity_id = transition_numbers[0]
        state = hass.states.get(entity_id)
        assert state is not None
        assert float(state.attributes.get("min", 0)) == 0
        assert float(state.attributes.get("max", 0)) == 300


async def test_number_entities_hub(
    hass: HomeAssistant,
    mock_config_entry_hub: MockConfigEntry,
    mock_scene_entities,
    mock_light_entities,
    mock_cover_entities,
):
    """Test number entities are created for each hub scene."""
    await hass.config_entries.async_setup(mock_config_entry_hub.entry_id)
    await hass.async_block_till_done()

    # 2 scenes × 3 number entities = 6
    number_states = hass.states.async_entity_ids("number")
    assert len(number_states) >= 6
