# Validation record

[Русский](VALIDATION.ru.md) · [Roadmap](ROADMAP.md)

The first section records local development results from 2026-09-22. The cloud
candidate is covered separately below. Dependency revisions are in [sources.json](../sources.json).
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

## First cloud candidate

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

This is a test candidate, not a qualified Release. Complete the cloud BD-J and
remaining tracks/chapters/stills/lifecycle matrix before publication as a Release.
