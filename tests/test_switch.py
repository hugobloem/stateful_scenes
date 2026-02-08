"""Tests for the switch platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import yaml
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from custom_components.stateful_scenes.const import DOMAIN
from custom_components.stateful_scenes.StatefulScenes import Hub, Scene
from custom_components.stateful_scenes.switch import (
    IgnoreAttributes,
    IgnoreUnavailable,
    RestoreOnDeactivate,
    StatefulSceneSwitch,
    async_setup_entry,
)
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .const import MOCK_CONFIG_ENTRY_HUB, MOCK_SCENES_YAML


class TestSwitchPlatformSetup:
    """Test switch platform setup."""

    async def test_async_setup_entry_hub_mode(
        self, mock_hass: HomeAssistant, mock_config_entry_hub, mock_aiofiles_read
    ):
        """Test setting up switch platform in hub mode."""
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

        # Setup switch platform
        entities = []

        async def mock_add_entities(new_entities):
            entities.extend(new_entities)

        result = await async_setup_entry(
            mock_hass, mock_config_entry_hub, mock_add_entities
        )

        assert result is True
        # Should create 4 entities per scene: main switch + 3 config switches
        assert len(entities) == 8  # 2 scenes * 4 entities

        # Verify entity types
        main_switches = [e for e in entities if isinstance(e, StatefulSceneSwitch)]
        config_switches = [e for e in entities if not isinstance(e, StatefulSceneSwitch)]

        assert len(main_switches) == 2
        assert len(config_switches) == 6

    async def test_async_setup_entry_single_scene_mode(
        self, mock_hass: HomeAssistant, mock_config_entry_single
    ):
        """Test setting up switch platform for single scene."""
        mock_config_entry_single.add_to_hass(mock_hass)

        # Setup single scene
        scene = Scene(mock_hass, mock_config_entry_single.data)
        mock_hass.data.setdefault(DOMAIN, {})
        mock_hass.data[DOMAIN][mock_config_entry_single.entry_id] = scene

        entities = []

        async def mock_add_entities(new_entities):
            entities.extend(new_entities)

        result = await async_setup_entry(
            mock_hass, mock_config_entry_single, mock_add_entities
        )

        assert result is True
        # Should create 4 entities: main switch + 3 config switches
        assert len(entities) == 4

    async def test_async_setup_entry_invalid_data(
        self, mock_hass: HomeAssistant, mock_config_entry_hub
    ):
        """Test setup with invalid data in hass.data."""
        mock_config_entry_hub.add_to_hass(mock_hass)

        # Setup with invalid data type
        mock_hass.data.setdefault(DOMAIN, {})
        mock_hass.data[DOMAIN][mock_config_entry_hub.entry_id] = "invalid"

        entities = []

        async def mock_add_entities(new_entities):
            entities.extend(new_entities)

        result = await async_setup_entry(
            mock_hass, mock_config_entry_hub, mock_add_entities
        )

        assert result is False


class TestStatefulSceneSwitch:
    """Test StatefulSceneSwitch entity."""

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
            "entities": {
                "light.living_room": {"state": "on", "brightness": 255}
            },
            "number_tolerance": 1,
        }
        return Scene(mock_hass, scene_config)

    async def test_switch_initialization(
        self, mock_hass: HomeAssistant, scene
    ):
        """Test switch initialization."""
        switch = StatefulSceneSwitch(scene)

        assert switch._scene == scene
        assert switch.name == "Test Scene"
        assert switch.unique_id == "test_scene"
        assert switch.icon == "mdi:lightbulb"

    async def test_switch_is_on(self, mock_hass: HomeAssistant, scene):
        """Test switch is_on property."""
        switch = StatefulSceneSwitch(scene)

        scene._is_on = False
        assert switch.is_on is False

        scene._is_on = True
        assert switch.is_on is True

    async def test_switch_turn_on(self, mock_hass: HomeAssistant, scene):
        """Test turning on the switch."""
        switch = StatefulSceneSwitch(scene)

        scene.async_turn_on = AsyncMock()

        await switch.async_turn_on()

        scene.async_turn_on.assert_called_once()

    async def test_switch_turn_off(self, mock_hass: HomeAssistant, scene):
        """Test turning off the switch."""
        switch = StatefulSceneSwitch(scene)

        scene.async_turn_off = AsyncMock()

        await switch.async_turn_off()

        scene.async_turn_off.assert_called_once()

    async def test_switch_device_info(self, mock_hass: HomeAssistant, scene):
        """Test switch device info."""
        switch = StatefulSceneSwitch(scene)

        device_info = switch.device_info

        assert device_info is not None
        assert "identifiers" in device_info
        assert "name" in device_info
        assert "manufacturer" in device_info
        assert scene.id in str(device_info["identifiers"])

    async def test_switch_extra_state_attributes(
        self, mock_hass: HomeAssistant, scene
    ):
        """Test switch extra state attributes."""
        switch = StatefulSceneSwitch(scene)

        scene.entity_id = "scene.test_scene"
        attrs = switch.extra_state_attributes

        assert "entity_id" in attrs
        assert attrs["entity_id"] == "scene.test_scene"

    async def test_switch_async_added_to_hass(
        self, mock_hass: HomeAssistant, scene
    ):
        """Test switch added to hass."""
        switch = StatefulSceneSwitch(scene)
        switch.hass = mock_hass

        scene.async_register_callback = AsyncMock()
        scene.callback_funcs = {}

        await switch.async_added_to_hass()

        # Verify callbacks were registered
        assert "schedule_update_func" in scene.callback_funcs
        assert "state_change_func" in scene.callback_funcs
        scene.async_register_callback.assert_called_once()

    async def test_switch_async_will_remove_from_hass(
        self, mock_hass: HomeAssistant, scene
    ):
        """Test switch removed from hass."""
        switch = StatefulSceneSwitch(scene)

        scene.async_unregister_callback = AsyncMock()

        await switch.async_will_remove_from_hass()

        scene.async_unregister_callback.assert_called_once()


class TestRestoreOnDeactivate:
    """Test RestoreOnDeactivate configuration switch."""

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

    async def test_restore_switch_initialization(
        self, mock_hass: HomeAssistant, scene
    ):
        """Test restore switch initialization."""
        switch = RestoreOnDeactivate(scene)

        assert switch._scene == scene
        assert switch.name == "Test Scene Restore on Deactivate"
        assert switch.unique_id == "test_scene_restore_on_deactivate"

    async def test_restore_switch_is_on(
        self, mock_hass: HomeAssistant, scene
    ):
        """Test restore switch is_on property."""
        switch = RestoreOnDeactivate(scene)

        scene.set_restore_on_deactivate(False)
        assert switch.is_on is False

        scene.set_restore_on_deactivate(True)
        assert switch.is_on is True

    async def test_restore_switch_turn_on(
        self, mock_hass: HomeAssistant, scene
    ):
        """Test turning on restore switch."""
        switch = RestoreOnDeactivate(scene)

        await switch.async_turn_on()

        assert scene.restore_on_deactivate is True

    async def test_restore_switch_turn_off(
        self, mock_hass: HomeAssistant, scene
    ):
        """Test turning off restore switch."""
        switch = RestoreOnDeactivate(scene)

        await switch.async_turn_off()

        assert scene.restore_on_deactivate is False


class TestIgnoreUnavailable:
    """Test IgnoreUnavailable configuration switch."""

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

    async def test_ignore_unavailable_initialization(
        self, mock_hass: HomeAssistant, scene
    ):
        """Test ignore unavailable switch initialization."""
        switch = IgnoreUnavailable(scene)

        assert switch._scene == scene
        assert switch.name == "Test Scene Ignore Unavailable"
        assert switch.unique_id == "test_scene_ignore_unavailable"

    async def test_ignore_unavailable_is_on(
        self, mock_hass: HomeAssistant, scene
    ):
        """Test ignore unavailable switch is_on property."""
        switch = IgnoreUnavailable(scene)

        scene.set_ignore_unavailable(False)
        assert switch.is_on is False

        scene.set_ignore_unavailable(True)
        assert switch.is_on is True

    async def test_ignore_unavailable_turn_on(
        self, mock_hass: HomeAssistant, scene
    ):
        """Test turning on ignore unavailable switch."""
        switch = IgnoreUnavailable(scene)

        await switch.async_turn_on()

        assert scene.ignore_unavailable is True

    async def test_ignore_unavailable_turn_off(
        self, mock_hass: HomeAssistant, scene
    ):
        """Test turning off ignore unavailable switch."""
        switch = IgnoreUnavailable(scene)

        await switch.async_turn_off()

        assert scene.ignore_unavailable is False


class TestIgnoreAttributes:
    """Test IgnoreAttributes configuration switch."""

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

    async def test_ignore_attributes_initialization(
        self, mock_hass: HomeAssistant, scene
    ):
        """Test ignore attributes switch initialization."""
        switch = IgnoreAttributes(scene)

        assert switch._scene == scene
        assert switch.name == "Test Scene Ignore Attributes"
        assert switch.unique_id == "test_scene_ignore_attributes"

    async def test_ignore_attributes_is_on(
        self, mock_hass: HomeAssistant, scene
    ):
        """Test ignore attributes switch is_on property."""
        switch = IgnoreAttributes(scene)

        scene.set_ignore_attributes(False)
        assert switch.is_on is False

        scene.set_ignore_attributes(True)
        assert switch.is_on is True

    async def test_ignore_attributes_turn_on(
        self, mock_hass: HomeAssistant, scene
    ):
        """Test turning on ignore attributes switch."""
        switch = IgnoreAttributes(scene)

        await switch.async_turn_on()

        assert scene.ignore_attributes is True

    async def test_ignore_attributes_turn_off(
        self, mock_hass: HomeAssistant, scene
    ):
        """Test turning off ignore attributes switch."""
        switch = IgnoreAttributes(scene)

        await switch.async_turn_off()

        assert scene.ignore_attributes is False
