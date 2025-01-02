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
from .const import (
    DEBOUNCE_MAX,
    DEBOUNCE_MIN,
    DEBOUNCE_STEP,
    TOLERANCE_MIN,
    TOLERANCE_MAX,
    TOLERANCE_STEP,
    DEVICE_INFO_MANUFACTURER,
    DOMAIN,
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

    entities = []
    if isinstance(data[entry.entry_id], StatefulScenes.Hub):
        hub = data[entry.entry_id]
        for scene in hub.scenes:
            entities += [TransitionNumber(scene), DebounceTime(scene), Tolerance(scene)]

    elif isinstance(data[entry.entry_id], StatefulScenes.Scene):
        scene = data[entry.entry_id]
        entities += [TransitionNumber(scene), DebounceTime(scene), Tolerance(scene)]

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

    async def async_set_native_value(self, value: float) -> None:
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


class DebounceTime(RestoreNumber):
    """Time to wait after activating a scene switch until evaluating if the scene is still active."""

    _attr_native_max_value = DEBOUNCE_MAX
    _attr_native_min_value = DEBOUNCE_MIN
    _attr_native_step = DEBOUNCE_STEP
    _attr_native_unit_of_measurement = "seconds"
    _attr_name = "Debounce Time"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, scene: StatefulScenes.Scene) -> None:
        """Initialize."""
        self._scene = scene
        self._name = f"{scene.name} Debounce Time"
        self._attr_unique_id = f"{scene.id}_debounce_time"

        _LOGGER.debug(
            "Setting initial debounce time for %s to %s",
            scene.name,
            scene.debounce_time,
        )
        self._scene.set_debounce_time(scene.debounce_time)

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

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        self._scene.set_debounce_time(value)

    async def async_added_to_hass(self) -> None:
        """Restore last state."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) and (
            last_number_data := await self.async_get_last_number_data()
        ):
            if last_state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
                _LOGGER.debug(
                    "Restoring debounce time for %s to %s",
                    self._scene.name,
                    last_number_data.native_value,
                )
                self._scene.set_debounce_time(last_number_data.native_value)

    @property
    def native_value(self) -> float:
        """Return the entity value to represent the entity state."""
        return self._scene.debounce_time


class Tolerance(RestoreNumber):
    """Tolerance to numbers to be considered equal when assessing a state."""

    _attr_native_max_value = TOLERANCE_MAX
    _attr_native_min_value = TOLERANCE_MIN
    _attr_native_step = TOLERANCE_STEP
    _attr_native_unit_of_measurement = "number"
    _attr_name = "Tolerance"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, scene: StatefulScenes.Scene) -> None:
        """Initialize."""
        self._scene = scene
        self._name = f"{scene.name} Tolerance"
        self._attr_unique_id = f"{scene.id}_tolerance"

        _LOGGER.debug(
            "Setting initial tolerance for %s to %s",
            scene.name,
            scene.number_tolerance,
        )
        self._scene.set_number_tolerance(scene.number_tolerance)

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

    async def async_set_native_value(self, value: int) -> None:
        """Update the current value."""
        self._scene.set_number_tolerance(value)

    async def async_added_to_hass(self) -> None:
        """Restore last state."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) and (
            last_number_data := await self.async_get_last_number_data()
        ):
            if last_state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
                _LOGGER.debug(
                    "Restoring debounce time for %s to %s",
                    self._scene.name,
                    last_number_data.native_value,
                )
                self._scene.set_number_tolerance(last_number_data.native_value)

    @property
    def native_value(self) -> float:
        """Return the entity value to represent the entity state."""
        return self._scene.number_tolerance
