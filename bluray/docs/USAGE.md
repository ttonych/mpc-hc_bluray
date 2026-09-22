# Using MPC-HC Blu-ray

[Русский](USAGE.ru.md) · [Project](../../README.md)

## Requirements and first launch

Use Windows x64 and readable Blu-ray contents. The project does not supply keys
or decryption components. Java and madVR are external components, not bundled
in the player ZIP. Ordinary media files can still use the usual MPC-HC paths.

Download the candidate linked from the [project page](../../README.md). If GitHub
wraps the artifact in another archive, extract the inner player ZIP into a new
writable folder. Keep `mpc-hc64.ini` beside `mpc-hc64.exe`: its presence selects
portable settings. Do not overlay your installed player. Launch that EXE directly
so file associations do not accidentally open another MPC-HC installation.

The MSVC-built LAV components require the x64 Microsoft Visual C++ v14 runtime
(at least the build toolset version). If it is absent, use the
[official Microsoft Redistributable installer](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist).

Select **Options → Playback → Output → madVR**, using an external **madVR 210 x64**
installation. The primary tested fullscreen configuration is **D3D11 fullscreen
windowed**. The fork does not enable exclusive or configure global madVR settings.
Those settings and external-filter preferences may be shared with other players.

## Java for BD-J

HDMV menus do not need Java; BD-J menus do. The tested installation is **Temurin
JDK 21.0.12.1+1 x64**. Playback needs a complete Java runtime with desktop/AWT
support; building the JAR additionally needs a JDK. A newer major Java version
is not automatically a compatible substitute.

In **Options → Playback → Blu-ray**, select the Java installation folder, not
`java.exe` or `jvm.dll`. **Check Java** checks the selected installation and runs
its launcher in a separate process. A successful result confirms Java startup,
not compatibility with a particular disc. The x64 player requires x64 Java;
an invalid explicitly selected installation cannot be applied.

Leaving the folder empty permits automatic discovery when opening a disc. For
reproducible tests, select the tested version explicitly. Use **Apply** or **OK**
and reopen the disc after changing Java. Keep the supplied `bluray-4.dll` and
both libbluray JARs from the same package together; do not mix runtime files from
different builds. Exact versions are in [sources.json](../sources.json).

## Opening a disc or ISO

1. On the Blu-ray options page choose **Disc menu** or **Main movie**. Main movie
   is the default in a fresh profile. Apply the choice before reopening a disc.
2. Use **Open DVD/BD** for a disc root or `BDMV` folder. The `index.bdmv` and
   `MovieObject.bdmv` entry points also follow the selected opening mode.
3. Open or drag a readable `.iso` file into the player. Native Windows mounting
   is required. The player attaches the image read-only and retains its own
   attachment across playlist changes, releasing it after closing playback.
   An image mounted externally is reused without forcing it to detach on close.
4. Opening an individual `.mpls` playlist or `.m2ts` clip plays that item through
   the usual file path; it is not a request for full disc navigation.

There is no separate Open Blu-ray Menu command. A menu error is reported rather
than silently starting the film. Unsupported images or mounting failures should
produce an error. Other image formats and third-party mounters are not included.

## Controls

| Action | Default control |
| --- | --- |
| Move menu selection | Arrow keys |
| Activate selection | Enter |
| Request top/title menu | Alt+T or Home |
| Request popup/root menu | Alt+R or the Apps key |
| Select with the mouse | Move/click where the disc implements mouse input |
| Switch chapters or seek in the film | Standard MPC-HC chapter commands and seek bar |

The player menu and context menu route to the same navigation commands. Disc
authoring can prohibit an action or provide keyboard-only menus. An inactive
command or a menu that does not respond to the mouse is not by itself proof of
a player fault. See **Options → Player → Keys** for customized key bindings.

Chapter ticks are hidden while disc menus are active and restored for the film.
The window caption uses disc metadata when available, otherwise the volume or
folder name. Fullscreen player controls should still appear at the bottom edge.

## Languages, region and compatibility

The Blu-ray page sets region, country and preferred menu/audio/subtitle languages.
These are preferences: a disc can omit a language or enforce its own selection.
Country and language fields also accept ISO two-letter country and three-letter
language codes. Changes apply on the next opening, after **Apply** or **OK**.

**Compatibility…** contains the inherited libbluray preferences, including age,
player profile, navigation restrictions and reported audio/video capabilities.
Leave automatic/default values unless investigating a reproducible disc issue.
These values tell a disc what the player reports; they do not install decoders
or establish HDR/MVC support. **OK** in this child dialog stages changes; the
main options window's **Apply/OK** saves them. **Cancel** discards unapplied
changes. Restoring defaults here does not reset disc saves.

## Disc saved data

Saved data and cache default to `bdj-data` beside the player. Separate folders
can be selected on the Blu-ray page. Changing a path neither moves nor deletes
existing files; keep the chosen folders writable and reopen the disc afterward.

**Disc data…** lists identified discs, aliases and last-opened dates, with search,
refresh and folder access. It uses the currently applied storage paths. Renaming
an alias changes only the displayed name, not a physical directory.

A confirmed **Reset** selects fresh saved-data/cache directories for that disc's
next opening. Previous files remain intact, an active session retains its paths,
and other identified discs keep their data. Shared legacy groups cannot be reset
as a single identified disc. Reset and alias changes take effect immediately;
cancelling the options window does not undo them. Back up valuable saves before
experiments and do not publish your catalogue or save files.

## Profiles and updates

The profile-import wizard and mandatory portable behavior of MPC-BE Blu-ray are
not yet ported. Keep the provided INI; without it, inherited MPC-HC behavior can
use the installed player's registry profile. For testing, use a fresh folder
and the supplied empty profile, then set only the options needed for the test.

The inherited update checker still queries official MPC-HC releases. Decline
automatic checking for this candidate and follow this fork's repository for
updates. See the [version scheme](RELEASING.md); the EXE/About version does not
yet show the complete fork release number.

For a new candidate, close the old player, extract into a separate folder and
retain the old folder for rollback. Check the [changelog](../CHANGELOG.md).
Start with the clean profile; if you later transfer settings or saves, work from
backup copies and check Java/storage paths. Do not point experimental resets at
the only copy of your real saved data. Never distribute a used INI or BD-J data.

## Troubleshooting and feedback

| Symptom | What to check |
| --- | --- |
| Film starts immediately | Choose Disc menu, apply and reopen the whole disc; do not open a clip/playlist directly. |
| HDMV works, BD-J fails | Select tested x64 Java, run Check Java, verify matching DLL/JAR files, then reopen. |
| Black picture or missing menu graphics | Verify madVR and its active mode; compare on a local desktop, since an RDP result is not equivalent. Record whether sound or menu selection still works. |
| Mouse does nothing | Try arrows/Enter and report whether this particular menu supports mouse input in the comparison player. |
| ISO stays at Opening or gives an error | Close playback and check whether Windows can mount and read the same image. Report the error and image type; do not mask read/CRC failures. |
| Preferences seem ignored | Apply changes and reopen the disc; check the EXE/INI folder, language availability and disc restrictions. |
| Startup reports a missing runtime | Check the x64 Visual C++ runtime and that the archive was fully extracted. |

Report reproducible problems in [this fork's issues](https://github.com/ttonych/mpc-hc_bluray/issues).
Include candidate commit/version, Windows and renderer mode, Java version for
BD-J, opening method, disc edition/region, exact steps and expected/actual behavior.
Distinguish keyboard from mouse results and menu from film playback. A comparison
with MPC-BE is useful with its exact version, but does not validate MPC-HC.
Review logs or screenshots for personal paths and private information before
sharing; do not attach disc contents, saves, personal profiles or memory dumps.

See [validation and limitations](VALIDATION.md) for the checked scenarios and
remaining gaps. A build that compiles or opens one menu is not a qualified release.
