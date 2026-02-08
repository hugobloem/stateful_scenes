"""Tests for the select platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import yaml
from homeassistant.core import HomeAssistant

from custom_components.stateful_scenes.const import DOMAIN
from custom_components.stateful_scenes.select import (
    StatefulSceneOffSelect,
    async_setup_entry,
)
from custom_components.stateful_scenes.StatefulScenes import Hub, Scene
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .const import MOCK_CONFIG_ENTRY_HUB, MOCK_SCENES_YAML


class TestSelectPlatformSetup:
    """Test select platform setup."""

    async def test_async_setup_entry_hub_mode(
        self, mock_hass: HomeAssistant, mock_config_entry_hub, mock_aiofiles_read
    ):
        """Test setting up select platform in hub mode."""
        mock_config_entry_hub.add_to_hass(mock_hass)

        # Setup hub
        with patch(
            "custom_components.stateful_scenes.load_scenes_file",
            return_value=yaml.safe_load(MOCK_SCENES_YAML),
        ):
            hub = Hub(
                hass=mock_hass,
                scene_confs=yaml.safe_load(MOCK_SCENES_YAML),
                number_tolerance=1,
            )
            mock_hass.data.setdefault(DOMAIN, {})
            mock_hass.data[DOMAIN][mock_config_entry_hub.entry_id] = hub

        entities = []

        async def mock_add_entities(new_entities):
            entities.extend(new_entities)

        await async_setup_entry(mock_hass, mock_config_entry_hub, mock_add_entities)

        # Should create 1 select entity per scene
        assert len(entities) == 2

        # Verify all are StatefulSceneOffSelect
        assert all(isinstance(e, StatefulSceneOffSelect) for e in entities)

    async def test_async_setup_entry_single_scene_mode(
        self, mock_hass: HomeAssistant, mock_config_entry_single
    ):
        """Test setting up select platform for single scene."""
        mock_config_entry_single.add_to_hass(mock_hass)

        # Setup single scene
        scene = Scene(mock_hass, mock_config_entry_single.data)
        mock_hass.data.setdefault(DOMAIN, {})
        mock_hass.data[DOMAIN][mock_config_entry_single.entry_id] = scene

        entities = []

        async def mock_add_entities(new_entities):
            entities.extend(new_entities)

        await async_setup_entry(
            mock_hass, mock_config_entry_single, mock_add_entities
        )

        # Should create 1 select entity
        assert len(entities) == 1


class TestStatefulSceneOffSelect:
    """Test StatefulSceneOffSelect entity."""

    @pytest.fixture
    def scene(self, mock_hass: HomeAssistant):
        """Create a test scene."""
        scene_config = {
            "name": "Test Scene",
            "entity_id": "scene.test_scene",
            "id": "test_scene",
            "icon": "mdi:lightbulb",
            "area": "Living Room",
            "learn": False,
            "entities": {"light.living_room": {"state": "on"}},
            "number_tolerance": 1,
        }
        return Scene(mock_hass, scene_config)

    @pytest.fixture
    def hub(self, mock_hass: HomeAssistant):
        """Create a test hub."""
        scene_confs = yaml.safe_load(MOCK_SCENES_YAML)
        return Hub(hass=mock_hass, scene_confs=scene_confs, number_tolerance=1)

    async def test_select_initialization(
        self, mock_hass: HomeAssistant, scene, hub
    ):
        """Test select initialization."""
        select = StatefulSceneOffSelect(scene, hub)

        assert select._scene == scene
        assert select._hub == hub
        assert select.name == "Test Scene Off Scene"
        assert select.unique_id == "test_scene_off_scene"
        assert "None" in select.options

    async def test_select_initialization_standalone(
        self, mock_hass: HomeAssistant, scene
    ):
        """Test select initialization without hub (standalone)."""
        select = StatefulSceneOffSelect(scene, None)

        assert select._scene == scene
        assert select._hub is None
        assert select.name == "Test Scene Off Scene"

    async def test_select_current_option(
        self, mock_hass: HomeAssistant, scene, hub
    ):
        """Test select current_option property."""
        select = StatefulSceneOffSelect(scene, hub)

        # Initial value should be None
        assert select.current_option == "None"

    async def test_select_device_info(
        self, mock_hass: HomeAssistant, scene, hub
    ):
        """Test select device info."""
        select = StatefulSceneOffSelect(scene, hub)

        device_info = select.device_info

        assert device_info is not None
        assert "identifiers" in device_info
        assert scene.id in str(device_info["identifiers"])

    async def test_select_async_added_to_hass(
        self, mock_hass: HomeAssistant, scene, hub
    ):
        """Test select added to hass."""
        select = StatefulSceneOffSelect(scene, hub)
        select.hass = mock_hass

        # Mock methods
        select._async_get_available_off_scenes = AsyncMock(
            return_value=[
                ("scene.off_scene_1", "Off Scene 1"),
                ("scene.off_scene_2", "Off Scene 2"),
            ]
        )

        await select.async_added_to_hass()

        # Verify options were populated
        assert len(select.options) > 1
        assert "None" in select.options

    async def test_get_available_off_scenes_with_hub(
        self, mock_hass: HomeAssistant, scene, hub
    ):
        """Test getting available off scenes with hub."""
        select = StatefulSceneOffSelect(scene, hub)
        select.hass = mock_hass

        available_scenes = await select._async_get_available_off_scenes()

        # Should return scenes from hub excluding current scene
        assert len(available_scenes) > 0
        # Current scene should not be in the list
        entity_ids = [s[0] for s in available_scenes]
        assert scene.entity_id not in entity_ids

    async def test_get_available_off_scenes_standalone(
        self, mock_hass: HomeAssistant, scene
    ):
        """Test getting available off scenes in standalone mode."""
        select = StatefulSceneOffSelect(scene, None)
        select.hass = mock_hass

        available_scenes = await select._async_get_available_off_scenes()

        # Should return all scene entities from hass except current scene
        assert isinstance(available_scenes, list)

    async def test_select_option(
        self, mock_hass: HomeAssistant, scene, hub
    ):
        """Test selecting an option."""
        select = StatefulSceneOffSelect(scene, hub)
        select.hass = mock_hass

        # Add some options first
        select._entity_id_map = {
            "None": "None",
            "Off Scene 1": "scene.off_scene_1",
            "Off Scene 2": "scene.off_scene_2",
        }
        select._attr_options = ["None", "Off Scene 1", "Off Scene 2"]

        # Select an off scene
        await select.async_select_option("Off Scene 1")

        assert scene.off_scene_entity_id == "scene.off_scene_1"

    async def test_select_none_option(
        self, mock_hass: HomeAssistant, scene, hub
    ):
        """Test selecting None option."""
        select = StatefulSceneOffSelect(scene, hub)
        select.hass = mock_hass

        # Set an off scene first
        scene.set_off_scene("scene.some_scene")
        assert scene.off_scene_entity_id == "scene.some_scene"

        # Select None
        await select.async_select_option("None")

        assert scene.off_scene_entity_id is None

    async def test_select_state_restoration(
        self, mock_hass: HomeAssistant, scene, hub
    ):
        """Test select state restoration."""
        select = StatefulSceneOffSelect(scene, hub)
        select.hass = mock_hass

        # Mock last state
        mock_last_state = MagicMock()
        mock_last_state.state = "Off Scene 1"

        with patch.object(select, "async_get_last_state", return_value=mock_last_state):
            select._entity_id_map = {
                "None": "None",
                "Off Scene 1": "scene.off_scene_1",
            }
            select._attr_options = ["None", "Off Scene 1"]
            select._async_get_available_off_scenes = AsyncMock(
                return_value=[("scene.off_scene_1", "Off Scene 1")]
            )

            await select.async_added_to_hass()

        # Should restore the previous selection
        assert select.current_option == "Off Scene 1"

    async def test_select_restore_on_deactivate_interaction(
        self, mock_hass: HomeAssistant, scene, hub
    ):
        """Test that selecting off scene disables restore on deactivate."""
        select = StatefulSceneOffSelect(scene, hub)
        select.hass = mock_hass

        # Enable restore first
        scene.set_restore_on_deactivate(True)
        assert scene.restore_on_deactivate is True

        # Add options
        select._entity_id_map = {
            "None": "None",
            "Off Scene": "scene.off_scene",
        }
        select._attr_options = ["None", "Off Scene"]

        # Select an off scene
        await select.async_select_option("Off Scene")

        # Restore should be disabled
        assert scene.restore_on_deactivate is False

    async def test_select_update_on_scene_change(
        self, mock_hass: HomeAssistant, scene, hub
    ):
        """Test select updates when scene list changes."""
        select = StatefulSceneOffSelect(scene, hub)
        select.hass = mock_hass

        # Initial scenes
        initial_scenes = [("scene.off_1", "Off 1")]
        select._async_get_available_off_scenes = AsyncMock(
            return_value=initial_scenes
        )

        await select.async_added_to_hass()
        initial_option_count = len(select.options)

        # Simulate scene list change
        updated_scenes = [
            ("scene.off_1", "Off 1"),
            ("scene.off_2", "Off 2"),
            ("scene.off_3", "Off 3"),
        ]
        select._async_get_available_off_scenes = AsyncMock(
            return_value=updated_scenes
        )

        # Trigger update
        await select._async_update_off_scenes()

        # Options should be updated
        assert len(select.options) > initial_option_count
