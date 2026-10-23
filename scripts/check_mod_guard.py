#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""sci-figure-kit mod 白名单回归测试。

为什么单独一个脚本：mod 系统的安全边界全在 mod.py 的 v_* 白名单上，
而白名单是最容易在后续改动里被无声放宽的东西。这个脚本把每条边界都
钉成一条用例，任何时候都能重跑确认它没被拆掉。

只依赖标准库，用全局 Python 跑：
    python scripts/check_mod_guard.py

退出码：0 全部符合预期 / 1 有用例不符
"""

import importlib.util
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))


def load_mod_module():
    p = os.path.join(HERE, "mod.py")
    spec = importlib.util.spec_from_file_location("sci_fig_mod", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


M = load_mod_module()


def _rel_r_py(x):
    """v_relpath 的扩展名闸门用例 —— 第二个参数走不了统一的单参调用。"""
    return M.v_relpath(x, (".R", ".py"))


# (校验函数, 值, 是否应被拒, 说明)
CASES = [
    # ---- id：会当作目录名，必须挡住路径穿越 ----
    (M.v_id, "../../Users/someone/.ssh",  True,  "id 路径穿越"),
    (M.v_id, "foo/../bar",              True,  "id 带分隔符"),
    (M.v_id, "C:/Windows",              True,  "id 是绝对路径"),
    (M.v_id, "GGPUBFIGS",               True,  "id 含大写"),
    (M.v_id, "-leading",                True,  "id 以 - 开头"),
    (M.v_id, "has space",               True,  "id 含空格"),
    (M.v_id, "ggpubfigs",               False, "id 正常"),
    (M.v_id, "sci-figure-snippets",     False, "id 正常（带连字符）"),

    # ---- spec：进 pip argv，挡住参数注入 ----
    (M.v_spec, "--target=C:/Windows",       True,  "spec 是 pip 选项"),
    (M.v_spec, "-e",                        True,  "spec 是 editable"),
    (M.v_spec, "-r",                        True,  "spec 是 -r"),
    (M.v_spec, "git+https://evil/x",        True,  "spec 含 git+（会挂住）"),
    (M.v_spec, "pkg @ https://evil/x",      True,  "spec 含 @ 直链"),
    (M.v_spec, "pkg; rm -rf /",             True,  "spec 含命令分隔符"),
    (M.v_spec, "pkg --index-url=http://e",  True,  "spec 夹带 pip 选项"),
    (M.v_spec, "pkg && whoami",             True,  "spec 含 shell 连接符"),
    (M.v_spec, "paperfig",                  False, "spec 正常"),
    (M.v_spec, "matplotlib==3.10.8",        False, "spec 正常（钉版）"),
    (M.v_spec, "seaborn>=0.13.2,<0.14",     False, "spec 正常（逗号范围）"),
    (M.v_spec, "omicverse[full]",           False, "spec 正常（extras）"),

    # ---- R 包名：会拼进 R 源码字符串 ----
    (M.v_rpkg, 'x"); system("calc"); ("',   True,  "R 包名逃逸字符串"),
    (M.v_rpkg, "pkg; system('x')",          True,  "R 包名含分号"),
    (M.v_rpkg, "pkg-name",                  True,  "R 包名含连字符（R 不允许）"),
    (M.v_rpkg, "ggpubfigs",                 False, "R 包名正常"),
    (M.v_rpkg, "ComplexHeatmap",            False, "R 包名正常（驼峰）"),

    # ---- ref：进 URL，也要挡住穿越 ----
    (M.v_ref, "v1.1.4",                     False, "ref 正常（tag）"),
    (M.v_ref, "main",                       False, "ref 正常（分支）"),
    (M.v_ref, "feature/x",                  False, "ref 正常（带斜杠分支）"),
    (M.v_ref, "abc123def",                  False, "ref 正常（SHA）"),
    (M.v_ref, 'x"); system("calc"); ("',    True,  "ref 逃逸字符串"),
    (M.v_ref, "../../../etc/passwd",        True,  "ref 路径穿越"),
    (M.v_ref, "a b",                        True,  "ref 含空格"),

    # ---- owner/repo：进 URL ----
    (M.v_gh_part, "JLSteenwyk",             False, "owner 正常"),
    (M.v_gh_part, "a b",                    True,  "owner 含空格"),
    (M.v_gh_part, "../../x",                True,  "owner 穿越"),

    # ---- 值拼进 R 双引号字面量 ----
    (M.r_lit, "D:/app/R/library",            False, "路径正常"),
    (M.r_lit, "D:\\app\\R\\library",        False, "反斜杠路径正常（会转正斜杠）"),
    (M.r_lit, 'x"; system("calc")',         True,  "路径含引号"),
    (M.r_lit, "x\ny",                       True,  "路径含换行"),

    # ---- 工作台项目名：既是目录名，也是 P3 的 URL / JSON 值 ----
    (M.v_project, "../../Users/someone/.ssh", True,  "项目名穿越"),
    (M.v_project, "..\\..\\Windows",        True,  "项目名反斜杠穿越"),
    (M.v_project, "a/b",                    True,  "项目名含分隔符"),
    (M.v_project, "C:/Windows",             True,  "项目名是绝对路径"),
    (M.v_project, "C:x",                    True,  "项目名含盘符"),
    (M.v_project, "//server/share",         True,  "项目名是 UNC"),
    (M.v_project, "..",                     True,  "项目名就是 .."),
    (M.v_project, ".",                      True,  "项目名就是 ."),
    (M.v_project, "",                       True,  "项目名为空"),
    (M.v_project, "_catalog",               True,  "项目名以 _ 开头（与哨兵撞名）"),
    (M.v_project, ".hidden",                True,  "项目名以 . 开头"),
    (M.v_project, "--yes",                  True,  "项目名以 - 开头（会被当 flag）"),
    (M.v_project, "a" * 65,                 True,  "项目名超长"),
    (M.v_project, "CON",                    True,  "项目名是保留设备名"),
    (M.v_project, "nul",                    True,  "项目名是保留设备名（小写）"),
    (M.v_project, "com1",                   True,  "项目名是保留设备名（COM1）"),
    (M.v_project, "lpt9",                   True,  "项目名是保留设备名（LPT9）"),
    (M.v_project, "a.",                     True,  "项目名以 . 结尾"),
    (M.v_project, "a..b",                   True,  "项目名含 .."),
    (M.v_project, "a b",                    True,  "项目名含空格"),
    (M.v_project, "火山图_panel",            False, "项目名正常（中文）"),
    (M.v_project, "fig-01",                 False, "项目名正常"),
    (M.v_project, "Nature.89mm",            False, "项目名正常（点与数字）"),

    # ---- 相对路径：会拼到 skill 树 / 项目目录下 ----
    (M.v_relpath, "templates/../mod.json",  True,  "relpath 穿越"),
    (M.v_relpath, "../mod.json",            True,  "relpath 开头穿越"),
    (M.v_relpath, "/etc/passwd",            True,  "relpath 是绝对路径"),
    (M.v_relpath, "C:/x.R",                 True,  "relpath 含盘符"),
    (M.v_relpath, "\\\\server\\share\\x.R", True,  "relpath 是 UNC"),
    (M.v_relpath, "templates\\x.R",         True,  "relpath 用反斜杠"),
    (M.v_relpath, "templates/a:b.R",        True,  "relpath 含非法字符"),
    (M.v_relpath, "templates/a?.R",         True,  "relpath 含通配符"),
    (M.v_relpath, "templates/",             True,  "relpath 末尾空段"),
    (M.v_relpath, "templates//x.R",         True,  "relpath 中间空段"),
    (M.v_relpath, "templates/CON.R",        True,  "relpath 含保留设备名"),
    (M.v_relpath, "templates/x.R.",         True,  "relpath 段以 . 结尾"),
    (M.v_relpath, " templates/x.R",         True,  "relpath 首部有空白"),
    (M.v_relpath, "",                       True,  "relpath 为空"),
    (M.v_relpath, "templates/theme-demo.R", False, "relpath 正常"),
    (M.v_relpath, "templates/sub/x.py",     False, "relpath 正常（子目录）"),

    # ---- 相对路径的扩展名闸门（模板只允许脚本与数据） ----
    (_rel_r_py, "templates/x.sh",           True,  "relpath 扩展名不在白名单"),
    (_rel_r_py, "templates/x.R",            False, "relpath 扩展名匹配（大写）"),
    (_rel_r_py, "templates/x.r",            False, "relpath 扩展名匹配（小写）"),
]


def main():
    print("sci-figure-kit mod 白名单回归测试")
    print("=" * 74)
    bad = []
    for fn, val, want_reject, desc in CASES:
        try:
            fn(val) if fn is not M.v_gh_part else fn(val, "owner")
            rejected, err = False, ""
        except M.VError as exc:
            rejected, err = True, str(exc)
        ok = rejected == want_reject
        if not ok:
            bad.append((desc, val, want_reject, rejected))
        tag = "ok  " if ok else "BAD "
        verdict = "拒绝" if rejected else "放行"
        shown = val if len(val) <= 30 else val[:27] + "..."
        print(f"{tag} {desc:<26} {shown!r:<34} -> {verdict}")

    print()
    n = len(CASES)
    if bad:
        print(f"{n - len(bad)}/{n} 通过 —— 以下 {len(bad)} 条不符预期：")
        for desc, val, want, got in bad:
            print(f"  · {desc}: {val!r} 期望 {'拒绝' if want else '放行'}，"
                  f"实际 {'拒绝' if got else '放行'}")
        print()
        print("RESULT: FAIL")
        return 1
    print(f"RESULT: {n}/{n} 全部符合预期（{sum(1 for c in CASES if c[2])} 条拒绝 / "
          f"{sum(1 for c in CASES if not c[2])} 条放行）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
