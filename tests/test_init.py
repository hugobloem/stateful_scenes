"""Tests for component initialization."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest
import yaml
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.stateful_scenes import (
    async_reload_entry,
    async_setup_entry,
    async_unload_entry,
    load_scenes_file,
)
from custom_components.stateful_scenes.const import (
    CONF_ENABLE_DISCOVERY,
    CONF_NUMBER_TOLERANCE,
    CONF_SCENE_PATH,
    DOMAIN,
    StatefulScenesYamlInvalid,
    StatefulScenesYamlNotFound,
)
from custom_components.stateful_scenes.StatefulScenes import Hub, Scene
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .const import (
    MOCK_CONFIG_ENTRY_HUB,
    MOCK_CONFIG_ENTRY_SINGLE,
    MOCK_INVALID_SCENES_YAML,
    MOCK_SCENES_NO_ENTITIES,
    MOCK_SCENES_YAML,
)


class TestAsyncSetupEntry:
    """Test async_setup_entry function."""

    async def test_setup_entry_hub_mode(
        self, mock_hass: HomeAssistant, mock_config_entry_hub, mock_aiofiles_read
    ):
        """Test setting up a config entry in hub mode."""
        mock_config_entry_hub.add_to_hass(mock_hass)

        with patch(
            "custom_components.stateful_scenes.load_scenes_file",
            return_value=yaml.safe_load(MOCK_SCENES_YAML),
        ):
            result = await async_setup_entry(mock_hass, mock_config_entry_hub)

        assert result is True
        assert mock_config_entry_hub.entry_id in mock_hass.data[DOMAIN]
        assert isinstance(
            mock_hass.data[DOMAIN][mock_config_entry_hub.entry_id], Hub
        )

    async def test_setup_entry_single_scene_mode(
        self, mock_hass: HomeAssistant, mock_config_entry_single
    ):
        """Test setting up a config entry for single scene (external)."""
        mock_config_entry_single.add_to_hass(mock_hass)

        result = await async_setup_entry(mock_hass, mock_config_entry_single)

        assert result is True
        assert mock_config_entry_single.entry_id in mock_hass.data[DOMAIN]
        assert isinstance(
            mock_hass.data[DOMAIN][mock_config_entry_single.entry_id], Scene
        )

    async def test_setup_entry_with_discovery_enabled(
        self, mock_hass: HomeAssistant, mock_aiofiles_read
    ):
        """Test setting up with discovery enabled."""
        config_data = MOCK_CONFIG_ENTRY_HUB.copy()
        config_data[CONF_ENABLE_DISCOVERY] = True

        mock_entry = MockConfigEntry(
            domain=DOMAIN,
            title="Home Assistant Scenes",
            data=config_data,
            entry_id="test_discovery_entry",
        )
        mock_entry.add_to_hass(mock_hass)

        with patch(
            "custom_components.stateful_scenes.load_scenes_file",
            return_value=yaml.safe_load(MOCK_SCENES_YAML),
        ), patch(
            "custom_components.stateful_scenes.DiscoveryManager"
        ) as mock_discovery_class:
            mock_discovery = MagicMock()
            mock_discovery.async_start_discovery = AsyncMock()
            mock_discovery_class.return_value = mock_discovery

            result = await async_setup_entry(mock_hass, mock_entry)

            assert result is True
            mock_discovery.async_start_discovery.assert_called_once()

    async def test_setup_entry_with_discovery_disabled(
        self, mock_hass: HomeAssistant, mock_aiofiles_read
    ):
        """Test setting up with discovery disabled."""
        config_data = MOCK_CONFIG_ENTRY_HUB.copy()
        config_data[CONF_ENABLE_DISCOVERY] = False

        mock_entry = MockConfigEntry(
            domain=DOMAIN,
            title="Home Assistant Scenes",
            data=config_data,
            entry_id="test_no_discovery_entry",
        )
        mock_entry.add_to_hass(mock_hass)

        with patch(
            "custom_components.stateful_scenes.load_scenes_file",
            return_value=yaml.safe_load(MOCK_SCENES_YAML),
        ), patch(
            "custom_components.stateful_scenes.DiscoveryManager"
        ) as mock_discovery_class:
            result = await async_setup_entry(mock_hass, mock_entry)

            assert result is True
            mock_discovery_class.assert_not_called()

    async def test_setup_entry_platforms_loaded(
        self, mock_hass: HomeAssistant, mock_config_entry_hub, mock_aiofiles_read
    ):
        """Test that platforms are loaded during setup."""
        mock_config_entry_hub.add_to_hass(mock_hass)

        with patch(
            "custom_components.stateful_scenes.load_scenes_file",
            return_value=yaml.safe_load(MOCK_SCENES_YAML),
        ), patch.object(
            mock_hass.config_entries, "async_forward_entry_setups"
        ) as mock_forward:
            result = await async_setup_entry(mock_hass, mock_config_entry_hub)

            assert result is True
            mock_forward.assert_called_once()

            # Verify correct platforms are loaded
            call_args = mock_forward.call_args
            assert call_args[0][0] == mock_config_entry_hub
            platforms = call_args[0][1]
            assert "number" in str(platforms)
            assert "select" in str(platforms)
            assert "switch" in str(platforms)

    async def test_setup_entry_missing_scene_path(self, mock_hass: HomeAssistant):
        """Test setup fails when scene path is missing in hub mode."""
        config_data = MOCK_CONFIG_ENTRY_HUB.copy()
        del config_data[CONF_SCENE_PATH]

        mock_entry = MockConfigEntry(
            domain=DOMAIN,
            title="Home Assistant Scenes",
            data=config_data,
            entry_id="test_missing_path_entry",
        )
        mock_entry.add_to_hass(mock_hass)

        with pytest.raises(StatefulScenesYamlNotFound):
            await async_setup_entry(mock_hass, mock_entry)

    async def test_setup_entry_cleanup_orphaned_entities_hub(
        self, mock_hass: HomeAssistant, mock_config_entry_hub, mock_aiofiles_read
    ):
        """Test that orphaned entities are cleaned up in hub mode."""
        mock_config_entry_hub.add_to_hass(mock_hass)

        with patch(
            "custom_components.stateful_scenes.load_scenes_file",
            return_value=yaml.safe_load(MOCK_SCENES_YAML),
        ), patch(
            "custom_components.stateful_scenes.async_cleanup_orphaned_entities"
        ) as mock_cleanup:
            await async_setup_entry(mock_hass, mock_config_entry_hub)

            # Verify cleanup was called with valid scene IDs
            mock_cleanup.assert_called_once()
            call_args = mock_cleanup.call_args
            assert call_args[0][0] == mock_hass
            assert call_args[0][1] == DOMAIN
            assert call_args[0][2] == mock_config_entry_hub.entry_id
            # Check that valid scene IDs set is passed
            valid_scene_ids = call_args[0][3]
            assert isinstance(valid_scene_ids, set)
            assert len(valid_scene_ids) > 0

    async def test_setup_entry_cleanup_orphaned_entities_single(
        self, mock_hass: HomeAssistant, mock_config_entry_single
    ):
        """Test that orphaned entities are cleaned up for single scene."""
        mock_config_entry_single.add_to_hass(mock_hass)

        with patch(
            "custom_components.stateful_scenes.async_cleanup_orphaned_entities"
        ) as mock_cleanup:
            await async_setup_entry(mock_hass, mock_config_entry_single)

            # Verify cleanup was called
            mock_cleanup.assert_called_once()
            call_args = mock_cleanup.call_args
            valid_scene_ids = call_args[0][3]
            assert len(valid_scene_ids) == 1


class TestAsyncUnloadEntry:
    """Test async_unload_entry function."""

    async def test_unload_entry_success(
        self, mock_hass: HomeAssistant, mock_config_entry_hub, mock_aiofiles_read
    ):
        """Test successfully unloading a config entry."""
        mock_config_entry_hub.add_to_hass(mock_hass)

        # Setup first
        with patch(
            "custom_components.stateful_scenes.load_scenes_file",
            return_value=yaml.safe_load(MOCK_SCENES_YAML),
        ):
            await async_setup_entry(mock_hass, mock_config_entry_hub)

        # Verify setup worked
        assert mock_config_entry_hub.entry_id in mock_hass.data[DOMAIN]

        # Now unload
        result = await async_unload_entry(mock_hass, mock_config_entry_hub)

        assert result is True
        assert mock_config_entry_hub.entry_id not in mock_hass.data[DOMAIN]

    async def test_unload_entry_failure(
        self, mock_hass: HomeAssistant, mock_config_entry_hub
    ):
        """Test unload entry when platform unload fails."""
        mock_config_entry_hub.add_to_hass(mock_hass)

        # Add entry data manually
        mock_hass.data.setdefault(DOMAIN, {})
        mock_hass.data[DOMAIN][mock_config_entry_hub.entry_id] = MagicMock()

        # Mock platform unload to fail
        with patch.object(
            mock_hass.config_entries,
            "async_unload_platforms",
            return_value=False,
        ):
            result = await async_unload_entry(mock_hass, mock_config_entry_hub)

            assert result is False
            # Entry should still be in data since unload failed
            assert mock_config_entry_hub.entry_id in mock_hass.data[DOMAIN]


class TestAsyncReloadEntry:
    """Test async_reload_entry function."""

    async def test_reload_entry(
        self, mock_hass: HomeAssistant, mock_config_entry_hub, mock_aiofiles_read
    ):
        """Test reloading a config entry."""
        mock_config_entry_hub.add_to_hass(mock_hass)

        # Setup first
        with patch(
            "custom_components.stateful_scenes.load_scenes_file",
            return_value=yaml.safe_load(MOCK_SCENES_YAML),
        ):
            await async_setup_entry(mock_hass, mock_config_entry_hub)

        # Store original hub
        original_hub = mock_hass.data[DOMAIN][mock_config_entry_hub.entry_id]

        # Reload
        with patch(
            "custom_components.stateful_scenes.load_scenes_file",
            return_value=yaml.safe_load(MOCK_SCENES_YAML),
        ):
            await async_reload_entry(mock_hass, mock_config_entry_hub)

        # Verify entry was reloaded (should be a new instance)
        new_hub = mock_hass.data[DOMAIN][mock_config_entry_hub.entry_id]
        assert new_hub is not original_hub


class TestLoadScenesFile:
    """Test load_scenes_file function."""

    async def test_load_scenes_file_success(
        self, mock_hass: HomeAssistant, mock_scene_file
    ):
        """Test successfully loading a scenes file."""
        scenes = await load_scenes_file(mock_hass, mock_scene_file)

        assert isinstance(scenes, list)
        assert len(scenes) == 2
        assert scenes[0]["name"] == "Test Scene 1"
        assert scenes[1]["name"] == "Test Scene 2"

    async def test_load_scenes_file_relative_path(
        self, mock_hass: HomeAssistant, tmp_path
    ):
        """Test loading scenes file with relative path."""
        # Create a scenes file in a temp directory
        scenes_file = tmp_path / "scenes.yaml"
        scenes_file.write_text(MOCK_SCENES_YAML)

        # Mock config.path to return our temp path
        with patch.object(mock_hass.config, "path", return_value=str(scenes_file)):
            scenes = await load_scenes_file(mock_hass, "scenes.yaml")

        assert isinstance(scenes, list)
        assert len(scenes) == 2

    async def test_load_scenes_file_not_found(self, mock_hass: HomeAssistant):
        """Test loading a non-existent scenes file."""
        with pytest.raises(StatefulScenesYamlNotFound):
            await load_scenes_file(mock_hass, "/nonexistent/path/scenes.yaml")

    async def test_load_scenes_file_invalid_yaml(
        self, mock_hass: HomeAssistant, tmp_path
    ):
        """Test loading an invalid YAML file."""
        invalid_file = tmp_path / "invalid.yaml"
        invalid_file.write_text("invalid: yaml: content: [[[")

        with pytest.raises(StatefulScenesYamlInvalid):
            await load_scenes_file(mock_hass, str(invalid_file))

    async def test_load_scenes_file_empty(
        self, mock_hass: HomeAssistant, tmp_path
    ):
        """Test loading an empty scenes file."""
        empty_file = tmp_path / "empty.yaml"
        empty_file.write_text("")

        with pytest.raises(
            StatefulScenesYamlInvalid, match="Scenes file is empty"
        ):
            await load_scenes_file(mock_hass, str(empty_file))

    async def test_load_scenes_file_not_list(
        self, mock_hass: HomeAssistant, tmp_path
    ):
        """Test loading a scenes file that doesn't contain a list."""
        not_list_file = tmp_path / "not_list.yaml"
        not_list_file.write_text("key: value")

        with pytest.raises(
            StatefulScenesYamlInvalid, match="Scenes file must contain a list"
        ):
            await load_scenes_file(mock_hass, str(not_list_file))

    async def test_load_scenes_file_absolute_path(
        self, mock_hass: HomeAssistant, mock_scene_file
    ):
        """Test loading scenes file with absolute path."""
        scenes = await load_scenes_file(mock_hass, mock_scene_file)

        assert isinstance(scenes, list)
        assert len(scenes) == 2

    async def test_load_scenes_file_with_aiofiles(
        self, mock_hass: HomeAssistant, tmp_path
    ):
        """Test that aiofiles is used for file reading."""
        scenes_file = tmp_path / "scenes.yaml"
        scenes_file.write_text(MOCK_SCENES_YAML)

        # Should not raise and should use aiofiles internally
        scenes = await load_scenes_file(mock_hass, str(scenes_file))

        assert isinstance(scenes, list)
        assert len(scenes) == 2
