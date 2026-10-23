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
