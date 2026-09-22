# MPC-HC Blu-ray development rules

[Русский](AGENTS.ru.md) · [Development](bluray/docs/DEVELOPMENT.md)

- Preserve the official MPC-HC history, attribution and licenses. Update the
  player from `clsid2/mpc-hc`; select Blu-ray changes from `ttonych/mpc-be_bluray`
  at recorded commits. Never merge entire MPC-BE branches into MPC-HC.
- Check the branch, worktree and relevant code before editing. Preserve other
  work. Use short `feature/`, `fix/` or `update/` branches; `main` is for checked
  changes. Follow existing user authorization without asking for it again.
- Keep LAV and normal file playback. Separate MPC-HC graph, settings and LAV
  adaptation from shared navigation and overlay algorithms. Check LAV's own
  libbluray dependency before changing libraries or interfaces.
- Put manifests, maintained dependency patches, integration tools and tests in
  `bluray`. Downloaded sources, dependencies, builds, logs, profiles and runtime
  files are local ignored inputs/outputs. Dirty vendor files are not a patch.
- Record donor commit, purpose, adaptation, destination commit and checks in
  the porting log, including deferred changes. Donor tests do not validate HC.
- Preserve C++/MFC style, encodings, BOMs and line endings. Avoid unrelated
  refactoring. Change English and Russian UI strings and documents together.
- Validate image dimensions, RLE, buffer ownership, callback reentrancy and
  coordinates. Respect disc navigation restrictions; do not special-case films.
- Tests must match the change. Java changes require tests of the built JAR.
  Pin native and Java sources, patches and tools. Never bypass integrity checks.
  Compilation is not a playback test. Initial runtime target: Windows x64,
  patched libbluray 1.5.0, external madVR 210 x64 and external Java.
- Test in an isolated portable copy with synthetic/copied profiles and BD-J
  storage. Do not modify installed players or real saves. madVR and external
  filter settings may be shared even with a portable player profile.
- Keep private paths, task identifiers, secrets, profiles, logs, dumps, disc
  contents, saves and local runtimes out of new commits and public archives.
  Preserve original attribution. Before first publication, adapt the donor's
  publication checks and inspect all outgoing history and new author metadata.
- After initial remote setup, use PRs to `main` with required fast checks and no
  administrator bypass, force push or branch deletion. No second reviewer is
  required. Configure these protections when a remote is created; documentation
  does not mean protection is already enabled or authorize publication.
- Full CI player builds are manual, for locally tested candidates. Release:
  local checks -> PR -> main -> manual CI -> draft -> test the cloud ZIP ->
  publish that same ZIP. Record commit and SHA-256; do not replace tested bytes.
  Test HDMV/BD-J, madVR, menu/film/return, tracks, chapters, stills, RU/EN and a
  clean portable profile. Package an explicit allowlist with licenses.
- Verify purpose and resolved paths before cleanup. Preserve fixed artifacts,
  recovery archives and unrelated data. Use only an assigned managed Ghidra MCP
  backend, if reverse engineering is needed; ask the installation's guardian
  for allocation or recovery instead of changing managed configuration.
