# MPC-HC Blu-ray integration

[Русский](README.ru.md)

Development starts from official MPC-HC **2.8.2**, preserving its history and
LAV-based playback. Common Blu-ray work comes from MPC-BE Blu-ray at a pinned
commit. Normal disc/folder/ISO opening follows the menu/main-movie preference;
there is no separate menu-opening command. The fork adds a libbluray navigation
engine, an adapter for LAV and native EN/RU settings. Native/JAR builds and
component checks pass. HDMV and one bounded BD-J cycle were observed; exact
madVR 210 identity is confirmed. D3D11 fullscreen windowed is the primary mode.
Broader disc testing and qualification of the exact cloud ZIP remain open.

- [Source pins](sources.json) and [imported file provenance](imports.json)
- [Development](docs/DEVELOPMENT.md)
- [Porting log](docs/PORTING.md)
- [Roadmap](docs/ROADMAP.md)
- [Fork changes](CHANGELOG.md)
- [Versioning and releases](docs/RELEASING.md) and [contributing](../CONTRIBUTING.md)
- [Usage](docs/USAGE.md) and [validation scope](docs/VALIDATION.md)

The target is Windows x64, libbluray 1.5.0 with maintained patches, external
Java and external madVR 210 x64. LAV's internal libbluray is a separate pinned
dependency; the new navigation runtime is not a drop-in replacement for it.
Upstream documentation and attribution are retained; the original contribution
guide is preserved as [UPSTREAM-CONTRIBUTING.md](../docs/UPSTREAM-CONTRIBUTING.md).
