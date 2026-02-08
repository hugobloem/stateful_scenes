"""Tests for the Hub class."""

from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant

from custom_components.stateful_scenes.const import (
    ATTRIBUTES_TO_CHECK,
    StatefulScenesYamlInvalid,
)
from custom_components.stateful_scenes.StatefulScenes import Hub

from .const import MOCK_SCENE_CONFIG_1, MOCK_SCENE_CONFIG_2


class TestHub:
    """Test the Hub class."""

    async def test_hub_initialization(self, mock_hass: HomeAssistant, mock_scenes_data):
        """Test hub initialization with scene configurations."""
        hub = Hub(hass=mock_hass, scene_confs=mock_scenes_data, number_tolerance=1)

        assert hub.number_tolerance == 1
        assert len(hub.scenes) == 2
        assert len(hub.scene_confs) == 2
        assert hub.hass == mock_hass

    async def test_hub_initialization_custom_tolerance(
        self, mock_hass: HomeAssistant, mock_scenes_data
    ):
        """Test hub initialization with custom tolerance."""
        hub = Hub(hass=mock_hass, scene_confs=mock_scenes_data, number_tolerance=5)

        assert hub.number_tolerance == 5
        # Scenes should inherit hub tolerance if not specified
        for scene in hub.scenes:
            assert scene.number_tolerance == 5

    async def test_validate_scene_valid(
        self, mock_hass: HomeAssistant, mock_scenes_data
    ):
        """Test scene validation with valid configuration."""
        hub = Hub(hass=mock_hass, scene_confs=[], number_tolerance=1)

        # Valid scene config
        valid_config = mock_scenes_data[0]
        assert hub.validate_scene(valid_config) is True

    async def test_validate_scene_missing_entities(self, mock_hass: HomeAssistant):
        """Test scene validation with missing entities."""
        hub = Hub(hass=mock_hass, scene_confs=[], number_tolerance=1)

        invalid_config = {
            "id": "test_scene",
            "name": "Test Scene",
            # Missing entities key
        }

        with pytest.raises(
            StatefulScenesYamlInvalid, match="Scene is missing entities"
        ):
            hub.validate_scene(invalid_config)

    async def test_validate_scene_missing_id(self, mock_hass: HomeAssistant):
        """Test scene validation with missing id."""
        hub = Hub(hass=mock_hass, scene_confs=[], number_tolerance=1)

        invalid_config = {
            "name": "Test Scene",
            "entities": {"light.test": {"state": "on"}},
            # Missing id key
        }

        with pytest.raises(StatefulScenesYamlInvalid, match="Scene is missing id"):
            hub.validate_scene(invalid_config)

    async def test_validate_scene_missing_entity_state(self, mock_hass: HomeAssistant):
        """Test scene validation with missing entity state."""
        hub = Hub(hass=mock_hass, scene_confs=[], number_tolerance=1)

        invalid_config = {
            "id": "test_scene",
            "name": "Test Scene",
            "entities": {
                "light.test": {
                    "brightness": 255,
                    # Missing state key
                }
            },
        }

        with pytest.raises(
            StatefulScenesYamlInvalid, match="Scene is missing state for entity"
        ):
            hub.validate_scene(invalid_config)

    async def test_extract_scene_configuration(
        self, mock_hass: HomeAssistant, mock_scenes_data
    ):
        """Test extracting scene configuration."""
        hub = Hub(hass=mock_hass, scene_confs=[], number_tolerance=1)

        scene_conf = mock_scenes_data[0]
        extracted = hub.extract_scene_configuration(scene_conf)

        assert extracted["name"] == "Test Scene 1"
        assert extracted["id"] == "test_scene_1"
        assert extracted["learn"] is False
        assert extracted["number_tolerance"] == 1
        assert "light.living_room" in extracted["entities"]
        assert "light.bedroom" in extracted["entities"]

    async def test_extract_scene_configuration_with_attributes(
        self, mock_hass: HomeAssistant, mock_scenes_data
    ):
        """Test extracting scene configuration with entity attributes."""
        hub = Hub(hass=mock_hass, scene_confs=[], number_tolerance=1)

        scene_conf = mock_scenes_data[0]
        extracted = hub.extract_scene_configuration(scene_conf)

        # Check light entity attributes
        light_config = extracted["entities"]["light.living_room"]
        assert light_config["state"] == "on"
        assert light_config["brightness"] == 255
        assert light_config["rgb_color"] == [255, 255, 255]

        # Check that only relevant attributes are included
        assert "state" in light_config
        assert "brightness" in light_config  # In ATTRIBUTES_TO_CHECK for light

    async def test_extract_scene_configuration_boolean_state_conversion(
        self, mock_hass: HomeAssistant
    ):
        """Test boolean state values are converted to strings."""
        hub = Hub(hass=mock_hass, scene_confs=[], number_tolerance=1)

        scene_conf = {
            "id": "test_bool",
            "name": "Bool Test",
            "entities": {
                "switch.test": {
                    "state": True,  # Boolean instead of string
                }
            },
        }

        extracted = hub.extract_scene_configuration(scene_conf)

        # Boolean should be converted to string
        assert extracted["entities"]["switch.test"]["state"] == "on"

        scene_conf["entities"]["switch.test"]["state"] = False
        extracted = hub.extract_scene_configuration(scene_conf)
        assert extracted["entities"]["switch.test"]["state"] == "off"

    async def test_extract_scene_configuration_filters_none_values(
        self, mock_hass: HomeAssistant
    ):
        """Test that None attribute values are filtered out."""
        hub = Hub(hass=mock_hass, scene_confs=[], number_tolerance=1)

        scene_conf = {
            "id": "test_none",
            "name": "None Test",
            "entities": {
                "light.test": {
                    "state": "on",
                    "brightness": None,  # Should be filtered
                    "rgb_color": [255, 255, 255],
                }
            },
        }

        extracted = hub.extract_scene_configuration(scene_conf)

        light_config = extracted["entities"]["light.test"]
        assert light_config["state"] == "on"
        assert light_config["rgb_color"] == [255, 255, 255]
        assert "brightness" not in light_config  # None should be filtered

    async def test_extract_scene_configuration_domain_filtering(
        self, mock_hass: HomeAssistant
    ):
        """Test that only domain-specific attributes are extracted."""
        hub = Hub(hass=mock_hass, scene_confs=[], number_tolerance=1)

        scene_conf = {
            "id": "test_domains",
            "name": "Domain Test",
            "entities": {
                "light.test": {
                    "state": "on",
                    "brightness": 200,  # Valid for light
                    "volume_level": 0.5,  # Not valid for light (media_player attr)
                },
                "media_player.test": {
                    "state": "playing",
                    "volume_level": 0.7,  # Valid for media_player
                    "brightness": 100,  # Not valid for media_player
                },
            },
        }

        extracted = hub.extract_scene_configuration(scene_conf)

        # Light should only have brightness, not volume_level
        light_config = extracted["entities"]["light.test"]
        assert "brightness" in light_config
        assert "volume_level" not in light_config

        # Media player should only have volume_level, not brightness
        media_config = extracted["entities"]["media_player.test"]
        assert "volume_level" in media_config
        assert "brightness" not in media_config

    async def test_extract_scene_configuration_custom_tolerance(
        self, mock_hass: HomeAssistant
    ):
        """Test scene-specific tolerance overrides hub tolerance."""
        hub = Hub(hass=mock_hass, scene_confs=[], number_tolerance=5)

        scene_conf = {
            "id": "test_tolerance",
            "name": "Tolerance Test",
            "number_tolerance": 10,  # Scene-specific tolerance
            "entities": {"light.test": {"state": "on"}},
        }

        extracted = hub.extract_scene_configuration(scene_conf)

        # Scene tolerance should override hub tolerance
        assert extracted["number_tolerance"] == 10

    def test_prepare_external_scene(self, mock_hass: HomeAssistant):
        """Test preparing external scene configuration."""
        hub = Hub(hass=mock_hass, scene_confs=[], number_tolerance=1)

        entity_id = "scene.external_scene"
        entities = {"light.kitchen": {"state": "on", "brightness": 200}}

        prepared = hub.prepare_external_scene(entity_id, entities)

        assert prepared["name"] == "External Scene"
        assert prepared["entity_id"] == entity_id
        assert prepared["learn"] is True
        assert prepared["entities"] == entities
        assert "id" in prepared
        assert "icon" in prepared
        assert "area" in prepared

    async def test_get_available_scenes(
        self, mock_hass: HomeAssistant, mock_scenes_data
    ):
        """Test getting list of available scenes."""
        hub = Hub(hass=mock_hass, scene_confs=mock_scenes_data, number_tolerance=1)

        available_scenes = hub.get_available_scenes()

        assert len(available_scenes) == 2
        assert "scene.test_scene_1" in available_scenes
        assert "scene.test_scene_2" in available_scenes

    async def test_get_scene_by_entity_id(
        self, mock_hass: HomeAssistant, mock_scenes_data
    ):
        """Test getting a scene by entity ID."""
        hub = Hub(hass=mock_hass, scene_confs=mock_scenes_data, number_tolerance=1)

        scene = hub.get_scene("scene.test_scene_1")

        assert scene is not None
        assert scene.entity_id == "scene.test_scene_1"
        assert scene.name == "Test Scene 1"

    async def test_get_scene_not_found(
        self, mock_hass: HomeAssistant, mock_scenes_data
    ):
        """Test getting a scene that doesn't exist."""
        hub = Hub(hass=mock_hass, scene_confs=mock_scenes_data, number_tolerance=1)

        scene = hub.get_scene("scene.nonexistent")

        assert scene is None

    async def test_hub_multiple_scenes_management(
        self, mock_hass: HomeAssistant, mock_scenes_data
    ):
        """Test hub manages multiple scenes correctly."""
        hub = Hub(hass=mock_hass, scene_confs=mock_scenes_data, number_tolerance=1)

        # Verify all scenes are created
        assert len(hub.scenes) == 2

        # Verify each scene is properly configured
        scene1 = hub.get_scene("scene.test_scene_1")
        assert scene1.name == "Test Scene 1"
        assert len(scene1.entities) == 3

        scene2 = hub.get_scene("scene.test_scene_2")
        assert scene2.name == "Test Scene 2"
        assert len(scene2.entities) == 3

    async def test_hub_with_empty_scenes(self, mock_hass: HomeAssistant):
        """Test hub with no scenes."""
        hub = Hub(hass=mock_hass, scene_confs=[], number_tolerance=1)

        assert len(hub.scenes) == 0
        assert len(hub.scene_confs) == 0
        assert hub.get_available_scenes() == []

    async def test_hub_scenes_inherit_tolerance(self, mock_hass: HomeAssistant):
        """Test that scenes without specific tolerance inherit from hub."""
        scene_conf = {
            "id": "test_scene",
            "name": "Test Scene",
            "entities": {"light.test": {"state": "on"}},
            # No number_tolerance specified
        }

        hub = Hub(hass=mock_hass, scene_confs=[scene_conf], number_tolerance=8)

        scene = hub.scenes[0]
        assert scene.number_tolerance == 8  # Should inherit from hub
