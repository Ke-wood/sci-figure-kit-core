#!/usr/bin/env python
"""sci-figure-kit 跨机器安装器。

三套环境互相隔离，装到用户自己选的根目录下（默认 D:/app）：

  <root>/envs/figkit       Python venv + cnsplots / SciencePlots / cmcrameri / marsilea
  <root>/R                 官方 CRAN R（Windows 静默安装）
  <root>/envs/omicverse    conda prefix + omicverse

用法：
  python install/bootstrap.py --root E:/tools/sci-fig
  python install/bootstrap.py --root E:/tools/sci-fig --only figkit
  python install/bootstrap.py --root E:/tools/sci-fig --dry-run

装完会写两份 envs.json：
  <root>/envs/envs.json     机器本地注册表
  <skill>/envs.json         skill 自带，换机器时跟着走

不装 R 或 conda 也能只装 figkit：三条腿互相独立，缺哪条体检就报哪条。
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import urllib.request

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(SKILL, "scripts")
REQUIREMENTS = os.path.join(SKILL, "requirements-figkit.txt")
R_VERSION = "4.6.1"
R_URL = f"https://cloud.r-project.org/bin/windows/base/R-{R_VERSION}-win.exe"

IS_WIN = os.name == "nt"


def say(msg: str) -> None:
    print(msg, flush=True)


def run(argv: list[str], timeout: int | None = None, check: bool = True) -> int:
    say("  $ " + " ".join(argv))
    proc = subprocess.run(argv, timeout=timeout)
    if check and proc.returncode != 0:
        raise SystemExit(f"命令失败（{proc.returncode}）：{' '.join(argv)}")
    return proc.returncode


def layout(root: str) -> dict:
    root = os.path.abspath(root).replace("\\", "/")
    return {
        "root": root,
        "venv": f"{root}/envs/figkit",
        "figpy": f"{root}/envs/figkit/Scripts/python.exe" if IS_WIN
                else f"{root}/envs/figkit/bin/python",
        "r": f"{root}/R",
        "rscript": f"{root}/R/bin/Rscript.exe" if IS_WIN else f"{root}/R/bin/Rscript",
        "r_lib": f"{root}/R/library",
        "omv": f"{root}/envs/omicverse",
        "omvpy": f"{root}/envs/omicverse/python.exe" if IS_WIN
                 else f"{root}/envs/omicverse/bin/python",
        "vendor": f"{root}/envs/_mods",
    }


def pick_base_python() -> str:
    """建 venv 用的解释器：优先当前 python，版本不够再找别的。"""
    if sys.version_info >= (3, 10):
        return sys.executable
    for cand in ("python3.14", "python3.13", "python3.12", "python3.11", "python3.10", "python"):
        found = shutil.which(cand)
        if found:
            return found
    raise SystemExit("找不到 Python ≥3.10，无法建 figkit 环境。先装 Python 再说。")


def install_figkit(cfg: dict, dry: bool) -> bool:
    say("\n---------- [figkit] Python 绘图环境 ----------")
    if os.path.isfile(cfg["figpy"]):
        say(f"已存在：{cfg['figpy']}（只同步依赖）")
        if not dry:
            run([cfg["figpy"], "-m", "pip", "install", "-q", "-r", REQUIREMENTS])
        return True

    base = pick_base_python()
    say(f"用 {base} 建 venv：{cfg['venv']}")
    if dry:
        return True
    os.makedirs(os.path.dirname(cfg["venv"]), exist_ok=True)
    run([base, "-m", "venv", cfg["venv"]])
    run([cfg["figpy"], "-m", "pip", "install", "-q", "--upgrade", "pip"])
    run([cfg["figpy"], "-m", "pip", "install", "-r", REQUIREMENTS])
    run([cfg["figpy"], "-c",
         "import matplotlib,cnsplots;print('figkit ok', matplotlib.__version__, cnsplots.__version__)"])
    return True


def find_existing_r() -> str | None:
    """找机器上已有的 Rscript —— 有就复用，绝不重复下载一套 R。"""
    env_path = os.environ.get("RSCRIPT")
    if env_path and os.path.isfile(env_path):
        return env_path
    rhome = os.environ.get("R_HOME")
    if rhome:
        for cand in (os.path.join(rhome, "bin", "Rscript.exe"),
                     os.path.join(rhome, "bin", "Rscript")):
            if os.path.isfile(cand):
                return cand
    found = shutil.which("Rscript")
    if found:
        return found
    import glob
    if IS_WIN:
        pats = [
            r"C:/Program Files/R/R-*/bin/Rscript.exe",
            r"C:/Program Files/R/R-*/bin/x64/Rscript.exe",
            os.path.expanduser(r"~/AppData/Local/Programs/R/R-*/bin/Rscript.exe"),
        ]
    else:
        pats = ["/opt/R/*/bin/Rscript",
                "/usr/local/lib/R/bin/Rscript",
                "/Library/Frameworks/R.framework/Resources/bin/Rscript"]
    hits = []
    for pat in pats:
        hits.extend(glob.glob(pat))
    return sorted(hits)[-1] if hits else None


def install_r(cfg: dict, dry: bool) -> bool:
    mode = cfg.get("r_mode", "install")
    say("\n---------- [R] ----------")
    if mode == "reuse":
        if not os.path.isfile(cfg["rscript"]):
            say(f"!! reuse 模式但找不到 {cfg['rscript']}")
            return False
        say(f"复用已有 R：{cfg['rscript']}（不下载、不安装第二套 R）")
        say(f"包只装到独立库：{cfg['r_lib']}（不写你原有的 library）")
    elif not IS_WIN:
        say("非 Windows：请用系统包管理器装 R（如 apt/brew），"
            "然后用 --r-mode reuse --r-path $(which Rscript) 复用它。")
        return False
    elif os.path.isfile(cfg["rscript"]):
        say(f"已存在：{cfg['rscript']}")
    else:
        exe = os.path.join(cfg["root"], "envs", "_R-installer.exe")
        say(f"下载 {R_URL}")
        if dry:
            return True
        os.makedirs(os.path.dirname(exe), exist_ok=True)
        urllib.request.urlretrieve(R_URL, exe)
        say(f"静默安装到 {cfg['r']}（无需管理员权限）")
        run([exe, "/VERYSILENT", f"/DIR={cfg['r']}", "/NORESTART", "/SUPPRESSMSGBOXES"], timeout=1800)
        os.remove(exe)

    if not os.path.isfile(cfg["rscript"]):
        say("!! 安装后仍找不到 Rscript.exe，跳过 R 包。")
        return False

    rcode = f'''
lib <- "{cfg['r_lib']}"
dir.create(lib, recursive = TRUE, showWarnings = FALSE)
.libPaths(c(lib, .libPaths()))     # 让 requireNamespace 也看得到独立库
repos <- c(CRAN = "https://cloud.r-project.org")
core <- c("dplyr","tidyr","stringr","purrr","tibble","forcats","magrittr",
          "rlang","data.table","reshape2","matrixStats",
          "ggplot2","scales","patchwork","cowplot","viridis","RColorBrewer",
          "ggrepel","ggh4x","ggbeeswarm","ggdist","ggalluvial","ggsignif",
          "ggplotify","scattermore","ggforce","ggpubr",
          "showtext","sysfonts","ragg","svglite","systemfonts",
          "ggsci","gggenomes","BiocManager","remotes","jsonlite")
install.packages(core, lib = lib, repos = repos, dependencies = NA, type = "binary")
install.packages(c("Seurat","SeuratObject","SCpubr"), lib = lib, repos = repos,
                 dependencies = NA, type = "binary")
BiocManager::install("ComplexHeatmap", lib = lib, ask = FALSE, update = FALSE)
missing <- core[!vapply(core, function(p) requireNamespace(p, lib.loc = lib, quietly = TRUE), logical(1))]
cat("缺失:", if (length(missing)) paste(missing, collapse = " ") else "无", "\\n")
'''
    fd, path = tempfile.mkstemp(suffix=".R", prefix="sci_fig_pkg_")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(rcode)
    try:
        if not dry:
            run([cfg["rscript"], path], timeout=5400)
    finally:
        os.remove(path)
    return True


def find_conda() -> str | None:
    env = os.environ.get("CONDA_EXE") or os.environ.get("CONDA")
    if env and os.path.isfile(env):
        return env
    found = shutil.which("conda")
    if found:
        return found
    for cand in (os.path.join(os.environ.get("SCI_FIG_ROOT") or "D:/app", "ana", "Scripts", "conda.exe"),
                 "C:/ProgramData/miniconda3/Scripts/conda.exe",
                 "C:/ProgramData/anaconda3/Scripts/conda.exe",
                 os.path.expanduser("~/miniconda3/Scripts/conda.exe"),
                 os.path.expanduser("~/anaconda3/Scripts/conda.exe")):
        if os.path.isfile(cand):
            return cand
    return None


def install_omicverse(cfg: dict, dry: bool) -> bool:
    say("\n---------- [omicverse] conda prefix ----------")
    conda = find_conda()
    if not conda:
        say("没找到 conda；跳过 omicverse。装了 Miniconda 后可用 --only omicverse 补。")
        return False
    say(f"conda: {conda}")
    if os.path.isfile(cfg["omvpy"]):
        say(f"已存在：{cfg['omvpy']}（只同步包）")
    else:
        if dry:
            return True
        os.makedirs(os.path.dirname(cfg["omv"]), exist_ok=True)
        run([conda, "create", "-y", "--prefix", cfg["omv"],
             "--override-channels", "-c", "conda-forge", "python=3.13", "pip"], timeout=3600)
    if not dry:
        run([cfg["omvpy"], "-m", "pip", "install", "-q", "--upgrade", "pip"])
        run([cfg["omvpy"], "-m", "pip", "install", "omicverse==2.3.2"], timeout=5400)
    return True


def write_config(cfg: dict) -> None:
    data = {
        "schema": 2,
        "conda_exe": find_conda() or "",
        "figkit_python": cfg["figpy"],
        "figkit_mode": "venv",
        "omicverse_python": cfg["omvpy"],
        "r_prefix": cfg["r"],
        "rscript": cfg["rscript"],
        "r_lib": cfg["r_lib"],
        "r_mode": cfg.get("r_mode", "install"),
        "r_needs_activation": False,
        "r_install": "official-cran" if cfg.get("r_mode") == "install" else "reused",
        "mods_vendor": cfg["vendor"],
        "fonts": {"cjk": "C:/Windows/Fonts/simhei.ttf", "cjk_family": "SimHei"},
    }
    for target in (os.path.join(cfg["root"], "envs", "envs.json"),
                   os.path.join(SKILL, "envs.json")):
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        say(f"写入配置：{target}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.environ.get("SCI_FIG_ROOT") or "D:/app",
                    help="安装根目录（默认 $SCI_FIG_ROOT 或 D:/app）")
    ap.add_argument("--only", choices=["figkit", "r", "omicverse"], default=None,
                    help="只装其中一套（可重复跑补齐）")
    ap.add_argument("--r-mode", choices=["auto", "reuse", "install"], default="auto",
                    help="auto=检测到已有 R 就复用；reuse=必须复用；install=总是装一套新的")
    ap.add_argument("--r-path", default=None, help="已有 R 的 Rscript 路径（配合 --r-mode reuse）")
    ap.add_argument("--dry-run", action="store_true", help="只打印将要做的事")
    args = ap.parse_args()

    cfg = layout(args.root)
    cfg["r_mode"] = "install"
    if args.r_mode in ("auto", "reuse"):
        found = args.r_path or find_existing_r()
        if found and os.path.isfile(found):
            cfg["rscript"] = found
            cfg["r"] = os.path.dirname(os.path.dirname(found))
            cfg["r_lib"] = os.path.join(args.root, "R", "library").replace("\\", "/")
            cfg["r_mode"] = "reuse"
        elif args.r_mode == "reuse":
            say("--r-mode reuse 但没找到 Rscript；用 --r-path 指定路径")
            return 2
        else:
            say("没检测到已有 R，将安装一套。若你其实已经装了 R，"
                "加 --r-mode reuse --r-path <Rscript 路径> 复用即可。")
    say("=" * 60)
    say(f"sci-figure-kit 安装  →  {cfg['root']}")
    say(f"skill: {SKILL}")
    say("=" * 60)
    if args.dry_run:
        say("（--dry-run：只打印，不动磁盘）")

    results = {}
    todo = [args.only] if args.only else ["figkit", "r", "omicverse"]
    for step in todo:
        try:
            if step == "figkit":
                results[step] = install_figkit(cfg, args.dry_run)
            elif step == "r":
                results[step] = install_r(cfg, args.dry_run)
            else:
                results[step] = install_omicverse(cfg, args.dry_run)
        except SystemExit as exc:
            say(f"✗ {step} 失败：{exc}")
            results[step] = False

    if not args.dry_run:
        write_config(cfg)
        say("\n---------- [体检] ----------")
        env = dict(os.environ, SCI_FIG_ENVS=os.path.join(cfg["root"], "envs", "envs.json"))
        subprocess.run([sys.executable, os.path.join(SCRIPTS, "check_envs.py")], env=env)

    say("\n结果：" + "、".join(f"{k}={'ok' if v else 'skip'}" for k, v in results.items()))
    say("缺的那套随时用 --only <figkit|r|omicverse> 补装。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
