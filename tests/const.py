"""Constants for tests."""

# Sample scene configurations for testing
MOCK_SCENE_CONFIG_1 = {
    "id": "test_scene_1",
    "name": "Test Scene 1",
    "icon": "mdi:lightbulb",
    "entities": {
        "light.living_room": {
            "state": "on",
            "brightness": 255,
            "rgb_color": [255, 255, 255],
        },
        "light.bedroom": {
            "state": "on",
            "brightness": 128,
        },
        "switch.fan": {
            "state": "on",
        },
    },
}

MOCK_SCENE_CONFIG_2 = {
    "id": "test_scene_2",
    "name": "Test Scene 2",
    "icon": "mdi:weather-night",
    "entities": {
        "light.living_room": {
            "state": "off",
        },
        "light.bedroom": {
            "state": "on",
            "brightness": 50,
        },
        "cover.garage": {
            "state": "closed",
            "current_position": 0,
        },
    },
}

MOCK_SCENE_CONFIG_EXTERNAL = {
    "id": "external_scene",
    "name": "External Scene",
    "entity_id": "scene.external_scene",
    "icon": "mdi:home",
    "learn": True,
    "entities": {
        "light.kitchen": {
            "state": "on",
            "brightness": 200,
        },
    },
}

# Sample entity states for testing
MOCK_ENTITY_STATES = {
    "light.living_room": {
        "state": "on",
        "attributes": {
            "brightness": 255,
            "rgb_color": [255, 255, 255],
            "friendly_name": "Living Room Light",
        },
    },
    "light.bedroom": {
        "state": "on",
        "attributes": {
            "brightness": 128,
            "friendly_name": "Bedroom Light",
        },
    },
    "switch.fan": {
        "state": "on",
        "attributes": {
            "friendly_name": "Fan",
        },
    },
    "light.kitchen": {
        "state": "on",
        "attributes": {
            "brightness": 200,
            "friendly_name": "Kitchen Light",
        },
    },
    "cover.garage": {
        "state": "closed",
        "attributes": {
            "current_position": 0,
            "friendly_name": "Garage Door",
        },
    },
}

# Mock config entry data
MOCK_CONFIG_ENTRY_HUB = {
    "scene_path": "scenes.yaml",
    "number_tolerance": 1,
    "restore_states_on_deactivate": False,
    "transition_time": 1,
    "debounce_time": 0.0,
    "ignore_unavailable": False,
    "enable_discovery": True,
}

MOCK_CONFIG_ENTRY_SINGLE = {
    "name": "External Scene",
    "id": "external_scene",
    "entity_id": "scene.external_scene",
    "icon": "mdi:home",
    "area": "Living Room",
    "learn": True,
    "entities": {"light.kitchen": {"state": "on", "brightness": 200}},
    "number_tolerance": 1,
}

# Sample scenes.yaml content
MOCK_SCENES_YAML = """
- id: test_scene_1
  name: Test Scene 1
  icon: mdi:lightbulb
  entities:
    light.living_room:
      state: on
      brightness: 255
      rgb_color: [255, 255, 255]
    light.bedroom:
      state: on
      brightness: 128
    switch.fan:
      state: on

- id: test_scene_2
  name: Test Scene 2
  icon: mdi:weather-night
  entities:
    light.living_room:
      state: off
    light.bedroom:
      state: on
      brightness: 50
    cover.garage:
      state: closed
      current_position: 0
"""

MOCK_INVALID_SCENES_YAML = """
- name: Invalid Scene
  entities:
    light.test:
      brightness: 100
"""

MOCK_SCENES_NO_ENTITIES = """
- id: bad_scene
  name: Bad Scene
"""
