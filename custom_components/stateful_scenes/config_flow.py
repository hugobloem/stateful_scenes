"""Adds config flow for Blueprint."""

from __future__ import annotations

import logging
import os

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from . import load_scenes_file

from .const import (
    CONF_DEBOUNCE_TIME,
    CONF_ENABLE_DISCOVERY,
    CONF_EXTERNAL_SCENE_ACTIVE,
    CONF_IGNORE_UNAVAILABLE,
    CONF_NUMBER_TOLERANCE,
    CONF_RESTORE_STATES_ON_DEACTIVATE,
    CONF_SCENE_ENTITIES,
    CONF_SCENE_ENTITY_ID,
    CONF_SCENE_NAME,
    CONF_SCENE_PATH,
    CONF_TRANSITION_TIME,
    DEBOUNCE_MAX,
    DEBOUNCE_MIN,
    DEBOUNCE_STEP,
    DEFAULT_DEBOUNCE_TIME,
    DEFAULT_ENABLE_DISCOVERY,
    DEFAULT_EXTERNAL_SCENE_ACTIVE,
    DEFAULT_IGNORE_UNAVAILABLE,
    DEFAULT_NUMBER_TOLERANCE,
    DEFAULT_RESTORE_STATES_ON_DEACTIVATE,
    DEFAULT_SCENE_PATH,
    DEFAULT_TRANSITION_TIME,
    DOMAIN,
    TOLERANCE_MAX,
    TOLERANCE_MIN,
    TOLERANCE_STEP,
    TRANSITION_MAX,
    TRANSITION_MIN,
    TRANSITION_STEP,
    StatefulScenesYamlInvalid,
    StatefulScenesYamlNotFound,
)
from .helpers import get_area_from_entity_id, get_name_from_entity_id
from .StatefulScenes import (
    Hub,
    Scene,
)

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Blueprint."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the ConfigFlow class."""
        self.configuration = {}
        self.curr_external_scene = 0

    def _detect_scenes_path(self) -> tuple[str, str | None]:
        """Detect the scenes.yaml path and return path and optional warning.

        Returns:
            Tuple of (detected_path, warning_message)
            warning_message is None if file was found successfully
        """
        # Try common scene file locations
        candidates = [
            "scenes.yaml",
            "scenes.yml",
            "config/scenes.yaml",
            "config/scenes.yml",
        ]

        for candidate in candidates:
            resolved_path = self.hass.config.path(candidate)
            if os.path.isfile(resolved_path):
                _LOGGER.debug("Auto-detected scenes file at: %s", resolved_path)
                return (candidate, None)

        # No file found - return default with warning
        warning = (
            "Could not auto-detect scenes.yaml location. "
            "Please verify the path or use an absolute path if your scenes file "
            "is in a custom location."
        )
        _LOGGER.info(
            "Could not auto-detect scenes.yaml, using default '%s'. "
            "User may need to adjust path during configuration.",
            DEFAULT_SCENE_PATH
        )
        return (DEFAULT_SCENE_PATH, warning)

    async def async_step_user(self, user_input: dict | None = None) -> dict:
        """Handle a flow initialized by the user."""
        return self.async_show_menu(
            step_id="user",
            menu_options=[
                "configure_internal_scenes",
                "select_external_scenes",
            ],
        )

    async def async_step_configure_internal_scenes(
        self,
        user_input: dict | None = None,
    ) -> config_entries.FlowResult:
        """Handle a flow initialized by the user."""
        errors = {}

        if user_input is not None:
            try:
                scene_confs = await load_scenes_file(self.hass, user_input[CONF_SCENE_PATH])
                _ = Hub(
                    hass=self.hass,
                    scene_confs=scene_confs,
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

        # Auto-detect scenes.yaml path
        detected_path, path_warning = self._detect_scenes_path()

        # Build description with warning if path not found
        description_placeholders = {}
        if path_warning:
            description_placeholders["path_warning"] = path_warning

        return self.async_show_form(
            step_id="configure_internal_scenes",
            last_step=True,
            description_placeholders=description_placeholders if path_warning else None,
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCENE_PATH,
                        default=detected_path,
                        description={
                            "suggested_value": detected_path
                        }
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        )
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
                    vol.Optional(
                        CONF_IGNORE_UNAVAILABLE, default=DEFAULT_IGNORE_UNAVAILABLE
                    ): selector.BooleanSelector(),
                    vol.Optional(
                        CONF_ENABLE_DISCOVERY, default=DEFAULT_ENABLE_DISCOVERY
                    ): selector.BooleanSelector(),
                }
            ),
            errors=errors,
        )

    async def async_step_integration_discovery(
        self, discovery_info: config_entries.ConfigEntry
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by discovery."""
        self.configuration = discovery_info
        self.configuration["hub"] = False

        unique_id = f"stateful_{discovery_info[CONF_SCENE_ENTITY_ID]}"
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()

        scene_name = get_name_from_entity_id(self.hass, discovery_info[CONF_SCENE_ENTITY_ID]) or "Unknown"
        scene_area = get_area_from_entity_id(self.hass, discovery_info[CONF_SCENE_ENTITY_ID]) or "No Area"
        self.context["title_placeholders"] = {
            "name": f"{scene_name} - {scene_area}"
        }

        return await self.async_step_configure_external_scene_entities()

    async def async_step_select_external_scenes(self, user_input=None):
        """Handle a flow step for selecting external scenes."""
        errors = {}

        if user_input is not None:
            self.configuration[CONF_SCENE_ENTITY_ID] = user_input[CONF_SCENE_ENTITY_ID]

            unique_id = f"stateful_{self.configuration[CONF_SCENE_ENTITY_ID]}"
            await self.async_set_unique_id(unique_id, raise_on_progress=False)

            return await self.async_step_configure_external_scene_entities()

        try:
            hub = [
                entry
                for entry in self.hass.data[DOMAIN].values()
                if isinstance(entry, Hub)
            ][0]
        except IndexError as err:
            _LOGGER.error(err)
            errors["base"] = "hub_not_found"

        excluded_entities = [scene._entity_id for scene in hub.scenes]
        excluded_entities += [
            entry.unique_id.replace("stateful_", "")
            for entry in self.hass.config_entries.async_entries(DOMAIN)
            if entry.unique_id
        ]
        all_entities = self.hass.states.async_entity_ids("scene")

        if all(entity in excluded_entities for entity in all_entities):
            errors["base"] = "no_configurable_scenes"

        # If user_input is None or there are errors, show the form again
        return self.async_show_form(
            step_id="select_external_scenes",
            data_schema=vol.Schema(
                {
                    # Define the fields for your second flow here
                    vol.Optional(CONF_SCENE_ENTITY_ID): selector.EntitySelector(
                        {
                            "filter": {"domain": "scene"},
                            "multiple": False,
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
                "scene_name": get_name_from_entity_id(self.hass, entity_id) or "Unknown Scene"
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
                "entity_name": get_name_from_entity_id(self.hass, entity_id) or "Unknown Entity",
            },
            errors=errors,
        )
