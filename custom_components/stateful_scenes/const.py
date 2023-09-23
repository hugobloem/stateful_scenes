"""Constants for the State Scene integration."""

DOMAIN = "stateful_scenes"

CONF_SCENE_PATH = "scene_path"
CONF_NUMBER_TOLERANCE = "number_tolerance"

DEFAULT_SCENE_PATH = "scenes.yaml"
DEFAULT_NUMBER_TOLERANCE = 1

ATTRIBUTES_TO_CHECK = {
    "light": {"brightness", "rgb_color"},
    "cover": {"position"},
    "media_player": {"volume_level", "source"},
    "fan": {"direction", "oscillating", "percentage"},
}

DEVICE_INFO_MANUFACTURER = "Stateful Scenes"
