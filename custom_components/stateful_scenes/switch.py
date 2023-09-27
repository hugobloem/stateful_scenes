"""Platform for light integration."""
from __future__ import annotations

import logging
from homeassistant.helpers.device_registry import DeviceInfo

import voluptuous as vol

# Import the device class from the component that you want to support
import homeassistant.helpers.config_validation as cv
from homeassistant.components.switch import PLATFORM_SCHEMA, SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.event import async_track_state_change
from homeassistant.config_entries import ConfigEntry


from . import StatefulScenes

from .const import (
    DOMAIN,
    CONF_SCENE_PATH,
    CONF_NUMBER_TOLERANCE,
    DEFAULT_SCENE_PATH,
    DEFAULT_NUMBER_TOLERANCE,
    DEVICE_INFO_MANUFACTURER,
)

_LOGGER = logging.getLogger(__name__)

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_SCENE_PATH, default=DEFAULT_SCENE_PATH): cv.string,
        vol.Optional(
            CONF_NUMBER_TOLERANCE, default=DEFAULT_NUMBER_TOLERANCE
        ): cv.positive_int,
    }
)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Awesome Light platform."""
    # Assign configuration variables.
    # The configuration check takes care they are present.
    scene_path = config[CONF_SCENE_PATH]

    # Setup connection with devices/cloud
    hub = StatefulScenes.Hub(hass, scene_path)

    # Add devices
    add_entities(StatefulSceneSwitch(scene) for scene in hub.scenes)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, add_entities: AddEntitiesCallback
) -> bool:
    """Set up this integration using UI."""
    assert hass is not None
    data = hass.data[DOMAIN]
    assert entry.entry_id in data
    _LOGGER.debug(
        "Setting up Stateful Scenes with data: %s and config_entry %s",
        data,
        entry,
    )
    hub = data[entry.entry_id]

    stateful_scene_switches = [StatefulSceneSwitch(scene) for scene in hub.scenes]

    add_entities(stateful_scene_switches)

    return True


class StatefulSceneSwitch(SwitchEntity):
    """Representation of an Awesome Light."""

    _attr_assumed_state = True
    _attr_has_entity_name = True
    _attr_name = "Stateful Scene"
    _attr_should_poll = False

    def __init__(self, scene) -> None:
        """Initialize an AwesomeLight."""
        self._scene = scene
        self._is_on = None
        self._name = "Stateful Scene"
        self._attr_unique_id = f"stateful_{scene.id}"

        self.register_callback()

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        return self._is_on

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

    def turn_on(self, **kwargs) -> None:
        """Instruct the light to turn on.

        You can skip the brightness part if your light does not support
        brightness control.
        """
        self._scene.turn_on()
        self._is_on = self._scene.is_on

    def turn_off(self, **kwargs) -> None:
        """Instruct the light to turn off."""
        self._scene.turn_off()
        self._is_on = self._scene.is_on

    def update(self) -> None:
        """Fetch new state data for this light.

        This is the only method that should fetch new data for Home Assistant.
        """
        self._is_on = self._scene.is_on

    def register_callback(self) -> None:
        """Register callback to update hass when state changes."""
        self._scene.register_callback(
            state_change_func=async_track_state_change,
            schedule_update_func=self.schedule_update_ha_state,
        )

    def unregister_callback(self) -> None:
        """Unregister callback."""
        self._scene.unregister_callback()
