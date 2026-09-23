# Versioning and releases

[Русский](RELEASING.ru.md) · [Development](DEVELOPMENT.md) · [Contributing](../../CONTRIBUTING.md)

## Fork version scheme

Use **`<MPC-HC base>-bluray.<release>`**, following the same meaning as MPC-BE
Blu-ray: the upstream player version and the fork's release number are distinct.

| Version | Meaning |
| --- | --- |
| `2.8.2-bluray.1` | First fork release on the MPC-HC 2.8.2 base; currently the planned first release |
| `2.8.2-bluray.2` | Next fork release on that same base |
| `2.8.3-bluray.1` | First release after a deliberate migration to MPC-HC 2.8.3; example, not a selected update |

Start the suffix at 1 for a newly adopted upstream base. New features, fixes and
component updates can all require a new fork release; libbluray 1.5.0 and madVR
210 remain separate component versions, not parts of the player version.

Candidate attempts do not consume release numbers. Identify each by full source
commit, Actions run and ZIP SHA-256. The current packager produces names such as
`mpc-hc_bluray-2.8.2-bluray.1-8183fe6579c1-x64.zip`. A rebuilt candidate, even from
the same source, needs its own hash and validation record.

At publication use a tag such as `2.8.2-bluray.1` pointing to the **exact built
commit**, and retain the tested ZIP name/bytes. Mark experimental releases as
GitHub prereleases. Promoting the same tested release does not require new bytes;
changed published payloads require a new fork release number. Never move an
already published tag or silently replace an asset under an existing release.

## Version implementation and release gate

[BlurayVersion.h](../../include/BlurayVersion.h) is the single maintained fork
release number, combined with the official base from `include/version.h`.
EXE ProductVersion, About, empty caption and the packager use that value. About
also shows the source hash. Numeric Windows versions retain the upstream layout
for resource compatibility. `update_version.bat` counts commits from the exact
official base tag, ignoring nearer fork or unrelated version tags.

The checker selects numeric fork versions from this repository's published
GitHub releases, including prereleases, and opens the selected release page.
It does not fall back to official MPC-HC or install files. Old upstream ignored
versions and last-check timestamps are not reused for fork decisions.

Local x64/RU builds, resource/version checks, tag/feed regressions and EN/RU
About/empty-release dialogs pass. The build scripts and packager reject a stale
EXE version. Change the release define, rebuild and validate before a new release.

The candidate's exact commit, completed checks and remaining qualification
are recorded in [Validation](VALIDATION.md). Always use its exact ZIP.
Do not create a release tag merely to make a candidate appear finished.

## Changelog policy

Maintain [CHANGELOG.md](../CHANGELOG.md) and [CHANGELOG.ru.md](../CHANGELOG.ru.md)
together. Keep new work in **Unreleased**, grouped into additions, fixes,
component/build changes and known limitations. On publication, give that section
the actual fork version and publication date (`YYYY-MM-DD`), then create a new
Unreleased section. Keep previous release sections intact.

Release notes summarize that version's changelog, requirements and limitations.
Keep detailed donor provenance in [Porting](PORTING.md) and evidence in
[Validation](VALIDATION.md); a user-facing changelog is not a raw commit list.
The original MPC-HC change history remains attributed to its original project.

## From a local change to a candidate

1. Complete local checks in a short branch and update paired documentation,
   changelog and applicable source/porting records.
2. Open a PR to protected `main`; review its diff and successful `source-check`.
   Merge only the checked revision. Full player builds are not ordinary PR jobs.
3. Manually run **[Blu-ray candidate build](../../.github/workflows/bluray-build.yml)**
   on the chosen merged revision. Record the actual run's source SHA. The workflow
   builds the pinned runtime, player, LAV and Russian resources, runs component
   checks and creates an allowlist ZIP; it does not publish a Release.
4. Download `mpc-hc-bluray-candidate-x64` before its 14-day artifact retention
   expires. Extract the inner player ZIP without modifying it. Verify:

   ```powershell
   python bluray/tools/package-player.py --verify <candidate.zip>
   Get-FileHash -Algorithm SHA256 <candidate.zip>
   ```

5. Prepare a draft Release with the candidate commit, version, exact ZIP,
   SHA-256, component versions, licenses/source information and EN/RU notes.
   The tag must identify the built sources, even if `main` later advances.

Java and madVR remain external. Packages contain an empty portable INI and
explicit runtime/document/license files, never a whole developer working folder.
New documentation goes into new candidates; do not patch an already fixed ZIP.

## Qualify and publish the same archive

Extract the downloaded ZIP into a **separate writable test folder**, keeping
the original ZIP unchanged. Use its clean portable profile and copied/synthetic
BD-J storage. Check program/runtime hashes, files and licenses, then test:

- HDMV and BD-J startup, menus, film and return to menu with external madVR 210;
  primary fullscreen mode is D3D11 fullscreen windowed.
- Keyboard navigation, supported mouse input and authored restrictions.
- Audio/subtitle selection, menu audio, chapter commands/markers and stills.
- Opening/closing/reopening and ISO mount ownership, including external mounts.
- Java startup and saved-data lifecycle, EN/RU settings and clean-profile behavior.
- Ordinary file playback when common graph/LAV/filter paths changed.

Record exact versions, scenarios and results, separating automatic checks,
observations and user confirmation. A local build's results do not qualify the
cloud ZIP. Missing disc coverage or a mount failure remains an open item, not a
pass. HDR/MVC and untested formats must not be inferred from a working menu.

Once qualification and the authorized release work are complete, publish the
draft with **the same ZIP and SHA-256**. If a fix changes package contents, create
and verify a new candidate through the same process. The existing candidate's
identity and limits are recorded in [Validation](VALIDATION.md).
