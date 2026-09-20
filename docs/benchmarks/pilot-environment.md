# Pilot environment pin (BP01)

Frozen 2026-09-19. This is the completion evidence for [BP01](implementation-plan.md#work-packages-and-completion-evidence): actual engine/hash/build, chosen machine, candidate pins, runner pairing, pilot schedule, and explicit unavailable modes. It does not itself contain fixtures, oracles, or measurements — those are BP02 onward.

## Machine

| Field | Value |
| --- | --- |
| Host | Single shared Linux workstation (not a dedicated/controlled benchmark machine) |
| OS | LMDE 7 "gigi" |
| Architecture | x86_64 |
| CPU | Intel Core i7-11850H, 16 logical CPUs |
| RAM | 62 GiB |
| Pinned date | 2026-09-19 |

This machine is a development workstation, not an isolated benchmark host. Background load, thermal throttling, and shared-resource contention are not controlled. Treat any timing collected here as pilot/smoke evidence only, per the study plan's caution against confusing a development session with a controlled performance run. This is the only machine this study uses; dedicated hardware and additional OS coverage (Windows/macOS) are explicitly descoped (2026-09-20, see implementation-plan.md's BP12 row) rather than pending -- tracked as a permanent unavailable mode below, not a gap awaiting resolution.

## Engine

| Field | Value |
| --- | --- |
| Release | Godot 4.7.1-stable |
| Build string | `4.7.1.stable.official.a13da4feb` (from `--version`) |
| Asset | `Godot_v4.7.1-stable_linux.x86_64` (standard GDScript editor/CLI build, not mono) |
| SHA-256 | `32f8d7596c4b41185512b1c49d69f2da3be018fd784a53e349fa92a98a97bcde` |
| Source | Reused from a pre-existing local install (`~/.local/opt/godot-4.7.1/`); not re-downloaded. Provenance is the official `godotengine/godot` GitHub release for tag `4.7.1-stable`. |
| Sandbox location | `pilot/godot/Godot_v4.7.1-stable_linux.x86_64` (gitignored; recorded here by hash, not committed as a binary) |

The official per-file checksum asset for this release (`godot-4.7.1-stable.tar.xz.sha256`) covers the source tarball, not this prebuilt zip, so it cannot directly verify this binary. Verification here relies on the build string embedded in the binary itself matching the expected tag and on the binary being copied (not modified) from a prior working install. An independent redownload-and-diff against `Godot_v4.7.1-stable_linux.x86_64.zip` from the same release is a reasonable follow-up before publishing correctness claims, but is not required to unblock BP02.

Confirmed to launch headless on this machine: `Godot_v4.7.1-stable_linux.x86_64 --version --headless` returns the build string above with exit 0.

## Candidate pin: gd-tools

| Field | Value |
| --- | --- |
| Package | `gd-tools-cli` 0.4.0 (PyPI name differs from the `gd-tools` GitHub repo name) |
| Upstream repo | [mansyar/gd-tools](https://github.com/mansyar/gd-tools) |
| Release tag | `v0.4.0`, commit `b5044c33e2928dad9c21c0d908bc799e33a25c34` |
| Install method | Pipenv, isolated per-tool environment |
| Environment location | `pilot/gd-tools/` (`Pipfile`, `Pipfile.lock` committed; `.venv/` gitignored, reproducible via `pipenv sync`) |
| Python | 3.13.5 (CPython, system interpreter; package declares `requires-python >=3.10`) |
| Verified | `pipenv run gd-tools --version` → `gd-tools 0.4.0` inside the pinned venv |

`Pipfile.lock` is the actual reproducibility artifact — it pins `gd-tools-cli` and its full transitive dependency set (`click`, `gdtoolkit`, `jinja2`, `junitparser`, `packaging`, `pydantic`, `pyyaml`, `requests`, `rich`, `tomli_w`) by resolved version and hash. A fresh checkout reproduces this exact environment with `pipenv sync` in `pilot/gd-tools/`.

No standalone `LICENSE` file was found in the upstream repo as of this pin; `pyproject.toml` declares MIT. This is an open item, not a blocker for the correctness pilot.

## Runner pairing

Per the [study plan](README.md#scope-and-comparison-units), the comparison unit is **tool + revision + engine binary + runner + collection mode + configuration**. The first pinned unit is:

> gd-tools v0.4.0 + Godot 4.7.1-stable (`a13da4feb`) + GUT v9.7.1 + supported/released GUT integration mode, on the machine above.

## Candidate pin: GUT

| Field | Value |
| --- | --- |
| Upstream repo | [bitwes/Gut](https://github.com/bitwes/Gut) |
| Target tag | `v9.7.1`, commit `aeb5d4f3f7f0a6c9b5e178876d6c99b791fda605` |
| Local checkout | `~/.local/opt/gut-src`, updated to `v9.7.1` (commit `aeb5d4f3f7f0a6c9b5e178876d6c99b791fda605`) during BP02. |
| Status | **Closed.** Vendored (full addon, including the GUI scenes the CLI runner depends on even headless) into `pilot/fixtures/cases/f064_zero_requested_tests/addons/gut/` for the F064 fixture. Confirmed working end-to-end against the pinned Godot 4.7.1 binary. |

## Pilot schedule

Following [implementation-plan.md](implementation-plan.md), with this document closing BP01:

| Package | Scope | Estimate |
| --- | --- | --- |
| BP01 | Freeze pilot scope and environment identity (this document) | 1–2 days — closed 2026-09-19 |
| BP02 | First independent tier-0 fixtures and oracles | 2–4 days |
| BP03 | Minimal orchestration/evidence harness | 2–4 days |
| BP04 | First gd-tools+GUT adapter run against BP02/BP03 | 2–4 days |

BP05 (remaining candidates: Nano Coverage, godot-code-coverage, GdUnit4 Coverage as a feature comparator) is not scheduled until BP04 produces a working baseline-to-report path.

## Explicit unavailable modes

Recorded now so later results aren't mistaken for broader coverage than they are:

- **Operating systems:** Linux only, permanently -- an explicit scope decision (2026-09-20), not a deferral. Windows and macOS are out of scope for this study; nothing here should be read as cross-platform evidence, and none is planned.
- **Engine variant:** standard GDScript build only. The mono (C#) build is not pinned; C# tooling (Coverlet, GdUnit4Net, GoDotTest) stays an adjacent/later study per the study plan's scope section.
- **Hardware:** shared development workstation, not a dedicated/controlled benchmark machine. No thermal, background-load, or scheduling isolation. Any timing from this machine is pilot/smoke evidence, not a performance-study result.
- **GdUnit4 Coverage:** deferred entirely. Its measurement engine is closed source and requires a patched Godot build outside this pin; it remains a BP05 feature comparator, not part of the correctness pilot.
- **Nano Coverage disk-instrumentation mode:** not pinned yet. Disk-mode-specific fixtures (F075, F079) require their own environment note when Nano is evaluated in BP05.
- **godot-code-coverage:** not pinned yet; scheduled for BP05.
- **Debugger integration (Godot Editor primary; VS Code `godot-tools` optional secondary; JetBrains/PyCharm dropped from scope 2026-09-20):** out of scope until BP11. No editor/IDE build or plugin version is pinned here.

## Reproduction

From a clean checkout of this repository:

```sh
# Engine: obtain Godot_v4.7.1-stable_linux.x86_64 independently (this repo does not
# vendor the binary) and verify:
sha256sum Godot_v4.7.1-stable_linux.x86_64
# expect: 32f8d7596c4b41185512b1c49d69f2da3be018fd784a53e349fa92a98a97bcde

# gd-tools:
cd pilot/gd-tools
pipenv sync
pipenv run gd-tools --version
# expect: gd-tools 0.4.0
```
