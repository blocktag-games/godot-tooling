# Artifacts manifest
Generated 2026-09-21. SHA-256 of each listed file at that commit. Regenerate with:
```
sha256sum <path>
```
| Path | SHA-256 | Role |
| --- | --- | --- |
| `docs/benchmarks/final-report.md` | `087b777e271d511aeecc779fd13122d9df9dd990118c0c483747a4c07f7d78e7` | Main published study (BP13) |
| `docs/benchmarks/maintainer-review-package.md` | `b96cee29a68dc327ddb52e2cc57727193282234dd1f44d538e8f8973428c3b7e` | Factual review material for tool maintainers, unsent |
| `docs/benchmarks/architecture-decision.md` | `40fd0b3d11f1def2b9d90523a04bbc32aa48aef45df0d3ae1995961aa530aea9` | Final architecture decision record |
| `docs/benchmarks/main-study-results.md` | `bf7a67d8414fe06cbdeaff6ad739f2693b1c8fce290f72b350acbdb8a4a9dac9` | BP10 controlled main study report |
| `docs/benchmarks/corpus-run-2026-09-19.md` | `0e1994ed7b4cb7a91a7bcdcb30f33dfc35a6dc0d867c6df1f051fdaf834f6ed1` | BP06 correctness corpus findings |
| `docs/benchmarks/performance-protocol.md` | `8015b444c9b80d586f644f815d8763982b35bc7e67c38ac687b295e6cf17f7e5` | Frozen performance protocol |
| `docs/benchmarks/performance-eligible-cells.tsv` | `c6114dd4c99b58da29a9a2087ad3f0fdc84c85e0b80d35d2b942483465547d27` | Frozen eligible (candidate,workload,condition) cells |
| `docs/benchmarks/pilot-observer-matrix.tsv` | `7c9410ab8df3fdfd1174a93a703a6023b98cf18a245606e87c5ccf4f4cb1e1d1` | BP08 observer-factor availability record |
| `docs/benchmarks/fixture-catalog.tsv` | `3072cf1b9441a27734c9f47d3baa024207d278fa0842aaaffeef1dcb850da752` | Full correctness fixture catalog (incl. F082) |
| `docs/benchmarks/experiment-matrix.tsv` | `cb3826df894673ce9faa13b68cc465ff4cb3014c69c5e307c7c4c00a6c5c98ce` | Experiment family status matrix |
| `docs/benchmarks/pilot-environment.md` | `68270fe43862e869103bef98bcd5b9206c3cc639ec7f2adfab5746a187ba7948` | Pinned engine/tool versions and hashes |
| `pilot/fixtures/oracles/F057.json` | `06d7a6747c8bae23b172d4f38ec5e5327c019b1e5c19de03754f7b06763b0a86` | gd-tools error-line-shift oracle |
| `pilot/fixtures/oracles/F082.json` | `8069a29747b215b4adf69c91b7bc6d3f0922a6709534aab2a76a5ccc185b907a` | Debugger-protocol error-line-shift oracle (both candidates) |
| `pilot/performance/pilot_results.tsv` | `0ae81882b5c9c3ffdb6cd369ed57b3c1eb4e824d24eae3307321cb213ad94eac` | BP07 pilot raw data (200 rows, exploratory) |
| `pilot/performance/main_study_results.tsv` | `2a3363683ca301f0416063946ecb8104b0bf25e85344b3d7b42881bf12dfa0aa` | BP10 main study raw data (1200 rows, confirmatory) |
| `pilot/performance/main_study_sessions.jsonl` | `28afb42547980fde25731f8c5aeb6b5a1006da384e9660e13b756a1ed0668361` | BP10 per-session schedule/quiescence/environment log |
| `pilot/performance/calibration_result.json` | `d474d6d77205e4bf2600ca8b271f1bc6c8f3d91c5c4219a03d6f4541fc341120` | Frozen per-workload input sizes and calibration diagnostics |
| `pilot/performance/environment.json` | `85ea3baf5a84b8d761ea69be83d49b799199dca56dbef1c0da5dc200195c51c1` | BP07 pilot environment snapshot |
| `pilot/candidates/nano-coverage-godot-PIN.md` | `c2a51e24c4066fef23c16d32ab2e01880e68790863a148bc79f652080a36f928` | Nano Coverage version pin and build record |
| `pilot/candidates/godot-code-coverage/PIN.md` | `f0be043119fca439bc6f87dd3434ac01492da4377bd5cdcc27b304a44a75fb51` | godot-code-coverage incompatibility record |

## Provenance and licensing

- This repository's own code, fixtures, and documentation are published under its existing Apache-2.0 license.
- Evaluated tools retain their own terms: gd-tools-cli 0.4.0 (see its own repository), Nano Coverage (Apache-2.0, confirmed against `LICENSE.md` in `pilot/candidates/nano-coverage-godot-PIN.md`), GUT v9.7.1, GdUnit4 v6.2.1. None of their source is redistributed in this manifest beyond what each project's own license permits; this project vendors pinned copies under `pilot/candidates/` and `pilot/fixtures/` per each tool's license, not by exception.
- The pinned Godot 4.7.1 binary is not committed to this repository (matches this project's established pattern); it is reproducible from the official `godotengine/godot` GitHub release for tag `4.7.1-stable`, recorded by build-string and provenance in `pilot-environment.md`.
- No third-party binaries, profiler captures, or machine-identifying paths are included in this manifest's listed files. `pilot/performance/environment.json` and `main_study_sessions.jsonl`'s embedded environment records contain this machine's CPU model, kernel version, and OS distribution — disclosed deliberately as part of the performance study's environment record, not scrubbed, since none of it identifies a person.

## What is NOT yet a complete "study bundle"

Per `reproducibility.md`'s status note, this manifest lists the artifacts that exist and matter for this study's headline claims — it is not the full `study.json`/`runs/<run-id>/` bundle layout `reproducibility.md`'s "Proposed release layout" section describes. Group 2 lifecycle fixtures beyond one spot-check (F042) are not swept against either candidate and have no corresponding raw-data artifact here; this is a stated scope gap (`final-report.md` §4), not an omission from this manifest.
