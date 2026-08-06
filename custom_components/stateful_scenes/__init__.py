"""Stateful scenes integration."""

from __future__ import annotations

import logging
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

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SWITCH,
]


def _get_registered_scene_ids(hass: HomeAssistant, exclude_entry_id: str) -> set[str]:
    """Return scene ids already registered by other loaded config entries.

    Used to avoid setting up scenes whose id is already claimed by another
    Stateful Scenes config entry, which would otherwise create entities with
    duplicate unique_ids (see hugobloem/stateful_scenes#209).
    """
    scene_ids: set[str] = set()
    for other_entry_id, entry_data in hass.data.get(DOMAIN, {}).items():
        if other_entry_id == exclude_entry_id:
            continue
        if isinstance(entry_data, Hub):
            scene_ids.update(scene.id for scene in entry_data.scenes)
        elif isinstance(entry_data, Scene):
            scene_ids.add(entry_data.id)
    return scene_ids


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

        # Skip scenes whose id is already claimed by another loaded config
        # entry (e.g. a second Hub pointing at an overlapping scenes file)
        # to avoid registering entities with duplicate unique_ids (#209).
        registered_scene_ids = _get_registered_scene_ids(hass, entry.entry_id)
        duplicate_scenes = [
            scene for scene in hub.scenes if scene.id in registered_scene_ids
        ]
        for scene in duplicate_scenes:
            _LOGGER.warning(
                "Scene '%s' (id: %s) is already registered by another "
                "Stateful Scenes config entry; skipping to avoid duplicate "
                "entities",
                scene.name,
                scene.id,
            )
        if duplicate_scenes:
            hub.scenes = [
                scene for scene in hub.scenes if scene.id not in registered_scene_ids
            ]

        hass.data[DOMAIN][entry.entry_id] = hub

        # Clean up orphaned entities for removed scenes
        valid_scene_ids = {scene.id for scene in hub.scenes}
        await async_cleanup_orphaned_entities(
            hass, DOMAIN, entry.entry_id, valid_scene_ids
        )

    else:
        scene = Scene(hass, entry.data)
        hass.data[DOMAIN][entry.entry_id] = scene

        # Clean up orphaned entities for single scene setup
        valid_scene_ids = {scene.id}
        await async_cleanup_orphaned_entities(
            hass, DOMAIN, entry.entry_id, valid_scene_ids
        )

    if is_hub and entry.data.get(CONF_ENABLE_DISCOVERY, False):
        discovery_manager = DiscoveryManager(hass, entry)
        await discovery_manager.async_start_discovery()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle unloading of an entry."""
    if unloaded := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle removal of an entry."""
    from homeassistant.helpers import entity_registry, device_registry

    er = entity_registry.async_get(hass)
    dr = device_registry.async_get(hass)

    # Remove all entities associated with this config entry
    entities_to_remove = [
        entity_id
        for entity_id, entity in er.entities.items()
        if entity.config_entry_id == entry.entry_id
    ]
    for entity_id in entities_to_remove:
        er.async_remove(entity_id)

    # Remove all devices associated with this config entry
    devices_to_remove = [
        device_id
        for device_id, device in dr.devices.items()
        if entry.entry_id in device.config_entries
    ]
    for device_id in devices_to_remove:
        dr.async_remove_device(device_id)


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
            f"No scenes file found at {resolved_path} (from input path: {scene_path})"
        )

    # Verify it's a file, not a directory
    if not os.path.isfile(resolved_path):
        raise StatefulScenesYamlNotFound(f"Path {resolved_path} is not a file")

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
