#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""下载源：pip / CRAN / Bioconductor / conda / R 安装器，全部由用户自己选。

为什么要有这一层
----------------
把一个写死的 URL 留在安装器里，等于把「今天能不能装上」交给运气。实测：CRAN 的
`bin/windows/base/` 只保留**最新一版**安装器，发布下一个版本后旧文件立刻 404
（`R-4.6.1-win.exe` 就已经 404 了，目录里只剩 4.6.2）。所以这里做两件事：

  1. **版本现查**：列目录取最大版本号，查不到才退回内置兜底值；
  2. **源可换**：官方 / 清华 TUNA / 中科大 USTC / 阿里云 / 本地离线目录，
     用一条命令或一个环境变量切换，不用改代码。

优先级（高 → 低）
----------------
    函数参数 > 环境变量 > envs.json 的 sources{} / source_preset > 预设 > 内置默认

写入 envs.json 的形态（installer 会自动写）：

    {"source_preset": "tuna",
     "sources": {"cran": "https://mirrors.tuna.tsinghua.edu.cn/CRAN"}}

环境变量：

    SCI_FIG_SOURCE           预设名：official | tuna | ustc | aliyun
    SCI_FIG_PIP_INDEX        pip 索引（留空 = 用 pip 自己的配置）
    SCI_FIG_CRAN             CRAN 镜像
    SCI_FIG_BIOC             Bioconductor 镜像根
    SCI_FIG_CONDA_CHANNELS   conda 频道，逗号或空格分隔
    SCI_FIG_OFFLINE_DIR      离线目录（内含 wheels/ 与 cran/）

本模块只依赖标准库：它在 venv 建起来之前就要能跑。
"""
from __future__ import annotations

import json
import os
import re
import urllib.request

# ---------------------------------------------------------------- 预设

# 所有 URL 都实测过（HTTP 200 / 文件存在）。阿里云没有 Bioconductor 镜像
# （实测 404），所以它的 bioc 指回官方，不假装有。
PRESETS = {
    "official": {
        "label": "官方源",
        "pip_index": None,               # None = 不传 --index-url，尊重你的 pip 配置
        "cran": "https://cloud.r-project.org",
        "bioc": "https://bioconductor.org",
        "conda_channels": ["conda-forge"],
    },
    "tuna": {
        "label": "清华 TUNA",
        "pip_index": "https://pypi.tuna.tsinghua.edu.cn/simple",
        "cran": "https://mirrors.tuna.tsinghua.edu.cn/CRAN",
        "bioc": "https://mirrors.tuna.tsinghua.edu.cn/bioconductor",
        "conda_channels": ["https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge"],
    },
    "ustc": {
        "label": "中科大 USTC",
        # 用 301 之后的最终地址，少一跳
        "pip_index": "https://mirrors.ustc.edu.cn/pypi/simple",
        "cran": "https://mirrors.ustc.edu.cn/CRAN",
        "bioc": "https://mirrors.ustc.edu.cn/bioc",
        "conda_channels": ["conda-forge"],
    },
    "aliyun": {
        "label": "阿里云",
        "pip_index": "https://mirrors.aliyun.com/pypi/simple",
        "cran": "https://mirrors.aliyun.com/CRAN",
        "bioc": "https://bioconductor.org",          # 阿里云无 Bioc 镜像（实测 404）
        "conda_channels": ["conda-forge"],
    },
}

DEFAULT_PRESET = "official"

# 兜底版本：只在「列目录」这一步失败时用。正常路径永远是现查出来的。
FALLBACK_R_VERSION = "4.6.2"

FIELD_ORDER = ("pip_index", "cran", "bioc", "conda_channels")

ENV_KEYS = {
    "pip_index": "SCI_FIG_PIP_INDEX",
    "cran": "SCI_FIG_CRAN",
    "bioc": "SCI_FIG_BIOC",
    "conda_channels": "SCI_FIG_CONDA_CHANNELS",
}

_FIELD_LABEL = {
    "pip_index": "pip",
    "cran": "CRAN",
    "bioc": "Bioconductor",
    "conda_channels": "conda",
}


# ---------------------------------------------------------------- 解析

def preset_names() -> list[str]:
    return list(PRESETS)


def resolve(cfg: dict | None = None, **over) -> dict:
    """算出本次要用的下载源。

    `over` 只接受 FIELD_ORDER 里的键，外加 source / offline_dir / r_version。
    """
    cfg = cfg or {}
    src: dict = {}

    explicit = over.get("source") or os.environ.get("SCI_FIG_SOURCE")
    preset = explicit or cfg.get("source_preset") or DEFAULT_PRESET
    if preset not in PRESETS:
        raise ValueError(
            f"未知下载源 {preset!r}；可选：{' / '.join(preset_names())}")

    src.update(PRESETS[DEFAULT_PRESET])      # 逐项兜底，避免预设缺键
    src.update(PRESETS[preset])
    src["preset"] = preset
    src["label"] = PRESETS[preset]["label"]

    # 显式点名预设时，**忽略** envs.json 里存的逐项值 —— 否则「切回 official」
    # 会被上次存下的镜像 URL 顶回去，看起来像 switch 没生效。
    if not explicit:
        user = cfg.get("sources") or {}
        for k in FIELD_ORDER:
            if user.get(k):
                src[k] = user[k]
    over.pop("source", None)

    for k, var in ENV_KEYS.items():
        v = os.environ.get(var)
        if v:
            src[k] = v

    offline_dir = (over.pop("offline_dir", None)
                   or os.environ.get("SCI_FIG_OFFLINE_DIR")
                   or cfg.get("offline_dir"))
    r_version = over.pop("r_version", None)

    for k in FIELD_ORDER:
        v = over.get(k)
        if v not in (None, "", []):
            src[k] = v

    if isinstance(src["conda_channels"], str):
        src["conda_channels"] = [c for c in re.split(r"[,;\s]+", src["conda_channels"]) if c]

    src["offline_dir"] = offline_dir or None
    src["r_version"] = r_version or None
    if src["offline_dir"]:
        src["cran"] = cran_file_url(src["offline_dir"])

    # 这些 URL 会被拼进 R 源码字符串（repos = c(CRAN = "...")），所以在这里
    # 就挡掉能闭合字符串或另起语句的字符；本地目录则归一成 file:// 仓库。
    for k in ("pip_index", "cran", "bioc"):
        v = src.get(k)
        if not v:
            continue
        if "://" not in v:
            v = cran_file_url(v)          # 传了个本地目录
        if any(c in v for c in ('"', "`", "\n", "\r", "\\")):
            raise ValueError(f"下载源 {k} 含非法字符：{v!r}")
        src[k] = v
    return src


def cran_file_url(path: str) -> str:
    """本地目录 → R 能用的 file:// 仓库地址（Windows 也要三个斜杠）。"""
    p = os.path.abspath(path).replace("\\", "/").rstrip("/")
    return "file:///" + p.lstrip("/")


# ---------------------------------------------------------------- 给各后端用

def pip_args(src: dict, upgrade: bool = False) -> list[str]:
    """pip 的通用参数。官方源时刻意**不传** --index-url：
    你机器上的 PIP_INDEX_URL / pip.ini 优先级应该高于我们的默认值。
    """
    args = ["--disable-pip-version-check", "--no-color", "--progress-bar", "off"]
    if upgrade:
        args.append("--upgrade")
    if src.get("offline_dir"):
        wheels = os.path.join(src["offline_dir"], "wheels")
        args += ["--no-index",
                 "--find-links", wheels if os.path.isdir(wheels) else src["offline_dir"]]
        return args
    idx = src.get("pip_index")
    if idx:
        args += ["--index-url", idx]
        if idx.startswith("http://"):
            host = re.sub(r"^https?://", "", idx).split("/")[0].split(":")[0]
            args += ["--trusted-host", host]
    return args


def cran_repos(src: dict) -> str:
    """R 源码片段：repos = c(CRAN = "...")"""
    url = (src.get("cran") or PRESETS["official"]["cran"]).rstrip("/")
    return f'c(CRAN = "{url}")'


def bioc_options(src: dict) -> str:
    """R 源码片段：把 BiocManager 指向镜像。"""
    url = (src.get("bioc") or PRESETS["official"]["bioc"]).rstrip("/")
    return f'options(BioC_mirror = "{url}")'


def conda_channel_args(src: dict) -> list[str]:
    chans = src.get("conda_channels") or ["conda-forge"]
    out = ["--override-channels"]
    for c in chans:
        out += ["-c", c]
    return out


# ---------------------------------------------------------------- R 安装器

def _fetch(url: str, timeout: float = 15.0) -> bytes:
    req = urllib.request.Request(
        url, headers={"User-Agent": "sci-figure-kit/installer"})
    with urllib.request.urlopen(req, timeout=timeout) as fh:
        return fh.read()


def _exists(url: str, timeout: float = 10.0) -> bool:
    """文件真的能下吗。有些镜像只认 GET（HEAD 405），所以两种都试。"""
    attempts = (("HEAD", {}), ("GET", {"Range": "bytes=0-0"}))
    for method, extra in attempts:
        headers = {"User-Agent": "sci-figure-kit/installer", **extra}
        try:
            req = urllib.request.Request(url, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=timeout) as fh:
                if 200 <= fh.status < 400:
                    return True
        except Exception:
            continue
    return False


def r_version_candidates(cran: str, timeout: float = 15.0) -> list[str]:
    """候选版本，新 → 旧。

    只信目录会发现不了镜像的两种毛病：
      * CRAN 只留最新一版，写死的旧版本 404；
      * 镜像的目录页可能是过期索引（阿里云的页面还写着 4.6.1，实际文件已是 4.6.2），
        直接取「目录里的最大值」会挑到一个 404。
    所以这里把「目录里出现过的」和「内置兜底版」合起来，逐个去 HEAD 验真。
    """
    url = cran.rstrip("/") + "/bin/windows/base/"
    seen: set[str] = set()
    try:
        html = _fetch(url, timeout).decode("utf-8", "replace")
        seen.update(re.findall(r"R-(\d+\.\d+\.\d+)-win\.exe", html))
    except Exception:
        pass
    seen.add(FALLBACK_R_VERSION)
    return sorted(seen, key=lambda v: tuple(int(x) for x in v.split(".")), reverse=True)


def latest_r_version(cran: str, timeout: float = 15.0) -> str:
    """列表里最新的一个（不验真，仅用于展示）。"""
    return r_version_candidates(cran, timeout)[0]


def r_installer_url(src: dict, timeout: float = 15.0) -> tuple[str, str]:
    """返回 (安装器 URL, 版本号)，且这个 URL **已经验过能下**，不会装到一半 404。"""
    cran = (src.get("cran") or PRESETS["official"]["cran"]).rstrip("/")
    base = f"{cran}/bin/windows/base"

    pinned = src.get("r_version")
    if pinned:
        return f"{base}/R-{pinned}-win.exe", pinned

    cands = r_version_candidates(cran, timeout)
    for ver in cands:
        url = f"{base}/R-{ver}-win.exe"
        if _exists(url, timeout):
            return url, ver
    # 全都不通：把最可能的那个交出去，让下载错误如实暴露
    return f"{base}/R-{cands[0]}-win.exe", cands[0]


def download(url: str, dest: str, tries: int = 3, timeout: float = 900.0) -> None:
    """带重试的下载。安装器 250 MB，一次网络抖动重来整包太亏。"""
    last: Exception | None = None
    for i in range(1, tries + 1):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "sci-figure-kit/installer"})
            with urllib.request.urlopen(req, timeout=timeout) as src, \
                    open(dest, "wb") as dst:
                while True:
                    chunk = src.read(1 << 20)
                    if not chunk:
                        break
                    dst.write(chunk)
            return
        except Exception as exc:      # noqa: BLE001
            last = exc
            if i < tries:
                print(f"  下载失败（第 {i} 次）：{exc}；重试…", flush=True)
    raise SystemExit(f"下载失败：{url}（{last}）")


# ---------------------------------------------------------------- 展示与落盘

def describe(src: dict) -> str:
    out = [f"下载源：{src.get('label', '')}（{src.get('preset', '')}）"]
    for k in FIELD_ORDER:
        v = src.get(k)
        if k == "pip_index" and not v:
            v = "pip 默认（尊重 PIP_INDEX_URL / pip.ini）"
        if k == "conda_channels":
            v = ", ".join(v or [])
        out.append(f"  {_FIELD_LABEL[k]:<12} {v}")
    if src.get("offline_dir"):
        out.append(f"  {'离线目录':<10} {src['offline_dir']}（pip 用 wheels/，CRAN 用 cran/）")
    if src.get("r_version"):
        out.append(f"  {'R 版本':<10} {src['r_version']}（指定）")
    return "\n".join(out)


def to_config(src: dict) -> dict:
    """给 envs.json 的那两块：source_preset + sources{}。

    只记**与预设不同的**项。全量记录会在切换预设时把上一次的镜像写回去，
    于是 `--source official` 看起来没生效。
    """
    preset = src.get("preset", DEFAULT_PRESET)
    base = dict(PRESETS[DEFAULT_PRESET])
    base.update(PRESETS.get(preset, {}))
    plain = {k: src[k] for k in FIELD_ORDER
             if src.get(k) not in (None, "", []) and src[k] != base.get(k)}
    if src.get("offline_dir"):
        plain["offline_dir"] = src["offline_dir"]
    out = {"source_preset": preset}
    if plain:
        out["sources"] = plain
    return out


def load_json(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def main(argv: list[str] | None = None) -> int:
    """命令行入口：python scripts/sources.py [预设名]"""
    import sys
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in ("-h", "--help"):
        print(__doc__)
        print("预设：" + " / ".join(f"{k}（{v['label']}）" for k, v in PRESETS.items()))
        return 0
    src = resolve(source=argv[0] if argv else None)
    print(describe(src))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
