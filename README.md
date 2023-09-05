# Stateful Scenes
> Do you want to use your Home Assistant scenes in HomeKit, but get annoyed when the scenes do not stay ‘on’? 

Stateful Scenes solves this problem by creating a switch for each scene and inferring the state of the scene by analysing the entities in the scene. Plus, when you activate a scene in Home Assistant, the scene will also turn on in HomeKit—magic!

## Installation
### HACS (not yet available)
Install via [HACS](https://hacs.xyz) by searching for `stateful scenes` in the integrations section

### Manal
Or, clone the repositort and copy the custom_components folder to your home assistant config folder.

```bash
git clone https://github.com/hugobloem/stateful_scenes.git
cp -r stateful_scenes/custom_components config/
```

## Configuration
Add the following code to your configuration to configure Stateful Scenes:
```yaml
switch:
  - platform: stateful_scenes
```
By default Home Assistant places all scenes inside `config/scenes.yaml` which is where this integration retrieves the scenes. If your configuration has a different location for scenes you can change the location by changing the `scene_path` variable.

Note that not all entities are supported yet. For the entities listed in the table the state is supported as well as the attributes in the table. Please open an issue if you want support for other entity domains and/or attributes.

| Entity Domain  | Attributes                 |
|----------------|----------------------------|
| `light`        | `brightness`, `rgb_color`  |
| `cover`        | `position`                 |
| `media_player` | `volume_level`, `source`   |

## HomeKit configuration
Once you have configured this integration, you can add the scenes to HomeKit. I assume that you already set up and configured the HomeKit integration. Expose the newly added switches to HomeKit. Then, in HomeKit define scenes for each of the switches defined by Stateful Scenes. 
