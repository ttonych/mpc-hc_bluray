# Validation record

[Русский](VALIDATION.ru.md) · [Roadmap](ROADMAP.md)

## First prerelease: 2.8.2-bluray.1

[Published on 2026-09-29](https://github.com/ttonych/mpc-hc_bluray/releases/tag/2.8.2-bluray.1).
[Cloud build 36602619838](https://github.com/ttonych/mpc-hc_bluray/actions/runs/36602619838)
built commit `b8695cf132ee649219c337e81582332c9614365a` after
[PR #11](https://github.com/ttonych/mpc-hc_bluray/pull/11), including the HDMV HDR fix.
Player, RU resources, component tests and tests of the built Java JAR passed.

ZIP: `mpc-hc_bluray-2.8.2-bluray.1-b8695cf132ee-x64.zip`.
SHA-256: `553bcb7148b220d72d1180c25ae033836ab4038068b8b333a601757753d2c0b4`.
All **101 payload hashes**, CRC/membership, clean profile seed, **20 HTML pages**,
local links and the LAV v4 manifest passed. Product version is `2.8.2-bluray.1`;
file version is `2.8.2.26 (b8695cf13) (main)`.

The following observations use a separate portable copy of this exact ZIP in
a local desktop session on 2026-09-29. They are agent checks, not new user reports.

| Exact-ZIP check | Result |
| --- | --- |
| Portable setup/import | Actual packaged seed, EN/RU cancellation/defaults/restart and native synthetic INI/shader import pass. Source bytes and installed HC registry remain unchanged; write and association guards pass. |
| HDR HDMV | Streets of Fire UHD: bright white/yellow menu graphics, selection highlights, chapter page, film, Alt+R popup and Alt+T return observed. This checks bitmap menu conversion, not HDR video accuracy. |
| SDR HDMV | Baby Boom: direct ISO opening, menu, film, top return, mouse selection of scenes and chapter activation pass. Chapter markers appear in film and disappear in the menu. |
| Initial still and BD-J | Casino Royale: the MPEG-2 startup notice is visible at sampled seconds 1, 4 and 6. BD-J menu, film, popup and top return pass. |
| UHD BD-J | A Knight's Tale: version selection, main menu, film, popup and top return pass using an externally mounted drive. TrueHD to DTS-HD changes the checked stream and native status; English PGS subtitles are visible. Chapter commands move to authored positions, including approximately 06:19 and 14:25. |
| BD-J restart | Restart in English shows the authored Resume Playback prompt; Yes resumes visible film from about 24:17 using only newly created private disc data. |
| Renderer and modules | Navigation/LAV module hashes match the ZIP. External madVR matches beta 210 below; external Temurin 21.0.12.1+1 x64 JVM is loaded. OSD confirms D3D11 fullscreen windowed for HDR HDMV and BD-J; shared renderer configuration is unchanged. |
| Read failures/recovery | All six injected LAV cases pass; transient retry and same-graph recovery match 576 baseline samples/timestamps, permanent errors produce bounded EC_ERRORABORT. HC displays the localized error in EN/RU; unlocking and reopening restores visible MPEG-2 video. |
| Multi-part reads | Both packaged libbluray DLLs pass four synthetic 12,288-byte clips, 13 request sizes and 49,993 calls each, with exact bytes/EOF and intact guards. The donor's original crash disc was not replayed on HC. |
| Ordinary files | Packaged filters decode H.264, HEVC Main10, AV1 and MPEG-2 to EOS through Null Renderer. H.264 is also visibly rendered through madVR after disc playback. |

All own test windows and owned mounts were closed; the pre-existing user mount
was preserved. ZIP, pristine extraction and packaged payload files remained
unchanged. The release publishes those same bytes; anonymous ZIP/checksum
downloads match and the release tag resolves to the built commit above.

Positive mouse-capable BD-J coverage, broader Java/saves/disc compatibility,
long OS/network timeouts, BD-Live/PiP, full MVC/stereo and HDR video accuracy
remain unqualified. The storage-specific native ISO attachment result is
excluded from player defects. Earlier Sony-intro observations below belong to
their own candidates; that intro was not sampled in this run.

## Earlier local checks

This historical section records local development results from 2026-09-22. Earlier cloud
candidates are covered below. Dependency revisions are in [sources.json](../sources.json).
Compilation, automated checks, agent observations and user reports are distinct.

| Scope | Evidence | Result |
| --- | --- | --- |
| ISO lifecycle | Native ownership/routing tests; agent runtime | Baby Boom to Casino Royale in one instance updates the caption and detaches the first image; ISO to an ordinary file releases the mount. Close/reopen passes. |
| ISO drag and drop | User report | Menu opens after the ISO routing fix. |
| ISO main-movie preference | Isolated INI and live native control state | Direct opening loads the 1:50:18 movie, chapter 1 of 25; this run has no usable video capture. The menu path was visually checked separately. |
| Exact renderer | Loaded module hash versus official archive | madVR 210 x64 confirmed; the PE version alone still reads 0.92.17.0. |
| Primary fullscreen mode | Agent observation | D3D11 fullscreen windowed; native controls appear at the bottom edge and chapters follow menu/film/return state. |
| Additional exclusive-mode check | Agent observation | D3D11 exclusive menu, film, renderer seek bar, seek to about 26 minutes and Alt+T return pass. The temporary setting was restored. This is not the recommended or default mode. |
| Ordinary files with custom LAV | Agent video observation and Null Renderer EOS test | Synthetic H.264, HEVC Main10, AV1 and MPEG-2 MKV fixtures render; software decode completes for all four. This is not exhaustive codec, audio or HDR validation. |
| Startup still | Agent observation and LAV regressions | Casino Royale Warning is visible after isolated MPEG-2 still handling was adapted. |
| BD-J | Earlier bounded agent checks | One disc: menu/film/return, copied-data reset/reopen, audio/subtitles and chapters. Full matrix remains open. |
| HDMV input | User report | Keyboard and mouse on White Sun of the Desert are provisionally accepted. |
| Sony intro | User report outside RDP | No current problem; an earlier intermittent black image has no established cause or dedicated fix. |

The authored A Knight's Tale menu tested here does not support mouse input,
according to the user. It cannot establish positive BD-J mouse compatibility.
The renderer's own exclusive seek bar does not establish chapter-marker drawing
in MPC-HC's native/OSD bars; those are separate paths.

Renderer reference: [official beta 210 archive](https://madshi.net/madVRhdrMeasure210.zip).
Archive SHA-256:
`2d714db856b8012a6676d809c59689f2f8752d2c2afeb7cb3f42137cf818276a`.
Loaded `madVR64.ax` and archive member SHA-256:
`c4093c6dfc2f549fab5f08bc940587c6fcb35195f8a589b1130d58bf5e4460e4`.
Neither renderer binaries nor screenshots/disc content are included in this repo.

Before release, repeat HDMV/BD-J, clean portable profile, EN/RU, menu/film/return,
tracks, chapters, warnings/stills and ordinary files using the exact cloud ZIP.
Record its source commit and SHA-256. Broader BD-J mouse/lifecycle coverage,
DVD ISO playback, HDR accuracy and MVC/stereo output remain unqualified.

## Earlier cloud candidate: LAV v4

[Manual build 35828150183](https://github.com/ttonych/mpc-hc_bluray/actions/runs/35828150183)
passed on 2026-09-23 from commit `c4d242333bed24cc48a23ab46650b597690f5637`
after [PR #8](https://github.com/ttonych/mpc-hc_bluray/pull/8). The cloud runner
built the player, LAV v4, native/Java runtime and RU resources; component and
built-JAR checks, including patch application and the HC error handler, passed.

ZIP: `mpc-hc_bluray-2.8.2-bluray.1-c4d242333bed-x64.zip`.
SHA-256: `7706ad819ed43e8d73b15b8b7efb6a5539d642b4acd48d48399c00f7b677cf95`.
All **101 payload hashes**, CRC, exact membership, the clean profile seed,
**20 HTML pages**, local links and the LAV v4 build/patch manifest passed.
The EXE reports `2.8.2-bluray.1`, file version `2.8.2.20 (c4d242333) (main)`.

| Exact-ZIP check | Result |
| --- | --- |
| Actual packaged LAV, injected read failures | All six cases pass: baseline, one failure within a clip, one at the boundary, persistent failure at both positions, standalone M2TS. Transient retry and same-graph recovery match all 576 baseline samples. Persistent errors produce EC_ERRORABORT with bounded attempts. |
| Ordinary decoding | Packaged LAV decodes synthetic H.264, HEVC Main10, AV1 and MPEG-2 to EOS through Null Renderer. |
| Portable first start | Packaged seed, EN/RU wizard, cancellation, defaults and restart pass; installed HC registry unchanged. |
| HC read error EN/RU | Locking the second synthetic clip closes the graph and shows the localized error. After unlocking, reopening restores visible MPEG-2 video through madVR in both languages. Native control state, the earlier GDI message checks and local-desktop video captures were inspected. |
| Loaded binaries | Loaded navigation and LAV DLLs match the ZIP. External madVR matches the beta 210 hash above; the external JVM is loaded for BD-J. |
| Manual import and guards | The native file picker selects a synthetic INI; settings and a shader are copied, source bytes and the installed HC registry remain unchanged. Read-only profile and association-write guards pass. |
| HDMV | Baby Boom: menu, Enter to film, Alt+T return, mouse selection of the scene menu and a chapter. Chapter marks are visible in film and absent in the menu. |
| Casino Royale | The initial MPEG-2 player-update notice is visible throughout sampled frames. Menu, film, Alt+R popup and Alt+T return are visible. This checks that notice, not every authored still. |
| BD-J | A Knight's Tale UHD: Sony intro, version selection, main menu, film, Alt+R popup and Alt+T return. Playback uses an externally mounted drive. |
| BD-J tracks and chapters | TrueHD to DTS-HD selection changes the checked stream and native status; English subtitles are visible. Next/previous chapter commands move between about 06:19 and 14:26. Chapter marks follow film/menu state. |
| BD-J restart | After closing/restarting the player in English, the authored Resume Playback prompt appears; Yes resumes visible film at about 06:50 using only newly created private disc data. |
| Fullscreen | The madVR OSD shows D3D11 fullscreen windowed for both HDMV film and the UHD BD-J menu. Shared renderer settings were not changed. |
| Ordinary video | The synthetic H.264 file renders through madVR after disc playback. Software decode of all four codecs is recorded above. |

The initial RDP session deferred video checks. They were completed later on
2026-09-23 in a confirmed local desktop session, using a separate portable copy
of this same ZIP. The observations above belong to this candidate; the earlier
candidate's results remain separate. ZIP, pristine extraction and packaged
payload files are unchanged; only private profile/test data were added or updated.
All test players are closed, native image mounts are gone and the test-owned
external mount was released. The storage-specific ISO issue was not investigated.

The deferred desktop checks are complete within the stated scope. Positive BD-J
mouse coverage, broader Java/saves/disc coverage and long OS/network timeouts
remain open. This candidate was not published; the first release above supersedes it.

## Earlier portable cloud candidate

The read-error fix described in the final section was added after this candidate;
this candidate still contains LAV adapter v3.

[Manual build 35797167081](https://github.com/ttonych/mpc-hc_bluray/actions/runs/35797167081)
passed on 2026-09-22 UTC from commit
`19dfdc8b307fbc04768ce60d14e1b13b3afee9e8` after
[PR #5](https://github.com/ttonych/mpc-hc_bluray/pull/5). Player, custom LAV, RU
resources, component and actual-JAR HAVi checks passed on the cloud runner.
Runtime checks completed on 2026-09-23 UTC using a separate copy of this ZIP.

Artifact: `mpc-hc-bluray-candidate-x64`.
ZIP: `mpc-hc_bluray-2.8.2-bluray.1-19dfdc8b307f-x64.zip`.
SHA-256: `9dc27852b30f95c4245b656b0d392b9036ca7395864853bd85762a49031adbef`.
CRC, exact membership, all **100 payload hashes**, the clean profile seed and
local Markdown/HTML links and anchors passed. The package contains **20 HTML
pages**. The ZIP and all original extracted files were unchanged after testing.

| Cloud ZIP check | Agent result |
| --- | --- |
| First launch EN/RU | Actual packaged seed, both wizard languages, cancellation, defaults and restart passed. Installed MPC-HC registry was unchanged. |
| Manual import and guards | Synthetic INI was selected through the native file dialog; settings and a shader were imported, source bytes preserved. Read-only profile and association-write guards passed. |
| Runtime identity | Loaded LAV/navigation DLLs matched the packaged files. External madVR matched beta 210 above; external Temurin 21.0.12.1+1 x64 loaded for BD-J. |
| Fullscreen | madVR OSD showed D3D11 fullscreen windowed. The shared exclusive setting remained disabled. |
| BD-J | A Knight's Tale UHD: version selection, main menu, film, Alt+R popup and Alt+T return were visible. |
| BD-J tracks and chapters | TrueHD to DTS-HD selection changed native stream status; selected English subtitles were visible. Next/previous chapter commands changed position. Chapter marks appeared for film and were absent in the top menu. |
| BD-J close/reopen | The authored Resume Playback prompt appeared and resumed the film from newly created private disc data. No original saves were used. |
| HDMV | Baby Boom native ISO: menu, Enter to visible film and Alt+T return. Chapter marks followed film/menu state. |
| Startup still | Casino Royale's initial player-update notice was visible, including while paused. This does not qualify every warning or still. |
| ISO lifecycle | Captions changed on replacement; player-owned native mounts were released on replacement/file opening. The external BD-J mount was retained until explicitly released after testing. |
| Ordinary files | H.264 video was visible through madVR; H.264, HEVC Main10, AV1 and MPEG-2 decoded to EOS through the packaged LAV and Null Renderer. |

In this test, native Windows attachment of the A Knight's Tale ISO returned
error **2**. On 2026-09-23 the user identified this as a property of the ISO's
storage setup and asked to exclude it from player defect investigation. It is
not an open MPC-HC defect or release blocker. Existing WinCDEmu attached it; the checks above
opened the mounted drive's `BDMV/index.bdmv`. They validate BD-J playback from
that drive, not direct native ISO attachment or automatic third-party mounting.
See the [opening guide](USAGE.md#opening-a-disc-or-iso).

The earlier user-confirmed ISO drag gesture was not repeated for this exact ZIP.
A mouse-capable BD-J menu, broader discs/Java/saves lifecycle, decoder/audio
coverage, DVD ISO, HDR accuracy and MVC/stereo remain unqualified. This is an
experimental candidate that was not published. Test players and owned mounts
were closed; shared renderer settings and original profiles were not changed.
Later documentation updates leave this candidate's source commit and bytes fixed.

## First cloud candidate (historical)

[Manual build 35781918063](https://github.com/ttonych/mpc-hc_bluray/actions/runs/35781918063)
passed on 2026-09-22 UTC, from commit
`8183fe6579c113bebe1ab4b2818807c41400de16`. Player, custom LAV, RU resources,
component checks and actual-JAR HAVi checks passed on the cloud runner.

Artifact: `mpc-hc-bluray-candidate-x64`.
ZIP: `mpc-hc_bluray-2.8.2-bluray.1-8183fe6579c1-x64.zip`.
SHA-256: `dee5f9188d227b4dacfe2b20ae09a2f7ccf5ef29e211fe67b1c6f8ca5ee7eefc`.
The downloaded ZIP passed CRC, exact membership, all 76 payload hashes and clean
profile checks. The ZIP and original extraction were preserved; runtime used a
separate copy, a fresh portable profile and external madVR/Java.

| Cloud ZIP check | Agent result |
| --- | --- |
| Loaded components | LAV and navigation DLLs came from the cloud package; loaded madVR matched the beta 210 hash above. |
| HDMV | Baby Boom menu, Enter to film and Alt+T return were visible. |
| Fullscreen | madVR OSD confirmed D3D11 fullscreen windowed. Exclusive remained disabled. |
| Main-movie preference | Baby Boom opened directly into the 1:50:18 film; video and chapter markers were visible in the English player. |
| ISO replacement and close | Caption changed on replacement; owned mounts were released on replacement/close. |
| Startup still | Casino Royale's initial player-update notice was visible. This observation is limited to that notice. |
| Ordinary files | H.264 video was visible with madVR; H.264, HEVC Main10, AV1 and MPEG-2 decoded to EOS through the packaged LAV and Null Renderer. |
| EN/RU | Both Blu-ray settings pages were visually checked. |
| BD-J | Not completed: the current A Knight's Tale ISO was readable, but both the player and Windows Mount-DiskImage failed to attach it with Windows error 2. No BD-J runtime pass is claimed for this ZIP. |

A local test helper initially introduced malformed line endings while changing
the test INI. That caused a startup exception in the subtitle-dialog settings
parser. Correcting the helper/profile and repeating startup/main-movie playback
passed; the cloud archive was unchanged.

That candidate was not published as a Release. Its BD-J check remained incomplete;
subsequent checks above apply to the newer ZIP, not retrospectively to this one.

## Local read-failure checks, 2026-09-23

LAV adapter **hc-menu-bridge-v4** and HC's graph-event handler pass locally.
The earlier `19dfdc8b307f` cloud ZIP remains unchanged and contains v3.
The current v4 cloud candidate is recorded separately above.

- A generated 24-second MPLS has two distinct MPEG-2 clips with different source
  timestamps. Actual LAV DLLs feed a memory sink. Process-local ReadFile injection
  compares sizes, payload hashes and timestamps for all 576 compressed samples.
- One CRC failure inside clip 1 or at the start of clip 2 retries at the same
  position and matches every baseline sample. v3 negative controls lose/truncate
  samples or shift time. The failure-free baseline is unchanged.
- Persistent failure produces EC_ERRORABORT instead of EC_COMPLETE. Each logical
  read retries once; two buffered calls produce four failed OS reads here. Stop
  returns promptly. Removing the fault and seeking to zero in the same graph
  restores all 576 baseline samples. Standalone M2TS delivers 288 samples.
- Separate actual-LAV software decode to Null Renderer completes for synthetic
  H.264, HEVC Main10, AV1 and MPEG-2 MKV.
- Native HC EN/RU checks lock the second synthetic clip with LockFileEx. HC
  closes the graph and displays its localized error. Unlocking/reopening restores
  visible playback with madVR 210, verified by its loaded module hash. These are
  agent observations. x64/RU builds and existing LAV timing/still tests pass.
- Tests cover the actual HC error-handler branch (including a failing old-code
  control), clean patch application, v3 upgrade, idempotence and edited-input refusal.

The compressed-sample probe does not itself decode video or qualify disc menus.
Injected failures return immediately: bounded retry is not a timeout on a blocked
Windows call. Network reconnection, invalid handles and damaged sectors are
outside these checks. These local results do not qualify the separate cloud ZIP.
User discs, mounts, profiles and global
renderer settings were unchanged. The storage-specific ISO issue stays excluded.
