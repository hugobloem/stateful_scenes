"""Stateful Scenes for Home Assistant."""

import asyncio
import logging

import yaml
import os
from homeassistant.core import HomeAssistant
from homeassistant.helpers.template import area_id
from homeassistant.helpers import entity_registry

from .const import ATTRIBUTES_TO_CHECK

_LOGGER = logging.getLogger(__name__)


class StatefulScenesYamlNotFound(Exception):
    """Raised when specified yaml is not found."""


class StatefulScenesYamlInvalid(Exception):
    """Raised when specified yaml is invalid."""


def get_entity_id_from_id(hass: HomeAssistant, id: str) -> str:
    """Get entity_id from scene id."""
    entity_ids = hass.states.async_entity_ids("scene")
    for entity_id in entity_ids:
        state = hass.states.get(entity_id)
        if state.attributes.get("id", None) == id:
            return entity_id
    return None

def get_id_from_entity_id(hass: HomeAssistant, entity_id: str) -> str:
    """Get scene id from entity_id."""
    er = entity_registry.async_get(hass)
    return entity_registry.async_resolve_entity_id(er, entity_id)


def get_name_from_entity_id(hass: HomeAssistant, entity_id: str) -> str:
    """Get scene name from entity_id."""
    er = entity_registry.async_get(hass)
    name = er.async_get(entity_id).original_name
    return name if name is not None else entity_id

def get_icon_from_entity_id(hass: HomeAssistant, entity_id: str) -> str:
    """Get scene icon from entity_id."""
    er = entity_registry.async_get(hass)
    icon = er.async_get(entity_id).icon
    return icon if icon is not None else None


class Hub:
    """State scene class."""

    def __init__(
        self,
        hass: HomeAssistant,
        scene_path: str,
        external_scenes: dict = {},
        number_tolerance: int = 1,
    ) -> None:
        """Initialize the Hub class.

        Args:
            hass (HomeAssistant): Home Assistant instance
            scene_path (str): Path to the yaml file containing the scenes
            external_scenes (list): List of external scenes
            number_tolerance (int): Tolerance for comparing numbers

        Raises:
            StatefulScenesYamlNotFound: If the yaml file is not found
            StatefulScenesYamlInvalid: If the yaml file is invalid

        """
        self.scene_path = scene_path
        self.number_tolerance = number_tolerance
        self.hass = hass
        self.scenes = []

        scene_confs = self.load_scenes()
        for scene_conf in scene_confs:
            if not self.validate_scene(scene_conf):
                continue
            self.scenes.append(
                Scene(
                    self.hass,
                    self.extract_scene_configuration(scene_conf),
                    self.number_tolerance,
                )
            )

        for entity_id, conf in external_scenes.items():
            scene_conf = self.prepare_external_scene(entity_id, conf["entities"])
            self.scenes.append(
                Scene(
                    self.hass,
                    self.extract_scene_configuration(scene_conf),
                    self.number_tolerance,
                )
            )

    def load_scenes(self) -> list:
        """Load scenes from yaml file."""
        # check if file exists
        if self.scene_path is None:
            raise StatefulScenesYamlNotFound("Scenes file not specified.")
        if not os.path.exists(self.scene_path):
            raise StatefulScenesYamlNotFound("No scenes file " + self.scene_path)

        try:
            with open(self.scene_path, encoding="utf-8") as f:
                scenes_confs = yaml.load(f, Loader=yaml.FullLoader)
        except OSError as err:
            raise StatefulScenesYamlInvalid(
                "No scenes found in " + self.scene_path
            ) from err

        if not scenes_confs or not isinstance(scenes_confs, list):
            raise StatefulScenesYamlInvalid("No scenes found in " + self.scene_path)

        return scenes_confs

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
            raise StatefulScenesYamlInvalid("Scene is missing entities: " + scene_conf["name"])

        if "id" not in scene_conf:
            raise StatefulScenesYamlInvalid("Scene is missing id: " + scene_conf["name"])

        for entity_id, scene_attributes in scene_conf["entities"].items():
            if "state" not in scene_attributes:
                raise StatefulScenesYamlInvalid(
                    "Scene is missing state for entity " + entity_id + scene_conf["name"]
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
            "icon": scene_conf.get("icon", get_icon_from_entity_id(self.hass, entity_id)),
            "entity_id": entity_id,
            "area": area_id(self.hass, entity_id),
            "learn": scene_conf.get("learn", False),
            "entities": entities,
        }

    def prepare_external_scene(self, entity_id, entities) -> dict:
        """Prepare external scene configuration."""
        return {
            "name": get_name_from_entity_id(self.hass, entity_id),
            "id": get_id_from_entity_id(self.hass, entity_id),
            "icon": get_icon_from_entity_id(self.hass, entity_id),
            "entity_id": entity_id,
            "area": area_id(self.hass, entity_id),
            "learn": True,
            "entities": entities,
        }


class Scene:
    """State scene class."""

    def __init__(
        self, hass: HomeAssistant, scene_conf: dict, number_tolerance=1
    ) -> None:
        """Initialize."""
        self.hass = hass
        self.number_tolerance = number_tolerance
        self.name = scene_conf["name"]
        self._entity_id = scene_conf["entity_id"]
        self._id = scene_conf["id"]
        self.area_id = scene_conf["area"]
        self.learn = scene_conf["learn"]
        self.entities = scene_conf["entities"]
        self.icon = scene_conf["icon"]
        self._is_on = None
        self._transition_time = None
        self._restore_on_deactivate = True
        self._debounce_time: float = 0

        self.callback = None
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
            raise StatefulScenesYamlInvalid("Cannot find entity_id for: " + self.name + self._entity_id)

        self.hass.services.call(
            domain="scene",
            service="turn_on",
            target={"entity_id": self._entity_id},
            service_data={"transition": self._transition_time},
        )
        self._is_on = True

    def turn_off(self):
        """Turn off all entities in the scene."""
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
    def transition_time(self) -> float:
        """Get the transition time."""
        return self._transition_time

    def set_transition_time(self, transition_time):
        """Set the transition time."""
        self._transition_time = transition_time

    @property
    def debounce_time(self) -> float:
        return self._debounce_time
    
    def set_debounce_time(self, debounce_time: float):
        self._debounce_time = debounce_time

    @property
    def restore_on_deactivate(self) -> bool:
        """Get the restore on deactivate flag."""
        return self._restore_on_deactivate

    def set_restore_on_deactivate(self, restore_on_deactivate):
        """Set the restore on deactivate flag."""
        self._restore_on_deactivate = restore_on_deactivate

    def register_callback(self, state_change_func, schedule_update_func):
        """Register callback."""
        self.schedule_update = schedule_update_func
        self.callback = state_change_func(
            self.hass, self.entities.keys(), self.update_callback
        )

    def unregister_callback(self):
        """Unregister callbacks."""
        if self.callback is not None:
            self.callback()
            self.callback = None

    async def update_callback(self, entity_id, old_state, new_state):
        """Update the scene when a tracked entity changes state."""
        self.store_entity_state(entity_id, self.states[entity_id])
        if self.is_interesting_update(old_state, new_state):
            await asyncio.sleep(self.debounce_time)
            self.schedule_update(True)

    def is_interesting_update(self, old_state, new_state):
        if not self.compare_values(old_state.state, new_state.state):
            return True
        
        if new_state.domain in ATTRIBUTES_TO_CHECK:
            entity_attrs = new_state.attributes
            old_entity_attrs = old_state.attributes
            for attribute in ATTRIBUTES_TO_CHECK.get(new_state.domain):
                if (
                    attribute not in old_entity_attrs
                    or attribute not in entity_attrs
                ):
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
        """Check the state of the scene."""
        for entity_id in self.entities:
            state = self.hass.states.get(entity_id)
            self.states[entity_id] = self.check_state(entity_id, state)
        self._is_on = all(self.states.values())

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
