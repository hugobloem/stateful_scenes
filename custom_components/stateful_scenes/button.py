"""Platform for button integration."""

from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import StatefulScenes
from .const import DEVICE_INFO_MANUFACTURER, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> bool:
    """Set up this integration using UI."""
    assert hass is not None
    data = hass.data[DOMAIN]
    assert entry.entry_id in data
    _LOGGER.debug(
        "Setting up Stateful Scenes button with data: %s and config_entry %s",
        data,
        entry,
    )

    entities = []
    if isinstance(data[entry.entry_id], StatefulScenes.Hub):
        hub = data[entry.entry_id]
        for scene in hub.scenes:
            entities.append(RecaptureSceneButton(scene))

    elif isinstance(data[entry.entry_id], StatefulScenes.Scene):
        scene = data[entry.entry_id]
        entities.append(RecaptureSceneButton(scene))

    else:
        _LOGGER.error("Invalid entity type for %s", entry.entry_id)
        return False

    async_add_entities(entities)

    return True


class RecaptureSceneButton(ButtonEntity):
    """Button entity to recapture the scene state."""

    _attr_has_entity_name = True
    _attr_name = "Recapture Scene"
    _attr_icon = "mdi:eye-refresh"

    def __init__(self, scene: StatefulScenes.Scene) -> None:
        """Initialize."""
        self._scene = scene
        self._attr_unique_id = f"{scene.id}_recapture"
        self._attr_device_info = DeviceInfo(
            identifiers={(self._scene.id,)},
            name=self._scene.name,
            manufacturer=DEVICE_INFO_MANUFACTURER,
            suggested_area=self._scene.area_id,
        )

    async def async_press(self) -> None:
        """Handle the button press."""
        await self._scene.async_update_scene_definition()