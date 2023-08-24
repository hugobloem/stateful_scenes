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

        self.load_scenes()

    def load_scenes(self) -> bool:
        with open(self.scene_path, "r") as f:
            scenes_confs = yaml.load(f, Loader=yaml.FullLoader)

        if scenes_confs is None:
            raise Exception("No scenes found in " + self.scene_path)

        for scene_conf in scenes_confs:
            self.scenes.append(Scene(self.hass, scene_conf, self.number_tolerance))


class Scene:
    def __init__(
        self, hass: HomeAssistant, scene_conf: dict, number_tolerance=1
    ) -> None:
        """Initialize."""
        self.hass = hass
        self.scene_conf = scene_conf
        self.number_tolerance = number_tolerance
        self.name = scene_conf["name"]
        self.id = scene_conf["id"]
        self._is_on = None
        self.update()

    @property
    def is_on(self):
        return self._is_on

    def update(self):
        self._is_on = self.get_state()

    def turn_on(self, **kwargs):
        self.hass.services.call(
            domain="scene",
            service="turn_on",
            target={"entity_id": "scene." + self.name.lower().replace(" ", "_")},
        )
        self._is_on = True

    def turn_off(self, **kwargs):
        self.hass.services.call(
            domain="homeassistant",
            service="turn_off",
            target={"entity_id": self.scene_conf["entities"].keys()},
        )
        self._is_on = False

    def get_state(self):
        for entity, attributes in self.scene_conf["entities"].items():
            ent_state = self.hass.states.get(entity)
            if ent_state is None:
                _LOGGER.warning("Entity not found: " + entity)
                return None
            ent_attrs = ent_state.attributes
            if not self.compare_values(attributes["state"], ent_state.state):
                _LOGGER.debug(
                    "Entity state not matching: "
                    + entity
                    + " "
                    + attributes["state"]
                    + " "
                    + ent_state.state
                )
                return False
            for attribute in ATTRIBUTES_TO_CHECK.get(ent_state.domain):
                if attribute not in attributes:
                    continue
                value = attributes[attribute]
                if not self.compare_values(value, ent_attrs[attribute]):
                    _LOGGER.debug(
                        "Entity attribute not matching: "
                        + entity
                        + " "
                        + str(attribute)
                        + " "
                        + str(value)
                        + " "
                        + str(ent_attrs[attribute])
                    )
                    return False
        return True

    def compare_values(self, value1, value2):
        if isinstance(value1, dict):
            if isinstance(value2, dict):
                for key, value in value1.items():
                    if key not in value2:
                        return False
                    if not self.compare_values(value, value2[key]):
                        return False
                return True
            else:
                return False
        elif isinstance(value1, list) or isinstance(value1, tuple):
            if isinstance(value2, list) or isinstance(value2, tuple):
                for value in value1:
                    if value not in value2:
                        return False
                return True
            else:
                return False
        elif isinstance(value1, int) or isinstance(value1, float):
            if isinstance(value2, int) or isinstance(value2, float):
                return (value1 - value2) <= self.number_tolerance
            else:
                return False
        else:
            return value1 == value2
