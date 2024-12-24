# Changelog

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
