# Development

[Русский](DEVELOPMENT.ru.md) · [Rules](../../AGENTS.md) · [Contributing](../../CONTRIBUTING.md) · [Releases](RELEASING.md)

## Repository layout

| Path | Purpose |
| --- | --- |
| `src/mpc-hc`, `include`, `src/thirdparty` | MPC-HC source and recorded dependencies, including LAV |
| `bluray/sources.json`, `bluray/imports.json` | Exact component pins and donor provenance |
| `bluray/patches`, `bluray/ports` | Maintained library/LAV patches and source adaptations |
| `bluray/tools` | Build, regression, publication and packaging tools |
| `bluray/docs`, `bluray/CHANGELOG*.md` | Paired guides, validation, porting records and fork changes |
| `bluray/vendor`, `bluray/dependencies`, `bluray/build`, `bluray/out`, `bluray/diagnostics`, `bluray/runtime` | Ignored local inputs, outputs and test data |

Clone this fork with its Git history; run the commands below from its root.
Keep `origin` for the fork and `upstream` for official MPC-HC. Inspect source
revisions before building; do not substitute a downloaded snapshot for history.
The version scheme is [MPC-HC base plus fork release number](RELEASING.md).

## Sources and tools

The baseline is tag `2.8.2` of `clsid2/mpc-hc`, commit
`a84d0cf38a1866f3518bb819c901300dacff5a9b`. Preserve its history and submodule
pins. The selected donor is `270cfdd4369224dd4108d0b1d1b8a4ab7b8fc56d` of
`ttonych/mpc-be_bluray`. See [sources.json](../sources.json).

Use Visual Studio 2022 with C++, x64 MFC/ATL and Windows SDK 10.0.19041.0,
NASM 2.16.03, Git, PowerShell and Python 3.12 or newer. The scripts discover
Visual Studio and change only the current process environment. The player
wrapper explicitly selects the SDK/UCRT paths discovered by VsDevCmd.

From the repository root, initialize the recorded dependencies:

```powershell
git submodule update --init --recursive
```

Do not treat an interrupted clone as a completed checkout. In particular, LAV
has its own FFmpeg, libbluray and qsdecoder submodules. Preserve the recorded
revisions when recovering a failed download.

## Runtime and player build

```powershell
./bluray/tools/test-bootstrap.ps1
```

This verifies/downloads the libbluray archive, applies the native patches in
order (`mouse-page-v1`, `playmark-seek-v1`) and the independent Java patch
`bdj-toggle-v1`. It checks clean/repeated application and refusal to overwrite
unexpected edits, then compiles extracted production mark-tracker and process
query functions against synthetic test fixtures using the x64 C++ compiler.
It does not build libbluray DLLs/JARs or run a disc. Patch bytes and manifests
retain donor hashes; `imports.json` distinguishes adapted test launchers.

Build the menu runtime before the player (it supplies the pinned headers).
`$javaRoot` must name Temurin JDK 21.0.12.1+1 x64, with javac 21.0.12.1.
The dependency preparation must finish successfully; alternatively pass an
already verified x64 dependency prefix with the recorded vcpkg baseline.

```powershell
./bluray/tools/prepare-dependencies.ps1
./bluray/tools/build-libbluray.ps1 -DependencyRoot ./bluray/build/vcpkg_installed/x64-windows
./bluray/tools/build-bdj.ps1 -JavaHome $javaRoot
./bluray/tools/test-bdj-toggle.ps1 -JavaHome $javaRoot
./bluray/tools/test-menu-components.ps1
```

To build the x64 Release player, put `nasm.exe` on PATH and run:

```powershell
./bluray/tools/build-player-core.ps1
```

Alternatively pass `-NasmDirectory` with your local NASM directory. The script
uses the solution's `Apps\mpc-hc` target so library build ordering is retained.
Logs go to ignored `bluray/diagnostics`; outputs use upstream `bin` locations.
This builds the player with embedded English resources. It does not build LAV,
language DLLs, the new menu runtime or a release package. Upstream full build
instructions remain in [Compilation.md](../../docs/Compilation.md).

For the Russian resource DLL, use an isolated Python environment:

```powershell
python -m venv bluray/tools/.venv
./bluray/tools/.venv/Scripts/python.exe -m pip install -r bluray/tools/requirements-resources.txt
./bluray/tools/build-russian-resources.ps1
```

This uses upstream resource generation without normalizing tracked PO files.

## Local LAV prototype and portable copy

The MSVC configuration uses a modern MSYS shell and GNU make 4.4.1 (the tested
package revision/hash is in `sources.json`). Define `$msysRoot`, `$makeBin`
and `$nasmBin` as your local tool directories; make must work with that MSYS
runtime. Player libraries, including zlib, must already be built.

```powershell
python ./bluray/tools/apply-lav-patch.py
./bluray/tools/build-lav-msvc.ps1 -MsysRoot $msysRoot -MakeDirectory $makeBin -NasmDirectory $nasmBin -Configure
python ./bluray/tools/test-lav-menu-bridge.py
python ./bluray/tools/test-lav-navigation-timestamps.py
python ./bluray/tools/test-lav-mpeg2-stills.py
./bluray/tools/test-lav-runtime.ps1
./bluray/tools/prepare-local-player.ps1 -Destination ./bluray/runtime/test-01
```

The patch installer verifies the exact LAV commit, patch hash and source-file
hashes; it rejects unrelated edits. The runtime test uses software decoding
and a Null Renderer, without changing registered filter settings. The MSVC
FFmpeg configuration uses Schannel and the built-in AV1 decoder; GCC-only
external dependencies are absent. Validate normal-file/codec parity before a
release. Build logs/manifests are in ignored `bluray/diagnostics`.

`prepare-local-player.ps1` requires a new destination, copies only the explicit
runtime list and creates an empty portable INI. It includes both Java JARs,
the Russian resource DLL and source/license manifests. Java and madVR are
external. In this test player, select madVR as the video renderer and open
**Options > Playback > Blu-ray**. Select the pinned Java folder there, or leave
automatic discovery enabled. Do not reuse an installed player's INI or BD-J data.

The Blu-ray page selects **Main movie** (the default) or **Disc menu** for normal
opening, including **Open DVD/BD** and the disc's `index.bdmv` entry point.
The shared opening path recognizes disc roots, `BDMV`, `index.bdmv` and
`MovieObject.bdmv`; individual playlists/clips retain normal playback.
Use **Open DVD/BD** for a disc root or `BDMV` folder. Open or drop a local/UNC
`.iso` file directly: Windows attaches it read-only and Blu-ray follows the same
menu/main-movie preference. The player holds its attachment through playlist
changes and releases it after closing the graph; an existing external attachment
is reused without forced detachment. Unsupported images and mount errors are
reported instead of being sent to the ordinary video parser. Native Windows ISO
support is required; third-party mounting tools and other image formats are not
included. The temporary separate menu-opening command has been removed. Menu playback
requires madVR. A menu-opening failure is reported without silently opening the film.

The page also sets region, country, menu/audio/subtitle language, Java and
separate BD-J saved-data/cache folders. Country and language names come from
Windows; ISO country (two-letter) and language (three-letter) codes can be entered.
Empty storage paths use `bdj-data` next to the player. Settings take effect on the
next disc opening; changing paths does not move or delete existing data.
Apply validates all fields before saving; Cancel discards unapplied edits.
The Java status checks the JVM Windows image and architecture. Invalid or
mismatched explicit installations cannot be applied. Check Java runs the selected
installation through a separate hidden java.exe -version process. It has a
10-second timeout, a 64 KiB output limit and a kill-on-close job; closing options
or changing fields cancels it. Java option-injection environment variables are
omitted only in that child. Success proves launcher startup, not BD-J or disc
compatibility. Automatic Java discovery still occurs on disc opening; select a
folder to run this explicit check.

Arrow/Enter keys navigate; Home or the standard Title Menu command (Alt+T by
default) requests the top menu. Apps or Root Menu (Alt+R) requests the popup.
Main/context menu entries use the same navigation commands. Disc restrictions
still apply. The full language/disc/renderer regression matrix remains development work.

**Blu-ray > Compatibility...** exposes the 14 recorded libbluray preferences,
including age, player profile, navigation restrictions and reported capabilities.
Presets, descriptions and optional technical details retain the pinned donor
semantics. These are capabilities reported to disc menus; they do not enable new
decoders or change renderer HDR output. The child dialog edits a copy: its OK
stages changes, while Apply/OK in the main options window saves them. Either
Cancel discards its unapplied edits. Default/All defaults restore automatic
settings in the draft and do not reset any disc saves.


**Blu-ray > Disc data...** lists identified discs and shared legacy folders,
with search, aliases, last-opened dates, refresh and folder access. It uses applied
storage paths even while the options page contains edits. Rename and confirmed
reset take effect immediately; cancelling options does not undo them. Reset
selects empty saved-data/cache directories for the disc's next opening. Previous
files and active sessions retain their paths; no data is deleted. Legacy groups
can contain multiple discs and cannot be reset as an identified disc. The cache
button uses the current applied cache root, which may be shared. Aliases do not
rename physical folders.

Run ./bluray/tools/test-disc-java.ps1 for synthetic storage and Java process
checks. test-bluray-opening-settings.py also checks Apply with JVM image fixtures.
No installed profile or real disc saves are used by these tests.

## Port and publication workflow

Keep common algorithms and library patches close to the donor; adapt UI,
DirectShow graph, streams and clock handling separately. The maintained LAV patch supplies
PID-based stream selection, PlayItem boundaries and presentation start. Record each
transfer, deferral and HC-specific check in [PORTING.md](PORTING.md).

Use local feature/fix/update branches. Once an authorized remote exists, use
PRs and required fast checks to main. Full CI builds run manually for tested
candidates. Publication requires the privacy/history checks and exact ZIP
verification described in [AGENTS.md](../../AGENTS.md). These scripts do not
publish or alter installed players. Runtime tests need a separate portable
profile, copied/synthetic BD-J storage, pinned Java and madVR 210.

Command routing regression (MSVC x64, including original-code negative control):

```powershell
. ./bluray/tools/Enter-BuildEnvironment.ps1
python ./bluray/tools/test-navigation-commands.py
python ./bluray/tools/test-navigation-commands.py --baseline
python ./bluray/tools/test-navigation-display.py
python ./bluray/tools/test-bluray-opening-settings.py
python ./bluray/tools/test-bluray-compatibility.py
```

When adapting menu mouse input, keep fullscreen toolbar visibility updates even
when the disc consumes movement. Verify bottom-edge hover in menu/film/return;
check native toolbars separately from renderer OSD. Use D3D11 fullscreen windowed
as the primary madVR mode; do not enable exclusive as a test prerequisite.

ISO regression: run `./bluray/tools/test-iso-opening.ps1`; optionally pass a local
`-ImagePath` for native mount ownership checks. In the MSVC environment, run
`python ./bluray/tools/test-iso-routing.py` for production dispatch/error tests.

## Candidate checks and packaging

Run `prepare-build-tools.ps1` from `bluray/tools` to download hash-pinned NASM and
make; it uses the Git for Windows MSYS shell. Run `test-components.ps1 -JavaHome
$javaRoot` for the complete native and actual-JAR component suite. Repeated build
environment setup is safe and does not grow PATH.

Fast PR checks validate new blobs throughout outgoing history, reviewed new author/
committer identities, docs, RU resources and package regressions. Original upstream
author metadata is preserved. Full `bluray-build.yml` runs only by manual dispatch.
`package-player.py` accepts the manual cloud environment, verifies clean source and
LAV patches, assembles explicit program/license/source lists and a fresh portable
INI, checks recorded hashes and writes a new ZIP without overwriting earlier ones.
Use `python bluray/tools/package-player.py --verify <candidate.zip>` after download.
It neither bundles Java/madVR nor publishes a Release. Qualify the exact archive
with [the runtime matrix](VALIDATION.md) before publication.

The complete version/tag/changelog and draft-to-publication procedure is in
[Releasing](RELEASING.md). Current packaged guides are Markdown; MPC-BE's offline
HTML documentation renderer is not ported. Relative links to files outside the
package are rewritten to the exact source commit by the packager.

## Updating the two sources and dependencies

Select updates deliberately in an `update/` branch. Preserve original history,
authors and licenses, and finish local checks before the PR. A newer upstream
release alone does not authorize changing the base.

- **MPC-HC:** adopt a selected official tag, resolve HC/Blu-ray integration
  conflicts and update submodules to the tag's recorded revisions. Recheck graph,
  settings, resources, revision calculation and normal playback. Change source
  pins and paired changelogs together.
- **MPC-BE Blu-ray:** compare a fixed donor commit with the last recorded one.
  Classify each change as shared, adapted, already present, inapplicable or
  deferred, with dependent patches/tests. Do not merge the whole donor branch.
  Keep common algorithms close, and document HC-specific results in Porting.
- **LAV:** preserve the maintained bridge's PID selection, PlayItem boundaries,
  timestamps and MPEG-2 still behavior. Rebase its patch against the selected
  revision with new reviewed manifests; test both menu and ordinary-file paths.
  LAV's internal libbluray remains a separate dependency.
- **libbluray:** review upstream fixes before removing or adapting a patch.
  Verify DLL/JAR/header versions together, including the internal playlist
  structures used for menu audio; these are not a stable public ABI. The menu
  engine currently accepts 1.5.0. Update version checks and package/source/license
  records deliberately; passing a checksum is not an API/ABI compatibility test.
- **Java:** pin build JDK and tested playback runtime separately as applicable.
  Rebuild both JARs and run actual-JAR HAVi tests after Java changes, then check
  BD-J startup, navigation and saves in the player.

For each update, preserve the old candidate, use a new isolated portable test
folder and qualify the resulting cloud ZIP before release. Avoid replacing
manifests merely to silence an unexplained hash or source mismatch.

## Text encoding

Fork Markdown is UTF-8. In PowerShell use explicit `-Encoding UTF8` when reading
or writing it; a system-default encoding round trip can corrupt Russian labels
even in the English README. Preserve resource encodings/BOMs and existing line
endings, especially `.rc`, rather than applying a bulk conversion. The fast
documentation checker requires valid UTF-8 and exact EN/RU navigation labels;
review the displayed text as well as its automatic checks.
