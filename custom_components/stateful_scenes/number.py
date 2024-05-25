"""Platform for number integration."""

from __future__ import annotations

import logging

# Import the device class from the component that you want to support
from homeassistant.components.number import RestoreNumber
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import StatefulScenes
from .const import DEVICE_INFO_MANUFACTURER, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, add_entities: AddEntitiesCallback
) -> bool:
    """Set up this integration using UI."""
    assert hass is not None
    data = hass.data[DOMAIN]
    assert entry.entry_id in data
    _LOGGER.debug(
        "Setting up Stateful Scenes number with data: %s and config_entry %s",
        data,
        entry,
    )

    entities = []
    if isinstance(data[entry.entry_id], StatefulScenes.Hub):
        hub = data[entry.entry_id]
        for scene in hub.scenes:
            entities.append(TransitionNumber(scene))

    elif isinstance(data[entry.entry_id], StatefulScenes.Scene):
        scene = data[entry.entry_id]
        entities.append(TransitionNumber(scene))

    else:
        _LOGGER.error("Invalid entity type for %s", entry.entry_id)
        return False

    add_entities(entities)

    return True


class TransitionNumber(RestoreNumber):
    """Number entity to store the transition time."""

    _attr_native_max_value = 300
    _attr_native_min_value = 0
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = "seconds"
    _attr_name = "Transition Time"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, scene: StatefulScenes.Scene) -> None:
        """Initialize."""
        self._scene = scene
        self._name = f"{scene.name} Transition Time"
        self._attr_unique_id = f"{scene.id}_transition_time"

        if scene.transition_time is not None:
            _LOGGER.debug(
                "Setting initial transition time for %s to %s",
                scene.name,
                scene.transition_time,
            )
            self._scene.set_transition_time(scene.transition_time)

    @property
    def name(self) -> str:
        """Return the display name of this light."""
        return self._name

    @property
    def device_info(self) -> DeviceInfo | None:
        """Return the device info."""
        return DeviceInfo(
            identifiers={(self._scene.id,)},
            name=self._scene.name,
            manufacturer=DEVICE_INFO_MANUFACTURER,
            suggested_area=self._scene.area_id,
        )

    def set_native_value(self, value: float) -> None:
        """Update the current value."""
        self._scene.set_transition_time(value)

    async def async_added_to_hass(self) -> None:
        """Restore last state."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) and (
            last_number_data := await self.async_get_last_number_data()
        ):
            if last_state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
                _LOGGER.debug(
                    "Restoring transition time for %s to %s",
                    self._scene.name,
                    last_number_data.native_value,
                )
                self._scene.set_transition_time(last_number_data.native_value)

    @property
    def native_value(self) -> float:
        """Return the entity value to represent the entity state."""
        return self._scene.transition_time
