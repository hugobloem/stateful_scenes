"""Constants for Stateful Scenes tests."""

from custom_components.stateful_scenes.const import (
    CONF_DEBOUNCE_TIME,
    CONF_ENABLE_DISCOVERY,
    CONF_IGNORE_UNAVAILABLE,
    CONF_NUMBER_TOLERANCE,
    CONF_RESTORE_STATES_ON_DEACTIVATE,
    CONF_SCENE_PATH,
    CONF_TRANSITION_TIME,
)

SCENES_YAML_CONTENT = """- id: '1001'
  name: Test Scene 1
  entities:
    light.living_room:
      state: 'on'
      brightness: 255
    light.bedroom:
      state: 'off'
- id: '1002'
  name: Test Scene 2
  entities:
    light.living_room:
      state: 'on'
      brightness: 128
    cover.blinds:
      state: 'open'
      current_position: 75
"""

MOCK_HUB_DATA = {
    CONF_SCENE_PATH: "scenes.yaml",
    CONF_NUMBER_TOLERANCE: 1,
    CONF_RESTORE_STATES_ON_DEACTIVATE: False,
    CONF_TRANSITION_TIME: 1.0,
    CONF_DEBOUNCE_TIME: 0.0,
    CONF_IGNORE_UNAVAILABLE: False,
    CONF_ENABLE_DISCOVERY: False,
    "hub": True,
}

MOCK_EXTERNAL_SCENE_DATA = {
    "name": "External Scene",
    "entity_id": "scene.external_test",
    "id": "ext_1001",
    "area": None,
    "learn": True,
    "icon": None,
    "number_tolerance": 1,
    "entities": {
        "light.living_room": {"state": "on", "brightness": 200},
        "light.bedroom": {"state": "off"},
    },
    "hub": False,
}

SCENE_CONF_MINIMAL = {
    "name": "Minimal Scene",
    "entity_id": "scene.minimal",
    "id": "minimal_1",
    "area": None,
    "learn": False,
    "icon": None,
    "number_tolerance": 1,
    "entities": {
        "light.test_light": {"state": "on"},
    },
}

SCENE_CONF_FULL = {
    "name": "Full Scene",
    "entity_id": "scene.full",
    "id": "full_1",
    "area": "Living Room",
    "learn": False,
    "icon": "mdi:lightbulb",
    "number_tolerance": 2,
    "entities": {
        "light.living_room": {"state": "on", "brightness": 255, "rgb_color": [255, 0, 0]},
        "light.bedroom": {"state": "off"},
        "cover.blinds": {"state": "open", "current_position": 100},
    },
}

SCENE_YAML_RAW = [
    {
        "id": "1001",
        "name": "Test Scene 1",
        "entities": {
            "light.living_room": {
                "state": "on",
                "brightness": 255,
            },
            "light.bedroom": {
                "state": "off",
            },
        },
    },
    {
        "id": "1002",
        "name": "Test Scene 2",
        "entities": {
            "light.living_room": {
                "state": "on",
                "brightness": 128,
            },
            "cover.blinds": {
                "state": "open",
                "current_position": 75,
            },
        },
    },
]

SCENE_YAML_BOOL_STATES = [
    {
        "id": "bool_1",
        "name": "Bool Scene",
        "entities": {
            "light.test": {
                "state": True,
                "brightness": 128,
            },
            "switch.test": {
                "state": False,
            },
        },
    },
]

SCENE_YAML_INVALID_NO_ENTITIES = [
    {
        "id": "invalid_1",
        "name": "Invalid Scene",
    },
]

SCENE_YAML_INVALID_NO_ID = [
    {
        "name": "Invalid Scene",
        "entities": {
            "light.test": {"state": "on"},
        },
    },
]

SCENE_YAML_INVALID_NO_STATE = [
    {
        "id": "invalid_3",
        "name": "Invalid Scene",
        "entities": {
            "light.test": {"brightness": 128},
        },
    },
]
