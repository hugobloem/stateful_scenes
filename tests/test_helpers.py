"""Tests for helper functions."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from custom_components.stateful_scenes.const import DOMAIN
from custom_components.stateful_scenes.helpers import (
    _extract_scene_id_from_unique_id,
    _get_device_entities,
    async_cleanup_orphaned_entities,
    get_area_from_entity_id,
    get_icon_from_entity_id,
    get_id_from_entity_id,
    get_name_from_entity_id,
)
from pytest_homeassistant_custom_component.common import MockConfigEntry


class TestHelperFunctions:
    """Test helper functions."""

    async def test_get_id_from_entity_id(self, mock_hass: HomeAssistant):
        """Test getting scene ID from entity_id."""
        # Mock entity registry
        registry = er.async_get(mock_hass)
        entry = registry.async_get_or_create(
            "scene",
            "homeassistant",
            "test_scene_1",
            suggested_object_id="test_scene_1",
        )

        result = get_id_from_entity_id(mock_hass, "scene.test_scene_1")

        # async_resolve_entity_id returns the entity_id itself
        assert result == "scene.test_scene_1"

    async def test_get_id_from_entity_id_none(self, mock_hass: HomeAssistant):
        """Test getting ID from None entity_id."""
        result = get_id_from_entity_id(mock_hass, None)
        assert result is None

    async def test_get_id_from_entity_id_not_found(self, mock_hass: HomeAssistant):
        """Test getting ID from non-existent entity_id."""
        result = get_id_from_entity_id(mock_hass, "scene.nonexistent")
        # Should return None for non-existent entity
        assert result is None

    async def test_get_name_from_entity_id(self, mock_hass: HomeAssistant):
        """Test getting friendly name from entity_id."""
        mock_hass.states.async_set(
            "scene.test_scene",
            "scenestate",
            {"friendly_name": "Test Scene Name"},
        )

        result = get_name_from_entity_id(mock_hass, "scene.test_scene")
        assert result == "Test Scene Name"

    async def test_get_name_from_entity_id_none(self, mock_hass: HomeAssistant):
        """Test getting name from None entity_id."""
        result = get_name_from_entity_id(mock_hass, None)
        assert result is None

    async def test_get_name_from_entity_id_no_attribute(
        self, mock_hass: HomeAssistant
    ):
        """Test getting name when friendly_name attribute is missing."""
        mock_hass.states.async_set("scene.test_scene", "scenestate", {})

        result = get_name_from_entity_id(mock_hass, "scene.test_scene")
        assert result is None

    async def test_get_icon_from_entity_id(self, mock_hass: HomeAssistant):
        """Test getting icon from entity_id."""
        mock_hass.states.async_set(
            "scene.test_scene",
            "scenestate",
            {"icon": "mdi:lightbulb"},
        )

        result = get_icon_from_entity_id(mock_hass, "scene.test_scene")
        assert result == "mdi:lightbulb"

    async def test_get_icon_from_entity_id_none(self, mock_hass: HomeAssistant):
        """Test getting icon from None entity_id."""
        result = get_icon_from_entity_id(mock_hass, None)
        assert result is None

    async def test_get_icon_from_entity_id_no_attribute(
        self, mock_hass: HomeAssistant
    ):
        """Test getting icon when icon attribute is missing."""
        mock_hass.states.async_set("scene.test_scene", "scenestate", {})

        result = get_icon_from_entity_id(mock_hass, "scene.test_scene")
        assert result is None

    async def test_get_area_from_entity_id_entity_area(
        self, mock_hass: HomeAssistant
    ):
        """Test getting area from entity that has area assigned."""
        # Create area
        area_reg = ar.async_get(mock_hass)
        area = area_reg.async_create("Living Room")

        # Create entity with area
        entity_reg = er.async_get(mock_hass)
        entity_reg.async_get_or_create(
            "scene",
            "homeassistant",
            "test_scene",
            suggested_object_id="test_scene",
            area_id=area.id,
        )

        result = get_area_from_entity_id(mock_hass, "scene.test_scene")
        assert result == "Living Room"

    async def test_get_area_from_entity_id_device_area(
        self, mock_hass: HomeAssistant
    ):
        """Test getting area from entity's device when entity has no area."""
        # Create area
        area_reg = ar.async_get(mock_hass)
        area = area_reg.async_create("Kitchen")

        # Create device with area
        device_reg = dr.async_get(mock_hass)
        device = device_reg.async_get_or_create(
            config_entry_id="test_entry",
            identifiers={("test", "device_1")},
            area_id=area.id,
        )

        # Create entity with device but no area
        entity_reg = er.async_get(mock_hass)
        entity_reg.async_get_or_create(
            "scene",
            "homeassistant",
            "test_scene",
            suggested_object_id="test_scene",
            device_id=device.id,
        )

        result = get_area_from_entity_id(mock_hass, "scene.test_scene")
        assert result == "Kitchen"

    async def test_get_area_from_entity_id_none(self, mock_hass: HomeAssistant):
        """Test getting area from None entity_id."""
        result = get_area_from_entity_id(mock_hass, None)
        assert result is None

    async def test_get_area_from_entity_id_no_area(self, mock_hass: HomeAssistant):
        """Test getting area when entity has no area."""
        entity_reg = er.async_get(mock_hass)
        entity_reg.async_get_or_create(
            "scene",
            "homeassistant",
            "test_scene",
            suggested_object_id="test_scene",
        )

        result = get_area_from_entity_id(mock_hass, "scene.test_scene")
        assert result is None

    async def test_get_area_from_entity_id_not_found(self, mock_hass: HomeAssistant):
        """Test getting area from non-existent entity."""
        result = get_area_from_entity_id(mock_hass, "scene.nonexistent")
        assert result is None


class TestExtractSceneIdFromUniqueId:
    """Test _extract_scene_id_from_unique_id function."""

    def test_extract_scene_id_with_stateful_prefix(self):
        """Test extracting scene ID with stateful_ prefix."""
        result = _extract_scene_id_from_unique_id("stateful_test_scene")
        assert result == "test_scene"

    def test_extract_scene_id_with_restore_suffix(self):
        """Test extracting scene ID with _restore_on_deactivate suffix."""
        result = _extract_scene_id_from_unique_id(
            "test_scene_restore_on_deactivate"
        )
        assert result == "test_scene"

    def test_extract_scene_id_with_ignore_unavailable_suffix(self):
        """Test extracting scene ID with _ignore_unavailable suffix."""
        result = _extract_scene_id_from_unique_id("test_scene_ignore_unavailable")
        assert result == "test_scene"

    def test_extract_scene_id_with_ignore_attributes_suffix(self):
        """Test extracting scene ID with _ignore_attributes suffix."""
        result = _extract_scene_id_from_unique_id("test_scene_ignore_attributes")
        assert result == "test_scene"

    def test_extract_scene_id_with_transition_time_suffix(self):
        """Test extracting scene ID with _transition_time suffix."""
        result = _extract_scene_id_from_unique_id("test_scene_transition_time")
        assert result == "test_scene"

    def test_extract_scene_id_with_debounce_time_suffix(self):
        """Test extracting scene ID with _debounce_time suffix."""
        result = _extract_scene_id_from_unique_id("test_scene_debounce_time")
        assert result == "test_scene"

    def test_extract_scene_id_with_tolerance_suffix(self):
        """Test extracting scene ID with _tolerance suffix."""
        result = _extract_scene_id_from_unique_id("test_scene_tolerance")
        assert result == "test_scene"

    def test_extract_scene_id_with_off_scene_suffix(self):
        """Test extracting scene ID with _off_scene suffix."""
        result = _extract_scene_id_from_unique_id("test_scene_off_scene")
        assert result == "test_scene"

    def test_extract_scene_id_no_prefix_or_suffix(self):
        """Test extracting scene ID with no recognized prefix or suffix."""
        result = _extract_scene_id_from_unique_id("plain_scene_id")
        assert result is None

    def test_extract_scene_id_complex_name(self):
        """Test extracting scene ID with complex scene name."""
        result = _extract_scene_id_from_unique_id(
            "my_complex_scene_name_restore_on_deactivate"
        )
        assert result == "my_complex_scene_name"


class TestGetDeviceEntities:
    """Test _get_device_entities function."""

    async def test_get_device_entities(self, mock_hass: HomeAssistant):
        """Test getting entities for a device."""
        # Create device
        device_reg = dr.async_get(mock_hass)
        device = device_reg.async_get_or_create(
            config_entry_id="test_entry",
            identifiers={("test", "device_1")},
        )

        # Create entities for the device
        entity_reg = er.async_get(mock_hass)
        entity1 = entity_reg.async_get_or_create(
            "switch",
            DOMAIN,
            "entity1",
            suggested_object_id="entity1",
            device_id=device.id,
        )
        entity2 = entity_reg.async_get_or_create(
            "number",
            DOMAIN,
            "entity2",
            suggested_object_id="entity2",
            device_id=device.id,
        )

        # Create entity for a different device
        other_device = device_reg.async_get_or_create(
            config_entry_id="test_entry",
            identifiers={("test", "device_2")},
        )
        entity_reg.async_get_or_create(
            "switch",
            DOMAIN,
            "entity3",
            suggested_object_id="entity3",
            device_id=other_device.id,
        )

        result = _get_device_entities(entity_reg, device.id)

        # Should only return entities for the specified device
        assert len(result) == 2
        entity_ids = [e.id for e in result]
        assert entity1.id in entity_ids
        assert entity2.id in entity_ids

    async def test_get_device_entities_no_entities(self, mock_hass: HomeAssistant):
        """Test getting entities for device with no entities."""
        device_reg = dr.async_get(mock_hass)
        device = device_reg.async_get_or_create(
            config_entry_id="test_entry",
            identifiers={("test", "device_1")},
        )

        entity_reg = er.async_get(mock_hass)
        result = _get_device_entities(entity_reg, device.id)

        assert len(result) == 0


class TestAsyncCleanupOrphanedEntities:
    """Test async_cleanup_orphaned_entities function."""

    async def test_cleanup_orphaned_entities(self, mock_hass: HomeAssistant):
        """Test cleaning up orphaned entities."""
        # Create config entry
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            entry_id="test_entry",
        )

        # Create device
        device_reg = dr.async_get(mock_hass)
        device = device_reg.async_get_or_create(
            config_entry_id=config_entry.entry_id,
            identifiers={(DOMAIN, "test_device")},
        )

        # Create entities - one valid, one orphaned
        entity_reg = er.async_get(mock_hass)
        valid_entity = entity_reg.async_get_or_create(
            "switch",
            DOMAIN,
            "stateful_valid_scene",
            suggested_object_id="valid_scene",
            config_entry=config_entry,
            device_id=device.id,
        )
        orphaned_entity = entity_reg.async_get_or_create(
            "switch",
            DOMAIN,
            "stateful_orphaned_scene",
            suggested_object_id="orphaned_scene",
            config_entry=config_entry,
            device_id=device.id,
        )

        # Valid scene IDs (only valid_scene exists)
        valid_scene_ids = {"valid_scene"}

        await async_cleanup_orphaned_entities(
            mock_hass, DOMAIN, config_entry.entry_id, valid_scene_ids
        )

        # Verify orphaned entity was removed
        assert entity_reg.async_get(valid_entity.entity_id) is not None
        assert entity_reg.async_get(orphaned_entity.entity_id) is None

    async def test_cleanup_orphaned_devices(self, mock_hass: HomeAssistant):
        """Test cleaning up orphaned devices."""
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            entry_id="test_entry",
        )

        # Create device with entities
        device_reg = dr.async_get(mock_hass)
        device_with_entities = device_reg.async_get_or_create(
            config_entry_id=config_entry.entry_id,
            identifiers={(DOMAIN, "device_with_entities")},
        )

        # Create orphaned device (no entities)
        orphaned_device = device_reg.async_get_or_create(
            config_entry_id=config_entry.entry_id,
            identifiers={(DOMAIN, "orphaned_device")},
        )

        # Add entity to first device
        entity_reg = er.async_get(mock_hass)
        entity_reg.async_get_or_create(
            "switch",
            DOMAIN,
            "stateful_valid_scene",
            suggested_object_id="valid_scene",
            config_entry=config_entry,
            device_id=device_with_entities.id,
        )

        valid_scene_ids = {"valid_scene"}

        await async_cleanup_orphaned_entities(
            mock_hass, DOMAIN, config_entry.entry_id, valid_scene_ids
        )

        # Verify orphaned device was removed
        assert device_reg.async_get(device_with_entities.id) is not None
        assert device_reg.async_get(orphaned_device.id) is None

    async def test_cleanup_no_orphaned_entities(self, mock_hass: HomeAssistant):
        """Test cleanup when there are no orphaned entities."""
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            entry_id="test_entry",
        )

        entity_reg = er.async_get(mock_hass)
        device_reg = dr.async_get(mock_hass)
        device = device_reg.async_get_or_create(
            config_entry_id=config_entry.entry_id,
            identifiers={(DOMAIN, "test_device")},
        )

        # Create valid entity
        valid_entity = entity_reg.async_get_or_create(
            "switch",
            DOMAIN,
            "stateful_valid_scene",
            suggested_object_id="valid_scene",
            config_entry=config_entry,
            device_id=device.id,
        )

        valid_scene_ids = {"valid_scene"}

        await async_cleanup_orphaned_entities(
            mock_hass, DOMAIN, config_entry.entry_id, valid_scene_ids
        )

        # Verify entity still exists
        assert entity_reg.async_get(valid_entity.entity_id) is not None

    async def test_cleanup_multiple_config_entries(self, mock_hass: HomeAssistant):
        """Test cleanup only affects specified config entry."""
        config_entry1 = MockConfigEntry(
            domain=DOMAIN,
            entry_id="test_entry_1",
        )
        config_entry2 = MockConfigEntry(
            domain=DOMAIN,
            entry_id="test_entry_2",
        )

        entity_reg = er.async_get(mock_hass)

        # Create entities for different config entries
        entity1 = entity_reg.async_get_or_create(
            "switch",
            DOMAIN,
            "stateful_orphaned_scene",
            suggested_object_id="orphaned_scene_1",
            config_entry=config_entry1,
        )
        entity2 = entity_reg.async_get_or_create(
            "switch",
            DOMAIN,
            "stateful_orphaned_scene",
            suggested_object_id="orphaned_scene_2",
            config_entry=config_entry2,
        )

        # Cleanup for config_entry1 only
        valid_scene_ids = set()  # No valid scenes

        await async_cleanup_orphaned_entities(
            mock_hass, DOMAIN, config_entry1.entry_id, valid_scene_ids
        )

        # Verify only entry1's entity was removed
        assert entity_reg.async_get(entity1.entity_id) is None
        assert entity_reg.async_get(entity2.entity_id) is not None
