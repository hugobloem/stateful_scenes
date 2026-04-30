"""Tests for Stateful Scenes discovery."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from custom_components.stateful_scenes.const import DOMAIN
from custom_components.stateful_scenes.discovery import DiscoveryManager


async def test_should_process_device_scene_entity(hass: HomeAssistant):
    """Test discovery processes non-HA scene entities."""
    manager = DiscoveryManager(hass, MagicMock())

    # Create a mock entity entry that looks like an external scene
    mock_entry = MagicMock()
    mock_entry.disabled = False
    mock_entry.domain = "scene"
    mock_entry.platform = "hue"

    assert manager.should_process_device(mock_entry) is True


async def test_should_not_process_ha_scene(hass: HomeAssistant):
    """Test discovery skips HA-native scene entities."""
    manager = DiscoveryManager(hass, MagicMock())

    mock_entry = MagicMock()
    mock_entry.disabled = False
    mock_entry.domain = "scene"
    mock_entry.platform = "homeassistant"

    assert manager.should_process_device(mock_entry) is False


async def test_should_not_process_disabled(hass: HomeAssistant):
    """Test discovery skips disabled entities."""
    manager = DiscoveryManager(hass, MagicMock())

    mock_entry = MagicMock()
    mock_entry.disabled = True
    mock_entry.domain = "scene"
    mock_entry.platform = "hue"

    assert manager.should_process_device(mock_entry) is False


async def test_should_not_process_non_scene(hass: HomeAssistant):
    """Test discovery skips non-scene entities."""
    manager = DiscoveryManager(hass, MagicMock())

    mock_entry = MagicMock()
    mock_entry.disabled = False
    mock_entry.domain = "light"
    mock_entry.platform = "hue"

    assert manager.should_process_device(mock_entry) is False


async def test_discovery_manager_start(hass: HomeAssistant):
    """Test discovery manager scans entity registry."""
    # Register a mock scene entity
    entity_reg = er.async_get(hass)
    entity_reg.async_get_or_create(
        domain="scene",
        platform="hue",
        unique_id="hue_scene_001",
        suggested_object_id="hue_living_room",
    )

    manager = DiscoveryManager(hass, MagicMock())

    with patch(
        "custom_components.stateful_scenes.discovery.discovery_flow.async_create_flow"
    ) as mock_create_flow:
        await manager.async_start_discovery()

    # Should have dispatched a discovery flow for the hue scene
    mock_create_flow.assert_called_once()
    call_args = mock_create_flow.call_args
    assert call_args[0][1] == DOMAIN
    assert call_args[1]["data"]["entity_id"] == "scene.hue_living_room"


async def test_discovery_skips_existing_entries(hass: HomeAssistant):
    """Test discovery skips entities that already have config entries."""
    entity_reg = er.async_get(hass)
    entry = entity_reg.async_get_or_create(
        domain="scene",
        platform="hue",
        unique_id="hue_scene_002",
        suggested_object_id="hue_bedroom",
    )

    # Create a config entry that matches this entity
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=f"stateful_{entry.id}",
        data={"entity_id": "scene.hue_bedroom", "hub": False},
    )
    mock_entry.add_to_hass(hass)

    manager = DiscoveryManager(hass, MagicMock())

    with patch(
        "custom_components.stateful_scenes.discovery.discovery_flow.async_create_flow"
    ) as mock_create_flow:
        await manager.async_start_discovery()

    # Should NOT dispatch a flow since entry already exists
    mock_create_flow.assert_not_called()
