"""Select platform for Stateful Scenes to provide 'off' scene select."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast

from homeassistant.helpers.entity_registry import ReadOnlyDict

if TYPE_CHECKING:
    # mypy cannot workout _cache Protocol with attrs
    from propcache import cached_property as under_cached_property
else:
    from propcache import under_cached_property

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import (
    Event,
    EventStateChangedData,
    HomeAssistant,
    State,
    callback,
)
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    DEFAULT_OFF_SCENE_ENTITY_ID, 
    DEVICE_INFO_MANUFACTURER, 
    DOMAIN, 
    SceneStateProtocol,
)

from .StatefulScenes import Hub, Scene

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Stateful Scenes select."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    entities: list[StatefulSceneOffSelect] = []

    if isinstance(data, Hub):
        entities.extend(StatefulSceneOffSelect(scene, data) for scene in data.scenes)
    elif isinstance(data, Scene):
        entities.append(StatefulSceneOffSelect(data, None))

    async_add_entities(entities)


class StatefulSceneOffSelect(SelectEntity):
    """Representation of a Stateful Scene select entity."""

    def __init__(self, scene: Scene, hub: Hub | None) -> None:
        """Initialize the select entity."""
        self._entity_id_map: dict[str, str] = {DEFAULT_OFF_SCENE_ENTITY_ID: DEFAULT_OFF_SCENE_ENTITY_ID}
        self._attr_options = list(self._entity_id_map.keys())
        self._attr_current_option = list(self._entity_id_map.keys())[0]
        self._attr_options_ordered = False  # Preserve our ordering
        super().__init__()
        self._scene = scene
        self._hub = hub
        self.unique_id = f"{scene.id}_off_scene"
        self._attr_name = f"{scene.name} Off Scene"
        self._cache: dict[str, bool | DeviceInfo] = {}
        self._attr_entity_category = EntityCategory.CONFIG
        self._restore_on_deactivate_state: str | None = None

    def _get_available_off_scenes(self) -> list[tuple[str, str]]:
        """Get list of available scenes with friendly names."""
        scenes: list[tuple[str, str]] = [(DEFAULT_OFF_SCENE_ENTITY_ID, DEFAULT_OFF_SCENE_ENTITY_ID)]

        if self._hub:
            for opt in self._hub.get_available_scenes():
                if opt != self._scene.entity_id:
                    hub_scene = cast(SceneStateProtocol | None, self._hub.get_scene(opt))
                    if hub_scene:
                        friendly_name = hub_scene.attributes.get("friendly_name", opt)
                        scenes.append((opt, friendly_name))
        else:
            # Stand-alone case, filter out internal scenes and current scene
            hub_scenes: set[str] = set(self._hub.get_available_scenes()) if self._hub else set()
            states: list[State] = self._scene.hass.states.async_all("scene")
            for state in states:
                if state.entity_id != self._scene.entity_id and state.entity_id not in hub_scenes:
                    scene_entity = cast(SceneStateProtocol | None, self._scene.hass.states.get(state.entity_id))
                    if scene_entity:
                        friendly_name = scene_entity.attributes.get("friendly_name", state.entity_id)
                        scenes.append((state.entity_id, friendly_name))

        # Sort scenes by friendly name
        scenes.sort(key=lambda x: x[1].lower())
        return scenes

    @property
    def available(self) -> bool:    # type: ignore[incompatible-override] # Need UI to update
        """Return entity is available based on restore state toggle state."""
        return self._restore_on_deactivate_state == "off"

    @callback
    def async_update_restore_state(
        self, event: Event[EventStateChangedData] | None = None
    ) -> None:
        """Sync with the restore state toggle."""
        if event:
            new_state = event.data.get("new_state")
            if new_state and hasattr(new_state, "state"):
                self._restore_on_deactivate_state = str(new_state.state)
                entity_id: str | None = event.data.get("entity_id")
                _LOGGER.debug(
                    "Restore on Deactivate state for %s: %s",
                    entity_id,
                    self._restore_on_deactivate_state,
                )

                scenes = self._get_available_off_scenes()
                self._entity_id_map = {friendly_name: entity_id for entity_id, friendly_name in scenes}
                self._attr_options = [friendly_name for _, friendly_name in scenes]
                self.async_write_ha_state()
        else:
            _LOGGER.warning("Event is None, callback not triggered")

    async def async_added_to_hass(self) -> None:
        """Sync 'off' scene select availability with 'Resotre on Deactivate' state."""
        restore_entity_id = (
            f"switch.{self._scene.name.lower().replace(' ', '_')}_restore_on_deactivate"
        )
        _LOGGER.debug("Setting up state change listener for %s", restore_entity_id)
        async_track_state_change_event(
            self.hass, [restore_entity_id], self.async_update_restore_state
        )
        state = self.hass.states.get(restore_entity_id)
        if state:
            self._restore_on_deactivate_state = state.state
            _LOGGER.debug(
                "Initial Restore on Deactivate state for %s: %s",
                restore_entity_id,
                self._restore_on_deactivate_state,
            )

    @under_cached_property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            # In this integration's platform files following perhaps should be...
            # identifiers={(DOMAIN, self._scene.id)},
            # but the integration would break changing one file alone
            identifiers={(self._scene.id,)},
            name=self._scene.name,
            manufacturer=DEVICE_INFO_MANUFACTURER,
            suggested_area=self._scene.area_id,
        )

    def select_option(self, option: str) -> None:
        """Update the current selected option."""
        entity_id = self._entity_id_map[option]
        if entity_id == DEFAULT_OFF_SCENE_ENTITY_ID:
            self._scene.set_off_scene(None)
        else:
            self._scene.set_off_scene(entity_id)
        self._attr_current_option = option

    @property
    def options(self) -> list[str]: # type: ignore[incompatible-override] # Need UI to update
        """Return the list of available options."""
        return self._attr_options
