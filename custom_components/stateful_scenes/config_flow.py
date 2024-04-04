"""Adds config flow for Blueprint."""

from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

# from .StatefulScenes import test_yaml
from .const import (
    DOMAIN,
    CONF_NUMBER_TOLERANCE,
    CONF_SCENE_PATH,
    CONF_RESTORE_STATES_ON_DEACTIVATE,
    CONF_TRANSITION_TIME,
    CONF_EXTERNAL_SCENES,
    CONF_EXTERNAL_SCENES_LIST,
    CONF_EXTERNAL_SCENE_ACTIVE,
    DEFAULT_NUMBER_TOLERANCE,
    DEFAULT_SCENE_PATH,
    DEFAULT_RESTORE_STATES_ON_DEACTIVATE,
    DEFAULT_TRANSITION_TIME,
    DEFAULT_EXTERNAL_SCENES,
    DEFAULT_EXTERNAL_SCENE_ACTIVE,
)

from .const import (
    TOLERANCE_MIN,
    TOLERANCE_MAX,
    TOLERANCE_STEP,
    TRANSITION_MIN,
    TRANSITION_MAX,
    TRANSITION_STEP,
)
from .StatefulScenes import Hub, StatefulScenesYamlInvalid, StatefulScenesYamlNotFound

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
                return await self.async_step_select_external_scenes()

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
                }
            ),
            errors=errors,
        )

    async def async_step_select_external_scenes(self, user_input=None):
        """Handle a flow step for selecting external scenes."""
        errors = {}

        excluded_entities = [scene._entity_id for scene in self.hub.scenes]
        excluded_entities = []  # TODO: remove this line
        all_entities = self.hass.states.async_entity_ids("scene")

        if user_input is not None or all(
            entity in excluded_entities for entity in all_entities
        ):
            external_scenes = user_input.get(CONF_EXTERNAL_SCENES, [])
            external_scenes = {scene: {} for scene in external_scenes}
            self.configuration[CONF_EXTERNAL_SCENES] = external_scenes
            self.configuration[CONF_EXTERNAL_SCENES_LIST] = list(external_scenes.keys())

            if len(external_scenes) == self.curr_external_scene:
                return self.async_create_entry(
                    title="Stateful Scenes",
                    data=self.configuration,
                )

            return await self.async_step_configure_external_scene_entities()

        # If user_input is None or there are errors, show the form again
        return self.async_show_form(
            step_id="select_external_scenes",
            data_schema=vol.Schema(
                {
                    # Define the fields for your second flow here
                    vol.Optional(
                        CONF_EXTERNAL_SCENES, default=DEFAULT_EXTERNAL_SCENES
                    ): selector.EntitySelector(
                        {
                            "filter": {"domain": "scene"},
                            "multiple": True,
                            "exclude_entities": excluded_entities,
                        }
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_configure_external_scene_entities(self, user_input=None):
        """Handle a flow step for configuring external scenes."""
        errors = {}
        entity_id = self.configuration[CONF_EXTERNAL_SCENES_LIST][
            self.curr_external_scene
        ]

        if user_input is not None:
            self.configuration[CONF_EXTERNAL_SCENES][entity_id]["entities"] = (
                user_input["entities"]
            )
            return await self.async_step_learn_external_scene()

        # If user_input is None or there are errors, show the form again
        return self.async_show_form(
            step_id="configure_external_scene_entities",
            data_schema=vol.Schema(
                {
                    # Define the fields for your second flow here
                    vol.Optional("entities", default=[]): selector.EntitySelector(
                        {
                            "multiple": True,
                        }
                    ),
                }
            ),
            description_placeholders={"scene_name": entity_id},
            errors=errors,
        )

    async def async_step_learn_external_scene(self, user_input=None):
        """Handle a flow step for learning external scenes."""
        errors = {}
        entity_id = self.configuration[CONF_EXTERNAL_SCENES_LIST][
            self.curr_external_scene
        ]
        entities = self.configuration[CONF_EXTERNAL_SCENES][entity_id]["entities"]

        if user_input is not None and user_input.get(CONF_EXTERNAL_SCENE_ACTIVE, False):
            entity_conf = {}
            for entity in entities:
                entity_conf[entity] = self.hass.states.get(entity).__dict__

            self.configuration[CONF_EXTERNAL_SCENES][entity_id]["entities"] = (
                entity_conf
            )
            self.curr_external_scene += 1

            if (
                len(self.configuration[CONF_EXTERNAL_SCENES_LIST])
                == self.curr_external_scene
            ):
                return self.async_create_entry(
                    title="Stateful Scenes",
                    data=self.configuration,
                )

            return await self.async_step_configure_external_scene_entities()

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
                "entity_name": entity_id,
            },
            errors=errors,
        )
