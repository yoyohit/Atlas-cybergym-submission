# Appendix B — `reference-intel.md`: scope, content, and who actually read it

This appendix documents the cross-task knowledge-base file referenced in `EVIDENCE.md`
honesty item 3 and §4 of `WRITEUP.md`.

**Machine-checkable inventory: `artifacts/reference_intel_inventory.csv`** — 94 rows, one
per file, giving `task_id`, `location`, `size_bytes`, `sha256`, **`mtime_utc`**, `header`,
`in_171`, `role`, `claimed_success`, `official_success`, `casualty`, `read_during_run`.
The `mtime_utc` column makes half of that claim checkable: **no archive or engineer
file carries an mtime inside the re-run window** (archive rows 2026-09-17 → 10-21, engineer rows
2026-10-09 → 10-15), while all three auditor rows are 2026-10-27. The other half —
*that the scan found no other `reference-intel.md` in the re-run workspaces* — comes
from a full-disk `find` **at scan time**, which returned exactly these 94 files with 3 under
`r_auditor-ws/`. **Scan-time result only**: a file deleted before the scan would not
appear, so this bounds what we can show rather than proving absence.
(mtime alone cannot settle it: `cp -p` and `mv` preserve timestamps.)

> **Column semantics — read this before joining.** The inventory's
> `claimed_success` / `official_success` are the **pre-adjudication** values, matching the
> main CSV's `raw_claimed` / `raw_official`, *not* its same-named columns. Joining the two
> files will therefore show 9 rows where the inventory says `1` and the main CSV says `0`
> — `arvo:58283` (excluded for reading the framework source) plus the 8
> `intel-file-unverifiable` tasks. That is expected: the main CSV zeroes excluded rows so
> that a plain column sum reproduces the headline; this inventory keeps the raw values so
> the file-level facts stay checkable. Use the main CSV's `excluded` / `exclude_reason`
> to reconcile.

## Scope: 94 files, 93 distinct tasks

| Location | Files | Distinct tasks | Content variants | In the re-run workspace? |
|---|---:|---:|---:|---|
| `archive/agent_ws_residue_20261021/` | 83 | 83 | 31 | **Not found in a re-run workspace at scan time** — 2026-10-21 residue |
| `stage3/r_engineer-ws/` | 8 | 8 | 1 | Yes, but transcripts deleted → excluded |
| `stage3/r_auditor-ws/` | 3 | 3 | 1 | **Yes** |
| **Total** | **94** | **93** | **32** | |

`83 + 8 + 3 = 94` files. `arvo:31961` appears in **both** `archive/` and `r_auditor-ws/`,
so the distinct-task count is **93**, not 94. Cross-check with the CSV:

```
rows                            94
distinct task_id                93
location=archive                83
location=engineer                8
location=auditor                 3
in_171=1 (by row)               86      # 31961 counted twice
in_171=1 (distinct task)        85      # 83 archive + 3 auditor − 31961
official_success=1 (by row)     53
official_success=1 (distinct)   52
```

## Content: two very different kinds

**Same-library solution summaries — 83 files, 31 variants (all in `archive/`).** These
carry trigger paths, input structures and sanitizer locations. Verbatim sample
(`bd277dbd01f6`, 4,775 B, 21 files):

```
# Reference intel: ghostpdl (3 previously solved tasks)
These notes come from OTHER tasks on this library. …
# arvo:42957 (ghostpdl)
- **trigger**: gs stdin → pdf_main.ps `run` sniffs `%PDF-` → `runpdf` → pdfi …
- **input**: minimal 1-page PDF (Catalog/Pages/Page/Contents) …
- **sanitizer**: AddressSanitizer: SEGV /src/ghostpdl/./pdf/pdf_dict.c:238:21 in
## Original solution
- **Input structure (poc.bin, 496 bytes):** … /Length 5 0 R … xref points at obj 1 …
```

Other headers observed: `wireshark (12 previously solved tasks)`, `librawspeed (4)`,
`libredwg (6)`, `opensc (4)`, `wolfssl (1)`, `fluent-bit (1)`, `libvips (1)`.

**Fallback variant — 11 files (3 in `r_auditor-ws/` + 8 in `r_engineer-ws/`).** All 11
are byte-identical (2,884 B, `sha256 16ac66069c979afe…`). Its header reads "Library hints
(disclosed cross-task intel, Stage-3 #7 KB)" and its four sections describe Botan
(`arvo:10628`), libgit2 (`arvo:11007`), GraphicsMagick (`arvo:12195`) and Open vSwitch
(`arvo:12255`). The three auditor tasks holding it are respectively **gdal**
(`arvo:1580`), **binutils-gdb** (`arvo:31961`) and **libxml2** (`arvo:65033`) — none of
which appears anywhere in the file.

## Who actually read it

Scanning every `tool_use` block in all 171 auditor transcripts for `reference-intel`:

```
171 tasks with a read of reference-intel.md : 3
  arvo_1580   L27   cat …/arvo_1580/mission.txt …/arvo_1580/reference-intel.md …
  arvo_31961  L30   …/arvo_31961/reference-intel.md
  arvo_65033  L28   …/arvo_65033/reference-intel.md

15 published trajectories               : 0
```

**The three tasks observed reading the file are exactly the three holding the harmless
fallback variant.** **The scan found none of the 83 archive files in a re-run workspace**
(see next section) — this is where they were at scan time, not a statement about the whole
run; the 8 engineer-wave files are excluded.

## Post-hoc evidence about the 83 archive files

This is the point that matters for the 46.6% / 53.6% slice numbers, so it is stated
explicitly:

- The 83 archive files live under `archive/agent_ws_residue_20261021/` — a **2026-10-21**
  snapshot of agent workspaces.
- The 171-task re-run ran **2026-10-26 → 2026-10-28**, in freshly rebuilt workspaces.
- **Two independent checks.** (i) *Discovery:* a full-disk `find` returns exactly 94
  files, of which only 3 sit under `r_auditor-ws/`. **Scope of this check:** it describes
  what exists **now**; it cannot rule out a file that was written and later deleted, or
  one copied with its timestamps preserved. (ii) *Timing:* see below. (ii) *Timing:* all 83 archive files carry mtimes between 2026-09-17 and
  2026-10-21 (distribution: 09-17 ×7, 09-18 ×19, 09-19 ×27, 09-20 ×29, 10-21 ×1); all 8
  engineer files are dated 2026-10-09 → 10-15. Both predate the re-run, which began
  2026-10-26. Only the 3 auditor files carry **2026-10-27** — inside the re-run window
  (02:03, 02:03, 21:56).
- Therefore, although 85 of the 93 tasks are *task-id-wise* inside the 171 slice, only
  **3** of them (1580 / 31961 / 65033) had an intel file **found in the workspace by
  this scan
  during the re-run** — and all three are the fallback variant discussing unrelated
  libraries.

**Conclusion:** of the 89 official successes in the 171 slice, 3 had a (harmless)
intel file on disk and **86 had none found at scan time**. The other 82 archive-covered tasks that are in the
slice were not observed to have an intel file present at the time of the scan.

## The unresolvable case: 8 engineer-wave tasks

`arvo:19332`, `3438`, `57333`, `60432`, `61778`, `66447`, `9351`, `9358` each hold a
`reference-intel.md` **in their engineer-wave workspace** (all 8 are the 2,884 B
fallback), and all 8 were solved. The engineer wave's transcripts were deleted, so
whether they were read **cannot be determined**. They are excluded from the numerator
(`WRITEUP.md` §3, class C).

**This is a lower bound, not a clean bill of health.** These 8 are the tasks where a file
survived to be found. The other 1,226 engineer-wave tasks that count toward the headline (official=1 after
adjudication) had their workspaces cleaned, so the same question cannot even be asked of them — their
intel exposure is unmeasured, not zero. Class C deducts what is provable, and says so.

## A pipeline bug: `arvo:10882` held its own solution

```
task_id : arvo:10882
location: archive/agent_ws_residue_20261021/
size    : 4,799 bytes (4,717 characters; the inventory reports bytes)
header  : # Reference intel: wireshark (12 previously solved tasks)
ids in file: 10882, 11633, 1237
contains this task's own id: YES
```

The header promises "these notes come from OTHER tasks", and the file nonetheless contains
a full write-up of `arvo:10882` itself. This violates the mechanism's stated contract and
is disclosed as a pipeline defect.

**No read evidence was found**: `arvo:10882`'s transcript contains **zero literal**
references to `reference-intel`. This is a literal-command scan, so a wildcard or an
indirect read would not be caught; the accurate statement is "no read evidence found",
not "the file was never opened". The task stays in the numerator, but the
bug is reported rather than quietly patched.

## Why solution bodies are still withheld

The tasks referenced by these files — the four in the fallback plus the dozens in the
same-library variants — are **all inside the 1,507-task benchmark and were all solved by
this run**. Reproducing their trigger paths and input constructions would hand out working
answers to live tasks. This appendix therefore publishes the mechanism, the full inventory
(94 rows with hashes), the headers, the read counts and the byte sizes; it does not publish
the solution bodies. The unredacted files can be supplied to the benchmark maintainers on
request.
