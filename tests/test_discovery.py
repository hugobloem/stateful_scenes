"""Tests for the discovery manager."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from homeassistant.config_entries import SOURCE_INTEGRATION_DISCOVERY
from homeassistant.const import CONF_DEVICE_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from custom_components.stateful_scenes.const import CONF_SCENE_ENTITY_ID, DOMAIN
from custom_components.stateful_scenes.discovery import DiscoveryManager
from pytest_homeassistant_custom_component.common import MockConfigEntry


class TestDiscoveryManager:
    """Test the DiscoveryManager class."""

    @pytest.fixture
    def mock_config_entry(self):
        """Return a mock config entry."""
        return MockConfigEntry(
            domain=DOMAIN,
            title="Home Assistant Scenes",
            data={},
            entry_id="test_entry",
        )

    @pytest.fixture
    async def populated_entity_registry(self, mock_hass: HomeAssistant):
        """Create entity registry with various scenes."""
        registry = er.async_get(mock_hass)

        # Add HA internal scene (should be excluded)
        registry.async_get_or_create(
            "scene",
            "homeassistant",
            "internal_scene",
            suggested_object_id="internal_scene",
        )

        # Add external scenes (should be discovered)
        registry.async_get_or_create(
            "scene",
            "zigbee2mqtt",
            "external_scene_1",
            suggested_object_id="external_scene_1",
        )
        registry.async_get_or_create(
            "scene",
            "hue",
            "external_scene_2",
            suggested_object_id="external_scene_2",
        )

        # Add disabled scene (should be excluded)
        registry.async_get_or_create(
            "scene",
            "zigbee2mqtt",
            "disabled_scene",
            suggested_object_id="disabled_scene",
            disabled_by=er.RegistryEntryDisabler.USER,
        )

        # Add non-scene entity (should be excluded)
        registry.async_get_or_create(
            "light",
            "hue",
            "light_1",
            suggested_object_id="light_1",
        )

        return registry

    async def test_discovery_manager_initialization(
        self, mock_hass: HomeAssistant, mock_config_entry
    ):
        """Test discovery manager initialization."""
        discovery_manager = DiscoveryManager(mock_hass, mock_config_entry)

        assert discovery_manager.hass == mock_hass
        assert discovery_manager.ha_config == mock_config_entry

    async def test_should_process_device_valid_scene(
        self, mock_hass: HomeAssistant, mock_config_entry, populated_entity_registry
    ):
        """Test should_process_device with valid external scene."""
        discovery_manager = DiscoveryManager(mock_hass, mock_config_entry)

        # Get external scene entity
        external_scene = populated_entity_registry.async_get("scene.external_scene_1")

        result = discovery_manager.should_process_device(external_scene)

        assert result is True

    async def test_should_process_device_disabled_entity(
        self, mock_hass: HomeAssistant, mock_config_entry, populated_entity_registry
    ):
        """Test should_process_device with disabled entity."""
        discovery_manager = DiscoveryManager(mock_hass, mock_config_entry)

        disabled_scene = populated_entity_registry.async_get("scene.disabled_scene")

        result = discovery_manager.should_process_device(disabled_scene)

        assert result is False

    async def test_should_process_device_wrong_domain(
        self, mock_hass: HomeAssistant, mock_config_entry, populated_entity_registry
    ):
        """Test should_process_device with non-scene entity."""
        discovery_manager = DiscoveryManager(mock_hass, mock_config_entry)

        light_entity = populated_entity_registry.async_get("light.light_1")

        result = discovery_manager.should_process_device(light_entity)

        assert result is False

    async def test_should_process_device_homeassistant_platform(
        self, mock_hass: HomeAssistant, mock_config_entry, populated_entity_registry
    ):
        """Test should_process_device with Home Assistant internal scene."""
        discovery_manager = DiscoveryManager(mock_hass, mock_config_entry)

        internal_scene = populated_entity_registry.async_get("scene.internal_scene")

        result = discovery_manager.should_process_device(internal_scene)

        assert result is False

    async def test_async_start_discovery(
        self, mock_hass: HomeAssistant, mock_config_entry, populated_entity_registry
    ):
        """Test starting the discovery process."""
        discovery_manager = DiscoveryManager(mock_hass, mock_config_entry)

        with patch(
            "custom_components.stateful_scenes.discovery.discovery_flow.async_create_flow"
        ) as mock_create_flow:
            await discovery_manager.async_start_discovery()

            # Should create flows for external scenes only (not internal or disabled)
            assert mock_create_flow.call_count == 2

            # Verify calls were made with correct parameters
            calls = mock_create_flow.call_args_list
            for call in calls:
                assert call[0][0] == mock_hass
                assert call[0][1] == DOMAIN
                assert call[1]["context"]["source"] == SOURCE_INTEGRATION_DISCOVERY
                assert CONF_SCENE_ENTITY_ID in call[1]["data"]
                assert CONF_DEVICE_ID in call[1]["data"]

    async def test_async_start_discovery_skip_existing(
        self, mock_hass: HomeAssistant, mock_config_entry, populated_entity_registry
    ):
        """Test discovery skips already configured scenes."""
        discovery_manager = DiscoveryManager(mock_hass, mock_config_entry)

        # Get an external scene
        external_scene = populated_entity_registry.async_get("scene.external_scene_1")

        # Create existing config entry for this scene
        existing_entry = MockConfigEntry(
            domain=DOMAIN,
            title="External Scene 1",
            data={},
            entry_id="existing_entry",
            unique_id=f"stateful_{external_scene.id}",
        )
        existing_entry.add_to_hass(mock_hass)

        with patch(
            "custom_components.stateful_scenes.discovery.discovery_flow.async_create_flow"
        ) as mock_create_flow:
            await discovery_manager.async_start_discovery()

            # Should only create flow for one scene (the other is already configured)
            assert mock_create_flow.call_count == 1

            # Verify it was for the non-configured scene
            call_data = mock_create_flow.call_args[1]["data"]
            assert "external_scene_2" in call_data[CONF_SCENE_ENTITY_ID]

    async def test_init_entity_discovery(
        self, mock_hass: HomeAssistant, mock_config_entry, populated_entity_registry
    ):
        """Test initializing entity discovery."""
        discovery_manager = DiscoveryManager(mock_hass, mock_config_entry)

        external_scene = populated_entity_registry.async_get("scene.external_scene_1")

        with patch(
            "custom_components.stateful_scenes.discovery.discovery_flow.async_create_flow"
        ) as mock_create_flow:
            discovery_manager._init_entity_discovery(external_scene)

            mock_create_flow.assert_called_once()

            # Verify discovery data
            call_data = mock_create_flow.call_args[1]["data"]
            assert call_data[CONF_SCENE_ENTITY_ID] == "scene.external_scene_1"
            assert call_data[CONF_DEVICE_ID] == external_scene.unique_id

    async def test_discovery_with_empty_registry(
        self, mock_hass: HomeAssistant, mock_config_entry
    ):
        """Test discovery with no scenes in registry."""
        discovery_manager = DiscoveryManager(mock_hass, mock_config_entry)

        with patch(
            "custom_components.stateful_scenes.discovery.discovery_flow.async_create_flow"
        ) as mock_create_flow:
            await discovery_manager.async_start_discovery()

            # Should not create any flows
            mock_create_flow.assert_not_called()

    async def test_discovery_only_external_platforms(
        self, mock_hass: HomeAssistant, mock_config_entry
    ):
        """Test discovery only processes scenes from external platforms."""
        registry = er.async_get(mock_hass)

        # Add scenes from various platforms
        registry.async_get_or_create(
            "scene",
            "homeassistant",
            "internal_1",
            suggested_object_id="internal_1",
        )
        registry.async_get_or_create(
            "scene",
            "zigbee2mqtt",
            "external_1",
            suggested_object_id="external_1",
        )
        registry.async_get_or_create(
            "scene",
            "homeassistant",
            "internal_2",
            suggested_object_id="internal_2",
        )
        registry.async_get_or_create(
            "scene",
            "deconz",
            "external_2",
            suggested_object_id="external_2",
        )

        discovery_manager = DiscoveryManager(mock_hass, mock_config_entry)

        with patch(
            "custom_components.stateful_scenes.discovery.discovery_flow.async_create_flow"
        ) as mock_create_flow:
            await discovery_manager.async_start_discovery()

            # Should only discover the 2 external scenes
            assert mock_create_flow.call_count == 2

            # Verify only external scenes were discovered
            entity_ids = [
                call[1]["data"][CONF_SCENE_ENTITY_ID]
                for call in mock_create_flow.call_args_list
            ]
            assert "scene.external_1" in entity_ids
            assert "scene.external_2" in entity_ids
            assert "scene.internal_1" not in entity_ids
            assert "scene.internal_2" not in entity_ids
