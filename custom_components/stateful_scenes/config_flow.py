"""Adds config flow for Blueprint."""

from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    CONF_NUMBER_TOLERANCE,
    CONF_SCENE_PATH,
    CONF_RESTORE_STATES_ON_DEACTIVATE,
    CONF_TRANSITION_TIME,
    CONF_EXTERNAL_SCENE_ACTIVE,
    DEFAULT_NUMBER_TOLERANCE,
    DEFAULT_SCENE_PATH,
    DEFAULT_RESTORE_STATES_ON_DEACTIVATE,
    DEFAULT_TRANSITION_TIME,
    DEFAULT_EXTERNAL_SCENE_ACTIVE,
    CONF_SCENE_ENTITY_ID,
    CONF_SCENE_NAME,
    CONF_SCENE_ENTITIES,
)

from .const import (
    CONF_DEBOUNCE_TIME,
    DEBOUNCE_MAX,
    DEBOUNCE_MIN,
    DEBOUNCE_STEP,
    DEFAULT_DEBOUNCE_TIME,
    TOLERANCE_MIN,
    TOLERANCE_MAX,
    TOLERANCE_STEP,
    TRANSITION_MIN,
    TRANSITION_MAX,
    TRANSITION_STEP,
)
from .StatefulScenes import (
    Hub,
    Scene,
    StatefulScenesYamlInvalid,
    StatefulScenesYamlNotFound,
)
from .helpers import get_name_from_entity_id

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Blueprint."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the ConfigFlow class."""
        self.configuration = {}
        self.curr_external_scene = 0

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.FlowResult:
        """Handle a flow initialized by the user."""
        errors = {}

        if user_input is not None:
            try:
                self.hub = Hub(
                    hass=self.hass,
                    scene_path=user_input[CONF_SCENE_PATH],
                    number_tolerance=user_input[CONF_NUMBER_TOLERANCE],
                )
            except StatefulScenesYamlInvalid as err:
                _LOGGER.warning(err)
                errors["base"] = "invalid_yaml"
            except StatefulScenesYamlNotFound as err:
                _LOGGER.warning(err)
                errors["base"] = "yaml_not_found"
            except Exception as err:
                _LOGGER.warning(err)
                errors["base"] = "unknown"
            else:
                self.configuration.update(user_input)
                self.configuration["hub"] = True
                return self.async_create_entry(
                    title="Home Assistant Scenes",
                    data=self.configuration,
                )

        return self.async_show_form(
            step_id="user",
            last_step=True,
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
                        selector.NumberSelectorConfig(
                            min=TOLERANCE_MIN, max=TOLERANCE_MAX, step=TOLERANCE_STEP
                        )
                    ),
                    vol.Optional(
                        CONF_RESTORE_STATES_ON_DEACTIVATE,
                        default=DEFAULT_RESTORE_STATES_ON_DEACTIVATE,
                    ): selector.BooleanSelector(),
                    vol.Optional(
                        CONF_TRANSITION_TIME, default=DEFAULT_TRANSITION_TIME
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=TRANSITION_MIN, max=TRANSITION_MAX, step=TRANSITION_STEP
                        )
                    ),
                    vol.Optional(
                        CONF_DEBOUNCE_TIME, default=DEFAULT_DEBOUNCE_TIME
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=DEBOUNCE_MIN, max=DEBOUNCE_MAX, step=DEBOUNCE_STEP
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_integration_discovery(
        self, discovery_info: config_entries.ConfigEntry
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by discovery."""
        self.configuration = discovery_info

        unique_id = f"stateful_{discovery_info[CONF_SCENE_ENTITY_ID]}"
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()

        self.context["title_placeholders"] = {
            "name": get_name_from_entity_id(
                self.hass, discovery_info[CONF_SCENE_ENTITY_ID]
            ),
        }

        return await self.async_step_configure_external_scene_entities()

    async def async_step_configure_external_scene_entities(self, user_input=None):
        """Handle a flow step for configuring external scenes."""
        errors = {}
        entity_id = self.configuration.get(CONF_SCENE_ENTITY_ID, None)

        if entity_id is None:
            errors["base"] = "no_entity_id"

        if user_input is not None:
            self.configuration[CONF_SCENE_ENTITIES] = user_input[CONF_SCENE_ENTITIES]
            return await self.async_step_learn_external_scene()

        # If user_input is None or there are errors, show the form again
        return self.async_show_form(
            step_id="configure_external_scene_entities",
            data_schema=vol.Schema(
                {
                    # Define the fields for your second flow here
                    vol.Optional(
                        CONF_SCENE_ENTITIES, default=[]
                    ): selector.EntitySelector(
                        {
                            "multiple": True,
                        }
                    ),
                }
            ),
            description_placeholders={
                "scene_name": get_name_from_entity_id(self.hass, entity_id)
            },
            errors=errors,
        )

    async def async_step_learn_external_scene(self, user_input=None):
        """Handle a flow step for learning external scenes."""
        errors = {}
        entity_id = self.configuration[CONF_SCENE_ENTITY_ID]
        entities = self.configuration[CONF_SCENE_ENTITIES]

        try:
            hub = [
                entry
                for entry in self.hass.data[DOMAIN].values()
                if isinstance(entry, Hub)
            ][0]
        except IndexError as err:
            _LOGGER.error(err)
            errors["base"] = "hub_not_found"

        await self.hass.services.async_call(
            domain="scene",
            service="turn_on",
            target={"entity_id": entity_id},
            service_data={"transition": 0},
        )

        if user_input is not None and user_input.get(CONF_EXTERNAL_SCENE_ACTIVE, False):
            entity_id = self.configuration[CONF_SCENE_ENTITY_ID]
            entities = Scene.learn_scene_states(self.hass, entities)
            scene_conf = hub.prepare_external_scene(entity_id, entities)
            scene_conf = hub.extract_scene_configuration(scene_conf)

            return self.async_create_entry(
                title=scene_conf[CONF_SCENE_NAME],
                data=scene_conf,
            )

        # If user_input is None or there are errors, show the form again
        return self.async_show_form(
            step_id="learn_external_scene",
            data_schema=vol.Schema(
                {
                    # Define the fields for your second flow here
                    vol.Optional(
                        CONF_EXTERNAL_SCENE_ACTIVE,
                        default=DEFAULT_EXTERNAL_SCENE_ACTIVE,
                    ): selector.BooleanSelector(),
                }
            ),
            description_placeholders={
                "entity_name": get_name_from_entity_id(self.hass, entity_id),
            },
            errors=errors,
        )
