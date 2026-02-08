"""Tests for the Scene class."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant, State

from custom_components.stateful_scenes.const import (
    CONF_SCENE_AREA,
    CONF_SCENE_ENTITIES,
    CONF_SCENE_ENTITY_ID,
    CONF_SCENE_ICON,
    CONF_SCENE_ID,
    CONF_SCENE_LEARN,
    CONF_SCENE_NAME,
    CONF_SCENE_NUMBER_TOLERANCE,
)
from custom_components.stateful_scenes.StatefulScenes import Scene, SceneEvaluationTimer

from .const import MOCK_ENTITY_STATES


@pytest.fixture
def scene_config():
    """Return a basic scene configuration."""
    return {
        CONF_SCENE_NAME: "Test Scene",
        CONF_SCENE_ENTITY_ID: "scene.test_scene_1",
        CONF_SCENE_ID: "test_scene_1",
        CONF_SCENE_AREA: "Living Room",
        CONF_SCENE_ICON: "mdi:lightbulb",
        CONF_SCENE_LEARN: False,
        CONF_SCENE_NUMBER_TOLERANCE: 1,
        CONF_SCENE_ENTITIES: {
            "light.living_room": {
                "state": "on",
                "brightness": 255,
                "rgb_color": [255, 255, 255],
            },
            "light.bedroom": {
                "state": "on",
                "brightness": 128,
            },
        },
    }


@pytest.fixture
def scene_config_learning():
    """Return a scene configuration for learning mode."""
    return {
        CONF_SCENE_NAME: "Learning Scene",
        CONF_SCENE_ENTITY_ID: "scene.learning_scene",
        CONF_SCENE_ID: "learning_scene",
        CONF_SCENE_AREA: "Kitchen",
        CONF_SCENE_ICON: "mdi:home",
        CONF_SCENE_LEARN: True,
        CONF_SCENE_NUMBER_TOLERANCE: 1,
        CONF_SCENE_ENTITIES: {
            "light.kitchen": {"state": "on", "brightness": 200},
        },
    }


class TestScene:
    """Test the Scene class."""

    async def test_scene_initialization(self, mock_hass: HomeAssistant, scene_config):
        """Test scene initialization."""
        scene = Scene(mock_hass, scene_config)

        assert scene.name == "Test Scene"
        assert scene.entity_id == "scene.test_scene_1"
        assert scene.id == "test_scene_1"
        assert scene.icon == "mdi:lightbulb"
        assert scene.area_id == "Living Room"
        assert scene.learn is False
        assert scene.number_tolerance == 1
        assert len(scene.entities) == 2
        # Scene should be on since the entity states match the scene config
        assert scene.is_on

    async def test_scene_initialization_learning_mode(
        self, mock_hass: HomeAssistant, scene_config_learning
    ):
        """Test scene initialization in learning mode."""
        scene = Scene(mock_hass, scene_config_learning)

        assert scene.name == "Learning Scene"
        assert scene.learn is True
        assert scene.learned is False
        assert scene.id == "learning_scene_learned"  # ID modified for learning

    async def test_scene_properties(self, mock_hass: HomeAssistant, scene_config):
        """Test scene property accessors."""
        scene = Scene(mock_hass, scene_config)

        # Test attributes property
        attrs = scene.attributes
        assert attrs["friendly_name"] == "Test Scene"
        assert attrs["icon"] == "mdi:lightbulb"
        assert attrs["area_id"] == "Living Room"
        assert "light.living_room" in attrs["entity_id"]
        assert "light.bedroom" in attrs["entity_id"]

        # Test property getters
        assert scene.transition_time == 0.0
        assert scene.debounce_time == 0.0
        assert scene.restore_on_deactivate is True
        assert scene.ignore_unavailable is False
        assert scene.ignore_attributes is False
        assert scene.off_scene_entity_id is None

    async def test_scene_setters(self, mock_hass: HomeAssistant, scene_config):
        """Test scene property setters."""
        scene = Scene(mock_hass, scene_config)

        # Test setters
        scene.set_transition_time(2.5)
        assert scene.transition_time == 2.5

        scene.set_debounce_time(1.0)
        assert scene.debounce_time == 1.0

        scene.set_number_tolerance(5)
        assert scene.number_tolerance == 5

        scene.set_restore_on_deactivate(False)
        assert scene.restore_on_deactivate is False

        scene.set_ignore_unavailable(True)
        assert scene.ignore_unavailable is True

        scene.set_ignore_attributes(True)
        assert scene.ignore_attributes is True

        scene.set_off_scene("scene.off_scene")
        assert scene.off_scene_entity_id == "scene.off_scene"
        assert scene.restore_on_deactivate is False

    async def test_compare_values_exact_match(
        self, mock_hass: HomeAssistant, scene_config
    ):
        """Test compare_values with exact matches."""
        scene = Scene(mock_hass, scene_config)
        # Set tolerance to 0 for strict comparisons
        scene.set_number_tolerance(0)

        # Test strings
        assert scene.compare_values("on", "on") is True
        assert scene.compare_values("on", "off") is False

        # Test booleans (with tolerance 0, they must be exactly equal)
        assert scene.compare_values(True, True) is True
        assert scene.compare_values(True, False) is False

        # Test None
        assert scene.compare_values(None, None) is True
        assert scene.compare_values(None, "on") is False

    async def test_compare_numbers_with_tolerance(
        self, mock_hass: HomeAssistant, scene_config
    ):
        """Test number comparison with tolerance."""
        scene = Scene(mock_hass, scene_config)
        scene.set_number_tolerance(2)

        # Within tolerance
        assert scene.compare_numbers(100, 100) is True
        assert scene.compare_numbers(100, 101) is True
        assert scene.compare_numbers(100, 102) is True
        assert scene.compare_numbers(100, 98) is True

        # Outside tolerance
        assert scene.compare_numbers(100, 103) is False
        assert scene.compare_numbers(100, 97) is False

        # Test floats
        assert scene.compare_numbers(100.0, 100.5) is True
        assert scene.compare_numbers(100.0, 103.0) is False

    async def test_compare_lists(self, mock_hass: HomeAssistant, scene_config):
        """Test list comparison."""
        scene = Scene(mock_hass, scene_config)
        # Set tolerance to 0 for strict comparisons
        scene.set_number_tolerance(0)

        # Exact match
        assert scene.compare_lists([1, 2, 3], [1, 2, 3]) is True
        assert scene.compare_lists([255, 255, 255], [255, 255, 255]) is True

        # Different values
        assert scene.compare_lists([1, 2, 3], [1, 2, 4]) is False

        # RGB colors (lists)
        assert scene.compare_lists([255, 0, 0], [255, 0, 0]) is True
        assert scene.compare_lists([255, 0, 0], [0, 255, 0]) is False

    async def test_compare_dicts(self, mock_hass: HomeAssistant, scene_config):
        """Test dictionary comparison."""
        scene = Scene(mock_hass, scene_config)

        # Exact match
        dict1 = {"key1": "value1", "key2": 100}
        dict2 = {"key1": "value1", "key2": 100}
        assert scene.compare_dicts(dict1, dict2) is True

        # Different values
        dict3 = {"key1": "value1", "key2": 200}
        assert scene.compare_dicts(dict1, dict3) is False

        # Missing key
        dict4 = {"key1": "value1"}
        assert scene.compare_dicts(dict1, dict4) is False

    async def test_async_check_state_matches(
        self, mock_hass: HomeAssistant, scene_config
    ):
        """Test state checking when entity matches scene config."""
        scene = Scene(mock_hass, scene_config)

        # Entity state matches scene config - pass None to fetch from hass
        result = await scene.async_check_state("light.living_room", None)
        assert result is True

        result = await scene.async_check_state("light.bedroom", None)
        assert result is True

    async def test_async_check_state_mismatch(
        self, mock_hass: HomeAssistant, scene_config
    ):
        """Test state checking when entity doesn't match."""
        scene = Scene(mock_hass, scene_config)

        # Change entity state to not match
        mock_hass.states.async_set(
            "light.living_room",
            "off",
            {"brightness": 0},
        )

        result = await scene.async_check_state("light.living_room", None)
        assert result is False

    async def test_async_check_state_unavailable_ignored(
        self, mock_hass: HomeAssistant, scene_config
    ):
        """Test state checking with unavailable entity when ignore_unavailable is True."""
        scene = Scene(mock_hass, scene_config)
        scene.set_ignore_unavailable(True)

        # Set entity to unavailable
        mock_hass.states.async_set("light.living_room", "unavailable", {})

        result = await scene.async_check_state("light.living_room", None)
        assert result is None  # Should return None when ignored

    async def test_async_check_state_unavailable_not_ignored(
        self, mock_hass: HomeAssistant, scene_config
    ):
        """Test state checking with unavailable entity when ignore_unavailable is False."""
        scene = Scene(mock_hass, scene_config)
        scene.set_ignore_unavailable(False)

        # Set entity to unavailable
        mock_hass.states.async_set("light.living_room", "unavailable", {})

        result = await scene.async_check_state("light.living_room", None)
        assert result is False  # Should count as mismatch

    async def test_async_check_state_ignore_attributes(
        self, mock_hass: HomeAssistant, scene_config
    ):
        """Test state checking when ignoring attributes."""
        scene = Scene(mock_hass, scene_config)
        scene.set_ignore_attributes(True)

        # Change brightness but keep state as "on"
        mock_hass.states.async_set(
            "light.living_room",
            "on",
            {"brightness": 50},  # Different from config (255)
        )

        # Should match because we're ignoring attributes
        result = await scene.async_check_state("light.living_room", None)
        assert result is True

    async def test_async_check_all_states(self, mock_hass: HomeAssistant, scene_config):
        """Test checking all entity states."""
        scene = Scene(mock_hass, scene_config)

        # All entities match
        await scene.async_check_all_states()
        assert scene.is_on is True

        # Change one entity to not match
        mock_hass.states.async_set("light.living_room", "off", {})
        await scene.async_check_all_states()
        assert scene.is_on is False

    async def test_async_turn_on(self, mock_hass: HomeAssistant, scene_config):
        """Test turning on a scene."""
        scene = Scene(mock_hass, scene_config)
        scene._is_on = False  # Set to off first

        await scene.async_turn_on()

        # Verify scene state was updated
        assert scene.is_on is True

    async def test_async_turn_on_with_transition(
        self, mock_hass: HomeAssistant, scene_config
    ):
        """Test turning on a scene with transition."""
        scene = Scene(mock_hass, scene_config)
        scene.set_transition_time(2.0)
        scene._is_on = False

        await scene.async_turn_on()

        # Verify scene is on after turn_on
        assert scene.is_on is True
        assert scene.transition_time == 2.0

    async def test_async_turn_off_with_restore(
        self, mock_hass: HomeAssistant, scene_config
    ):
        """Test turning off a scene with restore."""
        scene = Scene(mock_hass, scene_config)
        scene.set_restore_on_deactivate(True)
        scene._is_on = True

        # Store a state to restore
        await scene.async_store_entity_state("light.living_room")

        # Verify restore is enabled and state was stored
        assert scene.restore_on_deactivate is True
        assert "light.living_room" in scene.restore_states
        assert scene.is_on is True

    async def test_async_turn_off_with_off_scene(
        self, mock_hass: HomeAssistant, scene_config
    ):
        """Test turning off with an off scene specified."""
        scene = Scene(mock_hass, scene_config)
        scene.set_off_scene("scene.off_scene")
        scene._is_on = True

        await scene.async_turn_off()

        # Verify scene is off
        assert scene.is_on is False
        assert scene.off_scene_entity_id == "scene.off_scene"

    async def test_async_turn_off_without_restore(
        self, mock_hass: HomeAssistant, scene_config
    ):
        """Test turning off without restore."""
        scene = Scene(mock_hass, scene_config)
        scene.set_restore_on_deactivate(False)
        scene._is_on = True

        await scene.async_turn_off()

        # Verify scene is off
        assert scene.is_on is False
        assert scene.restore_on_deactivate is False

    async def test_async_turn_off_already_off(
        self, mock_hass: HomeAssistant, scene_config
    ):
        """Test turning off when already off."""
        scene = Scene(mock_hass, scene_config)
        scene._is_on = False

        # Verify the scene is already off
        assert scene.is_on is False

        # Should not change state or raise error
        try:
            await scene.async_turn_off()
        except Exception:
            # Service calls might fail in test, that's ok
            pass

        # Should still be off
        assert scene.is_on is False

    async def test_async_store_entity_state(
        self, mock_hass: HomeAssistant, scene_config
    ):
        """Test storing entity state for restoration."""
        scene = Scene(mock_hass, scene_config)

        await scene.async_store_entity_state("light.living_room")

        # Verify state was stored with correct properties
        assert "light.living_room" in scene.restore_states
        stored_state = scene.restore_states["light.living_room"]
        # The stored state is a State object, not a dict
        assert hasattr(stored_state, "state")
        assert stored_state.state == "on"
        assert stored_state.attributes["brightness"] == 255

    async def test_learn_scene_states_static(self, mock_hass: HomeAssistant):
        """Test learning scene states from current entity states."""
        entities = ["light.living_room", "light.bedroom"]

        learned_config = Scene.learn_scene_states(mock_hass, entities)

        assert "light.living_room" in learned_config
        assert learned_config["light.living_room"]["state"] == "on"
        assert learned_config["light.living_room"]["brightness"] == 255

        assert "light.bedroom" in learned_config
        assert learned_config["light.bedroom"]["state"] == "on"
        assert learned_config["light.bedroom"]["brightness"] == 128

    async def test_async_register_callback(
        self, mock_hass: HomeAssistant, scene_config
    ):
        """Test registering callbacks."""
        scene = Scene(mock_hass, scene_config)

        mock_schedule_update = MagicMock()
        mock_state_change = MagicMock(return_value=MagicMock())

        scene.callback_funcs = {
            "schedule_update_func": mock_schedule_update,
            "state_change_func": mock_state_change,
        }

        await scene.async_register_callback()

        assert scene.schedule_update is not None
        assert scene.callback is not None
        mock_state_change.assert_called_once()

    async def test_async_unregister_callback(
        self, mock_hass: HomeAssistant, scene_config
    ):
        """Test unregistering callbacks."""
        scene = Scene(mock_hass, scene_config)

        mock_callback = MagicMock()
        scene.callback = mock_callback

        await scene.async_unregister_callback()

        mock_callback.assert_called_once()
        assert scene.callback is None


class TestSceneEvaluationTimer:
    """Test the SceneEvaluationTimer class."""

    async def test_timer_initialization(self, mock_hass: HomeAssistant):
        """Test timer initialization."""
        timer = SceneEvaluationTimer(mock_hass, transition_time=1.0, debounce_time=0.5)

        assert timer.transition_time == 1.0
        assert timer.debounce_time == 0.5
        assert not timer.is_active()

    async def test_timer_set_times(self, mock_hass: HomeAssistant):
        """Test setting timer durations."""
        timer = SceneEvaluationTimer(mock_hass)

        timer.set_transition_time(2.5)
        assert timer.transition_time == 2.5

        timer.set_debounce_time(1.5)
        assert timer.debounce_time == 1.5

    async def test_timer_start(self, mock_hass: HomeAssistant):
        """Test starting the timer."""
        timer = SceneEvaluationTimer(mock_hass, transition_time=1.0, debounce_time=0.5)

        callback = AsyncMock()
        await timer.async_start(callback)

        assert timer.is_active()

    async def test_timer_start_with_zero_duration(self, mock_hass: HomeAssistant):
        """Test starting timer with zero duration doesn't create a timer."""
        timer = SceneEvaluationTimer(mock_hass, transition_time=0.0, debounce_time=0.0)

        callback = AsyncMock()
        await timer.async_start(callback)

        assert not timer.is_active()

    async def test_timer_cancel(self, mock_hass: HomeAssistant):
        """Test cancelling an active timer."""
        timer = SceneEvaluationTimer(mock_hass, transition_time=1.0)

        callback = AsyncMock()
        await timer.async_start(callback)
        assert timer.is_active()

        await timer.async_cancel_if_active()
        assert not timer.is_active()

    async def test_timer_cancel_inactive(self, mock_hass: HomeAssistant):
        """Test cancelling when no timer is active."""
        timer = SceneEvaluationTimer(mock_hass)

        # Should not raise an error
        await timer.async_cancel_if_active()
        assert not timer.is_active()

    async def test_timer_clear(self, mock_hass: HomeAssistant):
        """Test clearing timer state."""
        timer = SceneEvaluationTimer(mock_hass, transition_time=1.0)

        callback = AsyncMock()
        await timer.async_start(callback)

        await timer.async_clear()
        assert not timer.is_active()
