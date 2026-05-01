"""Tests for Stateful Scenes switch platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.stateful_scenes.const import DOMAIN


async def test_switch_setup_hub(
    hass: HomeAssistant,
    mock_config_entry_hub: MockConfigEntry,
    mock_scene_entities,
    mock_light_entities,
    mock_cover_entities,
):
    """Test switch entities are created for hub scenes."""
    await hass.config_entries.async_setup(mock_config_entry_hub.entry_id)
    await hass.async_block_till_done()

    # Each scene creates: StatefulSceneSwitch, RestoreOnDeactivate, IgnoreUnavailable, IgnoreAttributes
    # With 2 scenes, that's 8 switch entities
    states = hass.states.async_entity_ids("switch")
    assert len(states) >= 8


async def test_switch_setup_external(
    hass: HomeAssistant,
    mock_config_entry_external: MockConfigEntry,
    mock_light_entities,
):
    """Test switch entities are created for external scene."""
    await hass.config_entries.async_setup(mock_config_entry_external.entry_id)
    await hass.async_block_till_done()

    # External scene creates: StatefulSceneSwitch, RestoreOnDeactivate, IgnoreUnavailable, IgnoreAttributes
    states = hass.states.async_entity_ids("switch")
    assert len(states) >= 4


async def test_switch_turn_on(
    hass: HomeAssistant,
    mock_config_entry_external: MockConfigEntry,
    mock_light_entities,
):
    """Test turning on the scene switch calls scene.turn_on."""
    hass.states.async_set(
        "scene.external_test",
        "scening",
        {"friendly_name": "External Scene", "id": "ext_1001"},
    )
    await hass.config_entries.async_setup(mock_config_entry_external.entry_id)
    await hass.async_block_till_done()

    # Find the stateful scene switch
    entity_id = "switch.stateful_scene"
    # Get all switch entities - find the one that's the main switch
    switch_states = [
        eid
        for eid in hass.states.async_entity_ids("switch")
        if "restore" not in eid and "ignore" not in eid
    ]

    if switch_states:
        entity_id = switch_states[0]

    with patch(
        "custom_components.stateful_scenes.StatefulScenes.Scene.async_turn_on",
        new_callable=AsyncMock,
    ) as mock_turn_on:
        await hass.services.async_call(
            "switch", "turn_on", {"entity_id": entity_id}, blocking=True
        )

    mock_turn_on.assert_called_once()


async def test_switch_turn_off(
    hass: HomeAssistant,
    mock_config_entry_external: MockConfigEntry,
    mock_light_entities,
):
    """Test turning off the scene switch calls scene.turn_off."""
    hass.states.async_set(
        "scene.external_test",
        "scening",
        {"friendly_name": "External Scene", "id": "ext_1001"},
    )
    await hass.config_entries.async_setup(mock_config_entry_external.entry_id)
    await hass.async_block_till_done()

    switch_states = [
        eid
        for eid in hass.states.async_entity_ids("switch")
        if "restore" not in eid and "ignore" not in eid
    ]

    if switch_states:
        entity_id = switch_states[0]
    else:
        entity_id = "switch.stateful_scene"

    with patch(
        "custom_components.stateful_scenes.StatefulScenes.Scene.async_turn_off",
        new_callable=AsyncMock,
    ) as mock_turn_off:
        await hass.services.async_call(
            "switch", "turn_off", {"entity_id": entity_id}, blocking=True
        )

    mock_turn_off.assert_called_once()


async def test_restore_on_deactivate_switch(
    hass: HomeAssistant,
    mock_config_entry_external: MockConfigEntry,
    mock_light_entities,
):
    """Test RestoreOnDeactivate switch toggles scene property."""
    await hass.config_entries.async_setup(mock_config_entry_external.entry_id)
    await hass.async_block_till_done()

    # Find the restore on deactivate switch
    restore_switches = [
        eid for eid in hass.states.async_entity_ids("switch") if "restore" in eid
    ]

    if restore_switches:
        entity_id = restore_switches[0]
        await hass.services.async_call(
            "switch", "turn_on", {"entity_id": entity_id}, blocking=True
        )
        await hass.async_block_till_done()

        scene = hass.data[DOMAIN][mock_config_entry_external.entry_id]
        assert scene.restore_on_deactivate is True

        await hass.services.async_call(
            "switch", "turn_off", {"entity_id": entity_id}, blocking=True
        )
        await hass.async_block_till_done()

        assert scene.restore_on_deactivate is False


async def test_ignore_unavailable_switch(
    hass: HomeAssistant,
    mock_config_entry_external: MockConfigEntry,
    mock_light_entities,
):
    """Test IgnoreUnavailable switch toggles scene property."""
    await hass.config_entries.async_setup(mock_config_entry_external.entry_id)
    await hass.async_block_till_done()

    ignore_switches = [
        eid
        for eid in hass.states.async_entity_ids("switch")
        if "ignore_unavailable" in eid
    ]

    if ignore_switches:
        entity_id = ignore_switches[0]
        await hass.services.async_call(
            "switch", "turn_on", {"entity_id": entity_id}, blocking=True
        )
        await hass.async_block_till_done()

        scene = hass.data[DOMAIN][mock_config_entry_external.entry_id]
        assert scene.ignore_unavailable is True


async def test_ignore_attributes_switch(
    hass: HomeAssistant,
    mock_config_entry_external: MockConfigEntry,
    mock_light_entities,
):
    """Test IgnoreAttributes switch toggles scene property."""
    await hass.config_entries.async_setup(mock_config_entry_external.entry_id)
    await hass.async_block_till_done()

    ignore_switches = [
        eid
        for eid in hass.states.async_entity_ids("switch")
        if "ignore_attributes" in eid or "ignore_attr" in eid
    ]

    if ignore_switches:
        entity_id = ignore_switches[0]
        await hass.services.async_call(
            "switch", "turn_on", {"entity_id": entity_id}, blocking=True
        )
        await hass.async_block_till_done()

        scene = hass.data[DOMAIN][mock_config_entry_external.entry_id]
        assert scene.ignore_attributes is True
