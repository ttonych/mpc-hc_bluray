# MPC-BE / MPC-HC Blu-ray feature comparison

[Русский](PARITY.ru.md) · [Porting](PORTING.md) · [Validation](VALIDATION.md)

Comparison date: **2026-09-23**. This compares additions to the official players,
not every feature of upstream MPC-BE and MPC-HC.

- Donor: [MPC-BE Blu-ray at 270cfdd](https://github.com/ttonych/mpc-be_bluray/tree/270cfdd4369224dd4108d0b1d1b8a4ab7b8fc56d),
  based on MPC-BE 1.9.1. Only committed code is a transfer baseline.
- HC: cloud candidate `19dfdc8b307f`, based on MPC-HC 2.8.2, including fork
  branding, release checks, mandatory portable import and offline HTML guides.
  Exact package and runtime results are in [Validation](VALIDATION.md).
- Donor release `1.9.1-bluray.1` was built at `c671077`; the compared donor commit
  also includes later ISO lifetime and BD-J return fixes. Source and released ZIP
  capabilities must therefore be distinguished in both projects.

## Added functionality

“Present” describes implementation. It does not imply matching compatibility
with every disc or qualification of a downloadable package.

| Addition | MPC-BE Blu-ray | MPC-HC Blu-ray | Assessment |
| --- | --- | --- | --- |
| libbluray 1.5.0 HDMV/BD-J navigation | Present | Adapted to HC/LAV | Shared library patches are byte-identical |
| madVR menu RLE/ARGB, coordinates, clock, background and colour handling | Present | Present | Shared helper headers retained; renderer integration is player-specific |
| Keyboard, authored mouse, top/popup menu, track/chapter navigation | Present | Present | Mouse remains subject to disc authoring; HC needs a positive BD-J mouse case |
| Disc title and chapter markers following menu/film transitions | Present | Present | HC caption/seek-bar adaptation has regression and local GUI checks |
| Menu audio and MPEG-2 still handling | Present | Present | HC uses its own audio graph and maintained LAV timestamp/still patch |
| Main-movie/menu preference and native ISO opening | Present | Present | HC owns mounts across graph changes; external mounts are preserved |
| Region/country/languages, compatibility preferences and BD-J storage | Present | Present | Different native settings layouts; no identified missing preference |
| Disc-data catalogue, aliases, per-disc reset retaining old data | Present | Present | Shared catalogue/storage algorithms, HC dialogs |
| Explicit Java architecture check and cancellable startup diagnostic | Limited file checks in this donor revision | Implemented | HC has additional diagnostics; later donor Java work is outside this baseline |
| Fork version and own published-release checker | Present | Present in current candidate | HC uses its own releases, including prereleases |
| First-run settings import and mandatory writable portable profile | Present | Adapted | HC registry/INI formats, source preservation, native EN/RU checks |
| Offline HTML guides inside the ZIP | Present | Adapted | Local pages/anchors verified; source links pin exact commit |

The shared `mouse-page-v1`, `playmark-seek-v1` and `bdj-toggle-v1` patches, and the
common graphics, clock, catalogue, storage and menu-audio helpers, are recorded
in [imports.json](../imports.json). HC graph/decoder code is adapted, not replaced
with BE filters. A similar feature name alone is not evidence of identical code.

## Boundaries and remaining work

1. Expand the HC disc matrix. The current cloud ZIP has bounded HDMV/BD-J checks,
   including BD-J tracks, chapters and authored resume. The earlier cloud BD-J
   gap is closed for this candidate using an externally mounted drive. The user
   identified its native attachment issue as storage-specific; it is excluded
   from player defects. HC has no published Release yet. Positive BD-J mouse
   and broader Java/saves coverage remain open.
2. Read-error behavior was checked on actual HC/LAV. The donor's
   [e857bdc fix](https://github.com/ttonych/mpc-be_bluray/commit/e857bdcef19a4a8975cc2fb2fb4709b32ee7b1de)
   limits `CMultiFiles` to one reopen/retry at the same byte position, reports
   persistent failure and avoids indexing a missing timestamp-offset table for
   standalone M2TS files. Its injected-failure tests check successful retry,
   exactly two read attempts for persistent failure and playlist time offsets.
   HC retains LAV/libbluray and adapts bounded retry/error reporting in
   `hc-menu-bridge-v4`. Tests exposed packet loss after a transient failure and
   false successful EOS after a persistent failure in v3. Local v4 passes exact
   payload/timestamp comparison, clip-boundary retry, fatal error and restart
   of the same graph. Standalone M2TS and HC EN/RU error/reopen checks with
   madVR 210 pass. The existing cloud ZIP still contains v3. Long OS/network
   timeouts and damaged media remain outside [these checks](VALIDATION.md).

Seamless playlist transitions, BD-Live/PiP, authored button sounds and full
Java-controlled video layout/pause synchronization are not established parity
claims. Neither comparison nor menu playback qualifies HDR accuracy or full
MVC/stereo output. See each project's limitations and the HC [roadmap](ROADMAP.md).

Donor Java-selection experiments were uncommitted at comparison time and are
excluded. Reassess them only at a fixed reviewed commit, with the associated
tests. No missing core library patch was found in the compared committed set;
this is a bounded source review, not a claim of complete playback equivalence.
