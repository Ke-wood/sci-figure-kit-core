# Environments: paths, install, repair

Everything lives under **one root** you choose (`SCI_FIG_ROOT`, default `D:/app`).
Nothing is written into your global Python or R installation.

| Backend | Path | What |
|---|---|---|
| figkit | `{root}/envs/figkit` | Python venv: cnsplots, SciencePlots, cmcrameri, marsilea |
| R | `{root}/R` | official CRAN R + ggplot2, ComplexHeatmap, SCpubr, ggenomes, Seurat |
| omicverse | `{root}/envs/omicverse` | conda prefix: omicverse |

The machine-local registry is `{root}/envs/envs.json`. Resolution order:

```
$SCI_FIG_ENVS  →  <skill>/envs.json  →  {root}/envs/envs.json  →  built-in defaults
```

`install/bootstrap.py` writes both files, so the skill keeps working after you move it.

## Install

```bash
python install/bootstrap.py --root /path/to/sci-fig        # all three
python install/bootstrap.py --root /path/to/sci-fig --only figkit
```

The three backends are independent; a missing backend fails only its own health probes.

## Download sources (user's choice)

Everything is fetched from configurable sources — nothing is hardcoded except the
official defaults:

```bash
python install/bootstrap.py --root X --source tuna     # official | tuna | ustc | aliyun
python install/bootstrap.py --list-sources
python scripts/mod.py sources [tuna]                   # show / switch, used by mod installs too
```

Per-channel overrides: `--pip-index`, `--cran-mirror`, `--bioc-mirror`,
`--conda-channel`, `--offline-dir`. Env vars: `SCI_FIG_SOURCE`,
`SCI_FIG_PIP_INDEX`, `SCI_FIG_CRAN`, `SCI_FIG_BIOC`, `SCI_FIG_CONDA_CHANNELS`,
`SCI_FIG_OFFLINE_DIR`. The choice is persisted in `envs.json`
(`source_preset` + `sources{}`), so re-runs and mod installs reuse it.

`official` means for pip: **pass no `--index-url` at all**, i.e. honour the user's
`PIP_INDEX_URL` / `pip.ini`.

`--offline-dir D:/bundle` expects `bundle/wheels/*.whl` (pip `--no-index
--find-links`) and `bundle/cran/` (a CRAN repo used as a `file:///` source).

### R version is resolved, not pinned

CRAN keeps only the **latest** Windows installer in `bin/windows/base/`; a pinned
version 404s within weeks (`R-4.6.1-win.exe` is already gone — only 4.6.2 remains).
The installer lists that directory and takes the max, falling back to a constant
only if the listing fails. Pin explicitly with `--r-version`.

## Why R comes from CRAN, not conda

conda-forge's Windows R ships **two mingw toolchains** (m2w64 based on MSVCRT and
mingw-w64-ucrt based on UCRT). R 4.5+ is a UCRT build, so DLLs from the wrong side
trigger "Mingw-w64 runtime failure" pseudo-relocation overflows — intermittently, which
makes it look like a random crash. Mixing CRAN binaries on top of conda's runtime makes it
worse, not better. Use the official CRAN installer.

## Repair

Each `scripts/install_*.sh` is idempotent. After any change:

```bash
python scripts/check_envs.py
```
