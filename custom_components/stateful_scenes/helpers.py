"""Helper functions for stateful_scenes."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry, device_registry, area_registry
from homeassistant.helpers.template import state_attr


def get_id_from_entity_id(hass: HomeAssistant, entity_id: str) -> str:
    """Get scene id from entity_id."""
    er = entity_registry.async_get(hass)
    return entity_registry.async_resolve_entity_id(er, entity_id)


def get_name_from_entity_id(hass: HomeAssistant, entity_id: str) -> str:
    """Get scene name from entity_id."""
    return state_attr(hass, entity_id, "friendly_name")


def get_icon_from_entity_id(hass: HomeAssistant, entity_id: str) -> str:
    """Get scene icon from entity_id."""
    return state_attr(hass, entity_id, "icon")


def get_area_from_entity_id(hass: HomeAssistant, entity_id: str) -> str:
    """Get scene area from entity_id."""
    er = entity_registry.async_get(hass)
    areas = area_registry.async_get(hass).areas
    entity = er.async_get(entity_id)
    if entity.area_id is not None:
        return areas[entity.area_id].name
    dr = device_registry.async_get(hass)
    device = dr.async_get(entity.device_id)
    return areas[device.area_id].name if device.area_id is not None else None
