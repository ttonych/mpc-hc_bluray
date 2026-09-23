# Porting log

[Русский](PORTING.ru.md)

Donor snapshot: [270cfdd](https://github.com/ttonych/mpc-be_bluray/commit/270cfdd4369224dd4108d0b1d1b8a4ab7b8fc56d).
HC baseline: [2.8.2 / a84d0cf](https://github.com/clsid2/mpc-hc/commit/a84d0cf38a1866f3518bb819c901300dacff5a9b).
Destination: initial port commit `5004099` and follow-up fixes, accepted through
[PR #1](https://github.com/ttonych/mpc-hc_bluray/pull/1). There is no published
Release. Current candidate checks and outstanding limits are in [Validation](VALIDATION.md).

## Initial port snapshot, 2026-09-22

The initial table and checks below are historical. Later entries record completed
follow-up work; an open item in this initial snapshot is not the current status.

| Donor change | Purpose and HC adaptation | Status and HC checks, 2026-09-22 |
| --- | --- | --- |
| Process query hook, `4c11331253f27fee0e37c0ac369e2427af83bc42` | Replace the stale whole-PEB write with one byte, validate NTSTATUS/pointers/lengths, clear pointer-sized debug port. Apply to `src/mpc-hc/mplayerc.cpp`; retain HC formatting. | Applied. Actual HC function passes donor regression under MSVC x64. Original HC function fails the negative control on whole-PEB write. Player core Release x64 builds before and after. |
| `mouse-page-v1` then `playmark-seek-v1`, snapshot above | Native menu hit-testing and mark delivery at seek boundaries; patch bytes/manifests unchanged. | Imported. Hashes, clean/repeated application, known intermediate stage, refusal to overwrite edits and synthetic mark tracker pass. Fresh x64 DLL built; required exports/version verified and loaded by the HC menu engine. |
| `bdj-toggle-v1`, snapshot above | HAVi toggle action/state handling; patch bytes/manifests unchanged. | Imported. Patch application/integrity checks pass. Both JARs built with pinned Java; HAVi regression passes against the actual JAR (toggle ordering, virtual dispatch, direct action, release, sounds and disabled/grouped controls). |
| Navigation, overlays, clock, RLE and menu input | Share algorithms; adapt HC MainFrm/graph and madVR access. | Imported engine and component tests; new HC graph/input adapter compiles. One authored HDMV menu, scene page and film start were visually observed with madVR. Return from film is logged; its final frame and broader coverage remain unconfirmed. |
| BE splitter and decoder changes | PID stream mapping, PlayItem boundary, PTS/stills/EOS behavior. | Adapted as maintained `hc-menu-bridge-v3` LAV patch: transport PID mapping, cached atomic PlayItem read boundary and presentation start. Component tests, full MSVC filter build and software decode to Null Renderer pass. MPEG-2 stills/EOS are adapted in LAV avcodec; release codec parity remains open. |
| Portable profiles, BD-J storage, packaging and publication checks | Keep test storage isolated and public output clean. | Fresh portable copy assembled from an explicit file list; local BD-J storage and manifests included. GUI HDMV smoke test started. Publication/history scanning and release ZIP remain pending. |

Test runner changes are limited to HC paths, MSVC support and unattended failure
reporting. [imports.json](../imports.json) records donor file hashes. Shared
patch manifests still carry the donor's file and patch checksums.

## Initial validation and remaining work

- Visual Studio 2022 17.14, MSVC 14.44.35207, SDK 10.0.19041.0, NASM 2.16.03.
- Player Release x64, embedded English resources and Russian language DLL build.
- Bootstrap/patch-chain, process-query, RLE, ARGB, coordinates, clock, menu audio,
  background, LAV bridge and actual-JAR HAVi regressions pass.
- All LAV dependencies are checked out at their original recorded commits.
  The local MSVC build passes, including all three LAV filters and FFmpeg.
  Its Schannel/software AV1 configuration omits GCC-only external dependencies;
  it is a prototype configuration, not a claim of release codec parity.
- Local COM smoke test opens the canvas and decodes video through the built LAV
  source/decoder to Null Renderer. In the GUI, the same local LAV filters and
  registered x64 madVR were loaded; the canvas is black by design.
- In the Russian portable player, an HDMV main menu, scene page and film start
  (including subtitles) were visually observed with madVR. Mouse selection,
  Home from the scene page and Enter to start the film worked. Logs show the
  intro transition, OSD attachment, successful PID selection and return from
  film. Screen capture was intermittent, so the final return frame remains
  unconfirmed. Audio quality, stills and broader disc coverage remain open.
- The registered madVR reports file version 0.92.17.0; that alone does not prove
  beta 210. Exact renderer build, broader BD-J coverage, ordinary-file
  regression coverage, English GUI and release ZIP validation remain open.
- The donor's uncommitted Java-selection UI experiment is not part of this port.

User confirmation, 2026-09-22: the HDMV disc tested above worked without observed problems; keyboard and mouse are provisionally accepted. This is user confirmation, separate from automated tests and agent observations.

## BD-J opening check, 2026-09-22

The separate Open Blu-ray Menu command started an authored BD-J disc with the
pinned Java 21.0.12.1+1 runtime. JVM loading and ARGB delivery were confirmed;
menu display, arrow selection, Enter to start the film and Home back to the
menu were visually observed with madVR. A mouse click did not visibly activate
a menu item on this disc; disc mouse support versus integration still needs
investigation. This is one startup/navigation cycle, not broad BD-J coverage.
At this stage normal Open DVD/BD still selected the main movie; see the later
normal-opening/settings entry below.

## Standard navigation commands, 2026-09-22

Port the four menu command/update branches from donor `270cfdd`: Title Menu
(Alt+T by default) calls the Blu-ray top menu; Root Menu (Alt+R) calls the popup.
The same handlers serve the main/context menus and configurable shortcuts.
Direction, activation and leave commands now go to the navigator. Availability
uses its disc restrictions and active-menu state; DVD-only submenu commands
remain disabled. HC loading guards prevent commands during graph changes.
The extracted production-handler regression passes; original HC fails the
negative control. The test also checks unchanged DVD and ordinary-file behavior.

Release x64 rebuild passed. In the running BD-J player, Alt+T reached the top-menu handler and returned to the menu; Alt+R reached the popup handler, and the popup was also visually checked via its command. Native menu states for Title/Root were enabled when allowed. A separate context-menu screenshot was not obtained; it uses the same tested handlers.

### Disc caption, chapters and sparse frames

Adapted `UpdateChapterMarkers`, disc-name resolution and its priority over
internal playlists from the same `270cfdd4369224dd4108d0b1d1b8a4ab7b8fc56d`.
HC retains its chapter preference and title style; menu transitions update both
normal and OSD seek bars without continuous repaint. Every open resolves the
caption again: metadata, volume/folder label, then `Blu-ray`.
`test-navigation-display.py` exercises production methods, transitions, chapter
bag replacement, preferences, no MRU writes and ordinary captions.

LAV patch `hc-menu-bridge-v3` retains the v2 timing fix: generic MPEG-TS
discontinuity repair is disabled only after navigation sets the PlayItem limit.
Ordinary opening retains its prior policy. This preserves authored sparse-frame
gaps but did not, by itself, resolve madVR's black startup screen.

Adapted isolated MPEG-2 I-picture repetition and separate sequence-end submission
from `MPCVideoDec.cpp` at the pinned donor. LAV retains its decoders and EOS flags.
Bounds are 16 MiB per cached packet, 60 seconds and at most 3600 cadence steps;
flush cancels repetition and flush/reinitialization/EOS clear the cache. Preroll
is excluded. Unlike BE, LAV applies playback rate downstream, so cadence here
stays in source timestamp units. Non-parser hardware paths are not verified.
The manifest records provenance, SHA-256 and GPL-3.0-or-later for the additions;
the MPC-BE authors list is preserved. No destination commit/PR yet.

`test-lav-mpeg2-stills.py` compiles the actual parser/repetition methods and checks
cadence, exact compressed bytes, ordinary frames/other codecs, preroll, invalid
bounds, cancellation, errors and reset. A real short playlist yields 170 decoded
frames with software and DXVA2 copy-back. An ordinary I/P/B MPEG-2 sample retains
its original 72 frames. The MKV COM/Null Renderer smoke test passes.

After the user remounted the image, the previously failing clip reads completely;
CRC was a separate source error. In portable HC, the agent visually observed the
warning, its paused frame, the following menu, film start and Alt+T return.
Chapter markers disappear in the active menu, return for film and disappear again
on menu return. The caption was read from HC's window. These are agent observations;
the user confirmed the old build's black screen, not yet the new build.
Disc replacement, fullscreen OSD markers and other stills remain in the broader
matrix; madVR's file version does not independently prove exact beta 210.

## Normal opening and basic settings, 2026-09-22

Adapted the pinned donor's `PPageBluray.cpp/.h` country/language controls and
`BlurayDialogs.cpp` Java/storage handling into one native HC property page.
`imports.json` records the source hashes and partial scope. HC's opening adapter
resolves only disc entry points and routes them by the existing `BluRayMenus`
setting. The default retains main-movie playback; the explicit menu command
overrides the preference. Internal navigation playlists cannot re-enter this
opening path. DVD, individual playlists and ordinary files keep their prior path.
Menu failures are handled without a silent main-movie fallback.

The page validates a draft before saving all fields, preserving existing advanced
values. Cancel/failed Apply writes nothing. Java checks require a real JVM file;
storage changes neither move nor delete data. The donor's full compatibility and
catalogue UI is deferred; its uncommitted Java experiment remains excluded.
`BlurayOpen.h`, HC page integration and the production-method test runner are HC
adaptations. Destination remains the uncommitted local worktree; no PR or release.

`test-bluray-opening-settings.py` compiles actual routing, path validation and
Apply methods with synthetic filesystem/profile fixtures: valid/invalid disc
roots, direct clips/DVD exclusions, navigation guard, handled failures, language
codes, Java layouts, absolute storage paths, atomic save and cancellation pass.
Navigation-display regression and player/EN/RU builds pass. In an isolated GUI,
the agent observed both normal Open DVD/BD modes, explicit menu override, saved
settings after restart, discarded edits on Cancel and the EN/RU page layouts.
With menu mode enabled, an ordinary MPEG-2 sample still displays through madVR.
These are automated results and agent observations, not new user confirmation;
other opening entry points and the broader disc/renderer matrix remain to test.

## Unified opening and compatibility UI, 2026-09-22

Removed the temporary File/context-menu command for explicit menu opening,
including its handler and RU/EN resources. Normal Open DVD/BD uses the existing
opening preference. Adapted pinned `BlurayDialogs.cpp` value choices and paired
resources into a native HC modal editor for all 14 `BlurayAdvancedSettings`
fields. Preset semantics and number validation stay shared; HC keeps a child
draft and persists it only through the parent page's validated Apply.
No decoder, renderer or libbluray playback code changes in this step.

The EN/RU production-helper regression found identical translated labels for
default versus explicit age 255. Selection now follows the preset index/value,
so equal labels cannot discard an explicit override. Tests cover all presets in
both languages, deliberate label collisions, numeric bounds, rejected edits,
selected/all defaults, child Cancel/OK and outer failed/successful Apply.
The disc-data catalogue remains deferred; there is no destination commit/PR yet.

The x64 core and Russian resources build successfully. A live isolated portable
GUI check confirms child Cancel, outer Cancel, invalid-age rejection, explicit
preset selection, Apply, restart, and accepted/cancelled resets. English and
Russian layouts were inspected; all 150 compiled compatibility strings match
the corresponding sources. The standard disc command remains and the temporary
menu-opening command is absent.

Restart testing exposed an HC settings bug: `UINT_MAX` doubled as the missing-key
sentinel, silently discarding an explicit `0xFFFFFFFF` capability mask. Loading
now distinguishes absence using a second fallback without changing the profile
format. The production save/load regression failed before the fix and passes
for 0, INT_MAX, 0x80000000 and UINT_MAX across all unrestricted fields. The live
restart check confirms UINT_MAX as well. These are agent checks; disc playback
was not requalified in this UI/settings step.

## Disc-data catalogue and Java diagnostics, 2026-09-22

The catalogue portion of pinned MPC-BE BlurayDialogs and its storage regression
are adapted to HC's themed modal UI. Shared storage/catalogue algorithms and
disk layout remain unchanged. HC adds current cache-folder access, applied-path
isolation and immediate-operation/retention explanations.

JVM image checks and the asynchronous external version probe are HC additions.
No JVM is loaded into the player by settings. A suspended child is assigned to a
kill-on-close job before resuming; only its standard I/O handles are inherited.
Tests cover PE architecture, JDK8 layout, stdout/stderr, environment isolation,
nonzero exit, output limits, timeout and cancellation. The opening/settings test
now uses artificial PE headers instead of empty JVM files. x64/RU builds pass.

Donor storage regressions, Java process tests and transactional Apply tests pass.
Agent GUI checks cover EN/RU layouts, actual Java version output, search, rename,
legacy reset disabled, cancelled/confirmed reset, retained old files and another
disc, unapplied-path isolation and wrong-architecture Apply rejection. Real saves
were not reset. BD-J playback/reopen after reset remains in the wider disc matrix.
Changes remain local and uncommitted.

## BD-J runtime matrix and fullscreen controls, 2026-09-22

On one authored BD-J disc, the agent reset only a copied catalogue with a synthetic
file in its old persistent root. Reopening resolved the new empty generation and
loaded the intro/menu. Original source hashes and the old marker were retained.
The source contained catalogue entries, not authored Java saves; saved-progress
reset and restoration are therefore still unqualified.

Keyboard selection switched DTS-HD to TrueHD through the disc popup; the requested
PIDs were enabled successfully, and the player status changed accordingly. English
subtitles were visible after selection. Audio was not verified by listening.
Alt+R popup, Alt+T top menu, next/previous chapter, seeking and fullscreen playback
were observed. Native toolbar markers disappeared in menus and returned in film.
Repeated mouse activation on the version/main menus did not respond, including
real pointer input. The user subsequently confirmed that this particular authored
menu does not support mouse input, so this is expected behavior, not an HC defect.
General BD-J mouse support needs a separate positive test on a suitable disc.
The native mouse result 0 means an event was queued in AWT, not button activation.

HC's Blu-ray mouse handler returned before updating toolbar visibility. Moving to
the bottom edge could not reveal native fullscreen controls in a menu, while film
controls worked. The handled branch now updates visibility before returning.
Live before/after menu/film/return checks pass; x64/RU builds, command/display
regressions and an ordinary MPEG-2 visual smoke pass. The renderer's exclusive-mode
OSD bar, exact madVR 210, other discs and broader codec coverage remain open.

The user reports normal Sony playback outside RDP; the agent saw the intro on
initial open and reopen. No Sony-specific change or confirmed cause is claimed.
No donor code, shared renderer settings or original profile data was changed.

## Native ISO opening, 2026-09-22

Dropped ISO files previously reached ordinary LAV/FFmpeg probing and could remain
at Opening. HC now intercepts ISO before ordinary graph construction, using the
Windows Virtual Disk approach from pinned MPC-BE DiskImage/OpenIso. Only native
ISO support is adapted; third-party mounters and compressed/other formats are
excluded. The new adapter uses read-only, non-permanent attachments, device-number
matching, a bounded drive-letter wait and RAII ownership. Existing attachments
are reused without DetachVirtualDisk. HC graph switches preserve the owner until
the disc is closed, and Reopen resolves the original image instead of a stale drive.
Failed/unsupported ISO inputs are consumed with an error, never a file-parser fallback.

Production handler regressions cover menu/main-movie/DVD routing, cancellation,
failures and owner lifetime. The native API test checks the real image, preservation
of an existing attachment and release of an owned one. x64/EN/RU builds and the
opening/settings, navigation command and display regressions pass. The agent
observed Blu-ray menu, film start, return, close/unmount and reopen through madVR;
the user separately confirmed that dragging the ISO into the new player opens
its menu. Automated desktop drag simulation was inconclusive and is not counted
as a pass. DVD ISO playback, other filesystem/image types and the broader renderer
matrix are not qualified by this change. No donor files or public remote changed.

## Publication tools and stabilization

The scanner, packaging approach, docs/resource checker and workflows were adapted
from the same pinned donor; source file hashes are in `imports.json`. HC changes
cover LAV manifests/licenses, PO translations, public identities and the exact HC
build sequence. Local scanner/package regressions and all component checks pass.
Renderer identity, ISO lifecycle and ordinary-file results are in [VALIDATION.md](VALIDATION.md).
D3D11 fullscreen windowed is primary; no global renderer setting is bundled.

The initial HC port is commit `5004099e31c7fb7833060b3d9b8c8d0fa4b1b9d5`, reviewed
with publication follow-ups in [PR #1](https://github.com/ttonych/mpc-hc_bluray/pull/1).

## Documentation and version policy review

Compared committed donor README and user/developer guides at `270cfdd` above,
then expanded the HC guides against HC implementation and validation records.
The base-version/fork-release numbering convention is adopted in [Releasing](RELEASING.md).
The donor's EXE branding/updater, mandatory portable policy, profile import and
offline HTML generator are explicitly deferred, not documented as HC features.
The original HC contribution guide is preserved separately. This documentation
change fixes UTF-8 navigation and strengthens paired-document checks; it does
not alter the player, donor checkout or existing cloud ZIP.

## Fork branding and release checks, 2026-09-23

Continued the preceding deferred branding work from the same donor `270cfdd`.
`BlurayReleaseVersion.h` is byte-identical to the donor; the release-version probe
is adapted to HC tags and extended to exercise the actual GitHub feed parser.
Hashes and source paths are recorded in `imports.json`. HC retains its MFC/WinINet
transport, native dialogs and profile storage. Selection accepts published fork
prereleases and opens only validated release URLs from the HC repository.

The HC-specific version header drives About/ProductVersion/caption and packaging;
numeric PE/resource versions retain upstream semantics. The real revision batch
is tested with nearer fork and unrelated tags. Local x64/RU builds, version/feed/
caption/package checks pass. Native EN/RU About and live empty-release dialogs
were inspected; no published-release download or disc playback is claimed by
this change. The earlier cloud ZIP is unchanged. Portable import and offline HTML
remain open; [Parity](PARITY.md) records the committed feature comparison.

## Portable profile and HTML, 2026-09-23

Source remains pinned MPC-BE `270cfdd4369224dd4108d0b1d1b8a4ab7b8fc56d`.
Adapted `PortableTest`, `PortableProfileImport`, its component test and
`package_docs.py`; `imports.json` records exact source paths/hashes. HC has no
opt-in portable flag: it is mandatory. Import preserves sources, uses HC formats
(A–P binary and decimal DWORD), excludes history/playlists and resets BD-J paths.
HLSL subfolders retain their structure. A separate window class/AppID and blocked
association writes separate the fork from an installed HC.

Native importer and complete actual-JAR component tests, x64/RU builds, EN/RU
setup, cancellation, manual import, restart, write rejection and unchanged
source/installed profiles pass locally. HTML/package tests verify local links
and anchors. This is local evidence; the new cloud ZIP and its BD-J session
require separate qualification.

Merged as HC commit `019c3dcfe0373378f9c0c8f93a1a8e1b1c0aedcd` through
[PR #5](https://github.com/ttonych/mpc-hc_bluray/pull/5), merge commit
`19dfdc8b307fbc04768ce60d14e1b13b3afee9e8`. The manual cloud candidate from that
merge passed package/HTML, portable import and bounded HDMV/BD-J runtime checks;
the exact SHA-256 and remaining limits are in [Validation](VALIDATION.md).
Documentation follow-ups do not rebuild or replace that ZIP.
