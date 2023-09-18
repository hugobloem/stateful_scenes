import yaml
from homeassistant.core import HomeAssistant
import logging
from .const import ATTRIBUTES_TO_CHECK

_LOGGER = logging.getLogger(__name__)


class Hub:
    """State scene class."""

    def __init__(
        self, hass: HomeAssistant, scene_path: str, number_tolerance=1
    ) -> None:
        """Initialize."""
        self.scene_path = scene_path
        self.number_tolerance = number_tolerance
        self.hass = hass
        self.scenes = []

        scene_confs = self.load_scenes()
        for scene_conf in scene_confs:
            self.scenes.append(
                Scene(
                    self.hass,
                    self.extract_scene_configuration(scene_conf),
                    self.number_tolerance,
                )
            )

    def load_scenes(self) -> list:
        """Load scenes from yaml file."""
        with open(self.scene_path, "r", encoding="ascii") as f:
            scenes_confs = yaml.load(f, Loader=yaml.FullLoader)

        if scenes_confs is None:
            raise IOError("No scenes found in " + self.scene_path)

        return scenes_confs

    def extract_scene_configuration(self, scene_conf) -> dict:
        """Extract entities and attributes from a scene."""
        entities = {}
        for entity_id, scene_attributes in scene_conf["entities"].items():
            domain = entity_id.split(".")[0]
            attributes = {"state": scene_attributes["state"]}

            if domain in ATTRIBUTES_TO_CHECK:
                for attribute, value in scene_attributes.items():
                    if attribute in ATTRIBUTES_TO_CHECK.get(domain):
                        attributes[attribute] = value

            entities[entity_id] = attributes

        return {
            "name": scene_conf["name"],
            "id": scene_conf["id"],
            "entities": entities,
        }


class Scene:
    def __init__(
        self, hass: HomeAssistant, scene_conf: dict, number_tolerance=1
    ) -> None:
        """Initialize."""
        self.hass = hass
        self.number_tolerance = number_tolerance
        self.name = scene_conf["name"]
        self.id = scene_conf["id"]
        self.entities = scene_conf["entities"]
        self._is_on = None

        self.callback = None
        self.schedule_update = None
        self.states = {entity_id: False for entity_id in self.entities.keys()}

    @property
    def is_on(self):
        """Return true if the scene is on."""
        return self._is_on

    def turn_on(self):
        """Turn on the scene."""
        self.hass.services.call(
            domain="scene",
            service="turn_on",
            target={"entity_id": "scene." + self.name.lower().replace(" ", "_")},
        )
        self._is_on = True

    def turn_off(self):
        """Turn off all entities in the scene."""
        self.hass.services.call(
            domain="homeassistant",
            service="turn_off",
            target={"entity_id": self.entities.keys()},
        )
        self._is_on = False

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

    def update_callback(self, entity_id, old_state, new_state):
        """Update the scene when a tracked entity changes state."""
        self.check_state(entity_id, new_state)
        self._is_on = all(self.states.values())
        self.schedule_update(True)

    def check_state(self, entity_id, new_state):
        """Check the state of the scene."""
        if new_state is None:
            _LOGGER.warning("Entity not found: %(entity_id)s", entity_id=entity_id)
            self.states[entity_id] = False

        # Check state
        if not self.compare_values(self.entities[entity_id]["state"], new_state.state):
            _LOGGER.debug(
                "[%s] state not matching: %s: %s != %s.",
                self.name,
                entity_id,
                self.entities[entity_id]["state"],
                new_state.state,
            )
            self.states[entity_id] = False
            return

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
                        "[%s] attribute not matching: %s %s: %s %s.",
                        self.name,
                        entity_id,
                        attribute,
                        self.entities[entity_id][attribute],
                        entity_attrs[attribute],
                    )
                    self.states[entity_id] = False
                    return

        self.states[entity_id] = True

    def check_all_states(self):
        """Check the state of the scene."""
        for entity_id in self.entities.keys():
            state = self.hass.states.get(entity_id)
            self.check_state(entity_id, state)

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
