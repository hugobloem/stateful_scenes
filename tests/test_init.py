"""Tests for Stateful Scenes integration setup."""

from __future__ import annotations

import logging
import os

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry, entity_registry
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.stateful_scenes import (
    async_remove_entry,
    load_scenes_file,
)
from custom_components.stateful_scenes.const import (
    DOMAIN,
    StatefulScenesYamlInvalid,
    StatefulScenesYamlNotFound,
)
from custom_components.stateful_scenes.StatefulScenes import Hub, Scene

from .const import MOCK_HUB_DATA


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


async def test_async_setup_entry_hub_skips_already_registered_scene_ids(
    hass: HomeAssistant, mock_scenes_yaml, mock_scene_entities, caplog
):
    """Two Hub entries loading overlapping scene ids must not duplicate entities.

    Regression test for https://github.com/hugobloem/stateful_scenes/issues/209:
    "Platform stateful_scenes does not generate unique IDs" log spam on startup,
    caused by a second Stateful Scenes config entry registering number/select/
    switch entities whose unique_id (derived from the underlying scene id) was
    already claimed by another loaded entry.
    """
    entry1 = MockConfigEntry(domain=DOMAIN, data=MOCK_HUB_DATA, title="Hub 1")
    entry1.add_to_hass(hass)
    entry2 = MockConfigEntry(domain=DOMAIN, data=MOCK_HUB_DATA, title="Hub 2")
    entry2.add_to_hass(hass)

    # Setting up the first entry causes Home Assistant to also bootstrap any
    # other not-yet-loaded config entries for this domain (mirroring what
    # happens for real on a Home Assistant restart with two Hub entries).
    caplog.clear()
    with caplog.at_level(logging.ERROR):
        assert await hass.config_entries.async_setup(entry1.entry_id)
        await hass.async_block_till_done()

    assert entry2.state is ConfigEntryState.LOADED

    duplicate_id_errors = [
        record
        for record in caplog.records
        if record.levelno >= logging.ERROR
        and "does not generate unique IDs" in record.message
    ]
    assert not duplicate_id_errors, (
        "Setting up a second Hub entry with overlapping scene ids must not "
        f"trigger duplicate unique ID errors, got: "
        f"{[r.message for r in duplicate_id_errors]}"
    )

    # The second hub's scenes were already claimed by the first hub, so it
    # should not attempt to re-register any of them.
    hub2 = hass.data[DOMAIN][entry2.entry_id]
    assert hub2.scenes == []


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
