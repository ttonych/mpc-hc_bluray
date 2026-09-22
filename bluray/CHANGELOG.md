# Fork changes

[Русский](CHANGELOG.ru.md) · [Versioning and releases](docs/RELEASING.md)

This is the history of MPC-HC Blu-ray additions to the official player.
For changes in the base player, see the [official MPC-HC 2.8.2 notes](https://github.com/clsid2/mpc-hc/releases/tag/2.8.2).
Entries become dated version sections when a release is published.

## Unreleased

Planned first release: **2.8.2-bluray.1**, based on official MPC-HC **2.8.2**.
No Release has been published. Candidate identities and verification results
are recorded separately in [Validation](docs/VALIDATION.md).

### Added

- Mandatory portable settings and EN/RU first-run registry/INI import, with
  HLSL subfolder copying and unchanged sources. History/playlists and BD-J saves
  are excluded; a write failure never selects the installed player profile.
- Offline EN/RU HTML guides in the ZIP, with embedded styles and checked links.

- Experimental HDMV/BD-J navigation, keyboard and authored mouse input, madVR
  menu graphics and a separate menu audio graph.
- Standard top/popup menu commands (Alt+T/Alt+R), disc captions and chapter
  markers that hide in menus and return during film playback.
- Normal disc/folder opening with a main-movie/menu preference. The first-run wizard
  selects Disc menu; the temporary separate menu-opening command was removed.
- Read-only Windows ISO opening, including drag-and-drop. Player-owned mounts
  survive graph changes and release on close; external mounts are preserved
  and mounting errors are reported.
- Native English/Russian Blu-ray settings for region/languages, Java and
  separate BD-J save/cache paths, with validated Apply and safe Cancel.
- Compatibility settings with 14 libbluray preferences, descriptions, presets
  and draft-only defaults.
- Disc-data catalogue with search, aliases, folder access and per-disc reset
  that retains previous saves/cache.
- JVM architecture validation and bounded, cancellable Java startup diagnostics
  in a separate process.

- Fork version in About, EXE ProductVersion and the empty window caption, from
  one header shared with packaging. About also identifies the source revision.
- Update checks for this fork's published GitHub releases, including prereleases,
  with numeric comparison, a normal empty-release result and release-page links.

### Fixed

- Upstream revision calculation ignores fork and unrelated tags; package checks
  reject stale EXE/ProductVersion and mismatched Russian resource versions.
- Standard Blu-ray menu command availability and routing, respecting disc restrictions.
- LAV navigation timestamps preserve authored sparse-frame gaps; isolated MPEG-2
  still repetition and sequence-end handling fix the observed black startup warning.
  Ordinary playback retains its prior discontinuity policy.
- Native fullscreen controls remain reachable when Blu-ray handles mouse movement.
- Explicit 32-bit compatibility masks, including 0xFFFFFFFF, survive restart and
  remain distinct from automatic values across translations.
- Process-query handling updates only the PEB debug byte, validates results and
  buffers, and handles the full debug-port value.
- Corrupted Russian navigation text in the English README; fast checks now reject
  invalid UTF-8 and missing/corrupted paired-language links.

### Components, build and documentation

- Preserve official MPC-HC 2.8.2 history and LAV pins.
- Integrate libbluray 1.5.0 native/Java patches for menu mouse pages, seek marks
  and HAVi toggle behavior; record source hashes, provenance and component tests.
- Maintain the LAV PID/PlayItem/timestamp/still adapter separately from LAV's
  internal libbluray. Pin Temurin 21.0.12.1+1 x64 for current build/runtime checks.
- Add x64/EN/RU build scripts, actual-JAR and native regressions, publication/
  history/author checks, fast PR checks and manual cloud candidate builds.
- Package an explicit runtime/license/document file list with a clean portable INI.
  Java and madVR stay external; D3D11 fullscreen windowed is the primary madVR mode.
- Expand paired setup, Java, saves, troubleshooting, contribution and release
  guides; document the upstream-base/fork-release numbering scheme.

### Known limitations

- This remains experimental. Cloud candidate BD-J qualification and wider disc,
  Java/saves and mouse-capable-menu coverage are incomplete.
- The MSVC LAV configuration differs from the standard GCC build; full codec/audio
  parity, HDR accuracy, MVC/stereo and DVD ISO support are unqualified.
- The old cloud ZIP predates fork branding/updater, setup and HTML guides.
- See [Validation](docs/VALIDATION.md) for the distinction between component
  tests, local playback, user reports and checks of the exact cloud ZIP.
