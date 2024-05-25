"""Helper functions for stateful_scenes."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry


def get_id_from_entity_id(hass: HomeAssistant, entity_id: str) -> str:
    """Get scene id from entity_id."""
    er = entity_registry.async_get(hass)
    return entity_registry.async_resolve_entity_id(er, entity_id)


def get_name_from_entity_id(hass: HomeAssistant, entity_id: str) -> str:
    """Get scene name from entity_id."""
    er = entity_registry.async_get(hass)
    name = er.async_get(entity_id).original_name
    return name if name is not None else entity_id


def get_icon_from_entity_id(hass: HomeAssistant, entity_id: str) -> str:
    """Get scene icon from entity_id."""
    er = entity_registry.async_get(hass)
    icon = er.async_get(entity_id).icon
    return icon if icon is not None else None
