"""Platform for light integration."""

from __future__ import annotations

import logging

# Import the device class from the component that you want to support
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.switch import PLATFORM_SCHEMA, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.restore_state import RestoreEntity

from . import StatefulScenes
from .const import (
    CONF_NUMBER_TOLERANCE,
    CONF_SCENE_PATH,
    DEFAULT_NUMBER_TOLERANCE,
    DEFAULT_SCENE_PATH,
    DEVICE_INFO_MANUFACTURER,
    DOMAIN,
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
    entities = []
    if isinstance(data[entry.entry_id], StatefulScenes.Hub):
        hub = data[entry.entry_id]
        for scene in hub.scenes:
            entities += [
                StatefulSceneSwitch(scene),
                RestoreOnDeactivate(scene),
                IgnoreUnavailable(scene),
            ]

    elif isinstance(data[entry.entry_id], StatefulScenes.Scene):
        scene = data[entry.entry_id]
        entities += [
            StatefulSceneSwitch(scene),
            RestoreOnDeactivate(scene),
            IgnoreUnavailable(scene),
        ]

    else:
        _LOGGER.error("Invalid entity type for %s", entry.entry_id)
        return False

    add_entities(entities)

    return True


class StatefulSceneSwitch(SwitchEntity):
    """Representation of an Awesome Light."""

    _attr_assumed_state = False
    _attr_has_entity_name = True
    _attr_name = "Stateful Scene"
    _attr_should_poll = False

    def __init__(self, scene) -> None:
        """Initialize an AwesomeLight."""
        self._scene = scene
        self._is_on = None
        self._name = "Stateful Scene"
        self._icon = scene.icon
        self._attr_unique_id = f"stateful_{scene.id}"

        self._scene.callback_funcs = {
            "state_change_func": async_track_state_change_event,
            "schedule_update_func": self.schedule_update_ha_state,
        }
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
    def icon(self) -> str | None:
        """Return the icon of this light."""
        return self._icon

    @property
    def device_info(self) -> DeviceInfo | None:
        """Return the device info."""
        return DeviceInfo(
            identifiers={(self._scene.id,)},
            name=self._scene.name,
            suggested_area=self._scene.area_id,
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

    async def async_added_to_hass(self) -> None:
        """Validate and set the actual scene state on restart."""
        await super().async_added_to_hass()

        def _validate_scene_state():
            self._scene.check_all_states()
            self._is_on = self._scene.is_on
            self.schedule_update_ha_state()

        self.hass.loop.call_later(1, _validate_scene_state)

    def update(self) -> None:
        """Fetch new state data for this light.

        This is the only method that should fetch new data for Home Assistant.
        """
        self._scene.check_all_states()
        self._is_on = self._scene.is_on

    def register_callback(self) -> None:
        """Register callback to update hass when state changes."""
        self._scene.register_callback()

    def unregister_callback(self) -> None:
        """Unregister callback."""
        self._scene.unregister_callback()


class RestoreOnDeactivate(SwitchEntity, RestoreEntity):
    """Switch entity to restore the scene on deactivation."""

    _attr_name = "Restore On Deactivate"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_should_poll = True
    _attr_assumed_state = False

    def __init__(self, scene: StatefulScenes.Scene) -> None:
        """Initialize."""
        self._scene = scene
        self._name = f"{scene.name} Restore On Deactivate"
        self._attr_unique_id = f"{scene.id}_restore_on_deactivate"
        self._scene.set_restore_on_deactivate(scene.restore_on_deactivate)
        self._is_on = scene.restore_on_deactivate
        self._is_on = None

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

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        return self._is_on

    def turn_on(self, **kwargs) -> None:
        """Instruct the light to turn on.

        You can skip the brightness part if your light does not support
        brightness control.
        """
        self._scene.set_restore_on_deactivate(True)
        self._is_on = self._scene.restore_on_deactivate

    def turn_off(self, **kwargs) -> None:
        """Instruct the light to turn off."""
        self._scene.set_restore_on_deactivate(False)
        self._is_on = self._scene.restore_on_deactivate

    def update(self) -> None:
        """Fetch new state data for this light.

        This is the only method that should fetch new data for Home Assistant.
        """
        self._is_on = self._scene.restore_on_deactivate

    async def async_added_to_hass(self):
        """Handle entity which will be added."""
        state = await self.async_get_last_state()
        if not state:
            return
        self._scene.set_restore_on_deactivate(state.state == STATE_ON)
        self._is_on = state.state == STATE_ON


class IgnoreUnavailable(SwitchEntity, RestoreEntity):
    """Switch entity to ignore unavailable entities."""

    _attr_name = "Ignore unavailable entities"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_should_poll = True
    _attr_assumed_state = False

    def __init__(self, scene: StatefulScenes.Scene) -> None:
        """Initialize."""
        self._scene = scene
        self._name = f"{scene.name} Ignore Unavailable"
        self._attr_unique_id = f"{scene.id}_ignore_unavailable"
        self._scene.set_ignore_unavailable(scene.ignore_unavailable)
        self._is_on = scene.ignore_unavailable

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

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        return self._is_on

    def turn_on(self, **kwargs) -> None:
        """Instruct the light to turn on.

        You can skip the brightness part if your light does not support
        brightness control.
        """
        self._scene.set_ignore_unavailable(True)
        self._is_on = self._scene.restore_on_deactivate

    def turn_off(self, **kwargs) -> None:
        """Instruct the light to turn off."""
        self._scene.set_ignore_unavailable(False)
        self._is_on = self._scene.restore_on_deactivate

    def update(self) -> None:
        """Fetch new state data for this light.

        This is the only method that should fetch new data for Home Assistant.
        """
        self._is_on = self._scene.ignore_unavailable

    async def async_added_to_hass(self):
        """Handle entity which will be added."""
        state = await self.async_get_last_state()
        if not state:
            return
        self._scene.set_ignore_unavailable(state.state == STATE_ON)
        self._is_on = state.state == STATE_ON
