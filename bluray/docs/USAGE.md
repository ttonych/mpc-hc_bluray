# Using MPC-HC Blu-ray

[Русский](USAGE.ru.md) · [Project](../../README.md)

Extract a candidate ZIP into a new writable folder. Keep the supplied INI next to
the EXE: it selects portable settings. Do not overlay an installed player or copy
an existing personal profile into a package intended for redistribution.

1. Install madVR 210 x64 separately and select madVR in Options > Playback > Output.
   Use its D3D11 fullscreen windowed configuration; exclusive mode is not required.
2. For BD-J, install a matching x64 Java runtime. The tested version is Temurin
   21.0.12.1+1. Select its folder on the Blu-ray page and use Check Java if needed.
3. Select menus or main movie on the Blu-ray page. Open the disc/folder through
   Open DVD/BD, or drop an ISO into the window. No separate menu-opening command
   is needed. ISO support requires native Windows mounting and a readable image.
4. Navigate with arrows and Enter. Alt+T requests the title menu; Alt+R requests
   the popup/root menu. Mouse support and prohibited operations depend on the disc.

Disc saved data and cache default to `bdj-data` beside the player. The Disc data
dialog lists identified discs, supports aliases and prepares a fresh save/cache
location for the next opening. Reset retains previous files and does not reset
other discs. Never distribute your resulting INI or saved data.

Java and madVR are not included. Their system settings can be shared between
players even when MPC-HC uses a portable INI. Menu playback errors are reported;
the player does not silently fall back to the main film after a menu failure.
The project does not provide disc keys or decryption components.

See [validation and limitations](VALIDATION.md) before treating a candidate as a
replacement for your regular player. Ordinary file playback remains available.
