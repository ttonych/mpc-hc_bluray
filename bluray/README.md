# MPC-HC Blu-ray integration

[Русский](README.ru.md)

Development starts from official MPC-HC **2.8.2**, preserving its history and
LAV-based playback. Common Blu-ray work comes from MPC-BE Blu-ray at a pinned
commit. The local prototype adds **File > Open Blu-ray Menu**, a libbluray
navigation engine and an adapter for LAV. Native/JAR builds and component
checks pass. HDMV menu/film startup and one BD-J menu/film/return cycle were observed with madVR; broader disc testing and exact madVR 210 compatibility still require validation.

- [Source pins](sources.json) and [imported file provenance](imports.json)
- [Development](docs/DEVELOPMENT.md)
- [Porting log](docs/PORTING.md)
- [Roadmap](docs/ROADMAP.md)
- [Fork changes](CHANGELOG.md)

The target is Windows x64, libbluray 1.5.0 with maintained patches, external
Java and external madVR 210 x64. LAV's internal libbluray is a separate pinned
dependency; the new navigation runtime is not a drop-in replacement for it.
Upstream documentation and attribution remain in their original locations.
