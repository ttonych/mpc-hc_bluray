# Contributing to MPC-HC Blu-ray

[Русский](CONTRIBUTING.ru.md) · [Development](bluray/docs/DEVELOPMENT.md) · [Release process](bluray/docs/RELEASING.md)

Send fork issues and pull requests to
[ttonych/mpc-hc_bluray](https://github.com/ttonych/mpc-hc_bluray), targeting **main**.
This fork retains official MPC-HC history, authors and licenses. The original
contribution guide is preserved in [docs/UPSTREAM-CONTRIBUTING.md](docs/UPSTREAM-CONTRIBUTING.md);
its upstream destination and `develop` workflow do not describe this fork.

## Before changing code

Read [AGENTS.md](AGENTS.md), the [development guide](bluray/docs/DEVELOPMENT.md)
and [current limitations](bluray/docs/VALIDATION.md). Check the branch, worktree
and relevant code, preserving unrelated edits. Use a short `feature/`, `fix/` or
`update/` branch. Keep changes focused and follow existing C++/MFC conventions.

The player base comes from official MPC-HC; common Blu-ray work comes from a
recorded commit of MPC-BE Blu-ray. Do not merge whole MPC-BE branches or treat
uncommitted donor work as a source release. Record selections, adaptations,
deferrals and checks in the [porting log](bluray/docs/PORTING.md). Keep HC graph,
LAV and settings adaptations separate from shared algorithms. See
[sources.json](bluray/sources.json) and [imports.json](bluray/imports.json).

Maintain dependency changes as patches with manifests and relevant regressions.
An edit to ignored vendor files alone is not reproducible. Investigate checksum
failures; do not accept unexpected input by simply replacing its expected hash.

## Documentation and translations

Update English and Russian documents/UI strings together. Markdown is UTF-8;
read and write it with an explicit encoding, especially in Windows PowerShell.
Preserve resource BOMs and line endings, including UTF-16 resources and existing
PO formatting. Avoid repository-wide conversion or unrelated formatting.

Describe user-visible changes under **Unreleased** in both
[changelogs](bluray/CHANGELOG.md). Group additions, fixes, component updates and
known limitations; record detailed test evidence separately in Validation and
source provenance in Porting. Do not invent a release date or mark a version
released before publication. Update the roadmap when priorities or status change.

## Validation and pull requests

Run checks appropriate to the change. For documentation, verify paired text,
links, encoding and publication contents; rebuilding the player is unnecessary.
For player changes, build x64/EN/RU and test affected behavior, including ordinary
files when changing common playback paths. Java patches require the built-JAR
tests, not only stubs. Donor results and compilation do not prove HC playback.

With the resource-check environment from the development guide:

```powershell
./bluray/tools/.venv/Scripts/python.exe bluray/tools/check-docs-and-resources.py
python bluray/tools/check-public-tree.py
git diff --check
```

Use a fresh portable profile and copied or synthetic disc saves. Do not change
installed players or shared madVR preferences during an unrelated test. Distinguish
automated results, direct observations and user reports. Keep personal paths,
task identifiers, profiles, logs, dumps, saves, disc contents and local runtimes
out of commits and packages. Review new public author metadata while preserving
upstream attribution. The scanner supplements a human diff/history review.

Open a PR to `main` describing the problem, resulting behavior, validation and
remaining limits. The required `source-check` must pass; protection also applies
to administrators. A second person's approval is not required. Merge only the
checked revision, then delete the finished branch without losing unrelated work.
Do not bypass protection or push directly to `main`.

Ordinary pushes and PRs run fast checks. Full player builds are manual candidate
builds; release qualification and publication follow the separate
[release process](bluray/docs/RELEASING.md).
