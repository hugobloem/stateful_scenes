"""Fixtures for Stateful Scenes tests."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import yaml
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICE_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_mock_service,
)

from custom_components.stateful_scenes.const import (
    CONF_SCENE_ENTITY_ID,
    CONF_SCENE_PATH,
    DOMAIN,
)

from .const import (
    MOCK_CONFIG_ENTRY_HUB,
    MOCK_CONFIG_ENTRY_SINGLE,
    MOCK_ENTITY_STATES,
    MOCK_SCENES_YAML,
)


@pytest.fixture
def mock_scene_file(tmp_path):
    """Create a mock scenes.yaml file."""
    scenes_file = tmp_path / "scenes.yaml"
    scenes_file.write_text(MOCK_SCENES_YAML)
    return str(scenes_file)


@pytest.fixture
def mock_scenes_data():
    """Return mock scene data as a list of dicts."""
    return yaml.safe_load(MOCK_SCENES_YAML)


@pytest.fixture
async def mock_hass(hass: HomeAssistant) -> HomeAssistant:
    """Return a mocked Home Assistant instance with entity states."""
    # Register entities in the entity registry
    registry = er.async_get(hass)
    for entity_id in [
        "light.living_room",
        "light.bedroom",
        "light.kitchen",
        "switch.fan",
        "cover.garage",
    ]:
        registry.async_get_or_create(
            domain=entity_id.split(".")[0],
            platform="test",
            unique_id=f"{entity_id}_uid",
            suggested_object_id=entity_id.split(".")[1],
        )

    # Set up entity states
    for entity_id, entity_data in MOCK_ENTITY_STATES.items():
        hass.states.async_set(
            entity_id, entity_data["state"], entity_data["attributes"]
        )

    # Mock scene entities
    hass.states.async_set(
        "scene.test_scene_1",
        "scenestate",
        {
            "entity_id": ["light.living_room", "light.bedroom", "switch.fan"],
            "id": "test_scene_1",
            "friendly_name": "Test Scene 1",
            "icon": "mdi:lightbulb",
        },
    )
    hass.states.async_set(
        "scene.test_scene_2",
        "scenestate",
        {
            "entity_id": ["light.living_room", "light.bedroom", "cover.garage"],
            "id": "test_scene_2",
            "friendly_name": "Test Scene 2",
            "icon": "mdi:weather-night",
        },
    )
    hass.states.async_set(
        "scene.external_scene",
        "scenestate",
        {
            "entity_id": ["light.kitchen"],
            "id": "external_scene",
            "friendly_name": "External Scene",
            "icon": "mdi:home",
        },
    )

    # Mock services
    async_mock_service(hass, "scene", "turn_on")
    async_mock_service(hass, "homeassistant", "turn_off")

    return hass


@pytest.fixture
def mock_config_entry_hub() -> MockConfigEntry:
    """Return a mock config entry for hub mode."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Home Assistant Scenes",
        data=MOCK_CONFIG_ENTRY_HUB,
        entry_id="test_hub_entry",
        unique_id="stateful_scenes_hub",
    )


@pytest.fixture
def mock_config_entry_single() -> MockConfigEntry:
    """Return a mock config entry for single scene mode."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="External Scene",
        data=MOCK_CONFIG_ENTRY_SINGLE,
        entry_id="test_single_entry",
        unique_id="stateful_external_scene",
    )


@pytest.fixture
async def mock_entity_registry(hass: HomeAssistant) -> er.EntityRegistry:
    """Return a mock entity registry."""
    registry = er.async_get(hass)

    # Add mock entities
    registry.async_get_or_create(
        "switch",
        DOMAIN,
        "test_scene_1",
        suggested_object_id="test_scene_1",
        config_entry=MockConfigEntry(domain=DOMAIN, entry_id="test_hub_entry"),
    )
    registry.async_get_or_create(
        "switch",
        DOMAIN,
        "test_scene_2",
        suggested_object_id="test_scene_2",
        config_entry=MockConfigEntry(domain=DOMAIN, entry_id="test_hub_entry"),
    )

    return registry


@pytest.fixture
async def mock_device_registry(hass: HomeAssistant) -> dr.DeviceRegistry:
    """Return a mock device registry."""
    return dr.async_get(hass)


@pytest.fixture
async def mock_area_registry(hass: HomeAssistant) -> ar.AreaRegistry:
    """Return a mock area registry."""
    registry = ar.async_get(hass)

    # Add mock areas
    registry.async_create("Living Room")
    registry.async_create("Bedroom")
    registry.async_create("Kitchen")

    return registry


@pytest.fixture
def mock_aiofiles_read():
    """Mock aiofiles reading for scenes.yaml."""

    async def mock_read_file(file_path: str) -> str:
        """Mock file read."""
        if "invalid" in file_path:
            return "invalid: yaml: content:"
        if "not_found" in file_path:
            raise FileNotFoundError(f"File not found: {file_path}")
        return MOCK_SCENES_YAML

    with patch("aiofiles.open") as mock_open:
        mock_file = MagicMock()
        mock_file.__aenter__ = AsyncMock(return_value=mock_file)
        mock_file.__aexit__ = AsyncMock()
        mock_file.read = AsyncMock(return_value=MOCK_SCENES_YAML)
        mock_open.return_value = mock_file
        yield mock_open


@pytest.fixture
def mock_yaml_load(mock_scenes_data):
    """Mock yaml.safe_load for scenes.yaml."""
    with patch("yaml.safe_load", return_value=mock_scenes_data) as mock_load:
        yield mock_load


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    return


@pytest.fixture
async def setup_integration(
    hass: HomeAssistant, mock_config_entry_hub: MockConfigEntry, mock_scene_file
) -> ConfigEntry:
    """Set up the Stateful Scenes integration."""
    mock_config_entry_hub.add_to_hass(hass)

    # Patch the scene file loading
    with patch(
        "custom_components.stateful_scenes.load_scenes_file",
        return_value=yaml.safe_load(MOCK_SCENES_YAML),
    ):
        await hass.config_entries.async_setup(mock_config_entry_hub.entry_id)
        await hass.async_block_till_done()

    return mock_config_entry_hub
