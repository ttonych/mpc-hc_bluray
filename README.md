# MPC-HC Blu-ray

[Русский](README.ru.md) · [User guide](bluray/docs/USAGE.md) · [Changelog](bluray/CHANGELOG.md) · [Development](bluray/docs/DEVELOPMENT.md) · [Roadmap](bluray/docs/ROADMAP.md)

**Blu-ray HDMV and BD-J menus in MPC-HC, using libbluray and madVR.**

This independent, experimental Windows x64 fork is based on official **MPC-HC
2.8.2**, with **libbluray 1.5.0** and maintained patches. Common Blu-ray work
comes from [MPC-BE Blu-ray](https://github.com/ttonych/mpc-be_bluray). MPC-HC keeps
its own interface, playback graph and LAV filters, with a maintained LAV adapter.

The target for the first fork release is **2.8.2-bluray.1**. The prefix identifies
the MPC-HC base; the final number counts fork releases on that base. See
[versioning and releases](bluray/docs/RELEASING.md). Current sources show the
fork version in the EXE/About and check this fork's published GitHub releases.

## Test build and quick start

There is no qualified Release yet. The current cloud candidate is available from
[Actions run 35828150183](https://github.com/ttonych/mpc-hc_bluray/actions/runs/35828150183),
artifact `mpc-hc-bluray-candidate-x64`. GitHub sign-in may be required; artifacts
are retained for 14 days. Its exact commit, ZIP SHA-256 and completed checks are
recorded in [Validation](bluray/docs/VALIDATION.md). This exact ZIP passes LAV v4
read-error/recovery, portable import, ordinary decoding and bounded HDMV/BD-J
visual checks with madVR 210 in D3D11 fullscreen windowed mode.

1. Extract the inner player ZIP into a new writable folder. On first launch,
   choose settings import or defaults; the profile always stays beside the EXE.
2. Make sure the x64 Microsoft Visual C++ v14 runtime is installed; see
   [requirements](bluray/docs/USAGE.md#requirements-and-first-launch).
3. Use an external **madVR 210 x64** installation and select **Options → Playback
   → Output → madVR**. The primary fullscreen mode is **D3D11 fullscreen windowed**.
   The fork does not enable exclusive or alter global madVR settings.
4. For BD-J, select x64 Java in **Options → Playback → Blu-ray**. The tested
   version is **Temurin 21.0.12.1+1**; HDMV does not need Java.
5. Select **Disc menu** or **Main movie** on that page. Open the whole disc or
   `BDMV/index.bdmv`, or drop an ISO into the player. Opening a playlist or clip
   directly plays that item without full disc navigation.

Use arrows and **Enter** in menus, **Alt+T** for the top menu and **Alt+R** for the
popup menu. Disc authoring determines mouse support and permitted operations.
There is no separate Open Blu-ray Menu command.

## What the fork adds

- HDMV/BD-J navigation and menu graphics through madVR.
- Keyboard navigation and mouse input where the disc implements it.
- Disc captions, menu/film chapter-marker handling, menu audio and MPEG-2 still handling.
- Normal Blu-ray/ISO opening that follows the menu/main-movie preference.
- Native EN/RU settings for region, languages, Java, compatibility and disc data.
- A disc-data catalogue with aliases and per-disc reset that retains old files.
- Read-only native Windows ISO mounting; player-owned mounts are released on close.

The feature list describes the implementation, not compatibility with every disc.
Local tests and tests of the downloadable ZIP are listed separately in
[Validation](bluray/docs/VALIDATION.md).

## Profiles and updates

Current builds enforce a portable profile and offer first-run import of MPC-HC
settings from registry or INI. The source remains unchanged; history, playlists
and BD-J saves are not imported. A write failure reports an error. madVR and
external filters may still share system settings. See the
[profile guide](bluray/docs/USAGE.md#profiles-and-updates).

The current candidate checks published releases of **ttonych/mpc-hc_bluray**,
including prereleases, and offers their GitHub page without installing anything.
See [profiles and updates](bluray/docs/USAGE.md#profiles-and-updates).

## Current limits

- Menu graphics require madVR; other renderers are not validated for this path.
- The current cloud ZIP has bounded HDMV/BD-J menu, film, return, track/chapter,
  startup-still, ISO, ordinary-file and EN/RU setup coverage. This is a test candidate.
- Broad disc/Java/saves coverage, positive BD-J mouse coverage, full codec/audio
  parity, DVD ISO, HDR accuracy and MVC/stereo output remain unqualified.
- Compatibility preferences report capabilities to disc applications; they do
  not add decoders or prove support for every advertised feature.
- Java, madVR and disc-decryption components are not included. Disc contents
  must already be readable. Direct ISO opening requires native Windows attachment.
  For externally mounted images, open the drive or `BDMV/index.bdmv`.
  See [opening](bluray/docs/USAGE.md#opening-a-disc-or-iso).
- The MSVC LAV build uses built-in decoders and omits GCC-only external dependencies.

For symptoms and useful report details, see
[troubleshooting](bluray/docs/USAGE.md#troubleshooting-and-feedback).

New ZIPs also contain `Readme.html`, `Readme.ru.html` and paired HTML guides
for offline reading.

## Documentation and attribution

| Document | Contents |
| --- | --- |
| [User guide](bluray/docs/USAGE.md) | Setup, Java, opening, controls, settings, saves and troubleshooting |
| [Development](bluray/docs/DEVELOPMENT.md) | Source checkout, pinned tools, local builds, tests and component updates |
| [Contributing](CONTRIBUTING.md) | Branches, PRs, resources and publication checks |
| [Versioning and releases](bluray/docs/RELEASING.md) | Version numbers, manual Actions, candidate verification and publication |
| [Validation](bluray/docs/VALIDATION.md) / [Roadmap](bluray/docs/ROADMAP.md) | Evidence, limits and unfinished work |
| [Feature comparison](bluray/docs/PARITY.md) | Committed MPC-BE/HC additions, gaps and validation differences |
| [Porting log](bluray/docs/PORTING.md) / [Fork changes](bluray/CHANGELOG.md) | Donor adaptation and visible changes |

The original [MPC-HC](https://github.com/clsid2/mpc-hc) history,
[authors](docs/Authors.txt) and [license](COPYING.txt) are retained. Common menu
work is credited to [MPC-BE's authors](bluray/ports/MPC-BE-Authors.txt);
[sources.json](bluray/sources.json) and [imports.json](bluray/imports.json)
record component pins and provenance. Library patches are maintained by this
integration and are not claims of upstream acceptance.
