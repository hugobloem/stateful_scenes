"""Platform for number integration."""

from __future__ import annotations

import logging
from homeassistant.helpers.device_registry import DeviceInfo

import voluptuous as vol

# Import the device class from the component that you want to support
import homeassistant.helpers.config_validation as cv
from homeassistant.components.number import RestoreNumber
from homeassistant.const import EntityCategory, STATE_UNKNOWN, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry


from . import StatefulScenes

from .const import (
    DOMAIN,
    DEVICE_INFO_MANUFACTURER,
)

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
    hub = data[entry.entry_id]

    stateful_scene_number = [TransitionNumber(scene) for scene in hub.scenes]

    add_entities(stateful_scene_number)

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
                self._scene.set_transition_time(last_number_data.native_value)

    @property
    def native_value(self) -> float:
        """Return the entity value to represent the entity state."""
        return self._scene.transition_time
