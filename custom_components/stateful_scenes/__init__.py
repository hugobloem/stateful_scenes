"""Stateful scenes integration."""

from __future__ import annotations

import os

import aiofiles
import yaml

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import (
    CONF_ENABLE_DISCOVERY,
    CONF_NUMBER_TOLERANCE,
    CONF_SCENE_PATH,
    DOMAIN,
    StatefulScenesYamlInvalid,
    StatefulScenesYamlNotFound,
)
from .discovery import DiscoveryManager
from .StatefulScenes import Hub, Scene
from .helpers import async_cleanup_orphaned_entities

PLATFORMS: list[Platform] = [
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SWITCH,
]


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""
    hass.data.setdefault(DOMAIN, {})
    is_hub = entry.data.get("hub", None)

    if is_hub is None:
        is_hub = CONF_SCENE_PATH in entry.data

    if is_hub:
        if entry.data.get(CONF_SCENE_PATH, None) is None:
            raise StatefulScenesYamlNotFound("Scenes file not specified.")

        scene_confs = await load_scenes_file(hass, entry.data[CONF_SCENE_PATH])

        hub = Hub(
            hass=hass,
            scene_confs=scene_confs,
            number_tolerance=entry.data[CONF_NUMBER_TOLERANCE],
        )
        hass.data[DOMAIN][entry.entry_id] = hub

        # Clean up orphaned entities for removed scenes
        valid_scene_ids = {scene.id for scene in hub.scenes}
        await async_cleanup_orphaned_entities(hass, DOMAIN, entry.entry_id, valid_scene_ids)

    else:
        scene = Scene(hass, entry.data)
        hass.data[DOMAIN][entry.entry_id] = scene

        # Clean up orphaned entities for single scene setup
        valid_scene_ids = {scene.id}
        await async_cleanup_orphaned_entities(hass, DOMAIN, entry.entry_id, valid_scene_ids)

    if is_hub and entry.data.get(CONF_ENABLE_DISCOVERY, False):
        discovery_manager = DiscoveryManager(hass, entry)
        await discovery_manager.async_start_discovery()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    if unloaded := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


async def load_scenes_file(hass: HomeAssistant, scene_path: str) -> list:
    """Load scenes from yaml file.

    Args:
        hass: Home Assistant instance for path resolution
        scene_path: Path to scenes file (relative to config dir or absolute)

    Returns:
        List of scene configurations

    Raises:
        StatefulScenesYamlNotFound: If file path is invalid or file not found
        StatefulScenesYamlInvalid: If YAML parsing fails or no scenes found
    """
    # Validate input
    if scene_path is None:
        raise StatefulScenesYamlNotFound("Scenes file not specified.")

    if not scene_path or not scene_path.strip():
        raise StatefulScenesYamlNotFound("Scenes file path is empty.")

    # Resolve relative paths against config directory
    # This allows users to use "scenes.yaml" instead of "/config/scenes.yaml"
    resolved_path = hass.config.path(scene_path)

    # Check if file exists
    if not os.path.exists(resolved_path):
        raise StatefulScenesYamlNotFound(
            f"No scenes file found at {resolved_path} "
            f"(from input path: {scene_path})"
        )

    # Verify it's a file, not a directory
    if not os.path.isfile(resolved_path):
        raise StatefulScenesYamlNotFound(
            f"Path {resolved_path} is not a file"
        )

    try:
        async with aiofiles.open(resolved_path, encoding="utf-8") as f:
            scenes_confs = yaml.load(await f.read(), Loader=yaml.FullLoader)
    except OSError as err:
        raise StatefulScenesYamlInvalid(
            f"Error reading scenes file {resolved_path}: {err}"
        ) from err
    except yaml.YAMLError as err:
        raise StatefulScenesYamlInvalid(
            f"Invalid YAML in {resolved_path}: {err}"
        ) from err

    if not scenes_confs or not isinstance(scenes_confs, list):
        raise StatefulScenesYamlInvalid(
            f"No scenes found in {resolved_path}. "
            "Ensure the file contains a list of scenes."
        )

    return scenes_confs
