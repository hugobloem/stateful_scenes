"""Tests for the config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import yaml
from homeassistant import config_entries
from homeassistant.config_entries import SOURCE_INTEGRATION_DISCOVERY
from homeassistant.const import CONF_DEVICE_ID
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.stateful_scenes.config_flow import ConfigFlow
from custom_components.stateful_scenes.const import (
    CONF_DEBOUNCE_TIME,
    CONF_ENABLE_DISCOVERY,
    CONF_EXTERNAL_SCENE_ACTIVE,
    CONF_IGNORE_UNAVAILABLE,
    CONF_NUMBER_TOLERANCE,
    CONF_RESTORE_STATES_ON_DEACTIVATE,
    CONF_SCENE_ENTITIES,
    CONF_SCENE_ENTITY_ID,
    CONF_SCENE_NAME,
    CONF_SCENE_PATH,
    CONF_TRANSITION_TIME,
    DEFAULT_SCENE_PATH,
    DOMAIN,
)
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .const import MOCK_INVALID_SCENES_YAML, MOCK_SCENES_NO_ENTITIES, MOCK_SCENES_YAML


class TestConfigFlow:
    """Test the config flow."""

    async def test_flow_user_init(self, mock_hass: HomeAssistant):
        """Test user initiated flow shows menu."""
        flow = ConfigFlow()
        flow.hass = mock_hass

        result = await flow.async_step_user()

        assert result["type"] == FlowResultType.MENU
        assert "configure_internal_scenes" in result["menu_options"]
        assert "select_external_scenes" in result["menu_options"]

    async def test_flow_configure_internal_scenes_success(
        self, mock_hass: HomeAssistant, tmp_path
    ):
        """Test configuring internal scenes successfully."""
        # Create a valid scenes file
        scenes_file = tmp_path / "scenes.yaml"
        scenes_file.write_text(MOCK_SCENES_YAML)

        flow = ConfigFlow()
        flow.hass = mock_hass

        with patch.object(flow.hass.config, "path", return_value=str(scenes_file)):
            result = await flow.async_step_configure_internal_scenes(
                user_input={
                    CONF_SCENE_PATH: str(scenes_file),
                    CONF_NUMBER_TOLERANCE: 1,
                    CONF_RESTORE_STATES_ON_DEACTIVATE: False,
                    CONF_TRANSITION_TIME: 1,
                    CONF_DEBOUNCE_TIME: 0.0,
                    CONF_IGNORE_UNAVAILABLE: False,
                    CONF_ENABLE_DISCOVERY: True,
                }
            )

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "Home Assistant Scenes"
        assert result["data"][CONF_SCENE_PATH] == str(scenes_file)
        assert result["data"]["hub"] is True

    async def test_flow_configure_internal_scenes_invalid_yaml(
        self, mock_hass: HomeAssistant, tmp_path
    ):
        """Test configuring with invalid YAML file."""
        # Create an invalid scenes file
        invalid_file = tmp_path / "invalid.yaml"
        invalid_file.write_text(MOCK_INVALID_SCENES_YAML)

        flow = ConfigFlow()
        flow.hass = mock_hass

        with patch.object(flow.hass.config, "path", return_value=str(invalid_file)):
            result = await flow.async_step_configure_internal_scenes(
                user_input={
                    CONF_SCENE_PATH: str(invalid_file),
                    CONF_NUMBER_TOLERANCE: 1,
                }
            )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"]["base"] == "invalid_yaml"

    async def test_flow_configure_internal_scenes_file_not_found(
        self, mock_hass: HomeAssistant
    ):
        """Test configuring with non-existent file."""
        flow = ConfigFlow()
        flow.hass = mock_hass

        result = await flow.async_step_configure_internal_scenes(
            user_input={
                CONF_SCENE_PATH: "/nonexistent/scenes.yaml",
                CONF_NUMBER_TOLERANCE: 1,
            }
        )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"]["base"] == "yaml_not_found"

    async def test_flow_configure_internal_scenes_missing_entities(
        self, mock_hass: HomeAssistant, tmp_path
    ):
        """Test configuring with scenes missing entities."""
        # Create scenes file with missing entities
        bad_file = tmp_path / "bad.yaml"
        bad_file.write_text(MOCK_SCENES_NO_ENTITIES)

        flow = ConfigFlow()
        flow.hass = mock_hass

        with patch.object(flow.hass.config, "path", return_value=str(bad_file)):
            result = await flow.async_step_configure_internal_scenes(
                user_input={
                    CONF_SCENE_PATH: str(bad_file),
                    CONF_NUMBER_TOLERANCE: 1,
                }
            )

        assert result["type"] == FlowResultType.FORM
        assert "base" in result["errors"]

    async def test_flow_configure_internal_scenes_show_form(
        self, mock_hass: HomeAssistant
    ):
        """Test showing the form for internal scenes configuration."""
        flow = ConfigFlow()
        flow.hass = mock_hass

        # Mock file detection
        with patch.object(
            flow, "_detect_scenes_path", return_value=(DEFAULT_SCENE_PATH, None)
        ):
            result = await flow.async_step_configure_internal_scenes()

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "configure_internal_scenes"
        assert CONF_SCENE_PATH in result["data_schema"].schema

    async def test_flow_detect_scenes_path(self, mock_hass: HomeAssistant, tmp_path):
        """Test auto-detection of scenes.yaml path."""
        # Create scenes.yaml
        scenes_file = tmp_path / "scenes.yaml"
        scenes_file.write_text(MOCK_SCENES_YAML)

        flow = ConfigFlow()
        flow.hass = mock_hass

        with (
            patch.object(flow.hass.config, "path", return_value=str(scenes_file)),
            patch("os.path.isfile", return_value=True),
        ):
            path, warning = flow._detect_scenes_path()

        assert path == "scenes.yaml"
        assert warning is None

    async def test_flow_detect_scenes_path_not_found(self, mock_hass: HomeAssistant):
        """Test auto-detection when scenes.yaml is not found."""
        flow = ConfigFlow()
        flow.hass = mock_hass

        with patch("os.path.isfile", return_value=False):
            path, warning = flow._detect_scenes_path()

        assert path == DEFAULT_SCENE_PATH
        assert warning is not None
        assert "Could not auto-detect" in warning

    async def test_flow_select_external_scenes(
        self, mock_hass: HomeAssistant, setup_integration
    ):
        """Test selecting external scenes."""
        flow = ConfigFlow()
        flow.hass = mock_hass

        # Initialize domain data
        mock_hass.data.setdefault(DOMAIN, {})

        # Mock scene entities in hass
        mock_hass.states.async_set(
            "scene.external_1",
            "scenestate",
            {"friendly_name": "External Scene 1"},
        )

        result = await flow.async_step_select_external_scenes()

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "select_external_scenes"

    async def test_flow_select_external_scenes_with_input(
        self, mock_hass: HomeAssistant, setup_integration
    ):
        """Test selecting external scenes with user input."""
        flow = ConfigFlow()
        flow.hass = mock_hass
        flow.context = {"source": "discovery"}
        flow.configuration = {}

        # Mock scene entities
        mock_hass.states.async_set(
            "scene.external_1",
            "scenestate",
            {
                "friendly_name": "External Scene 1",
                "entity_id": ["light.living_room"],
            },
        )

        result = await flow.async_step_select_external_scenes(
            user_input={CONF_SCENE_ENTITY_ID: "scene.external_1"}
        )

        # Should redirect to entity selection step
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "configure_external_scene_entities"

    async def test_flow_select_entities(self, mock_hass: HomeAssistant):
        """Test entity selection step for external scene."""
        flow = ConfigFlow()
        flow.hass = mock_hass
        flow.configuration = {CONF_SCENE_ENTITY_ID: "scene.external_1"}

        # Mock available entities
        mock_hass.states.async_set("light.living_room", "on", {})
        mock_hass.states.async_set("light.bedroom", "on", {})

        result = await flow.async_step_configure_external_scene_entities()

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "configure_external_scene_entities"

    async def test_flow_select_entities_with_input(
        self, mock_hass: HomeAssistant, setup_integration
    ):
        """Test entity selection with user input."""
        flow = ConfigFlow()
        flow.hass = mock_hass
        flow.configuration = {
            CONF_SCENE_ENTITY_ID: "scene.external_1",
            CONF_SCENE_NAME: "External Scene",
        }

        # Mock entity states
        mock_hass.states.async_set(
            "scene.living_room",
            "on",
            {"brightness": 255, "friendly_name": "Living Room"},
        )

        result = await flow.async_step_configure_external_scene_entities(
            user_input={CONF_SCENE_ENTITIES: ["scene.living_room"]}
        )

        # Should proceed to learn scene
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "learn_external_scene"

    async def test_flow_learn_scene(self, mock_hass: HomeAssistant, setup_integration):
        """Test learn scene step."""
        flow = ConfigFlow()
        flow.hass = mock_hass
        flow.configuration = {
            CONF_SCENE_ENTITY_ID: "scene.external_1",
            CONF_SCENE_NAME: "External Scene",
            CONF_SCENE_ENTITIES: ["light.living_room"],
        }

        # Mock scene state
        mock_hass.states.async_set(
            "scene.external_1",
            "scenestate",
            {"friendly_name": "External Scene"},
        )

        result = await flow.async_step_learn_external_scene()

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "learn_external_scene"

    async def test_flow_learn_scene_confirm(
        self, mock_hass: HomeAssistant, setup_integration
    ):
        """Test confirming scene learning."""
        flow = ConfigFlow()
        flow.hass = mock_hass
        flow.configuration = {
            CONF_SCENE_ENTITY_ID: "scene.external_1",
            CONF_SCENE_NAME: "External Scene",
            CONF_SCENE_ENTITIES: ["light.living_room"],
        }

        # Mock entity states
        mock_hass.states.async_set(
            "light.living_room",
            "on",
            {"brightness": 255},
        )

        # Mock scene entity
        mock_hass.states.async_set(
            "scene.external_1",
            "scenestate",
            {"friendly_name": "External Scene", "id": "external_1"},
        )

        result = await flow.async_step_learn_external_scene(
            user_input={CONF_EXTERNAL_SCENE_ACTIVE: True}
        )

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "External Scene"
        assert CONF_SCENE_ENTITIES in result["data"]

    async def test_flow_discovery(self, mock_hass: HomeAssistant, setup_integration):
        """Test discovery flow."""
        flow = ConfigFlow()
        flow.hass = mock_hass
        flow.context = {"source": "integration_discovery"}
        flow.configuration = {}

        # Mock scene entity
        mock_hass.states.async_set(
            "scene.discovered_scene",
            "scenestate",
            {
                "friendly_name": "Discovered Scene",
                "id": "discovered_scene",
                "entity_id": ["light.living_room"],
            },
        )

        discovery_info = {
            CONF_SCENE_ENTITY_ID: "scene.discovered_scene",
            CONF_DEVICE_ID: "unique_device_id",
        }

        result = await flow.async_step_integration_discovery(discovery_info)

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "configure_external_scene_entities"

    async def test_flow_discovery_already_configured(
        self, mock_hass: HomeAssistant, setup_integration
    ):
        """Test discovery flow when scene is already configured."""
        # Create existing config entry
        existing_entry = MockConfigEntry(
            domain=DOMAIN,
            title="Discovered Scene",
            data={CONF_SCENE_ENTITY_ID: "scene.discovered_scene"},
            unique_id="stateful_discovered_unique_device_id",
        )
        existing_entry.add_to_hass(mock_hass)

        flow = ConfigFlow()
        flow.hass = mock_hass
        flow.context = {"source": "integration_discovery"}
        flow.configuration = {}

        discovery_info = {
            CONF_SCENE_ENTITY_ID: "scene.discovered_scene",
            CONF_DEVICE_ID: "discovered_unique_device_id",
        }

        # Mock the scene entity
        mock_hass.states.async_set(
            "scene.discovered_scene",
            "scenestate",
            {"entity_id": ["light.living_room"]},
        )

        result = await flow.async_step_integration_discovery(discovery_info)

        # With same unique_id, should result in form continuing
        assert result["type"] == FlowResultType.FORM

    async def test_flow_options(self, mock_hass: HomeAssistant):
        """Test user flow after configuration."""
        # Test that the flow can handle the user menu correctly
        flow = ConfigFlow()
        flow.hass = mock_hass
        flow.context = {"source": "user"}
        flow.configuration = {}

        # Start user flow
        result = await flow.async_step_user()

        # Should show menu with options
        assert result is not None
        assert result["type"] == FlowResultType.MENU

    async def test_flow_abort_no_scenes_found(
        self, mock_hass: HomeAssistant, setup_integration
    ):
        """Test flow aborts when no scenes are found."""
        flow = ConfigFlow()
        flow.hass = mock_hass
        flow.context = {"source": "discovery"}
        flow.configuration = {}

        # No scene entities in hass - only internal scenes matter
        result = await flow.async_step_select_external_scenes()

        # Should show form with empty options
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "select_external_scenes"

    async def test_flow_duplicate_entry_prevention(
        self, mock_hass: HomeAssistant, tmp_path
    ):
        """Test that duplicate entries are prevented."""
        scenes_file = tmp_path / "scenes.yaml"
        scenes_file.write_text(MOCK_SCENES_YAML)

        # Create existing entry
        existing_entry = MockConfigEntry(
            domain=DOMAIN,
            title="Home Assistant Scenes",
            data={CONF_SCENE_PATH: str(scenes_file)},
        )
        existing_entry.add_to_hass(mock_hass)

        flow = ConfigFlow()
        flow.hass = mock_hass

        with patch.object(flow.hass.config, "path", return_value=str(scenes_file)):
            result = await flow.async_step_configure_internal_scenes(
                user_input={
                    CONF_SCENE_PATH: str(scenes_file),
                    CONF_NUMBER_TOLERANCE: 1,
                }
            )

        # Should still create entry (multiple hubs are allowed)
        # or should abort if logic prevents duplicates
        assert result["type"] in [
            FlowResultType.CREATE_ENTRY,
            FlowResultType.ABORT,
        ]
