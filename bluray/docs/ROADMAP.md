# Roadmap

[Русский](ROADMAP.ru.md)

## Completed locally

- MPC-HC 2.8.2 history and dependency pins; x64 player, EN/RU resources,
  libbluray 1.5.0 DLL/JAR and the LAV adapter are built.
- Graphics, clocks, coordinates, menus, actual-JAR HAVi, PID/PlayItem,
  navigation command tests and the LAV Null Renderer smoke test pass.
- HDMV menus/film start and a BD-J menu/film/return cycle were observed. The
  user separately gave provisional keyboard/mouse confirmation on one HDMV disc.
- Alt+T/Alt+R and standard menu commands are connected. Disc captions and
  hiding chapter markers while menus are active, restoring them for film, are added.
- LAV preserves authored frame gaps and repeats isolated MPEG-2 stills for madVR.
  The startup warning is visually confirmed; parser regressions, software/DXVA2
  decoding and an ordinary MPEG-2 frame-count check pass. Menu/film/return
  chapter-marker transitions were visually checked.
- Normal Blu-ray opening now follows the main-movie/menu preference. A native
  EN/RU page exposes region/languages, Java and BD-J storage; production-method
  regressions, both builds and local Apply/Cancel/restart checks pass. Both opening
  modes and explicit menu override were visually checked with madVR.

- Disc catalogue and explicit Java diagnostics are implemented. Synthetic storage
  and child-process tests pass; EN/RU GUI, actual Java startup and x86 rejection
  in the x64 player are verified locally. Existing saves are retained.

- One BD-J disc now passes reset/reopen on copied catalogue data with a synthetic
  preservation marker, popup/top-menu navigation, audio selection, visible English
  subtitles and chapter next/previous/seeking. Native fullscreen toolbar chapter
  markers follow menu/film/return transitions. This is agent coverage of one disc.
- Fixed fullscreen player controls not appearing when Blu-ray menu input consumed
  mouse movement; the before/after GUI check and ordinary MPEG-2 smoke pass.

- ISO opening is implemented: native ownership/routing tests pass; menu, film,
  close and reopen were observed. The user confirmed ISO drag-and-drop to menu.

- ISO replacement/caption/unmount and ordinary-file transitions pass. Main-movie
  preference is confirmed through native state; see the capture limitation in
  [Validation](VALIDATION.md).
- Exact madVR 210 is confirmed by official archive/module hashes. D3D11 fullscreen
  windowed is the primary mode. A temporary exclusive seek-bar cycle also passed;
  original global settings were restored.
- H.264, HEVC Main10, AV1 and MPEG-2 synthetic files render with madVR and decode
  to EOS through custom LAV. Component and actual-JAR checks pass.
- Publication scanner, author metadata review, paired docs/resources checks,
  manual cloud workflow and allowlist packaging are prepared and tested locally.

## Next open work

1. Broader BD-J matrix: a mouse-capable menu, Java/saves lifecycle, other discs,
   menu audio/stills, language combinations and additional decoder paths.
2. Execute the protected PR/CI flow and prepare a cloud ZIP candidate. Test that
   exact ZIP with a clean profile before a Release; local results do not qualify it.

This remains experimental. Full compatibility, HDR accuracy, DVD ISO and MVC
stereo output are unqualified. New upstream versions do not replace pins automatically.

The separate menu-opening command used during initial testing has been removed.
Compatibility settings now pass native EN/RU layout, Apply/Cancel/default/restart
checks, including complete 32-bit mask persistence. The user reports normal Sony
intro playback outside RDP; the agent also observed it on initial open and reopen.
The former intermittent failure is not currently reproduced; no cause or fix is claimed.
The user confirms that this particular authored menu does not support mouse input;
its lack of click activation is expected, not an HC defect. General BD-J mouse
coverage remains open on a menu known to support it. Native fullscreen controls and the renderer seek bar are separate validation paths.
