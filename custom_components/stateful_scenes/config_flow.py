"""Adds config flow for Blueprint."""
from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

# from .StatefulScenes import test_yaml
from .const import (
    CONF_NUMBER_TOLERANCE,
    CONF_SCENE_PATH,
    DEFAULT_NUMBER_TOLERANCE,
    DEFAULT_SCENE_PATH,
    DOMAIN,
)
from .StatefulScenes import Hub, StatefulScenesYamlInvalid, StatefulScenesYamlNotFound

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Blueprint."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.FlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}

        print(user_input)
        if user_input is not None:
            try:
                Hub(
                    hass=self.hass,
                    scene_path=user_input[CONF_SCENE_PATH],
                    number_tolerance=user_input[CONF_NUMBER_TOLERANCE],
                )
            except StatefulScenesYamlInvalid as err:
                _LOGGER.warning(err)
                _errors["base"] = "invalid_yaml"
            except StatefulScenesYamlNotFound as err:
                _LOGGER.warning(err)
                _errors["base"] = "yaml_not_found"
            except Exception as err:
                _LOGGER.warning(err)
                _errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title="Stateful Scenes",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCENE_PATH, default=DEFAULT_SCENE_PATH
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
                    ),
                    vol.Optional(
                        CONF_NUMBER_TOLERANCE, default=DEFAULT_NUMBER_TOLERANCE
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(min=0, max=20, step=1)
                    ),
                }
            ),
            errors=_errors,
        )

    # async def _test_credentials(self, username: str, password: str) -> None:
    #     """Validate credentials."""
    #     client = IntegrationBlueprintApiClient(
    #         username=username,
    #         password=password,
    #         session=async_create_clientsession(self.hass),
    #     )
    #     await client.async_get_data()
