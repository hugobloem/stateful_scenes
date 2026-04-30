"""Tests for Stateful Scenes integration setup."""

from __future__ import annotations

import os

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.stateful_scenes import (
    load_scenes_file,
)
from custom_components.stateful_scenes.const import (
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


async def test_async_setup_entry_external_scene(
    hass: HomeAssistant, mock_config_entry_external: MockConfigEntry, mock_light_entities
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
        await load_scenes_file(hass, None) # type: ignore


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
