# Stateful Scenes
[![hacs_badge](https://img.shields.io/badge/HACS-Default-gren.svg)](https://github.com/custom-components/hacs)
![version](https://img.shields.io/github/v/release/hugobloem/stateful_scenes)
![GitHub all releases](https://img.shields.io/github/downloads/hugobloem/stateful_scenes/total)
![GitHub release (latest by SemVer)](https://img.shields.io/github/downloads/hugobloem/stateful_scenes/latest/total)

> Do you want to use your Home Assistant scenes in HomeKit, but get annoyed when the scenes do not stay ‘on’?

Stateful Scenes solves this problem by creating a switch for each scene and inferring the state of the scene by analysing the entities in the scene. Plus, when you activate a scene in Home Assistant, the scene will also turn on in HomeKit—magic!

## Installation
### HACS
Install via [HACS](https://hacs.xyz) by searching for `stateful scenes` in the integrations section, or simply click the button:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=hugobloem&repository=stateful_scenes&category=integration)

### Manual
Clone the repository and copy the custom_components folder to your home assistant config folder.

```bash
git clone https://github.com/hugobloem/stateful_scenes.git
cp -r stateful_scenes/custom_components config/
```

## Configuration
This integration is now configured via the config flow. After you have installed and restarted Home Assistant, go to Devices and Services, Add Integration, and search for Stateful Scenes. Alternatively, just click this button:

[![Open your Home Assistant instance and show an integration.](https://my.home-assistant.io/badges/integration.svg)](https://my.home-assistant.io/redirect/integration/?domain=stateful_scenes)

![Config flow screenshot](media/config-flow.png)

### Scene path
If your configuration has a different location for scenes you can change the location by changing the `Scene path` variable. By default, Home Assistant places all scenes inside `scenes.yaml` which is where this integration retrieves the scenes.

### Rounding tolerance
Some attributes such as light brightness will be rounded off. Therefore, to assess whether the scene is active a tolerance will be applied. The default tolerance of 1 will work for rounding errors of ±1. If this does not work for your setup consider increasing this value.

### Restore on deactivation
You can set up Stateful Scenes to restore the state of the entities when you want to turn off a scene. This can also be configured per Stateful Scene by going to the device page.

### Transition time
Furthermore, you can specify the default transition time for applying scenes. This will gradually change the lights of a scene to the specified state. It does need to be supported by your lights.

### Debounce time

After activating a scene by turning on a stateful scene switch, entities may need some time to achieve their desired states. When first turned on, the scene state switch will be assumed to be 'on'; the debounce time setting controls how long this integration will wait after observing a member entity state update event before reevaluating the entity state to determine if the scene is still active. If you're having issues with scenes immediately deactivating/reactivating, consider increasing this debounce time.

### Supported attributes
Note that while all entity states are supported only some entity attributes are supported at the moment. For the entities listed in the table the state is supported as well as the attributes in the table. Please open an issue, if you want support for other entity attributes.

| Entity Domain  | Attributes                               |
|----------------|------------------------------------------|
| `light`        | `brightness`, `rgb_color`, `effect`      |
| `cover`        | `position`                               |
| `media_player` | `volume_level`, `source`                 |
| `fan`          | `direction`, `oscillating`, `percentage` |


## Scene configurations
For each scene you can specify the individual transition time and whether to restore on deactivation by changing the variables on the scene's device page.


## HomeKit configuration
Once you have configured this integration, you can add the scenes to HomeKit. I assume that you already set up and configured the HomeKit integration. Expose the newly added switches to HomeKit. Then, in HomeKit define scenes for each Stateful Scenes switch.
