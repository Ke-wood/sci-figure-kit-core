#!/usr/bin/env python
"""仓库卫生检查：公开仓库里不能出现作者本机路径、机器本地状态或废文件。

跑法：python scripts/check_repo_hygiene.py
CI 与本地提交前都应通过。

除了扫字符串，这里还有一条**行为**检查：把 SCI_FIG_ROOT 指到临时目录跑一遍
`bootstrap.py --dry-run`，输出里不许再出现别的根目录。字符串能骗过去，行为不能。
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEXT_EXT = {".md", ".py", ".sh", ".json", ".yml", ".yaml", ".txt", ".ps1", ".R"}
SKIP_DIRS = {"__pycache__", ".git", "node_modules", ".venv"}

# 作者本机路径 / 用户名
FORBIDDEN = [
    re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+[A-Za-z0-9_.-]+"),
    re.compile(r"/home/[A-Za-z0-9_.-]+/"),
    re.compile(r"/Users/[A-Za-z0-9_.-]+/"),
]

# 未替换的模板占位符：曾经四个 install_*.sh 里写着 {root}/envs/...，
# 照跑会在当前目录建出一个名叫 "{root}" 的目录。
# 只查 shell 脚本：.py 里的 {root} 是 DEFAULTS 的运行时模板（会 replace 掉），合法。
PLACEHOLDER = re.compile(r"\{root\}")
PLACEHOLDER_EXT = {".sh", ".ps1"}

# 不应存在的机器本地文件
MUST_NOT_EXIST = ["envs.json", "_state.json", "scripts/_probe", ".venv"]


def iter_files():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            yield os.path.join(dirpath, name)


def check_sources_module() -> list[str]:
    """下载源预设必须字段齐全、URL 合法；离线目录要能转成 file:// 仓库。"""
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    try:
        import sources
    except Exception as exc:  # noqa: BLE001
        return [f"scripts/sources.py 无法导入：{exc}"]

    out: list[str] = []
    need = ("label", "pip_index", "cran", "bioc", "conda_channels")
    for name, p in sources.PRESETS.items():
        for k in need:
            if k not in p:
                out.append(f"下载源 {name} 缺字段 {k}")
        for k in ("cran", "bioc"):
            u = p.get(k) or ""
            if not u.startswith(("https://", "http://", "file://")):
                out.append(f"下载源 {name} 的 {k} 不是合法 URL：{u!r}")
        if not p.get("conda_channels"):
            out.append(f"下载源 {name} 没有 conda 频道")
    url = sources.cran_file_url(tempfile.gettempdir())
    if not url.startswith("file:///"):
        out.append(f"离线目录转 file:// 失败：{url!r}")
    return out


def check_root_is_configurable() -> list[str]:
    """把 SCI_FIG_ROOT 指到临时目录跑 dry-run，输出里不许再出现别的根目录。"""
    probe = os.path.join(tempfile.gettempdir(), "sci_fig_hygiene_root")
    env = dict(os.environ, SCI_FIG_ROOT=probe)
    env.pop("SCI_FIG_ENVS", None)
    try:
        proc = subprocess.run(
            [sys.executable, os.path.join(ROOT, "install", "bootstrap.py"),
             "--dry-run", "--only", "figkit", "--source", "official"],
            capture_output=True, text=True, timeout=180, env=env)
    except Exception as exc:  # noqa: BLE001
        return [f"bootstrap.py --dry-run 跑不起来：{exc}"]

    out = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0:
        return [f"bootstrap.py --dry-run 退出码 {proc.returncode}：{out[-400:]}"]
    if probe.replace("\\", "/") not in out.replace("\\", "/"):
        return ["bootstrap.py 没有按 SCI_FIG_ROOT 布局安装路径（写死了根目录？）"]
    leaked = [ln.strip() for ln in out.splitlines() if "D:/app" in ln.replace("\\", "/")]
    if leaked:
        return ["bootstrap.py 输出里还有写死的 D:/app：" + leaked[0][:120]]
    return []


def main() -> int:
    problems: list[str] = []

    for rel in MUST_NOT_EXIST:
        if os.path.exists(os.path.join(ROOT, rel)):
            problems.append(f"不该发布的机器本地文件/目录：{rel}")

    for path in iter_files():
        rel = os.path.relpath(path, ROOT)
        ext = os.path.splitext(path)[1].lower()
        if ext not in TEXT_EXT:
            continue
        if rel.replace("\\", "/").endswith("scripts/check_mod_guard.py"):
            continue  # 该文件里的路径是安全测试的构造用例
        try:
            text = open(path, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for pat in FORBIDDEN:
            for m in pat.finditer(text):
                line = text[: m.start()].count("\n") + 1
                problems.append(f"{rel}:{line} 含本机路径 {m.group(0)!r}")
        if ext in PLACEHOLDER_EXT:
            for m in PLACEHOLDER.finditer(text):
                line = text[: m.start()].count("\n") + 1
                problems.append(f"{rel}:{line} 含未替换的占位符 {{root}}")

    mods_dir = os.path.join(ROOT, "mods")
    mod_count = 0
    for name in sorted(os.listdir(mods_dir)):
        d = os.path.join(mods_dir, name)
        if not os.path.isdir(d) or name.startswith("_"):
            continue
        mj = os.path.join(d, "mod.json")
        if not os.path.isfile(mj):
            continue
        mod_count += 1
        try:
            mod = json.load(open(mj, encoding="utf-8"))
        except Exception as exc:
            problems.append(f"mods/{name}/mod.json 不是合法 JSON：{exc}")
            continue
        for key in ("id", "type", "purpose", "routes"):
            if key not in mod:
                problems.append(f"mods/{name}/mod.json 缺字段 {key}")
        if not os.path.isfile(os.path.join(d, "docs.md")):
            problems.append(f"mods/{name}/ 缺 docs.md")

    routing = os.path.join(ROOT, "references", "routing-mods.md")
    if not os.path.isfile(routing):
        problems.append("缺 references/routing-mods.md（跑 scripts/mod.py routes 生成）")

    problems.extend(check_sources_module())
    problems.extend(check_root_is_configurable())

    if problems:
        print(f"FAIL：{len(problems)} 处问题")
        for p in problems[:40]:
            print("  - " + p)
        return 1
    print(f"OK：无本机路径，{mod_count} 个 mod 清单合法，未发现机器本地状态")
    return 0


if __name__ == "__main__":
    sys.exit(main())
