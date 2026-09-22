# MPC-HC Blu-ray

[Р СѓСЃСЃРєРёР№](README.ru.md) В· [Usage](bluray/docs/USAGE.md) В· [Development](bluray/docs/DEVELOPMENT.md) В· [Roadmap](bluray/docs/ROADMAP.md)

An experimental Windows x64 fork of MPC-HC 2.8.2 with libbluray 1.5.0 HDMV/BD-J
menus and madVR integration. Selected common components come from
[MPC-BE Blu-ray](https://github.com/ttonych/mpc-be_bluray); MPC-HC keeps its own
interface, playback graph and maintained LAV adapter.

Open a Blu-ray disc, folder or ISO through the normal player commands. The
Blu-ray settings page selects menus or the main movie and configures Java,
languages, region, compatibility and disc saved data. Native Windows ISO mounting
is used; mounts created by the player are released on close or replacement.

madVR 210 x64 and Java are external installations. BD-J was tested with Temurin
21.0.12.1+1 x64. D3D11 fullscreen windowed is the primary fullscreen configuration;
the fork does not enable exclusive mode or change global madVR settings.

This is development software. Local/cloud observations and remaining gaps are recorded
in [Validation](bluray/docs/VALIDATION.md). HDR accuracy, MVC stereo output and
compatibility with all discs are not established. The MSVC LAV build uses built-in
decoders; GCC-only external codec dependencies are absent.

The official [MPC-HC](https://github.com/clsid2/mpc-hc) history, authors and
licenses are retained. See [COPYING](COPYING.txt), [port provenance](bluray/docs/PORTING.md),
[component pins](bluray/sources.json) and [fork changes](bluray/CHANGELOG.md).
Full candidate builds run manually in Actions; a Release is qualified only after
testing the exact cloud ZIP with a clean portable profile.
