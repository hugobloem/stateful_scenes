"""Constants for the State Scene integration."""

DOMAIN = "stateful_scenes"

CONF_SCENE_PATH = "scene_path"
CONF_NUMBER_TOLERANCE = "number_tolerance"
CONF_RESTORE_STATES_ON_DEACTIVATE = "restore_states_on_deactivate"
CONF_TRANSITION_TIME = "transition_time"

DEFAULT_SCENE_PATH = "scenes.yaml"
DEFAULT_NUMBER_TOLERANCE = 1
DEFAULT_RESTORE_STATES_ON_DEACTIVATE = False
DEFAULT_TRANSITION_TIME = 1

TOLERANCE_MIN = 0
TOLERANCE_MAX = 10
TOLERANCE_STEP = 1

TRANSITION_MIN = 0
TRANSITION_MAX = 300
TRANSITION_STEP = 0.5

ATTRIBUTES_TO_CHECK = {
    "light": {"brightness", "rgb_color", "effect"},
    "cover": {"position"},
    "media_player": {"volume_level", "source"},
    "fan": {"direction", "oscillating", "percentage"},
}

DEVICE_INFO_MANUFACTURER = "Stateful Scenes"
