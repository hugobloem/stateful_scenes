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

        scene_confs = await load_scenes_file(entry.data[CONF_SCENE_PATH])

        hass.data[DOMAIN][entry.entry_id] = Hub(
            hass=hass,
            scene_confs=scene_confs,
            number_tolerance=entry.data[CONF_NUMBER_TOLERANCE],
        )

    else:
        hass.data[DOMAIN][entry.entry_id] = Scene(hass, entry.data)

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


async def load_scenes_file(scene_path) -> list:
    """Load scenes from yaml file."""
    # check if file exists
    if scene_path is None:
        raise StatefulScenesYamlNotFound("Scenes file not specified.")
    if not os.path.exists(scene_path):
        raise StatefulScenesYamlNotFound("No scenes file " + scene_path)

    try:
        async with aiofiles.open(scene_path, encoding="utf-8") as f:
            scenes_confs = yaml.load(await f.read(), Loader=yaml.FullLoader)
    except OSError as err:
        raise StatefulScenesYamlInvalid("No scenes found in " + scene_path) from err

    if not scenes_confs or not isinstance(scenes_confs, list):
        raise StatefulScenesYamlInvalid("No scenes found in " + scene_path)

    return scenes_confs
