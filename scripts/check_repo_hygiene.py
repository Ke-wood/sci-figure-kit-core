#!/usr/bin/env python
"""仓库卫生检查：公开仓库里不能出现作者本机路径、机器本地状态或废文件。

跑法：python scripts/check_repo_hygiene.py
CI 与本地提交前都应通过。
"""
from __future__ import annotations

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEXT_EXT = {".md", ".py", ".sh", ".json", ".yml", ".yaml", ".txt", ".ps1", ".R"}
SKIP_DIRS = {"__pycache__", ".git", "node_modules", ".venv"}

# 作者本机路径 / 用户名
FORBIDDEN = [
    re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+[A-Za-z0-9_.-]+"),
    re.compile(r"/home/[A-Za-z0-9_.-]+/"),
    re.compile(r"/Users/[A-Za-z0-9_.-]+/"),
]

# 不应存在的机器本地文件
MUST_NOT_EXIST = ["envs.json", "_state.json", "scripts/_probe", ".venv"]


def iter_files():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            yield os.path.join(dirpath, name)


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

    if problems:
        print(f"FAIL：{len(problems)} 处问题")
        for p in problems[:40]:
            print("  - " + p)
        return 1
    print(f"OK：无本机路径，{mod_count} 个 mod 清单合法，未发现机器本地状态")
    return 0


if __name__ == "__main__":
    sys.exit(main())
