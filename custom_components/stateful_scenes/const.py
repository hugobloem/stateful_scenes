"""Constants for the State Scene integration."""

DOMAIN = "stateful_scenes"

# Hub configuration
CONF_SCENE_PATH = "scene_path"
CONF_NUMBER_TOLERANCE = "number_tolerance"
CONF_RESTORE_STATES_ON_DEACTIVATE = "restore_states_on_deactivate"
CONF_TRANSITION_TIME = "transition_time"
CONF_EXTERNAL_SCENE_ACTIVE = "external_scene_active"
CONF_DEBOUNCE_TIME = "debounce_time"
CONF_ENABLE_DISCOVERY = "enable_discovery"

DEFAULT_SCENE_PATH = "scenes.yaml"
DEFAULT_NUMBER_TOLERANCE = 1
DEFAULT_RESTORE_STATES_ON_DEACTIVATE = False
DEFAULT_TRANSITION_TIME = 1
DEFAULT_EXTERNAL_SCENE_ACTIVE = False
DEFAULT_DEBOUNCE_TIME = 0.0
DEFAULT_ENABLE_DISCOVERY = True

DEBOUNCE_MIN = 0
DEBOUNCE_MAX = 300
DEBOUNCE_STEP = 0.1

# Scene configuration
CONF_SCENE_NAME = "name"
CONF_SCENE_LEARN = "learn"
CONF_SCENE_NUMBER_TOLERANCE = "number_tolerance"
CONF_SCENE_ENTITY_ID = "entity_id"
CONF_SCENE_ID = "id"
CONF_SCENE_AREA = "area"
CONF_SCENE_ENTITIES = "entities"
CONF_SCENE_ICON = "icon"


TOLERANCE_MIN = 0
TOLERANCE_MAX = 10
TOLERANCE_STEP = 1

TRANSITION_MIN = 0
TRANSITION_MAX = 300
TRANSITION_STEP = 0.5

ATTRIBUTES_TO_CHECK = {
    "light": {"brightness", "rgb_color", "effect"},
    "cover": {"current_position"},
    "media_player": {"volume_level", "source"},
    "fan": {"direction", "oscillating", "percentage"},
    "climate": {"system_mode", "temperature"},
}

DEVICE_INFO_MANUFACTURER = "Stateful Scenes"
