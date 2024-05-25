"""Discovery of scenes external to HA."""

from __future__ import annotations

import logging

import homeassistant.helpers.entity_registry as er
from homeassistant.config_entries import SOURCE_INTEGRATION_DISCOVERY
from homeassistant.const import CONF_DEVICE_ID
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import discovery_flow
from homeassistant.helpers.typing import ConfigType

from .const import (
    DOMAIN,
    CONF_SCENE_ENTITY_ID,
)

_LOGGER = logging.getLogger(__name__)


class DiscoveryManager:
    """Device Discovery.

    This class is responsible for scanning the HA instance for devices and their
    manufacturer / model info
    It checks if any of these devices is supported in the batterynotes library
    When devices are found it will dispatch a discovery flow,
    so the user can add them to their HA instance.
    """

    def __init__(self, hass: HomeAssistant, ha_config: ConfigType) -> None:
        """Init."""
        self.hass = hass
        self.ha_config = ha_config

    async def start_discovery(self) -> None:
        """Start the discovery procedure."""
        _LOGGER.debug("Start auto discovering devices")
        entity_registry = er.async_get(self.hass)

        for entity_entry in list(entity_registry.entities.values()):
            if not self.should_process_device(entity_entry):
                continue

            self._init_entity_discovery(entity_entry)

        _LOGGER.debug("Done auto discovering devices")

    def should_process_device(self, entity_entry: er.EntityEntry) -> bool:
        """Do some validations on the registry entry to see if it qualifies for discovery."""
        if entity_entry.disabled:
            return False

        if entity_entry.domain != "scene":
            return False

        if entity_entry.platform == "homeassistant":
            return False

        return True

    @callback
    def _init_entity_discovery(
        self,
        entity_entry: er.EntityEntry,
    ) -> None:
        """Dispatch the discovery flow for a given entity."""
        existing_entries = [
            entry
            for entry in self.hass.config_entries.async_entries(DOMAIN)
            if entry.unique_id == f"stateful_{entity_entry.id}"
        ]
        if existing_entries:
            _LOGGER.debug(
                "%s: Already setup, skipping new discovery",
                f"{entity_entry.id}",
            )
            return

        discovery_data = {
            CONF_SCENE_ENTITY_ID: entity_entry.entity_id,
            CONF_DEVICE_ID: entity_entry.unique_id,
        }

        discovery_flow.async_create_flow(
            self.hass,
            DOMAIN,
            context={"source": SOURCE_INTEGRATION_DISCOVERY},
            data=discovery_data,
        )
