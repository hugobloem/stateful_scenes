"""Stateful Scenes for Home Assistant."""

import logging
from typing import Any

from homeassistant.core import Event, EventStateChangedData, HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.template import area_id, area_name

from .const import (
    ATTRIBUTES_TO_CHECK,
    CONF_SCENE_AREA,
    CONF_SCENE_ENTITIES,
    CONF_SCENE_ENTITY_ID,
    CONF_SCENE_ICON,
    CONF_SCENE_ID,
    CONF_SCENE_LEARN,
    CONF_SCENE_NAME,
    CONF_SCENE_NUMBER_TOLERANCE,
    SceneStateAttributes,
    StatefulScenesYamlInvalid,
)
from .helpers import (
    get_icon_from_entity_id,
    get_id_from_entity_id,
    get_name_from_entity_id,
)

_LOGGER = logging.getLogger(__name__)


def get_entity_id_from_id(hass: HomeAssistant, id: str) -> str:
    """Get entity_id from scene id."""
    entity_ids = hass.states.async_entity_ids("scene")
    for entity_id in entity_ids:
        state = hass.states.get(entity_id)
        if state.attributes.get("id", None) == id:
            return entity_id
    return None


class SceneEvaluationTimer:
    """Manages an HA scheduled cancellable timer for transition followed by debounce."""

    def __init__(
        self,
        hass: HomeAssistant,
        transition_time: float = 0.0,
        debounce_time: float = 0.0,
    ) -> None:
        """Initialize with no active timer."""
        self._cancel_callback = None
        self._transition_time = transition_time
        self._debounce_time = debounce_time
        self._hass = hass

    async def async_start(self, callback) -> None:
        """Start a new timer if we have a duration."""
        await self.async_cancel_if_active()
        if self.transition_time > 0 and self._hass is not None:
            _LOGGER.debug(
                "Starting scene evaluation timer for %s seconds",
                self.transition_time + self.debounce_time,
            )

            self._cancel_callback = async_call_later(
                self._hass,
                self.transition_time + self.debounce_time,
                callback,
            )

    @property
    def transition_time(self) -> float:
        """Get the timer duration."""
        return self._transition_time

    def set_transition_time(self, time: float) -> None:
        """Set the timer duration."""
        self._transition_time = time or 0.0

    @property
    def debounce_time(self) -> float:
        """Get the timer duration."""
        return self._debounce_time

    def set_debounce_time(self, time: float) -> None:
        """Set the timer duration."""
        self._debounce_time = time or 0.0

    async def async_cancel_if_active(self) -> None:
        """Cancel current timer if active."""
        if self._cancel_callback:
            _LOGGER.debug("Async cancelling active scene evaluation timer")
            self._cancel_callback()
            self._cancel_callback = None

    def is_active(self) -> bool:
        """Return whether there is an active scene evaluation timer."""
        return self._cancel_callback is not None

    async def async_clear(self) -> None:
        """Clear timer state without cancelling."""
        _LOGGER.debug("Clearing scene evaluation timer state")
        self._cancel_callback = None


class Scene:
    """State scene class."""

    def __init__(self, hass: HomeAssistant, scene_conf: dict) -> None:
        """Initialize."""
        self.hass = hass
        self.name: str = scene_conf[CONF_SCENE_NAME]
        self._entity_id: str = scene_conf[CONF_SCENE_ENTITY_ID]
        self._number_tolerance = scene_conf[CONF_SCENE_NUMBER_TOLERANCE]
        self._id = scene_conf[CONF_SCENE_ID]
        self._area_id: str = scene_conf[CONF_SCENE_AREA]
        self.learn = scene_conf[CONF_SCENE_LEARN]
        self.entities = scene_conf[CONF_SCENE_ENTITIES]
        self.icon = scene_conf[CONF_SCENE_ICON]
        self._is_on = False
        self._transition_time: float = 0.0
        self._restore_on_deactivate = True
        self._debounce_time: float = 0.0
        self._ignore_unavailable = False
        self._ignore_attributes = False
        self._off_scene_entity_id = None
        self._scene_evaluation_timer = SceneEvaluationTimer(
            hass, self._transition_time, self._debounce_time
        )
        self.callback = None
        self.callback_funcs = {}
        self.schedule_update = None
        self.states = dict.fromkeys(self.entities, False)
        self.restore_states = dict.fromkeys(self.entities)

        if self.learn:
            self.learned = False

        if self._entity_id is None:
            self._entity_id = get_entity_id_from_id(self.hass, self._id)

        hass.async_create_task(self.async_initialize())

    @property
    def attributes(self) -> SceneStateAttributes:
        """Return scene attributes matching SceneStateProtocol."""
        return SceneStateAttributes(
            {
                "friendly_name": self.name,
                "icon": self.icon,
                "area_id": self.area_id,
                "entity_id": list(self.entities.keys()),
            }
        )

    @property
    def entity_id(self) -> str:
        """Return the entity_id of the scene."""
        return self._entity_id

    @property
    def is_on(self):
        """Return true if the scene is on."""
        return self._is_on

    @property
    def id(self) -> str:
        """Return the id of the scene."""
        if self.learn:
            return self._id + "_learned"  # avoids non-unique id during testing
        return self._id

    @property
    def area_id(self) -> str:
        """Return the area_id of the scene."""
        return self._area_id

    async def async_turn_on(self):
        """Turn on the scene."""
        if self._entity_id is None:
            raise StatefulScenesYamlInvalid(
                "Cannot find entity_id for: " + self.name + self._entity_id
            )

        # Store the current state of the entities
        for entity_id in self.entities:
            await self.async_store_entity_state(entity_id)

        await self._scene_evaluation_timer.async_start(
            self.async_timer_evaluate_scene_state
        )

        await self.hass.services.async_call(
            domain="scene",
            service="turn_on",
            target={"entity_id": self._entity_id},
            service_data={"transition": self._transition_time},
        )
        self._is_on = True

    @property
    def off_scene_entity_id(self) -> str | None:
        """Return the entity_id of the off scene."""
        return self._off_scene_entity_id

    def set_off_scene(self, entity_id: str | None) -> None:
        """Set the off scene entity_id."""
        self._off_scene_entity_id = entity_id
        if entity_id:
            self._restore_on_deactivate = False

    async def async_set_off_scene(self, entity_id: str | None) -> None:
        """Set the off scene entity_id asynchronously."""
        self.set_off_scene(entity_id)

    async def async_turn_off(self):
        """Turn off all entities in the scene."""
        if not self._is_on:  # already off
            return

        if self._off_scene_entity_id:
            await self._scene_evaluation_timer.async_cancel_if_active()
            await self.hass.services.async_call(
                domain="scene",
                service="turn_on",
                target={"entity_id": self._off_scene_entity_id},
                service_data={"transition": self._transition_time},
            )
        elif self.restore_on_deactivate:
            await self._scene_evaluation_timer.async_start(
                self.async_timer_evaluate_scene_state
            )
            await self.async_restore()
        else:
            await self.hass.services.async_call(
                domain="homeassistant",
                service="turn_off",
                target={"entity_id": list(self.entities.keys())},
            )

        self._is_on = False

    @property
    def number_tolerance(self) -> int:
        """Get the number tolerance."""
        return self._number_tolerance

    def set_number_tolerance(self, number_tolerance):
        """Set the number tolerance."""
        self._number_tolerance = number_tolerance

    @property
    def transition_time(self) -> float:
        """Get the transition time."""
        return self._transition_time

    def set_transition_time(self, transition_time):
        """Set the transition time."""
        self._transition_time = transition_time
        self._scene_evaluation_timer.set_transition_time(transition_time)

    @property
    def debounce_time(self) -> float:
        """Get the debounce time."""
        return self._debounce_time

    def set_debounce_time(self, debounce_time: float):
        """Set the debounce time."""
        self._debounce_time = debounce_time or 0.0
        self._scene_evaluation_timer.set_debounce_time(debounce_time)

    @property
    def restore_on_deactivate(self) -> bool:
        """Get the restore on deactivate flag."""
        return self._restore_on_deactivate

    def set_restore_on_deactivate(self, restore_on_deactivate):
        """Set the restore on deactivate flag."""
        self._restore_on_deactivate = restore_on_deactivate

    @property
    def ignore_unavailable(self) -> bool:
        """Get the ignore unavailable flag."""
        return self._ignore_unavailable

    def set_ignore_unavailable(self, ignore_unavailable):
        """Set the ignore unavailable flag."""
        self._ignore_unavailable = ignore_unavailable

    @property
    def ignore_attributes(self) -> bool:
        """Get the ignore attributes flag."""
        return self._ignore_attributes

    def set_ignore_attributes(self, ignore_attributes):
        """Set the ignore attributes flag."""
        self._ignore_attributes = ignore_attributes

    async def async_initialize(self) -> None:
        """Initialize the scene and evaluate its initial state."""
        _LOGGER.debug("Initializing scene: %s", self.name)
        await self.async_check_all_states()
        _LOGGER.debug(
            "Initial state for scene %s: %s", self.name, "on" if self._is_on else "off"
        )

    async def async_register_callback(self):
        """Register callback."""
        schedule_update_func = self.callback_funcs.get("schedule_update_func", None)
        state_change_func = self.callback_funcs.get("state_change_func", None)
        if schedule_update_func is None or state_change_func is None:
            raise ValueError("No callback functions provided for scene.")

        self.schedule_update = schedule_update_func

        # Register state change callback for all entities in the scene
        entity_ids = list(self.entities.keys())
        _LOGGER.debug(
            "Registering callbacks for entities: %s in scene: %s",
            entity_ids,
            self.name,
        )

        # Set up state change tracking
        self.callback = state_change_func(
            self.hass, entity_ids, self.async_update_callback
        )

    async def async_unregister_callback(self):
        """Unregister callbacks."""
        if self.callback is not None:
            self.callback()
            self.callback = None

    async def async_update_callback(self, event: Event[EventStateChangedData]):
        """Update the scene when a tracked entity changes state."""
        entity_id = event.data.get("entity_id")
        new_state = event.data.get("new_state")
        old_state = event.data.get("old_state")

        _LOGGER.debug(
            "State change callback for %s in scene %s: old=%s new=%s",
            entity_id,
            self.name,
            old_state.state if old_state else None,
            new_state.state if new_state else None,
        )

        # Check if this update is interesting
        if self.is_interesting_update(old_state, new_state):
            if not self._scene_evaluation_timer.is_active():
                await self.async_evaluate_scene_state()

                # Store the old state
                await self.async_store_entity_state(entity_id, old_state)

    async def async_evaluate_scene_state(self):
        """Evaluate scene state immediately."""
        _LOGGER.debug("[Scene: %s] Starting scene evaluation", self.name)
        await self.async_check_all_states()
        if self.schedule_update:
            self.schedule_update(True)

    async def async_timer_evaluate_scene_state(self, _now):
        """Handle Callback from HA after expiration of SceneEvaluationTimer."""
        await self._scene_evaluation_timer.async_clear()
        _LOGGER.debug("SceneEvaluationTimer triggered eval callback: %s", self.name)
        await self.async_evaluate_scene_state()

    def is_interesting_update(self, old_state, new_state):
        """Check if the state change is interesting."""
        if old_state is None:
            if new_state is None:
                _LOGGER.warning("New State is None and Old State is None")
            return True
        if not self.compare_values(old_state.state, new_state.state):
            return True

        if new_state.domain in ATTRIBUTES_TO_CHECK:
            entity_attrs = new_state.attributes
            old_entity_attrs = old_state.attributes
            for attribute in ATTRIBUTES_TO_CHECK.get(new_state.domain):
                if attribute not in old_entity_attrs or attribute not in entity_attrs:
                    continue

                if not self.compare_values(
                    old_entity_attrs[attribute], entity_attrs[attribute]
                ):
                    return True
        return False

    async def async_check_state(self, entity_id, new_state):
        """Check if entity's current state matches the scene's defined state."""
        if new_state is None:
            # Check if entity exists in registry
            # Get entity registry directly
            registry = er.async_get(self.hass)
            entry = registry.async_get(entity_id)

            if entry is None:
                _LOGGER.debug(
                    "[Scene: %s] Entity %s not found in registry.",
                    self.name,
                    entity_id,
                )
                return False

            # Check if entity exists in state
            new_state = self.hass.states.get(entity_id)
            if new_state is None:
                _LOGGER.debug(
                    "[Scene: %s] Entity %s not found in state.",
                    self.name,
                    entity_id,
                )
                return False

        if self.ignore_unavailable and new_state.state == "unavailable":
            return None

        # Check state
        if not self.compare_values(self.entities[entity_id]["state"], new_state.state):
            _LOGGER.debug(
                "[%s] state not matching: %s: wanted=%s got=%s.",
                self.name,
                entity_id,
                self.entities[entity_id]["state"],
                new_state.state,
            )
            return False

        # Check attributes
        # If both desired and current states are "off", consider it a match regardless of attributes
        if new_state.state == "off" and self.entities[entity_id]["state"] == "off":
            return True

        if self.ignore_attributes:
            return True

        # Only check attributes if entity isn't "off"
        if new_state.domain in ATTRIBUTES_TO_CHECK:
            entity_attrs = new_state.attributes
            for attribute in ATTRIBUTES_TO_CHECK.get(new_state.domain):
                if (
                    attribute not in self.entities[entity_id]
                    or attribute not in entity_attrs
                ):
                    continue
                if not self.compare_values(
                    self.entities[entity_id][attribute], entity_attrs[attribute]
                ):
                    _LOGGER.debug(
                        "[%s] attribute not matching: %s %s: wanted=%s got=%s.",
                        self.name,
                        entity_id,
                        attribute,
                        self.entities[entity_id][attribute],
                        entity_attrs[attribute],
                    )
                    return False
        _LOGGER.debug(
            "[%s] Found match after %s updated",
            self.name,
            entity_id,
        )
        return True

    async def async_check_all_states(self):
        """Check the state of the scene.

        If all entities are in the desired state, the scene is on. If any entity is not
        in the desired state, the scene is off. Unavaiblable entities are ignored, but
        if all entities are unavailable, the scene is off.
        """
        for entity_id in self.entities:
            state = self.hass.states.get(entity_id)
            self.states[entity_id] = await self.async_check_state(entity_id, state)

        states = [state for state in self.states.values() if state is not None]
        result = all(states) if states else False
        self._is_on = result

    async def async_store_entity_state(self, entity_id, state=None):
        """Store the state of an entity."""
        if state is None:
            state = self.hass.states.get(entity_id)
        self.restore_states[entity_id] = state

    async def async_restore(self):
        """Restore the state entities."""
        entities = {}
        for entity_id, state in self.restore_states.items():
            if state is None:
                continue

            # restore state
            entities[entity_id] = {"state": state.state}

            # do not restore attributes if the entity is off
            if state.state == "off":
                continue

            # restore attributes
            if state.domain in ATTRIBUTES_TO_CHECK:
                entity_attrs = state.attributes
                for attribute in ATTRIBUTES_TO_CHECK.get(state.domain):
                    if attribute not in entity_attrs:
                        continue
                    entities[entity_id][attribute] = entity_attrs[attribute]

        service_data = {"entities": entities}
        if self._transition_time is not None:
            service_data["transition"] = self._transition_time
        await self.hass.services.async_call(
            domain="scene", service="apply", service_data=service_data
        )

    #    def store_entity_state(self, entity_id, state=None):
    #        """Store the state of an entity.
    #
    #        If the state is not provided, the current state of the entity is used.
    #        """
    #        if state is None:
    #            state = self.hass.states.get(entity_id)
    #        self.restore_states[entity_id] = state

    def restore(self):
        """Restore the state entities."""
        entities = {}
        for entity_id, state in self.restore_states.items():
            if state is None:
                continue

            # restore state
            entities[entity_id] = {"state": state.state}

            # do not restore attributes if the entity is off
            if state.state == "off":
                continue

            # restore attributes
            if state.domain in ATTRIBUTES_TO_CHECK:
                entity_attrs = state.attributes
                for attribute in ATTRIBUTES_TO_CHECK.get(state.domain):
                    if attribute not in entity_attrs:
                        continue
                    entities[entity_id][attribute] = entity_attrs[attribute]

        service_data = {"entities": entities}
        if self._transition_time is not None:
            service_data["transition"] = self._transition_time
        self.hass.services.call(
            domain="scene", service="apply", service_data=service_data
        )

    def compare_values(self, value1, value2):
        """Compare two values."""
        if isinstance(value1, dict) and isinstance(value2, dict):
            return self.compare_dicts(value1, value2)

        if (isinstance(value1, list) or isinstance(value1, tuple)) and (
            isinstance(value2, list) or isinstance(value2, tuple)
        ):
            return self.compare_lists(value1, value2)

        if (isinstance(value1, int) or isinstance(value1, float)) and (
            isinstance(value2, int) or isinstance(value2, float)
        ):
            return self.compare_numbers(value1, value2)

        return value1 == value2

    def compare_dicts(self, dict1, dict2):
        """Compare two dicts."""
        for key, value in dict1.items():
            if key not in dict2:
                return False
            if not self.compare_values(value, dict2[key]):
                return False
        return True

    def compare_lists(self, list1, list2):
        """Compare two lists."""
        for value1, value2 in zip(list1, list2):
            if not self.compare_values(value1, value2):
                return False
        return True

    def compare_numbers(self, number1, number2):
        """Compare two numbers."""
        return abs(number1 - number2) <= self.number_tolerance

    @staticmethod
    def learn_scene_states(hass: HomeAssistant, entities: list) -> dict:
        """Learn the state of the scene."""
        conf = {}
        for entity in entities:
            state = hass.states.get(entity)
            conf[entity] = {"state": state.state}
            conf[entity].update(state.attributes)
        return conf


class Hub:
    """State scene class."""

    def __init__(
        self,
        hass: HomeAssistant,
        scene_confs: dict[str, Any],
        number_tolerance: int = 1,
    ) -> None:
        """Initialize the Hub class.

        Args:
            hass (HomeAssistant): Home Assistant instance
            scene_confs (dict[str, Any]): Scene configurations from the scene file
            number_tolerance (int): Tolerance for comparing numbers

        Raises:
            StatefulScenesYamlNotFound: If the yaml file is not found
            StatefulScenesYamlInvalid: If the yaml file is invalid

        """
        self.number_tolerance = number_tolerance
        self.hass = hass
        self.scenes: list[Scene] = []
        self.scene_confs: list[dict[str, Any]] = []

        for scene_conf in scene_confs:
            if not self.validate_scene(scene_conf):
                continue
            self.scenes.append(
                Scene(
                    self.hass,
                    self.extract_scene_configuration(scene_conf),
                )
            )
            self.scene_confs.append(self.extract_scene_configuration(scene_conf))

    def validate_scene(self, scene_conf: dict) -> None:
        """Validate scene configuration.

        Args:
            scene_conf (dict): Scene configuration

        Raises:
            StatefulScenesYamlInvalid: If the scene is invalid

        Returns:
            bool: True if the scene is valid

        """

        if "entities" not in scene_conf:
            raise StatefulScenesYamlInvalid(
                "Scene is missing entities: " + scene_conf["name"]
            )

        if "id" not in scene_conf:
            raise StatefulScenesYamlInvalid(
                "Scene is missing id: " + scene_conf["name"]
            )

        for entity_id, scene_attributes in scene_conf["entities"].items():
            if "state" not in scene_attributes:
                raise StatefulScenesYamlInvalid(
                    "Scene is missing state for entity "
                    + entity_id
                    + scene_conf["name"]
                )

        return True

    def extract_scene_configuration(self, scene_conf: dict) -> dict:
        """Extract entities and attributes from a scene.

        Args:
            scene_conf (dict): Scene configuration

        Returns:
            dict: Scene configuration

        """
        entities = {}
        for entity_id, scene_attributes in scene_conf["entities"].items():
            domain = entity_id.split(".")[0]
            attributes = {"state": scene_attributes["state"]}

            if domain in ATTRIBUTES_TO_CHECK:
                for attribute, value in scene_attributes.items():
                    if attribute in ATTRIBUTES_TO_CHECK.get(domain):
                        attributes[attribute] = value

            entities[entity_id] = attributes

        entity_id = scene_conf.get("entity_id", None)
        if entity_id is None:
            entity_id = get_entity_id_from_id(self.hass, scene_conf.get("id"))

        return {
            "name": scene_conf["name"],
            "id": scene_conf.get("id", entity_id),
            "icon": scene_conf.get(
                "icon", get_icon_from_entity_id(self.hass, entity_id)
            ),
            "entity_id": entity_id,
            "area": area_name(self.hass, area_id(self.hass, entity_id)),
            "learn": scene_conf.get("learn", False),
            "entities": entities,
            "number_tolerance": scene_conf.get(
                "number_tolerance", self.number_tolerance
            ),
        }

    def prepare_external_scene(self, entity_id, entities) -> dict:
        """Prepare external scene configuration."""
        return {
            "name": get_name_from_entity_id(self.hass, entity_id),
            "id": get_id_from_entity_id(self.hass, entity_id),
            "icon": get_icon_from_entity_id(self.hass, entity_id),
            "entity_id": entity_id,
            "area": area_name(self.hass, area_id(self.hass, entity_id)),
            "learn": True,
            "entities": entities,
        }

    def get_available_scenes(self) -> list[str]:
        """Get list of all scenes from the hub."""
        scene_entities: list[str] = [scene.entity_id for scene in self.scenes]
        return scene_entities

    def get_scene(self, scene_id: str) -> Scene | None:
        """Get scene by entity ID."""
        return next(
            (scene for scene in self.scenes if scene.entity_id == scene_id), None
        )
