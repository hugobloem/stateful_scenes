"""Fixtures for Stateful Scenes tests."""

from __future__ import annotations

import os

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.stateful_scenes.const import DOMAIN

from .const import MOCK_EXTERNAL_SCENE_DATA, MOCK_HUB_DATA, SCENES_YAML_CONTENT


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    yield


@pytest.fixture
def mock_scenes_yaml(hass):
    """Write a test scenes.yaml to the hass config dir."""
    scenes_path = os.path.join(hass.config.config_dir, "scenes.yaml")
    with open(scenes_path, "w") as f:
        f.write(SCENES_YAML_CONTENT)
    return scenes_path


@pytest.fixture
def mock_config_entry_hub(hass, mock_scenes_yaml):
    """Create a mock config entry for hub setup."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_HUB_DATA,
        title="Home Assistant Scenes",
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
def mock_config_entry_external(hass):
    """Create a mock config entry for an external scene."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_EXTERNAL_SCENE_DATA,
        title="External Scene",
        unique_id="stateful_scene.external_test",
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
def mock_scene_entities(hass):
    """Set up mock scene entity states."""
    hass.states.async_set(
        "scene.test_scene_1",
        "scening",
        {
            "friendly_name": "Test Scene 1",
            "id": "1001",
            "entity_id": ["light.living_room", "light.bedroom"],
        },
    )
    hass.states.async_set(
        "scene.test_scene_2",
        "scening",
        {
            "friendly_name": "Test Scene 2",
            "id": "1002",
            "entity_id": ["light.living_room", "cover.blinds"],
        },
    )


@pytest.fixture
def mock_light_entities(hass):
    """Set up mock light entity states matching scene 1."""
    hass.states.async_set(
        "light.living_room",
        "on",
        {"brightness": 255, "friendly_name": "Living Room Light"},
    )
    hass.states.async_set(
        "light.bedroom",
        "off",
        {"friendly_name": "Bedroom Light"},
    )


@pytest.fixture
def mock_cover_entities(hass):
    """Set up mock cover entity states."""
    hass.states.async_set(
        "cover.blinds",
        "open",
        {"current_position": 75, "friendly_name": "Blinds"},
    )
