"""Tests for the number platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import yaml
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from custom_components.stateful_scenes.const import DOMAIN
from custom_components.stateful_scenes.number import (
    DebounceTime,
    Tolerance,
    TransitionNumber,
    async_setup_entry,
)
from custom_components.stateful_scenes.StatefulScenes import Hub, Scene
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .const import MOCK_CONFIG_ENTRY_HUB, MOCK_SCENES_YAML


class TestNumberPlatformSetup:
    """Test number platform setup."""

    async def test_async_setup_entry_hub_mode(
        self, mock_hass: HomeAssistant, mock_config_entry_hub, mock_aiofiles_read
    ):
        """Test setting up number platform in hub mode."""
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

        # Should create 3 number entities per scene: transition, debounce, tolerance
        assert len(entities) == 6  # 2 scenes * 3 entities

        # Verify entity types
        transition_entities = [e for e in entities if isinstance(e, TransitionNumber)]
        debounce_entities = [e for e in entities if isinstance(e, DebounceTime)]
        tolerance_entities = [e for e in entities if isinstance(e, Tolerance)]

        assert len(transition_entities) == 2
        assert len(debounce_entities) == 2
        assert len(tolerance_entities) == 2

    async def test_async_setup_entry_single_scene_mode(
        self, mock_hass: HomeAssistant, mock_config_entry_single
    ):
        """Test setting up number platform for single scene."""
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

        # Should create 3 number entities
        assert len(entities) == 3


class TestTransitionNumber:
    """Test TransitionNumber entity."""

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

    async def test_transition_number_initialization(
        self, mock_hass: HomeAssistant, scene
    ):
        """Test transition number initialization."""
        number = TransitionNumber(scene)

        assert number._scene == scene
        assert number.name == "Test Scene Transition Time"
        assert number.unique_id == "test_scene_transition_time"
        assert number.native_min_value == 0
        assert number.native_max_value == 300
        assert number.native_step == 0.5
        assert number.native_unit_of_measurement == "s"

    async def test_transition_number_native_value(
        self, mock_hass: HomeAssistant, scene
    ):
        """Test transition number native_value property."""
        number = TransitionNumber(scene)

        scene.set_transition_time(2.5)
        assert number.native_value == 2.5

        scene.set_transition_time(0.0)
        assert number.native_value == 0.0

    async def test_transition_number_set_value(
        self, mock_hass: HomeAssistant, scene
    ):
        """Test setting transition number value."""
        number = TransitionNumber(scene)
        number.hass = mock_hass

        await number.async_set_native_value(5.0)

        assert scene.transition_time == 5.0

    async def test_transition_number_device_info(
        self, mock_hass: HomeAssistant, scene
    ):
        """Test transition number device info."""
        number = TransitionNumber(scene)

        device_info = number.device_info

        assert device_info is not None
        assert "identifiers" in device_info
        assert scene.id in str(device_info["identifiers"])

    async def test_transition_number_state_restoration(
        self, mock_hass: HomeAssistant, scene
    ):
        """Test transition number state restoration."""
        number = TransitionNumber(scene)
        number.hass = mock_hass

        # Mock last state
        with patch.object(
            number, "async_get_last_number_data", return_value=MagicMock(native_value=3.5)
        ):
            await number.async_added_to_hass()

        assert scene.transition_time == 3.5


class TestDebounceTime:
    """Test DebounceTime entity."""

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

    async def test_debounce_time_initialization(
        self, mock_hass: HomeAssistant, scene
    ):
        """Test debounce time initialization."""
        number = DebounceTime(scene)

        assert number._scene == scene
        assert number.name == "Test Scene Debounce Time"
        assert number.unique_id == "test_scene_debounce_time"
        assert number.native_min_value == 0
        assert number.native_max_value == 300
        assert number.native_step == 0.1

    async def test_debounce_time_native_value(
        self, mock_hass: HomeAssistant, scene
    ):
        """Test debounce time native_value property."""
        number = DebounceTime(scene)

        scene.set_debounce_time(1.5)
        assert number.native_value == 1.5

        scene.set_debounce_time(0.0)
        assert number.native_value == 0.0

    async def test_debounce_time_set_value(
        self, mock_hass: HomeAssistant, scene
    ):
        """Test setting debounce time value."""
        number = DebounceTime(scene)
        number.hass = mock_hass

        await number.async_set_native_value(2.0)

        assert scene.debounce_time == 2.0

    async def test_debounce_time_device_info(
        self, mock_hass: HomeAssistant, scene
    ):
        """Test debounce time device info."""
        number = DebounceTime(scene)

        device_info = number.device_info

        assert device_info is not None
        assert "identifiers" in device_info
        assert scene.id in str(device_info["identifiers"])

    async def test_debounce_time_state_restoration(
        self, mock_hass: HomeAssistant, scene
    ):
        """Test debounce time state restoration."""
        number = DebounceTime(scene)
        number.hass = mock_hass

        # Mock last state
        with patch.object(
            number, "async_get_last_number_data", return_value=MagicMock(native_value=0.5)
        ):
            await number.async_added_to_hass()

        assert scene.debounce_time == 0.5


class TestTolerance:
    """Test Tolerance entity."""

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

    async def test_tolerance_number_initialization(
        self, mock_hass: HomeAssistant, scene
    ):
        """Test tolerance number initialization."""
        number = Tolerance(scene)

        assert number._scene == scene
        assert number.name == "Test Scene Tolerance"
        assert number.unique_id == "test_scene_tolerance"
        assert number.native_min_value == 0
        assert number.native_max_value == 20
        assert number.native_step == 1

    async def test_tolerance_number_native_value(
        self, mock_hass: HomeAssistant, scene
    ):
        """Test tolerance number native_value property."""
        number = Tolerance(scene)

        scene.set_number_tolerance(5)
        assert number.native_value == 5

        scene.set_number_tolerance(1)
        assert number.native_value == 1

    async def test_tolerance_number_set_value(
        self, mock_hass: HomeAssistant, scene
    ):
        """Test setting tolerance number value."""
        number = Tolerance(scene)
        number.hass = mock_hass

        await number.async_set_native_value(10)

        assert scene.number_tolerance == 10

    async def test_tolerance_number_device_info(
        self, mock_hass: HomeAssistant, scene
    ):
        """Test tolerance number device info."""
        number = Tolerance(scene)

        device_info = number.device_info

        assert device_info is not None
        assert "identifiers" in device_info
        assert scene.id in str(device_info["identifiers"])

    async def test_tolerance_number_state_restoration(
        self, mock_hass: HomeAssistant, scene
    ):
        """Test tolerance number state restoration."""
        number = Tolerance(scene)
        number.hass = mock_hass

        # Mock last state
        with patch.object(
            number, "async_get_last_number_data", return_value=MagicMock(native_value=7)
        ):
            await number.async_added_to_hass()

        assert scene.number_tolerance == 7

    async def test_tolerance_number_no_restoration(
        self, mock_hass: HomeAssistant, scene
    ):
        """Test tolerance number when no previous state exists."""
        number = Tolerance(scene)
        number.hass = mock_hass

        original_tolerance = scene.number_tolerance

        # Mock no last state
        with patch.object(number, "async_get_last_number_data", return_value=None):
            await number.async_added_to_hass()

        # Should keep original value
        assert scene.number_tolerance == original_tolerance
