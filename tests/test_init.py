"""Tests for Stateful Scenes integration setup."""

from __future__ import annotations

import os

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry, entity_registry
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.stateful_scenes import (
    async_remove_entry,
    load_scenes_file,
)
from custom_components.stateful_scenes.const import (
    CONF_SCENE_OVERRIDES,
    DOMAIN,
    StatefulScenesYamlInvalid,
    StatefulScenesYamlNotFound,
)
from custom_components.stateful_scenes.StatefulScenes import Hub, Scene


async def test_async_setup_entry_hub(
    hass: HomeAssistant, mock_config_entry_hub: MockConfigEntry, mock_scene_entities
):
    """Test setup of a hub config entry."""
    await hass.config_entries.async_setup(mock_config_entry_hub.entry_id)
    await hass.async_block_till_done()

    assert DOMAIN in hass.data
    assert mock_config_entry_hub.entry_id in hass.data[DOMAIN]
    assert isinstance(hass.data[DOMAIN][mock_config_entry_hub.entry_id], Hub)

    hub = hass.data[DOMAIN][mock_config_entry_hub.entry_id]
    assert len(hub.scenes) == 2
    assert hub.scenes[0].name == "Test Scene 1"
    assert hub.scenes[1].name == "Test Scene 2"


async def test_hub_recaptured_definition_persists_and_updates_switch(
    hass: HomeAssistant,
    mock_config_entry_hub: MockConfigEntry,
    mock_scene_entities,
    mock_light_entities,
):
    """Test recaptured hub definitions persist and update the scene switch."""
    await hass.config_entries.async_setup(mock_config_entry_hub.entry_id)
    await hass.async_block_till_done()

    hub = hass.data[DOMAIN][mock_config_entry_hub.entry_id]
    scene = hub.scenes[0]
    hass.states.async_set(
        "light.living_room",
        "on",
        {"brightness": 100, "friendly_name": "Living Room Light"},
    )
    await hass.async_block_till_done()

    switch_entity_id = entity_registry.async_get(hass).async_get_entity_id(
        "switch", DOMAIN, "stateful_1001"
    )
    assert switch_entity_id is not None
    assert hass.states.get(switch_entity_id).state == "off"

    await scene.async_update_scene_definition()
    await hass.async_block_till_done()

    assert mock_config_entry_hub.data[CONF_SCENE_OVERRIDES]["1001"][
        "light.living_room"
    ]["brightness"] == 100
    assert scene.is_on

    assert hass.states.get(switch_entity_id).state == "on"

    previous_data = mock_config_entry_hub.data
    hass.states.async_set("light.living_room", "on", {"brightness": 150})
    await scene.async_update_scene_definition()
    await hass.async_block_till_done()

    assert previous_data[CONF_SCENE_OVERRIDES]["1001"]["light.living_room"][
        "brightness"
    ] == 100
    assert mock_config_entry_hub.data is not previous_data

    assert await hass.config_entries.async_reload(mock_config_entry_hub.entry_id)
    await hass.async_block_till_done()
    reloaded_hub = hass.data[DOMAIN][mock_config_entry_hub.entry_id]
    assert reloaded_hub is not hub
    assert reloaded_hub.scenes[0].entities["light.living_room"]["brightness"] == 150
    assert hass.states.get(switch_entity_id).state == "on"


async def test_external_recaptures_do_not_mutate_saved_definitions(
    hass: HomeAssistant,
    mock_config_entry_external: MockConfigEntry,
    mock_light_entities,
):
    """Test each external recapture is detected as a new config-entry update."""
    await hass.config_entries.async_setup(mock_config_entry_external.entry_id)
    await hass.async_block_till_done()
    scene = hass.data[DOMAIN][mock_config_entry_external.entry_id]
    registry = entity_registry.async_get(hass)
    button_entity_id = registry.async_get_entity_id(
        "button", DOMAIN, f"{scene.id}_recapture"
    )
    assert button_entity_id is not None

    for brightness in (100, 150):
        previous_data = mock_config_entry_external.data
        previous_brightness = previous_data["entities"]["light.living_room"][
            "brightness"
        ]
        hass.states.async_set("light.living_room", "on", {"brightness": brightness})
        await hass.services.async_call(
            "button", "press", {"entity_id": button_entity_id}, blocking=True
        )
        await hass.async_block_till_done()
        assert previous_data["entities"]["light.living_room"][
            "brightness"
        ] == previous_brightness
        assert mock_config_entry_external.data is not previous_data
        assert mock_config_entry_external.data["entities"]["light.living_room"][
            "brightness"
        ] == brightness

    assert await hass.config_entries.async_reload(
        mock_config_entry_external.entry_id
    )
    await hass.async_block_till_done()
    reloaded_scene = hass.data[DOMAIN][mock_config_entry_external.entry_id]
    assert reloaded_scene is not scene
    assert reloaded_scene.entities["light.living_room"]["brightness"] == 150


async def test_async_setup_entry_external_scene(
    hass: HomeAssistant,
    mock_config_entry_external: MockConfigEntry,
    mock_light_entities,
):
    """Test setup of an external scene config entry."""
    await hass.config_entries.async_setup(mock_config_entry_external.entry_id)
    await hass.async_block_till_done()

    assert DOMAIN in hass.data
    assert mock_config_entry_external.entry_id in hass.data[DOMAIN]
    assert isinstance(hass.data[DOMAIN][mock_config_entry_external.entry_id], Scene)

    scene = hass.data[DOMAIN][mock_config_entry_external.entry_id]
    assert scene.name == "External Scene"
    assert "light.living_room" in scene.entities
    assert "light.bedroom" in scene.entities


async def test_async_unload_entry(
    hass: HomeAssistant, mock_config_entry_hub: MockConfigEntry, mock_scene_entities
):
    """Test unloading a config entry."""
    await hass.config_entries.async_setup(mock_config_entry_hub.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry_hub.entry_id in hass.data[DOMAIN]

    result = await hass.config_entries.async_unload(mock_config_entry_hub.entry_id)
    await hass.async_block_till_done()

    assert result is True
    assert mock_config_entry_hub.entry_id not in hass.data[DOMAIN]


async def test_load_scenes_file_success(hass: HomeAssistant, mock_scenes_yaml):
    """Test loading a valid scenes file."""
    scenes = await load_scenes_file(hass, "scenes.yaml")
    assert isinstance(scenes, list)
    assert len(scenes) == 2
    assert scenes[0]["name"] == "Test Scene 1"
    assert scenes[1]["name"] == "Test Scene 2"


async def test_load_scenes_file_not_found(hass: HomeAssistant):
    """Test loading a nonexistent scenes file raises error."""
    with pytest.raises(StatefulScenesYamlNotFound):
        await load_scenes_file(hass, "nonexistent.yaml")


async def test_load_scenes_file_none(hass: HomeAssistant):
    """Test loading with None path raises error."""
    with pytest.raises(StatefulScenesYamlNotFound):
        await load_scenes_file(hass, None)  # type: ignore


async def test_load_scenes_file_empty_string(hass: HomeAssistant):
    """Test loading with empty string raises error."""
    with pytest.raises(StatefulScenesYamlNotFound):
        await load_scenes_file(hass, "")


async def test_load_scenes_file_invalid_yaml(hass: HomeAssistant):
    """Test loading an invalid YAML file raises error."""
    path = os.path.join(hass.config.config_dir, "bad_scenes.yaml")
    with open(path, "w") as f:
        f.write("{{{{invalid yaml content: [}")

    with pytest.raises(StatefulScenesYamlInvalid):
        await load_scenes_file(hass, "bad_scenes.yaml")


async def test_load_scenes_file_empty_list(hass: HomeAssistant):
    """Test loading a file with empty list raises error."""
    path = os.path.join(hass.config.config_dir, "empty_scenes.yaml")
    with open(path, "w") as f:
        f.write("[]")

    with pytest.raises(StatefulScenesYamlInvalid):
        await load_scenes_file(hass, "empty_scenes.yaml")


async def test_load_scenes_file_not_a_list(hass: HomeAssistant):
    """Test loading a file without a list raises error."""
    path = os.path.join(hass.config.config_dir, "notlist.yaml")
    with open(path, "w") as f:
        f.write("key: value\n")

    with pytest.raises(StatefulScenesYamlInvalid):
        await load_scenes_file(hass, "notlist.yaml")


async def test_async_remove_entry_cleans_up_entities_and_devices(
    hass: HomeAssistant,
    mock_config_entry_external: MockConfigEntry,
    mock_light_entities,
):
    """Test removing a config entry cleans up its entities and devices."""
    await hass.config_entries.async_setup(mock_config_entry_external.entry_id)
    await hass.async_block_till_done()

    er = entity_registry.async_get(hass)
    dr = device_registry.async_get(hass)

    # Register a device and entity for this config entry
    device = dr.async_get_or_create(
        config_entry_id=mock_config_entry_external.entry_id,
        identifiers={(DOMAIN, "test_device_1")},
        name="Test Device",
    )
    er.async_get_or_create(
        domain="switch",
        platform=DOMAIN,
        unique_id="ext_1001",
        config_entry=mock_config_entry_external,
        device_id=device.id,
    )

    # Verify entity and device exist
    entities_before = [
        e
        for e in er.entities.values()
        if e.config_entry_id == mock_config_entry_external.entry_id
    ]
    assert len(entities_before) >= 1

    devices_before = [
        d
        for d in dr.devices.values()
        if mock_config_entry_external.entry_id in d.config_entries
    ]
    assert len(devices_before) >= 1

    # Unload then remove
    await hass.config_entries.async_unload(mock_config_entry_external.entry_id)
    await hass.async_block_till_done()

    await async_remove_entry(hass, mock_config_entry_external)

    # Verify entities are removed
    entities_after = [
        e
        for e in er.entities.values()
        if e.config_entry_id == mock_config_entry_external.entry_id
    ]
    assert len(entities_after) == 0

    # Verify devices are removed
    devices_after = [
        d
        for d in dr.devices.values()
        if mock_config_entry_external.entry_id in d.config_entries
    ]
    assert len(devices_after) == 0


async def test_async_remove_entry_no_entities(
    hass: HomeAssistant,
    mock_config_entry_external: MockConfigEntry,
    mock_light_entities,
):
    """Test removing an entry with no registered entities does not error."""
    await hass.config_entries.async_setup(mock_config_entry_external.entry_id)
    await hass.async_block_till_done()

    await hass.config_entries.async_unload(mock_config_entry_external.entry_id)
    await hass.async_block_till_done()

    # Should not raise even with no entities/devices to clean up
    await async_remove_entry(hass, mock_config_entry_external)


async def test_async_remove_entry_hub(
    hass: HomeAssistant,
    mock_config_entry_hub: MockConfigEntry,
    mock_scene_entities,
):
    """Test removing a hub config entry cleans up its devices."""
    await hass.config_entries.async_setup(mock_config_entry_hub.entry_id)
    await hass.async_block_till_done()

    er = entity_registry.async_get(hass)
    dr = device_registry.async_get(hass)

    # Register a device for the hub entry
    device = dr.async_get_or_create(
        config_entry_id=mock_config_entry_hub.entry_id,
        identifiers={(DOMAIN, "hub_device_1")},
        name="Hub Device",
    )
    er.async_get_or_create(
        domain="switch",
        platform=DOMAIN,
        unique_id="1001",
        config_entry=mock_config_entry_hub,
        device_id=device.id,
    )

    await hass.config_entries.async_unload(mock_config_entry_hub.entry_id)
    await hass.async_block_till_done()

    await async_remove_entry(hass, mock_config_entry_hub)

    # Verify cleanup
    entities_after = [
        e
        for e in er.entities.values()
        if e.config_entry_id == mock_config_entry_hub.entry_id
    ]
    assert len(entities_after) == 0

    devices_after = [
        d
        for d in dr.devices.values()
        if mock_config_entry_hub.entry_id in d.config_entries
    ]
    assert len(devices_after) == 0
