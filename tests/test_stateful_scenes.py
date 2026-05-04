"""Tests for Stateful Scenes core classes (Scene and Hub)."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from homeassistant.core import HomeAssistant, ServiceCall

from custom_components.stateful_scenes.const import StatefulScenesYamlInvalid
from custom_components.stateful_scenes.StatefulScenes import (
    Hub,
    Scene,
    SceneEvaluationTimer,
)

from .const import (
    SCENE_CONF_FULL,
    SCENE_CONF_MINIMAL,
    SCENE_YAML_BOOL_STATES,
    SCENE_YAML_INVALID_NO_ENTITIES,
    SCENE_YAML_INVALID_NO_ID,
    SCENE_YAML_INVALID_NO_STATE,
    SCENE_YAML_RAW,
)


# --- Scene compare_values tests ---


class TestCompareValues:
    """Tests for Scene.compare_values method."""

    def _make_scene(self, hass: HomeAssistant) -> Scene:
        """Create a Scene instance for testing."""
        return Scene(hass, SCENE_CONF_MINIMAL)

    async def test_compare_strings_case_insensitive(self, hass: HomeAssistant):
        """Test string comparison is case-insensitive."""
        scene = self._make_scene(hass)
        assert scene.compare_values("on", "ON") is True
        assert scene.compare_values("Off", "off") is True
        assert scene.compare_values("on", "off") is False

    async def test_compare_numbers_within_tolerance(self, hass: HomeAssistant):
        """Test number comparison within tolerance."""
        scene = self._make_scene(hass)
        # Default tolerance is 1
        assert scene.compare_values(100, 100) is True
        assert scene.compare_values(100, 101) is True
        assert scene.compare_values(100, 99) is True

    async def test_compare_numbers_outside_tolerance(self, hass: HomeAssistant):
        """Test number comparison outside tolerance."""
        scene = self._make_scene(hass)
        assert scene.compare_values(100, 102) is False
        assert scene.compare_values(100, 98) is False

    async def test_compare_numbers_float(self, hass: HomeAssistant):
        """Test float number comparison."""
        scene = self._make_scene(hass)
        assert scene.compare_values(100.0, 100.5) is True
        assert scene.compare_values(100.0, 101.5) is False

    async def test_compare_dicts(self, hass: HomeAssistant):
        """Test recursive dict comparison."""
        scene = self._make_scene(hass)
        assert scene.compare_values({"a": 1, "b": 2}, {"a": 1, "b": 2}) is True
        assert scene.compare_values({"a": 1}, {"a": 5}) is False  # diff > tolerance
        assert scene.compare_values({"a": 1}, {"a": 1, "b": 2}) is True  # dict1 subset
        assert scene.compare_values({"a": "on"}, {"a": "off"}) is False

    async def test_compare_lists(self, hass: HomeAssistant):
        """Test list comparison."""
        scene = self._make_scene(hass)
        assert scene.compare_values([255, 0, 0], [255, 0, 0]) is True
        assert (
            scene.compare_values([255, 0, 0], [255, 0, 1]) is True
        )  # within tolerance
        assert scene.compare_values([255, 0, 0], [255, 0, 5]) is False

    async def test_compare_tuples(self, hass: HomeAssistant):
        """Test tuple comparison."""
        scene = self._make_scene(hass)
        assert scene.compare_values((1, 2), (1, 2)) is True
        assert scene.compare_values((1, 2), (1, 5)) is False

    async def test_compare_none_values(self, hass: HomeAssistant):
        """Test None comparisons."""
        scene = self._make_scene(hass)
        assert scene.compare_values(None, None) is True
        assert scene.compare_values(None, "on") is False
        assert scene.compare_values("on", None) is False

    async def test_compare_mixed_types(self, hass: HomeAssistant):
        """Test comparison of non-matching types falls through to ==."""
        scene = self._make_scene(hass)
        assert scene.compare_values(True, True) is True
        # Note: bool is subclass of int in Python, so True(1) vs False(0)
        # differ by 1, which is within default tolerance of 1
        assert scene.compare_values(True, False) is True
        # Values that truly differ
        assert scene.compare_values("on", "off") is False


# --- Scene state checking tests ---


class TestSceneStateChecking:
    """Tests for Scene state checking."""

    async def test_check_state_matching(self, hass: HomeAssistant, mock_light_entities):
        """Test entity state matches scene definition."""
        scene = Scene(hass, SCENE_CONF_MINIMAL)
        state = hass.states.get("light.test_light")

        # Set up matching state
        hass.states.async_set("light.test_light", "on", {"friendly_name": "Test Light"})
        state = hass.states.get("light.test_light")
        result = await scene.async_check_state("light.test_light", state)
        assert result is True

    async def test_check_state_not_matching(self, hass: HomeAssistant):
        """Test entity state does not match scene definition."""
        scene = Scene(hass, SCENE_CONF_MINIMAL)
        hass.states.async_set(
            "light.test_light", "off", {"friendly_name": "Test Light"}
        )
        state = hass.states.get("light.test_light")
        result = await scene.async_check_state("light.test_light", state)
        assert result is False

    async def test_check_state_unavailable_ignored(self, hass: HomeAssistant):
        """Test unavailable entity is ignored when ignore_unavailable is True."""
        scene = Scene(hass, SCENE_CONF_MINIMAL)
        scene.set_ignore_unavailable(True)
        hass.states.async_set("light.test_light", "unavailable", {})
        state = hass.states.get("light.test_light")
        result = await scene.async_check_state("light.test_light", state)
        assert result is None

    async def test_check_state_unavailable_not_ignored(self, hass: HomeAssistant):
        """Test unavailable entity is not matched when ignore_unavailable is False."""
        scene = Scene(hass, SCENE_CONF_MINIMAL)
        scene.set_ignore_unavailable(False)
        hass.states.async_set("light.test_light", "unavailable", {})
        state = hass.states.get("light.test_light")
        result = await scene.async_check_state("light.test_light", state)
        assert result is False

    async def test_check_all_states_all_on(
        self, hass: HomeAssistant, mock_light_entities
    ):
        """Test all entities matching means scene is on."""
        conf = SCENE_CONF_FULL.copy()
        conf["entities"] = {
            "light.living_room": {"state": "on", "brightness": 255},
            "light.bedroom": {"state": "off"},
        }
        scene = Scene(hass, conf)
        await scene.async_check_all_states()
        assert scene.is_on is True

    async def test_check_all_states_partial(
        self, hass: HomeAssistant, mock_light_entities
    ):
        """Test partial entity match means scene is off."""
        conf = SCENE_CONF_FULL.copy()
        conf["entities"] = {
            "light.living_room": {"state": "on", "brightness": 255},
            "light.bedroom": {"state": "on"},  # bedroom is actually off
        }
        scene = Scene(hass, conf)
        await scene.async_check_all_states()
        assert scene.is_on is False

    async def test_check_state_with_attributes(self, hass: HomeAssistant):
        """Test state check includes attributes for light domain."""
        hass.states.async_set(
            "light.living_room",
            "on",
            {"brightness": 200, "friendly_name": "Living Room"},
        )
        conf = SCENE_CONF_FULL.copy()
        conf["entities"] = {
            "light.living_room": {"state": "on", "brightness": 255},
        }
        scene = Scene(hass, conf)
        # Brightness 200 vs 255 is outside tolerance of 2
        state = hass.states.get("light.living_room")
        result = await scene.async_check_state("light.living_room", state)
        assert result is False

    async def test_check_state_ignore_attributes(self, hass: HomeAssistant):
        """Test state check ignores attributes when ignore_attributes is True."""
        hass.states.async_set(
            "light.living_room",
            "on",
            {"brightness": 200, "friendly_name": "Living Room"},
        )
        conf = SCENE_CONF_FULL.copy()
        conf["entities"] = {
            "light.living_room": {"state": "on", "brightness": 255},
        }
        scene = Scene(hass, conf)
        scene.set_ignore_attributes(True)
        state = hass.states.get("light.living_room")
        result = await scene.async_check_state("light.living_room", state)
        assert result is True


# --- Scene turn on/off tests ---


class TestSceneTurnOnOff:
    """Tests for Scene turn on/off."""

    async def test_turn_on(
        self, hass: HomeAssistant, service_calls: list[ServiceCall], mock_light_entities
    ):
        """Test turning on a scene calls the scene service."""
        hass.states.async_set(
            "scene.minimal",
            "scening",
            {"friendly_name": "Minimal Scene", "id": "minimal_1"},
        )
        scene = Scene(hass, SCENE_CONF_MINIMAL)

        await scene.async_turn_on()

        assert scene.is_on is True
        assert len(service_calls) >= 1
        # Find the scene.turn_on call
        scene_calls = [
            c for c in service_calls if c.domain == "scene" and c.service == "turn_on"
        ]
        assert len(scene_calls) == 1

    async def test_turn_off_restore(
        self, hass: HomeAssistant, service_calls: list[ServiceCall], mock_light_entities
    ):
        """Test turning off with restore calls scene.apply."""
        hass.states.async_set("light.test_light", "on", {"friendly_name": "Test"})
        scene = Scene(hass, SCENE_CONF_MINIMAL)
        scene.set_restore_on_deactivate(True)
        scene._is_on = True

        # Store some entity state
        await scene.async_store_entity_state("light.test_light")
        service_calls.clear()

        await scene.async_turn_off()

        assert scene.is_on is False
        # Should call scene.apply to restore
        scene_apply_calls = [
            c for c in service_calls if c.domain == "scene" and c.service == "apply"
        ]
        assert len(scene_apply_calls) == 1

    async def test_turn_off_with_off_scene(
        self, hass: HomeAssistant, service_calls: list[ServiceCall]
    ):
        """Test turning off with an off-scene activates that scene."""
        hass.states.async_set("light.test_light", "on", {})
        scene = Scene(hass, SCENE_CONF_MINIMAL)
        scene._is_on = True
        scene.set_off_scene("scene.off_scene")
        service_calls.clear()

        await scene.async_turn_off()

        assert scene.is_on is False
        scene_calls = [
            c for c in service_calls if c.domain == "scene" and c.service == "turn_on"
        ]
        assert len(scene_calls) == 1

    async def test_turn_off_entities(
        self, hass: HomeAssistant, service_calls: list[ServiceCall]
    ):
        """Test turning off without restore calls homeassistant.turn_off."""
        hass.states.async_set("light.test_light", "on", {})
        scene = Scene(hass, SCENE_CONF_MINIMAL)
        scene.set_restore_on_deactivate(False)
        scene._is_on = True
        service_calls.clear()

        await scene.async_turn_off()

        assert scene.is_on is False
        ha_calls = [
            c
            for c in service_calls
            if c.domain == "homeassistant" and c.service == "turn_off"
        ]
        assert len(ha_calls) == 1

    async def test_turn_off_when_already_off(
        self, hass: HomeAssistant, service_calls: list[ServiceCall]
    ):
        """Test turning off when scene is already off does nothing."""
        scene = Scene(hass, SCENE_CONF_MINIMAL)
        scene._is_on = False
        service_calls.clear()

        await scene.async_turn_off()

        assert len(service_calls) == 0


# --- Scene properties tests ---


class TestSceneProperties:
    """Tests for Scene properties."""

    async def test_scene_id_normal(self, hass: HomeAssistant):
        """Test scene ID for normal scenes."""
        scene = Scene(hass, SCENE_CONF_MINIMAL)
        assert scene.id == "minimal_1"

    async def test_scene_id_learned(self, hass: HomeAssistant):
        """Test scene ID for learned scenes has _learned suffix."""
        conf = SCENE_CONF_MINIMAL.copy()
        conf["learn"] = True
        scene = Scene(hass, conf)
        assert scene.id == "minimal_1_learned"

    async def test_scene_name(self, hass: HomeAssistant):
        """Test scene name property."""
        scene = Scene(hass, SCENE_CONF_MINIMAL)
        assert scene.name == "Minimal Scene"

    async def test_scene_area_id(self, hass: HomeAssistant):
        """Test scene area_id property."""
        scene = Scene(hass, SCENE_CONF_FULL)
        assert scene.area_id == "Living Room"

    async def test_scene_attributes(self, hass: HomeAssistant):
        """Test scene attributes property."""
        scene = Scene(hass, SCENE_CONF_FULL)
        attrs = scene.attributes
        assert attrs["friendly_name"] == "Full Scene"
        assert attrs["icon"] == "mdi:lightbulb"
        assert "light.living_room" in attrs["entity_id"]

    async def test_set_number_tolerance(self, hass: HomeAssistant):
        """Test setting number tolerance."""
        scene = Scene(hass, SCENE_CONF_MINIMAL)
        scene.set_number_tolerance(5)
        assert scene.number_tolerance == 5

    async def test_set_transition_time(self, hass: HomeAssistant):
        """Test setting transition time."""
        scene = Scene(hass, SCENE_CONF_MINIMAL)
        scene.set_transition_time(2.5)
        assert scene.transition_time == 2.5

    async def test_set_debounce_time(self, hass: HomeAssistant):
        """Test setting debounce time."""
        scene = Scene(hass, SCENE_CONF_MINIMAL)
        scene.set_debounce_time(1.0)
        assert scene.debounce_time == 1.0

    async def test_set_restore_on_deactivate(self, hass: HomeAssistant):
        """Test setting restore on deactivate."""
        scene = Scene(hass, SCENE_CONF_MINIMAL)
        scene.set_restore_on_deactivate(True)
        assert scene.restore_on_deactivate is True
        scene.set_restore_on_deactivate(False)
        assert scene.restore_on_deactivate is False

    async def test_set_ignore_unavailable(self, hass: HomeAssistant):
        """Test setting ignore unavailable."""
        scene = Scene(hass, SCENE_CONF_MINIMAL)
        scene.set_ignore_unavailable(True)
        assert scene.ignore_unavailable is True

    async def test_set_ignore_attributes(self, hass: HomeAssistant):
        """Test setting ignore attributes."""
        scene = Scene(hass, SCENE_CONF_MINIMAL)
        scene.set_ignore_attributes(True)
        assert scene.ignore_attributes is True


# --- SceneEvaluationTimer tests ---


class TestSceneEvaluationTimer:
    """Tests for SceneEvaluationTimer."""

    async def test_timer_not_active_initially(self, hass: HomeAssistant):
        """Test timer is not active on init."""
        timer = SceneEvaluationTimer(hass, 0.0, 0.0)
        assert timer.is_active() is False

    async def test_timer_starts_with_transition_time(self, hass: HomeAssistant):
        """Test timer starts when transition time > 0."""
        timer = SceneEvaluationTimer(hass, 1.0, 0.0)
        callback = AsyncMock()
        await timer.async_start(callback)
        assert timer.is_active() is True
        await timer.async_cancel_if_active()

    async def test_timer_does_not_start_with_zero_transition(self, hass: HomeAssistant):
        """Test timer does not start when both transition and debounce time are 0."""
        timer = SceneEvaluationTimer(hass, 0.0, 0.0)
        callback = AsyncMock()
        await timer.async_start(callback)
        assert timer.is_active() is False

    async def test_timer_starts_with_debounce_only(self, hass: HomeAssistant):
        """Test timer starts when transition time is 0 but debounce time > 0.

        Regression test for https://github.com/.../issues/233:
        When transition time was 0 but debounce time was set, the timer would
        not start, making debounce ineffective.
        """
        timer = SceneEvaluationTimer(hass, 0.0, 5.0)
        callback = AsyncMock()
        await timer.async_start(callback)
        assert timer.is_active() is True
        await timer.async_cancel_if_active()

    async def test_timer_duration_debounce_only(self, hass: HomeAssistant):
        """Test timer uses only debounce time when transition is 0."""
        timer = SceneEvaluationTimer(hass, 0.0, 3.0)
        callback = AsyncMock()
        await timer.async_start(callback)
        assert timer.is_active() is True
        await timer.async_cancel_if_active()

    async def test_timer_cancel(self, hass: HomeAssistant):
        """Test cancelling an active timer."""
        timer = SceneEvaluationTimer(hass, 1.0, 0.0)
        callback = AsyncMock()
        await timer.async_start(callback)
        assert timer.is_active() is True

        await timer.async_cancel_if_active()
        assert timer.is_active() is False

    async def test_timer_clear(self, hass: HomeAssistant):
        """Test clearing timer state."""
        timer = SceneEvaluationTimer(hass, 1.0, 0.0)
        callback = AsyncMock()
        await timer.async_start(callback)
        await timer.async_cancel_if_active()
        await timer.async_clear()
        assert timer.is_active() is False

    async def test_timer_set_transition_time(self, hass: HomeAssistant):
        """Test setting transition time."""
        timer = SceneEvaluationTimer(hass, 1.0, 0.0)
        timer.set_transition_time(2.5)
        assert timer.transition_time == 2.5

    async def test_timer_set_debounce_time(self, hass: HomeAssistant):
        """Test setting debounce time."""
        timer = SceneEvaluationTimer(hass, 1.0, 0.0)
        timer.set_debounce_time(0.5)
        assert timer.debounce_time == 0.5


# --- Hub tests ---


class TestHub:
    """Tests for Hub class."""

    async def test_hub_creation(self, hass: HomeAssistant, mock_scene_entities):
        """Test Hub creates scenes from config."""
        hub = Hub(hass, SCENE_YAML_RAW, number_tolerance=1)
        assert len(hub.scenes) == 2
        assert hub.scenes[0].name == "Test Scene 1"
        assert hub.scenes[1].name == "Test Scene 2"

    async def test_hub_validate_scene_valid(
        self, hass: HomeAssistant, mock_scene_entities
    ):
        """Test valid scene passes validation."""
        hub = Hub(hass, SCENE_YAML_RAW, number_tolerance=1)
        result = hub.validate_scene(SCENE_YAML_RAW[0])
        assert result is True

    async def test_hub_validate_scene_missing_entities(self, hass: HomeAssistant):
        """Test scene missing entities raises error."""
        with pytest.raises(StatefulScenesYamlInvalid, match="missing entities"):
            Hub(hass, SCENE_YAML_INVALID_NO_ENTITIES, number_tolerance=1)

    async def test_hub_validate_scene_missing_id(self, hass: HomeAssistant):
        """Test scene missing id raises error."""
        with pytest.raises(StatefulScenesYamlInvalid, match="missing id"):
            Hub(hass, SCENE_YAML_INVALID_NO_ID, number_tolerance=1)

    async def test_hub_validate_scene_missing_state(self, hass: HomeAssistant):
        """Test scene entity missing state raises error."""
        with pytest.raises(StatefulScenesYamlInvalid, match="missing state"):
            Hub(hass, SCENE_YAML_INVALID_NO_STATE, number_tolerance=1)

    async def test_hub_extract_scene_configuration(
        self, hass: HomeAssistant, mock_scene_entities
    ):
        """Test extracting scene configuration normalizes data."""
        hub = Hub(hass, SCENE_YAML_RAW, number_tolerance=1)
        config = hub.extract_scene_configuration(SCENE_YAML_RAW[0])

        assert config["name"] == "Test Scene 1"
        assert config["id"] == "1001"
        assert "light.living_room" in config["entities"]
        assert config["entities"]["light.living_room"]["state"] == "on"
        assert config["entities"]["light.living_room"]["brightness"] == 255

    async def test_hub_extract_scene_configuration_bool_states(
        self, hass: HomeAssistant
    ):
        """Test bool states are converted to on/off strings."""
        hass.states.async_set(
            "scene.bool_scene",
            "scening",
            {"friendly_name": "Bool Scene", "id": "bool_1"},
        )
        hub = Hub(hass, SCENE_YAML_BOOL_STATES, number_tolerance=1)
        config = hub.extract_scene_configuration(SCENE_YAML_BOOL_STATES[0])

        assert config["entities"]["light.test"]["state"] == "on"
        assert config["entities"]["switch.test"]["state"] == "off"

    async def test_hub_extract_filters_attributes(
        self, hass: HomeAssistant, mock_scene_entities
    ):
        """Test extract only keeps relevant attributes per domain."""
        hub = Hub(hass, SCENE_YAML_RAW, number_tolerance=1)
        config = hub.extract_scene_configuration(SCENE_YAML_RAW[1])

        # cover.blinds should have current_position
        assert "current_position" in config["entities"]["cover.blinds"]
        assert config["entities"]["cover.blinds"]["current_position"] == 75

    async def test_hub_get_available_scenes(
        self, hass: HomeAssistant, mock_scene_entities
    ):
        """Test getting available scenes list."""
        hub = Hub(hass, SCENE_YAML_RAW, number_tolerance=1)
        scenes = hub.get_available_scenes()
        assert len(scenes) == 2

    async def test_hub_number_tolerance(self, hass: HomeAssistant, mock_scene_entities):
        """Test hub passes number tolerance to scenes."""
        hub = Hub(hass, SCENE_YAML_RAW, number_tolerance=5)
        assert hub.scenes[0].number_tolerance == 5


# --- Scene learn_scene_states tests ---


class TestLearnSceneStates:
    """Tests for Scene.learn_scene_states static method."""

    async def test_learn_scene_states(self, hass: HomeAssistant, mock_light_entities):
        """Test learning current entity states."""
        entities = ["light.living_room", "light.bedroom"]
        result = Scene.learn_scene_states(hass, entities)

        assert "light.living_room" in result
        assert result["light.living_room"]["state"] == "on"
        assert "light.bedroom" in result
        assert result["light.bedroom"]["state"] == "off"
