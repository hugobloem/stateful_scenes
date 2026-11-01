"""Tests for Stateful Scenes registry helper functions."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry, entity_registry
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.stateful_scenes.const import DOMAIN
from custom_components.stateful_scenes.helpers import (
    _get_device_entities,
    async_cleanup_orphaned_entities,
)


async def test_get_device_entities_returns_matching_entries(hass: HomeAssistant):
    """_get_device_entities should return registry entries for a device id."""
    entry = MockConfigEntry(domain=DOMAIN, title="Test Entry")
    entry.add_to_hass(hass)

    er = entity_registry.async_get(hass)
    dr = device_registry.async_get(hass)

    device = dr.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, "device_1")},
        name="Device 1",
    )
    entity = er.async_get_or_create(
        domain="switch",
        platform=DOMAIN,
        unique_id="stateful_entity_1",
        config_entry=entry,
        device_id=device.id,
    )

    entities = _get_device_entities(er, device.id)

    assert [e.entity_id for e in entities] == [entity.entity_id]
    assert _get_device_entities(er, "nonexistent_device") == []


async def test_async_cleanup_orphaned_entities_removes_stale_entity_and_device(
    hass: HomeAssistant,
):
    """Entities/devices for scene ids no longer present must be removed."""
    entry = MockConfigEntry(domain=DOMAIN, title="Test Entry")
    entry.add_to_hass(hass)

    er = entity_registry.async_get(hass)
    dr = device_registry.async_get(hass)

    device = dr.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, "orphan_device")},
        name="Orphan Device",
    )
    orphan_entity = er.async_get_or_create(
        domain="switch",
        platform=DOMAIN,
        unique_id="stateful_orphan_scene",
        config_entry=entry,
        device_id=device.id,
    )
    kept_entity = er.async_get_or_create(
        domain="switch",
        platform=DOMAIN,
        unique_id="stateful_kept_scene",
        config_entry=entry,
    )

    await async_cleanup_orphaned_entities(hass, DOMAIN, entry.entry_id, {"kept_scene"})

    assert er.async_get(orphan_entity.entity_id) is None
    assert er.async_get(kept_entity.entity_id) is not None
    assert dr.async_get(device.id) is None


async def test_async_cleanup_orphaned_entities_keeps_device_with_entities(
    hass: HomeAssistant,
):
    """A device must not be removed while it still has entities."""
    entry = MockConfigEntry(domain=DOMAIN, title="Test Entry")
    entry.add_to_hass(hass)

    er = entity_registry.async_get(hass)
    dr = device_registry.async_get(hass)

    device = dr.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, "shared_device")},
        name="Shared Device",
    )
    er.async_get_or_create(
        domain="switch",
        platform=DOMAIN,
        unique_id="stateful_kept_scene",
        config_entry=entry,
        device_id=device.id,
    )

    await async_cleanup_orphaned_entities(hass, DOMAIN, entry.entry_id, {"kept_scene"})

    assert dr.async_get(device.id) is not None


async def test_async_cleanup_orphaned_entities_no_matching_entities(
    hass: HomeAssistant,
):
    """Cleanup must not error when there is nothing to clean up."""
    entry = MockConfigEntry(domain=DOMAIN, title="Test Entry")
    entry.add_to_hass(hass)

    await async_cleanup_orphaned_entities(hass, DOMAIN, entry.entry_id, set())
