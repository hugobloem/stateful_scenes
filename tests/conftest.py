"""Pytest fixtures for testing Midea Smart AC."""

import pytest
from homeassistant.setup import async_setup_component


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture()
async def hass(hass):
    """Fixture to add virtual custom integration."""
    await async_setup_component(hass, "virtual", {})
    await hass.async_block_till_done()
    return hass
