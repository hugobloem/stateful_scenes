# Changelog

## [1.7.8](https://github.com/hugobloem/stateful_scenes/compare/v1.7.7...v1.7.8) (2026-02-07)


### 🐛 Bugfixes

* Handle None values from empty YAML fields to prevent AttributeError (fixes [#212](https://github.com/hugobloem/stateful_scenes/issues/212)) ([#231](https://github.com/hugobloem/stateful_scenes/issues/231)) ([cb26807](https://github.com/hugobloem/stateful_scenes/commit/cb26807266e8d6125250f24deb434704c8fd7247))


### 🔧 Miscellaneous Chores

* **deps:** update pip requirement from &lt;25.4,&gt;=24.1.1 to &gt;=24.1.1,&lt;26.1 ([#234](https://github.com/hugobloem/stateful_scenes/issues/234)) ([6b1ed00](https://github.com/hugobloem/stateful_scenes/commit/6b1ed00ad87273d358ebe198bc13825229702b97))

## [1.7.7](https://github.com/hugobloem/stateful_scenes/compare/v1.7.6...v1.7.7) (2025-12-01)


### 🐛 Bugfixes

* Add Home Assistant version to hacs.json ([#228](https://github.com/hugobloem/stateful_scenes/issues/228)) ([53ac523](https://github.com/hugobloem/stateful_scenes/commit/53ac523f7d5d2fcad4c5dc6df04a213def468cbe))

## [1.7.6](https://github.com/hugobloem/stateful_scenes/compare/v1.7.5...v1.7.6) (2025-11-30)


### 🔧 Miscellaneous Chores

* resolve_area_id not available before 2025.12.0 ([#225](https://github.com/hugobloem/stateful_scenes/issues/225)) ([fa04147](https://github.com/hugobloem/stateful_scenes/commit/fa04147669d5b58137c2f8a7e69d0fe6fb18b83a))

## [1.7.5](https://github.com/hugobloem/stateful_scenes/compare/v1.7.4...v1.7.5) (2025-11-30)


### 🐛 Bugfixes

* import issue 2025.12 ([#223](https://github.com/hugobloem/stateful_scenes/issues/223)) ([433855f](https://github.com/hugobloem/stateful_scenes/commit/433855f703d43e6d350437b2fe8f271036b7ea7e))


### 🔧 Miscellaneous Chores

* **deps:** bump actions/checkout from 5 to 6 ([#222](https://github.com/hugobloem/stateful_scenes/issues/222)) ([6ee180b](https://github.com/hugobloem/stateful_scenes/commit/6ee180bddee4652e1284901f7c11815cf311a189))
* **deps:** update pip requirement from &lt;25.3,&gt;=24.1.1 to &gt;=24.1.1,&lt;25.4 ([#221](https://github.com/hugobloem/stateful_scenes/issues/221)) ([524ef9c](https://github.com/hugobloem/stateful_scenes/commit/524ef9c5f08c6734a6e04d556c78f8c185600381))

## [1.7.4](https://github.com/hugobloem/stateful_scenes/compare/v1.7.3...v1.7.4) (2025-10-21)


### 🐛 Bugfixes

* YAML boolean state parsing issue ([#220](https://github.com/hugobloem/stateful_scenes/issues/220)) ([153f477](https://github.com/hugobloem/stateful_scenes/commit/153f477285ca2d15928ebb6e8ef645d14ce4e5b9))


### 🔧 Miscellaneous Chores

* **deps:** bump astral-sh/setup-uv from 6 to 7 ([#218](https://github.com/hugobloem/stateful_scenes/issues/218)) ([4a45195](https://github.com/hugobloem/stateful_scenes/commit/4a45195011908c3dd98240656db7827309d26854))

## [1.7.3](https://github.com/hugobloem/stateful_scenes/compare/v1.7.2...v1.7.3) (2025-08-19)


### 🐛 Bugfixes

* Robust handling of None values in scene configurations ([#213](https://github.com/hugobloem/stateful_scenes/issues/213)) [@thorstenhornung1](https://github.com/thorstenhornung1) ([e969b8b](https://github.com/hugobloem/stateful_scenes/commit/e969b8bf55a0d4598fa17128511d460ef4b234c8))


### 🔧 Miscellaneous Chores

* **deps:** bump actions/checkout from 4 to 5 ([#215](https://github.com/hugobloem/stateful_scenes/issues/215)) ([ff1bb83](https://github.com/hugobloem/stateful_scenes/commit/ff1bb83a1e9d3ba913341b5963191342a362f7d1))
* **deps:** update pip requirement from &lt;25.2,&gt;=24.1.1 to &gt;=24.1.1,&lt;25.3 ([#214](https://github.com/hugobloem/stateful_scenes/issues/214)) ([eb0ac29](https://github.com/hugobloem/stateful_scenes/commit/eb0ac299c05530cea85315c4359006c896803b43))

## [1.7.2](https://github.com/hugobloem/stateful_scenes/compare/v1.7.1...v1.7.2) (2025-07-05)


### 🐛 Bugfixes

* cleanup orphaned entities and devices when scenes are removed ([#208](https://github.com/hugobloem/stateful_scenes/issues/208)) ([01e235d](https://github.com/hugobloem/stateful_scenes/commit/01e235dad560cc603f0786269a1e37cf9819c934))


### 📝 Documentation

* add ignore attributes and ignore unavailable descriptions ([#207](https://github.com/hugobloem/stateful_scenes/issues/207)) ([52de508](https://github.com/hugobloem/stateful_scenes/commit/52de508fa2741858b15565c5e94e1262a4616584))

## [1.7.1](https://github.com/hugobloem/stateful_scenes/compare/v1.7.0...v1.7.1) (2025-07-03)


### 🐛 Bugfixes

* debounce not applied to storage of previous states ([61e3868](https://github.com/hugobloem/stateful_scenes/commit/61e3868ad10a8a30e932b96f4b162db9d4bfa725))

## [1.7.0](https://github.com/hugobloem/stateful_scenes/compare/v1.6.4...v1.7.0) (2025-05-02)


### 🚀 Features

* ignore attributes checking toggle ([#192](https://github.com/hugobloem/stateful_scenes/issues/192)) ([0d6e37e](https://github.com/hugobloem/stateful_scenes/commit/0d6e37ed3a86b7eb8a5f697299a410c53866013b))


### 🐛 Bugfixes

* convert synchronous methods to asynchronous in StatefulSceneOffSelect ([#200](https://github.com/hugobloem/stateful_scenes/issues/200)) ([a3784df](https://github.com/hugobloem/stateful_scenes/commit/a3784dfa1edf8fa3f01ef3d4cc342cc3efb4513e))
* remove unnecessary await from async_all call ([#201](https://github.com/hugobloem/stateful_scenes/issues/201)) ([761f372](https://github.com/hugobloem/stateful_scenes/commit/761f3726b3d6297a09064baea3050ab0e0fd78df))


### 🔨 Code Refactoring

* simplify state initialization using dict.fromkeys ([#199](https://github.com/hugobloem/stateful_scenes/issues/199)) ([84c3f3c](https://github.com/hugobloem/stateful_scenes/commit/84c3f3c5db276ec5ea517e374f8ab2252e7a4404))


### 🔧 Miscellaneous Chores

* **deps:** bump astral-sh/setup-uv from 5 to 6 ([#196](https://github.com/hugobloem/stateful_scenes/issues/196)) ([f230eae](https://github.com/hugobloem/stateful_scenes/commit/f230eae06fe5d2c318ab574c2a08a0bd6f879249))
* **deps:** update pip requirement from &lt;25.1,&gt;=24.1.1 to &gt;=24.1.1,&lt;25.2 ([#197](https://github.com/hugobloem/stateful_scenes/issues/197)) ([8974ebd](https://github.com/hugobloem/stateful_scenes/commit/8974ebd2a4df4dc00c693663aaeb2ece5685fef5))

## [1.6.4](https://github.com/hugobloem/stateful_scenes/compare/v1.6.3...v1.6.4) (2025-02-25)


### 🐛 Bugfixes

* debounce getter now returns correct value ([#181](https://github.com/hugobloem/stateful_scenes/issues/181)) ([f7a2aeb](https://github.com/hugobloem/stateful_scenes/commit/f7a2aeb2893d376b2336a7795877fe86243a7676))


### 🔧 Miscellaneous Chores

* **deps:** update pip requirement from &lt;24.4,&gt;=24.1.1 to >=24.1.1,<25.1 ([#184](https://github.com/hugobloem/stateful_scenes/issues/184)) ([dcad11c](https://github.com/hugobloem/stateful_scenes/commit/dcad11c6f6f98abff6eca791fd594520dd85ab70))
* Update Python interpreter path and streamline setup script ([#187](https://github.com/hugobloem/stateful_scenes/issues/187)) ([09c2d59](https://github.com/hugobloem/stateful_scenes/commit/09c2d59b23783c12a94e38d020b777fd42e1b95e))

## [1.6.3](https://github.com/hugobloem/stateful_scenes/compare/v1.6.2...v1.6.3) (2025-01-02)


### 🐛 Bugfixes

* Modify the integration to fully use HA async paradigm. ([#175](https://github.com/hugobloem/stateful_scenes/issues/175)) ([31d3dbc](https://github.com/hugobloem/stateful_scenes/commit/31d3dbcb20b4be751efe3f2ced809528b22400de))

## [1.6.2](https://github.com/hugobloem/stateful_scenes/compare/v1.6.1...v1.6.2) (2024-12-31)


### 🐛 Bugfixes

* Fixed off scene select restoration reading unavailable data ([#171](https://github.com/hugobloem/stateful_scenes/issues/171)) ([a4a3e33](https://github.com/hugobloem/stateful_scenes/commit/a4a3e3379f2ff7d2ae2b60ebcb8acb2badc2eb00))

## [1.6.1](https://github.com/hugobloem/stateful_scenes/compare/v1.6.0...v1.6.1) (2024-12-29)


### 🐛 Bugfixes

* address race condition and consider transition time when using debounce ([#167](https://github.com/hugobloem/stateful_scenes/issues/167)) ([efd0423](https://github.com/hugobloem/stateful_scenes/commit/efd0423d00ce21b1a0fa8db5f0b68222f68e6c51))
* If the scene 'on' state includes entities that are off don't check additional attributes ([#168](https://github.com/hugobloem/stateful_scenes/issues/168)) ([1c50f98](https://github.com/hugobloem/stateful_scenes/commit/1c50f98a71a83b6163f3ec180237bcff5c590e52))
* restore off scene during HA restart ([#165](https://github.com/hugobloem/stateful_scenes/issues/165)) ([3aa5776](https://github.com/hugobloem/stateful_scenes/commit/3aa5776b4c0f530d618f3072f329c47b397475e4))

## [1.6.0](https://github.com/hugobloem/stateful_scenes/compare/v1.5.2...v1.6.0) (2024-12-24)


### 🚀 Features

* Add an option to activate another scene when the Stateful Scene is turned off ([dd4ac5c](https://github.com/hugobloem/stateful_scenes/commit/dd4ac5cabe74f02ae297d0b18beaaebf16c1eefc))


### 🔨 Code Refactoring

* allowing the 'off' select to query Hub for some internal scene data ([#159](https://github.com/hugobloem/stateful_scenes/issues/159)) ([7c984b2](https://github.com/hugobloem/stateful_scenes/commit/7c984b27be3d1c02352ff73bd904d5e8056a4090))
* simplify entity attribute retrieval using state_attr ([#162](https://github.com/hugobloem/stateful_scenes/issues/162)) ([aa0eba1](https://github.com/hugobloem/stateful_scenes/commit/aa0eba1f28ec1f6491e0deefaf871e7d113015c4))


### 🔧 Miscellaneous Chores

* **deps:** bump astral-sh/setup-uv from 4 to 5 ([#160](https://github.com/hugobloem/stateful_scenes/issues/160)) ([ba0a613](https://github.com/hugobloem/stateful_scenes/commit/ba0a613347318c10ee34cd3a50bddf04fdbf6bb6))

## [1.5.2](https://github.com/hugobloem/stateful_scenes/compare/v1.5.1...v1.5.2) (2024-12-15)


### 🐛 Bugfixes

* Actual Scene State on Restart (fixes [#1146](https://github.com/hugobloem/stateful_scenes/issues/1146)), thanks to [@sayam93](https://github.com/sayam93) ([d6551c7](https://github.com/hugobloem/stateful_scenes/commit/d6551c70a91b8c811eb7545f34ae9dbcdbd16467))

## [1.5.1](https://github.com/hugobloem/stateful_scenes/compare/v1.5.0...v1.5.1) (2024-12-09)

This release fixes a bug that prevented new installations to be set up.

### 🐛 Bugfixes

* update Hub signature in config flow - fixes [#147](https://github.com/hugobloem/stateful_scenes/issues/147) ([#148](https://github.com/hugobloem/stateful_scenes/issues/148)) ([1b768a8](https://github.com/hugobloem/stateful_scenes/commit/1b768a8bd0da7192ea2a12b2ed989afa6bdebd93))

## [1.5.0](https://github.com/hugobloem/stateful_scenes/compare/v1.4.0...v1.5.0) (2024-12-04)


### 🚀 Features

* set rounding tolerance per scene ([#143](https://github.com/hugobloem/stateful_scenes/issues/143)) ([dd4448f](https://github.com/hugobloem/stateful_scenes/commit/dd4448f98c6d3483603f431394245c73d18476d9))


### 🐛 Bugfixes

* do not restore attributes when the state to restore is "off" ([#145](https://github.com/hugobloem/stateful_scenes/issues/145)) ([3567fd1](https://github.com/hugobloem/stateful_scenes/commit/3567fd196aa8aadf9747159c8afcdd3cb9611cd6))
* force store entity state when turning on ([#145](https://github.com/hugobloem/stateful_scenes/issues/145)) ([3567fd1](https://github.com/hugobloem/stateful_scenes/commit/3567fd196aa8aadf9747159c8afcdd3cb9611cd6))
* move imports source in config_flow.py ([e7c8af8](https://github.com/hugobloem/stateful_scenes/commit/e7c8af8becdaaff0491c3c5374694031b1c0059f))
* non-blocking file reading for scenes configuration ([#141](https://github.com/hugobloem/stateful_scenes/issues/141)) ([07e09d5](https://github.com/hugobloem/stateful_scenes/commit/07e09d55e05bf707ccf2b6d26b5209a737ea573a))


### 🔨 Code Refactoring

* scene file importing improvements ([#144](https://github.com/hugobloem/stateful_scenes/issues/144)) ([e1ee6d4](https://github.com/hugobloem/stateful_scenes/commit/e1ee6d48bc3abf453a943d4be2a6b3f33ce23b33))


### 🔧 Miscellaneous Chores

* **deps:** bump astral-sh/setup-uv from 3 to 4 ([#138](https://github.com/hugobloem/stateful_scenes/issues/138)) ([8d152ad](https://github.com/hugobloem/stateful_scenes/commit/8d152ad26970f90de3f2f37ae008ec53d61421fa))

## [1.4.0](https://github.com/hugobloem/stateful_scenes/compare/v1.3.2...v1.4.0) (2024-11-15)


### 🚀 Features

* add option to ignore unavailable entities ([#136](https://github.com/hugobloem/stateful_scenes/issues/136)) ([dff74e5](https://github.com/hugobloem/stateful_scenes/commit/dff74e5b27968d86424915a36409224e8fa45124))


### 🐛 Bugfixes

* correct documentation link ([#132](https://github.com/hugobloem/stateful_scenes/issues/132)) ([c096a14](https://github.com/hugobloem/stateful_scenes/commit/c096a144d3da1ceeb9b19e0a65b3a74433cca2d0))


### 🔧 Miscellaneous Chores

* **dev:** add recommended extensions for Python development ([#135](https://github.com/hugobloem/stateful_scenes/issues/135)) ([18c682d](https://github.com/hugobloem/stateful_scenes/commit/18c682d23f8298cbacc6b0448985d4070eeb15eb))
* **dev:** update Python image version and install dependencies ([#134](https://github.com/hugobloem/stateful_scenes/issues/134)) ([06c72ae](https://github.com/hugobloem/stateful_scenes/commit/06c72ae02ee833f23111856ad2b9d789b54bc532))


### 👷 Continuous Integration

* use uv in lint.yaml ([#137](https://github.com/hugobloem/stateful_scenes/issues/137)) ([5bc5c6e](https://github.com/hugobloem/stateful_scenes/commit/5bc5c6e3e8b0ec1e4126e01d02d27d5be3dac575))

## [1.3.2](https://github.com/hugobloem/stateful_scenes/compare/v1.3.1...v1.3.2) (2024-11-03)


### 🐛 Bugfixes

* **scene:** do not restore if already off ([#127](https://github.com/hugobloem/stateful_scenes/issues/127)) ([4166e78](https://github.com/hugobloem/stateful_scenes/commit/4166e789d52b7bdea17db58452980e358b40fb07))


### 🔧 Miscellaneous Chores

* **deps:** update pip requirement ([#125](https://github.com/hugobloem/stateful_scenes/issues/125)) ([fac5978](https://github.com/hugobloem/stateful_scenes/commit/fac597855d1cf24bb0686ddf5a2cef59d25b7070))


### 👷 Continuous Integration

* **release:** auto update manifest.json ([#128](https://github.com/hugobloem/stateful_scenes/issues/128)) ([8547d54](https://github.com/hugobloem/stateful_scenes/commit/8547d54ac20416df4a77eeba96aff55f82da7803))
* **release:** fix jsonpath ([#129](https://github.com/hugobloem/stateful_scenes/issues/129)) ([8c14432](https://github.com/hugobloem/stateful_scenes/commit/8c1443259076ff7fb06d2c86f48b9da9290c4b72))

## [1.3.1](https://github.com/hugobloem/stateful_scenes/compare/1.3.0...v1.3.1) (2024-10-18)


### 🐛 Bugfixes

* areas incorrectly resolved ([76ff77b](https://github.com/hugobloem/stateful_scenes/commit/76ff77b6d0c8efd9a8e316e865f89361afbba2e3))
* areas incorrectly resolved ([#119](https://github.com/hugobloem/stateful_scenes/issues/119)) ([85323e1](https://github.com/hugobloem/stateful_scenes/commit/85323e12bf53ce954a4f393a41d3080bdf26ce3b))
* **ci:** Rename release-please-manifest.json to .release-please-manifest.json ([#121](https://github.com/hugobloem/stateful_scenes/issues/121)) ([64a97e2](https://github.com/hugobloem/stateful_scenes/commit/64a97e253fa3c90f54ec6b7b6112135c5d32d223))


### 👷 Continuous Integration

* add pr-require-conventional-commit.yaml ([#123](https://github.com/hugobloem/stateful_scenes/issues/123)) ([e9e2c94](https://github.com/hugobloem/stateful_scenes/commit/e9e2c94cd4eedf2bdd8ab74caa91c52a260093a5))
* add release-please ([#120](https://github.com/hugobloem/stateful_scenes/issues/120)) ([fa3b082](https://github.com/hugobloem/stateful_scenes/commit/fa3b0827ae08c2d248fd445582443c5defce461c))
