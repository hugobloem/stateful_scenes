"""Stateful Scenes for Home Assistant."""

import asyncio
import logging

from homeassistant.core import Event, EventStateChangedData, HomeAssistant
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


class Hub:
    """State scene class."""

    def __init__(
        self,
        hass: HomeAssistant,
        scene_confs: dict,
        number_tolerance: int = 1,
    ) -> None:
        """Initialize the Hub class.

        Args:
            hass (HomeAssistant): Home Assistant instance
            scene_confs (str): Scene configurations from the scene file
            external_scenes (list): List of external scenes
            number_tolerance (int): Tolerance for comparing numbers

        Raises:
            StatefulScenesYamlNotFound: If the yaml file is not found
            StatefulScenesYamlInvalid: If the yaml file is invalid

        """
        self.scene_confs = scene_confs
        self.number_tolerance = number_tolerance
        self.hass = hass
        self.scenes = []
        self.scene_confs = []

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


class Scene:
    """State scene class."""

    def __init__(self, hass: HomeAssistant, scene_conf: dict) -> None:
        """Initialize."""
        self.hass = hass
        self.name = scene_conf[CONF_SCENE_NAME]
        self._entity_id = scene_conf[CONF_SCENE_ENTITY_ID]
        self._number_tolerance = scene_conf[CONF_SCENE_NUMBER_TOLERANCE]
        self._id = scene_conf[CONF_SCENE_ID]
        self.area_id = scene_conf[CONF_SCENE_AREA]
        self.learn = scene_conf[CONF_SCENE_LEARN]
        self.entities = scene_conf[CONF_SCENE_ENTITIES]
        self.icon = scene_conf[CONF_SCENE_ICON]
        self._is_on = None
        self._transition_time = 0.0
        self._restore_on_deactivate = True
        self._debounce_time: float = 0
        self._ignore_unavailable = False

        self.callback = None
        self.callback_funcs = {}
        self.schedule_update = None
        self.states = {entity_id: False for entity_id in self.entities}
        self.restore_states = {entity_id: None for entity_id in self.entities}

        if self.learn:
            self.learned = False

        if self._entity_id is None:
            self._entity_id = get_entity_id_from_id(self.hass, self._id)

    @property
    def is_on(self):
        """Return true if the scene is on."""
        return self._is_on

    @property
    def id(self):
        """Return the id of the scene."""
        if self.learn:
            return self._id + "_learned"  # avoids non-unique id during testing
        return self._id

    def turn_on(self):
        """Turn on the scene."""
        if self._entity_id is None:
            raise StatefulScenesYamlInvalid(
                "Cannot find entity_id for: " + self.name + self._entity_id
            )

        self.hass.services.call(
            domain="scene",
            service="turn_on",
            target={"entity_id": self._entity_id},
            service_data={"transition": self._transition_time},
        )
        self._is_on = True

    def turn_off(self):
        """Turn off all entities in the scene."""
        if not self._is_on:  # already off
            return

        if self.restore_on_deactivate:
            self.restore()
        else:
            self.hass.services.call(
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

    @property
    def debounce_time(self) -> float:
        """Get the debounce time."""
        return self._debounce_time

    def set_debounce_time(self, debounce_time: float):
        """Set the debounce time."""
        self._debounce_time = debounce_time or 0.0

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

    def register_callback(self):
        """Register callback."""
        schedule_update_func = self.callback_funcs.get("schedule_update_func", None)
        state_change_func = self.callback_funcs.get("state_change_func", None)
        if schedule_update_func is None or state_change_func is None:
            raise ValueError("No callback functions provided for scene.")
        self.schedule_update = schedule_update_func
        self.callback = state_change_func(
            self.hass, self.entities.keys(), self.update_callback
        )

    def unregister_callback(self):
        """Unregister callbacks."""
        if self.callback is not None:
            self.callback()
            self.callback = None

    async def update_callback(self, event: Event[EventStateChangedData]):
        """Update the scene when a tracked entity changes state."""
        entity_id = event.data.get("entity_id")
        new_state = event.data.get("new_state")
        old_state = event.data.get("old_state")

        self.store_entity_state(entity_id, old_state)
        if self.is_interesting_update(old_state, new_state):
            await asyncio.sleep(self.debounce_time)
            self.schedule_update(True)

    def is_interesting_update(self, old_state, new_state):
        """Check if the state change is interesting."""
        if old_state is None:
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

    def check_state(self, entity_id, new_state):
        """Check the state of the scene."""
        if new_state is None:
            _LOGGER.warning(f"Entity not found: {entity_id}")
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

    def check_all_states(self):
        """Check the state of the scene.

        If all entities are in the desired state, the scene is on. If any entity is not
        in the desired state, the scene is off. Unavaiblable entities are ignored, but
        if all entities are unavailable, the scene is off.
        """
        for entity_id in self.entities:
            state = self.hass.states.get(entity_id)
            self.states[entity_id] = self.check_state(entity_id, state)

        states = [state for state in self.states.values() if state is not None]

        if not states:
            self._is_on = False

        self._is_on = all(states)

    def store_entity_state(self, entity_id, state):
        """Store the state of an entity."""
        self.restore_states[entity_id] = state

    def restore(self):
        """Restore the state entities."""
        entities = {}
        for entity_id, state in self.restore_states.items():
            if state is None:
                continue
            entities[entity_id] = {"state": state.state}
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
