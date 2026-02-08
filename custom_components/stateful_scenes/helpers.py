"""Helper functions for stateful_scenes."""

import logging
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry, device_registry, area_registry
from homeassistant.helpers.template import state_attr

_LOGGER = logging.getLogger(__name__)


def get_id_from_entity_id(hass: HomeAssistant, entity_id: str | None) -> str | None:
    """Get scene id from entity_id."""
    if entity_id is None:
        return None
    er = entity_registry.async_get(hass)
    # Check if entity exists in registry
    if er.async_get(entity_id) is not None:
        return entity_registry.async_resolve_entity_id(er, entity_id)
    return None


def get_name_from_entity_id(hass: HomeAssistant, entity_id: str | None) -> str | None:
    """Get scene name from entity_id."""
    if entity_id is None:
        return None
    return state_attr(hass, entity_id, "friendly_name")


def get_icon_from_entity_id(hass: HomeAssistant, entity_id: str | None) -> str | None:
    """Get scene icon from entity_id."""
    if entity_id is None:
        return None
    return state_attr(hass, entity_id, "icon")


def get_area_from_entity_id(hass: HomeAssistant, entity_id: str | None) -> str | None:
    """Get scene area from entity_id."""
    if entity_id is None:
        return None
    er = entity_registry.async_get(hass)
    areas = area_registry.async_get(hass).areas
    entity = er.async_get(entity_id)
    if entity is None:
        return None
    if entity.area_id is not None:
        return areas[entity.area_id].name
    dr = device_registry.async_get(hass)
    device = dr.async_get(entity.device_id)
    return areas[device.area_id].name if device and device.area_id is not None else None


def _extract_scene_id_from_unique_id(unique_id: str) -> str | None:
    """Extract scene ID from entity unique_id."""
    if unique_id.startswith("stateful_"):
        return unique_id[9:]  # Remove "stateful_" prefix

    # Check for suffixes and remove them
    suffixes = [
        "_restore_on_deactivate",
        "_ignore_unavailable",
        "_ignore_attributes",
        "_transition_time",
        "_debounce_time",
        "_tolerance",
        "_off_scene",
    ]

    for suffix in suffixes:
        if unique_id.endswith(suffix):
            return unique_id[: -len(suffix)]

    return None


def _get_device_entities(er: entity_registry.EntityRegistry, device_id: str) -> list:
    """Get all entities for a device."""
    return [entity for entity in er.entities.values() if entity.device_id == device_id]


async def async_cleanup_orphaned_entities(
    hass: HomeAssistant, domain: str, entry_id: str, valid_scene_ids: set[str]
) -> None:
    """Remove orphaned stateful scene entities and devices that no longer have corresponding scenes."""
    er = entity_registry.async_get(hass)
    dr = device_registry.async_get(hass)

    # Find and remove orphaned entities
    entities_to_remove = []
    orphaned_devices = set()

    for entity_id, entity in er.entities.items():
        if (
            entity.platform == domain
            and entity.config_entry_id == entry_id
            and entity.unique_id
        ):
            scene_id = _extract_scene_id_from_unique_id(entity.unique_id)

            if scene_id and scene_id not in valid_scene_ids:
                entities_to_remove.append(entity_id)
                if entity.device_id:
                    orphaned_devices.add(entity.device_id)
                _LOGGER.info(
                    "Marking orphaned entity for removal: %s (scene_id: %s)",
                    entity_id,
                    scene_id,
                )

    # Remove orphaned entities
    for entity_id in entities_to_remove:
        _LOGGER.info("Removing orphaned entity: %s", entity_id)
        er.async_remove(entity_id)

    # Remove all orphaned devices (both from entities removed above and existing empty devices)
    devices_to_check = orphaned_devices.copy()

    # Add all devices belonging to this integration that have no entities
    for device_id, device in dr.devices.items():
        if entry_id in device.config_entries and not _get_device_entities(
            er, device_id
        ):
            devices_to_check.add(device_id)

    # Remove devices with no entities
    for device_id in devices_to_check:
        if not _get_device_entities(er, device_id):
            device = dr.devices.get(device_id)
            device_name = device.name if device else "Unknown"
            _LOGGER.info(
                "Removing orphaned device: %s (name: %s)", device_id, device_name
            )
            dr.async_remove_device(device_id)
