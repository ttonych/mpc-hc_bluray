# Fork changes

[Русский](CHANGELOG.ru.md)

## Unreleased — local development

- Start from official MPC-HC 2.8.2 with original history and LAV pins preserved.
- Port the donor process-query safety fix: update only the PEB debug byte,
  validate query results and buffers, and handle the full debug-port value.
- Import libbluray 1.5.0 native/Java patch manifests and component regressions;
  add x64 build/check scripts, source provenance and bilingual developer docs.
- Add experimental Blu-ray navigation, keyboard/mouse input, madVR overlay
  and a separate menu audio graph.
- Add maintained LAV PID-selection and PlayItem read-boundary patches; keep
  LAV's internal library separate from the libbluray 1.5.0 navigation runtime.
- Build fresh DLL/JARs, pin Java 21.0.12.1+1 x64 and check HAVi, overlay,
  coordinates, clock and LAV software decoding through a Null Renderer.
- Observe an initial HDMV menu with madVR in the local Russian portable player.
  One authored BD-J menu/film-start/return cycle also passes with pinned Java.
  Broad disc coverage and BD-J mouse input remain open; exact madVR 210 is verified below.
  The MSVC LAV configuration differs from the normal GCC build; no release yet.
- Connect standard navigation commands and their menu availability to Blu-ray:
  Alt+T/top menu, Alt+R/popup, directions, activation and leave; respect disc restrictions.
- Added disc captions and hiding chapter markers on normal/OSD seek bars while menus are active.
- In Blu-ray navigation, LAV preserves authored gaps between sparse frames;
  ordinary playback retains its previous discontinuity repair.
- Adapt MPC-BE isolated MPEG-2 still repetition and sequence-end release to LAV;
  the previously black startup warning is visible with madVR in the local player.
- Normal Blu-ray opening follows the menu/main-movie preference; main movie
  remains the default.
- Add a native EN/RU Blu-ray options page for region/languages, Java discovery/path
  and separate BD-J save/cache folders, with validated Apply and safe Cancel.
- Remove the temporary separate Open Blu-ray Menu command; normal Open DVD/BD
  follows the opening preference. Add a compatibility dialog with 14 settings,
  EN/RU descriptions, preset/numeric validation and draft-only defaults.

- Preserve explicit 32-bit compatibility masks, including 0xFFFFFFFF, after
  restarting the player; keep default and explicit choices distinct across translations.

- Add the EN/RU disc-data catalogue: search, aliases, legacy groups, folder
  access and per-disc reset retaining previous saved data and cache.
- Check JVM architecture before applying Java paths; add bounded, cancellable
  java -version diagnostics outside the player.
- Keep native fullscreen controls available when Blu-ray menus handle mouse movement.
- Open dropped ISO images through a read-only Windows virtual drive, following
  the Blu-ray menu/movie preference. Keep it through graph changes and release
  the owned attachment on close; preserve external mounts and report errors.

- Validate ISO replacement/unmount, exact madVR 210 identity and H.264/HEVC10/AV1/
  MPEG-2 ordinary files. D3D11 fullscreen windowed is the primary mode.
- Add publication/history/author checks, bilingual usage/validation records, fast
  PR checks, manual cloud build and clean allowlist ZIP packaging.
