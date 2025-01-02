"""Select platform for Stateful Scenes to provide 'off' scene select."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, cast

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
from homeassistant.helpers.restore_state import RestoreEntity

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


class StatefulSceneOffSelect(SelectEntity, RestoreEntity):
    """Representation of a Stateful Scene select entity."""

    def __init__(self, scene: Scene, hub: Hub | None) -> None:
        """Initialize the select entity."""
        self._entity_id_map: dict[str, str] = {
            DEFAULT_OFF_SCENE_ENTITY_ID: DEFAULT_OFF_SCENE_ENTITY_ID
        }
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
        self._off_scene_entity_id: str | None = (
            None  # Variable to store the off scene entity ID
        )

    def _get_available_off_scenes(self) -> list[tuple[str, str]]:
        """Get list of available scenes with friendly names."""
        scenes: list[tuple[str, str]] = []

        if self._hub:
            for opt in self._hub.get_available_scenes():
                if opt != self._scene.entity_id:
                    hub_scene = cast(
                        SceneStateProtocol | None, self._hub.get_scene(opt)
                    )
                    if hub_scene:
                        friendly_name = hub_scene.attributes.get("friendly_name", opt)
                        scenes.append((opt, friendly_name))
        else:
            # Stand-alone case, filter out internal scenes and current scene
            hub_scenes: set[str] = (
                set(self._hub.get_available_scenes()) if self._hub else set()
            )
            states: list[State] = self._scene.hass.states.async_all("scene")
            for state in states:
                if (
                    state.entity_id != self._scene.entity_id
                    and state.entity_id not in hub_scenes
                ):
                    scene_entity = cast(
                        SceneStateProtocol | None,
                        self._scene.hass.states.get(state.entity_id),
                    )
                    if scene_entity:
                        friendly_name = scene_entity.attributes.get(
                            "friendly_name", state.entity_id
                        )
                        scenes.append((state.entity_id, friendly_name))

        # Sort scenes by friendly name
        scenes.sort(key=lambda x: x[1].lower())

        scenes.insert(0, (DEFAULT_OFF_SCENE_ENTITY_ID, DEFAULT_OFF_SCENE_ENTITY_ID))

        return scenes

    @property
    def available(self) -> bool:  # type: ignore[incompatible-override] # Need UI to update
        """Return entity is available based on restore state toggle state."""
        return self._restore_on_deactivate_state == "off"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        return {
            "off_scene_entity_id": self._off_scene_entity_id,
        }

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
                    "Select Restore on Deactivate state for %s: %s",
                    entity_id,
                    self._restore_on_deactivate_state,
                )

                scenes = self._get_available_off_scenes()
                self._entity_id_map = {
                    friendly_name: entity_id for entity_id, friendly_name in scenes
                }
                self._attr_options = [friendly_name for _, friendly_name in scenes]
                self.async_write_ha_state()
        else:
            _LOGGER.warning("Select Event is None, callback not triggered")

    async def async_added_to_hass(self) -> None:
        """Restore last state and set up tracking."""
        await super().async_added_to_hass()

        # Initialize defaults
        self._off_scene_entity_id = None
        self._attr_current_option = DEFAULT_OFF_SCENE_ENTITY_ID

        # Restore state if available
        if last_state := await self.async_get_last_state():
            # Check for stored entity_id in attributes
            if stored_entity_id := last_state.attributes.get("off_scene_entity_id"):
                self._off_scene_entity_id = stored_entity_id
                state = self.hass.states.get(stored_entity_id)
                if state:
                    self._attr_current_option = state.attributes.get(
                        "friendly_name", stored_entity_id
                    )
            # Fall back to friendly name  if no stored entity_id for backward compatibility to 1.60
            elif last_state.state not in [
                None,
                "unavailable",
                "unknown",
                DEFAULT_OFF_SCENE_ENTITY_ID,
            ]:
                restored_state = last_state.state
                if not restored_state.startswith("scene."):
                    # Map friendly name to entity_id
                    states: list[State] = self.hass.states.async_all("scene")
                    for state in states:
                        if state.attributes.get("friendly_name") == restored_state:
                            self._off_scene_entity_id = state.entity_id
                            break
                else:
                    self._off_scene_entity_id = restored_state

                self._attr_current_option = restored_state

            self._scene.set_off_scene(self._off_scene_entity_id)
            _LOGGER.debug(
                "Restored off scene for %s to: %s (from: %s)",
                self._scene.name,
                self._off_scene_entity_id,
                last_state.state,
            )

        # Set up callback for future state changes
        restore_entity_id = (
            f"switch.{self._scene.name.lower().replace(' ', '_')}_restore_on_deactivate"
        )
        async_track_state_change_event(
            self.hass, [restore_entity_id], self.async_update_restore_state
        )

    @under_cached_property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(self._scene.id,)},
            name=self._scene.name,
            manufacturer=DEVICE_INFO_MANUFACTURER,
            suggested_area=self._scene.area_id,
        )

    async def async_select_option(self, option: str) -> None:
        """Update the current selected option."""
        self._attr_current_option = option

        if option == DEFAULT_OFF_SCENE_ENTITY_ID:
            self._off_scene_entity_id = None
        else:
            # Map friendly name to entity_id
            self._off_scene_entity_id = self._entity_id_map.get(option)

        await self._scene.async_set_off_scene(self._off_scene_entity_id)
        self.async_schedule_update_ha_state()

        _LOGGER.debug(
            "Selected off scene for %s: %s (entity_id: %s)",
            self._scene.name,
            option,
            self._off_scene_entity_id,
        )

    @property
    def options(self) -> list[str]:  # type: ignore[incompatible-override] # Need UI to update
        """Return the list of available options."""
        return self._attr_options
