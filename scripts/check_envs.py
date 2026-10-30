#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""sci-figure-kit 环境自检。

设计约束（刻意为之）：
  1. 本脚本只依赖 Python 标准库，用全局 Python 3.14 跑即可。
     它的职责是诊断"可能已经坏掉"的环境，所以它自己不能依赖被诊断对象。
     所有探测都通过 subprocess 驱动，绝不在本进程里 import matplotlib / omicverse。
  2. 关键探针不止测"能否 import"，还要测"能否真的写出图文件"——
     导入成功 != 能出图。R 的 DLL 缺失在 device-open 时才暴露，不在 library() 时。

配置解析顺序：$SCI_FIG_ENVS  ->  {root}/envs/envs.json  ->  本文件内置默认值。
第三层是关键：即使 json 被删掉，也能在这台机器上开箱工作。
"""

import importlib.util
import json
import os
import subprocess
import sys

# Windows GBK 控制台会把中文打成乱码
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("SCI_FIG_ROOT") or (
    "D:/app" if os.name == "nt" else os.path.expanduser("~/.sci-fig"))

try:
    import sources
except ImportError:                      # 按路径加载时 sys.path 里没有 scripts/
    sys.path.insert(0, HERE)
    import sources


def _load_mod():
    """import 兄弟脚本 mod.py，只为复用它的纯函数（目前是 png_dims）。

    这不破本脚本的既有纪律：**被诊断的对象绝不在本进程里 import**。mod.py
    自己也不 import matplotlib / omciverse，模块级只做常量与正则定义，所以
    借它一个函数是安全的。
    """
    p = os.path.join(HERE, "mod.py")
    spec = importlib.util.spec_from_file_location("sci_fig_mod", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


_MOD = _load_mod()
# 产物校验只有一份实现（在 mod.py）—— 不要在这里再写一遍，两份迟早会对
# 「什么算合法 PNG」产生不同意见。
png_dims = _MOD.png_dims

# ---------------------------------------------------------------- 默认配置

DEFAULTS = {
    "conda_exe": "{root}/ana/Scripts/conda.exe",
    "figkit_python": "{root}/envs/figkit/Scripts/python.exe",
    "figkit_mode": "venv",
    "omicverse_python": "{root}/envs/omicverse/python.exe",
    "r_prefix": "{root}/R",
    "rscript": "{root}/R/bin/Rscript.exe",
    "r_lib": "{root}/R/library",
    # 官方 CRAN 安装的 R，直调 Rscript.exe 即可，无需任何激活。
    # （曾经用 conda 装 R，那时必须走 conda run —— 见 references/envs.md）
    "r_needs_activation": False,
    # mod 的机器本地资产（与 envs.json 同级，不进分享 zip）
    "mods_vendor": "{root}/envs/_mods",
    "fonts": {"cjk": "C:/Windows/Fonts/simhei.ttf", "cjk_family": "SimHei"},
}

DEFAULTS = {k: (v.replace("{root}", ROOT) if isinstance(v, str) else v)
            for k, v in DEFAULTS.items()}

CONFIG_PATHS = [
    os.environ.get("SCI_FIG_ENVS"),
    # skill 自带的安装记录：换机器时跟着 skill 一起搬，优先级高于机器本地默认。
    # （installer 会同时写 <root>/envs/envs.json 与这里）
    os.path.join(os.path.dirname(HERE), "envs.json"),
    f"{ROOT}/envs/envs.json",
]

PROBE_DIR = os.environ.get("SCI_FIG_PROBE_DIR") or f"{ROOT}/envs/_probe"


def load_config():
    cfg = dict(DEFAULTS)
    src = "内置默认值"
    for p in CONFIG_PATHS:
        if p and os.path.isfile(p):
            try:
                with open(p, encoding="utf-8") as fh:
                    user = json.load(fh)
                cfg.update({k: v for k, v in user.items() if v is not None})
                src = p
            except Exception as exc:
                print(f"  !! 配置文件 {p} 解析失败：{exc}")
            break
    return cfg, src


def run(cmd, timeout=180, env_extra=None):
    """跑子进程，返回 (returncode, stdout+stderr)。绝不抛异常。"""
    env = dict(os.environ)
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    if env_extra:
        env.update(env_extra)
    try:
        p = subprocess.run(
            cmd, capture_output=True, timeout=timeout,
            encoding="utf-8", errors="replace", env=env,
        )
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        return -9, f"<超时 {timeout}s>"
    except FileNotFoundError as exc:
        return -2, f"<找不到可执行文件：{exc}>"
    except Exception as exc:
        return -1, f"<异常：{exc}>"


def first_line(text, n=110):
    for line in text.splitlines():
        line = line.strip()
        if line:
            return line[:n]
    return ""


# ---------------------------------------------------------------- 探针

def probe_conda(cfg):
    rc, out = run([cfg["conda_exe"], "--version"], timeout=120)
    if rc == 0:
        return True, f"{first_line(out)} @ {cfg['conda_exe']}", None
    return False, "conda 不可用", f"检查 {cfg['conda_exe']} 是否存在；conda 装在 {root}/ana"


def probe_figkit_import(cfg):
    py = cfg["figkit_python"]
    if not os.path.isfile(py):
        return False, f"不存在：{py}", "bash scripts/install_figkit.sh"
    code = (
        "import matplotlib,numpy,pandas,seaborn,scienceplots,cmcrameri,marsilea,cnsplots;"
        "import sys;"
        "print('py'+sys.version.split()[0],"
        "'mpl'+matplotlib.__version__,"
        "'np'+numpy.__version__,"
        "'cnsplots'+cnsplots.__version__)"
    )
    rc, out = run([py, "-c", code])
    if rc == 0:
        return True, first_line(out), None
    return False, first_line(out), f"{py} -m pip install -r requirements-figkit.txt"


def probe_figkit_render(cfg):
    """导入成功 != 能出图。这里真的画一张再读回 IHDR。"""
    py = cfg["figkit_python"]
    if not os.path.isfile(py):
        return False, "figkit 缺失，跳过", None
    os.makedirs(PROBE_DIR, exist_ok=True)
    png = os.path.join(PROBE_DIR, "figkit.png")
    code = (
        "import matplotlib;matplotlib.use('Agg');"
        "import matplotlib.pyplot as plt;"
        f"fig,ax=plt.subplots(figsize=(2,2));ax.plot([0,1],[0,1]);"
        f"fig.savefig(r'{png}',dpi=100);print('rendered')"
    )
    rc, out = run([py, "-c", code])
    if rc != 0:
        return False, first_line(out), "figkit 能导入但画不出图，检查 matplotlib 安装"
    dims = png_dims(png)
    if not dims or 0 in dims:
        return False, f"PNG 尺寸异常：{dims}", "渲染产物无效，重装 matplotlib"
    return True, f"PNG {dims[0]}x{dims[1]}", None


def _rscript(cfg, expr, timeout=240):
    """调用 R。

    官方 CRAN 安装的 R 直调 Rscript.exe 即可（工具链自洽，无需激活）。
    注意：-e 只用于单行表达式；多行 R 代码请写成 .R 文件后传文件名。
    """
    rs = cfg["rscript"]
    if cfg.get("r_needs_activation"):
        # 兼容仍使用 conda R 的机器
        cmd = [cfg["conda_exe"], "run", "--no-capture-output",
               "-p", cfg["r_prefix"], "Rscript.exe", "-e", expr]
    else:
        cmd = [rs, "-e", expr]
    # 复用用户的 R 时包在独立库里，必须显式告诉 R 去哪找
    return run(cmd, timeout=timeout, env_extra={"R_LIBS": cfg.get("r_lib", "")})


def probe_r_core(cfg):
    if not os.path.isdir(cfg["r_prefix"]):
        return False, f"不存在：{cfg['r_prefix']}", "bash scripts/install_r.sh"
    expr = (
        'suppressMessages({library(ggplot2);library(ggsci);library(gggenomes)});'
        'cat(as.character(getRversion()),'
        'as.character(packageVersion("ggplot2")),'
        'as.character(packageVersion("ggsci")),'
        'as.character(packageVersion("gggenomes")))'
    )
    rc, out = _rscript(cfg, expr)
    if rc == 0:
        return True, f"R {first_line(out)}", None
    return False, first_line(out), "bash scripts/install_r.sh"


def probe_r_compiled(cfg):
    """编译型包（ComplexHeatmap/Seurat/SCpubr）——DLL 缺失在这里才暴露。"""
    if not os.path.isdir(cfg["r_prefix"]):
        return False, "R 缺失，跳过", None
    expr = (
        'suppressMessages({library(ComplexHeatmap);library(Seurat);library(SCpubr)});'
        'cat(as.character(packageVersion("ComplexHeatmap")),'
        'as.character(packageVersion("Seurat")),'
        'as.character(packageVersion("SCpubr")))'
    )
    rc, out = _rscript(cfg, expr, timeout=420)
    if rc == 0:
        return True, f"ComplexHeatmap/Seurat/SCpubr {first_line(out)}", None
    return False, first_line(out), \
        "若报 Mingw-w64 runtime failure，说明 R 不是官方 CRAN 版；见 references/troubleshooting.md §1"


def probe_r_render_cjk(cfg):
    """R 能不能真的写出中文图——中文渲染是 R 侧最容易坏的一环。"""
    if not os.path.isdir(cfg["r_prefix"]):
        return False, "R 缺失，跳过", None
    os.makedirs(PROBE_DIR, exist_ok=True)
    png = os.path.join(PROBE_DIR, "r_cjk.png").replace("\\", "/")
    expr = (
        'suppressMessages({library(ggplot2);library(showtext)});'
        'showtext_auto();'
        'font_add("SimHei","C:/Windows/Fonts/simhei.ttf");'
        f'p<-ggplot(data.frame(x=1:3,y=1:3),aes(x,y))+geom_point()+'
        'labs(title="中文标题",x="处理组",y="表达量")+'
        'theme(text=element_text(family="SimHei"));'
        f'ggsave("{png}",p,width=89,height=60,units="mm",dpi=300);cat("ok")'
    )
    rc, out = _rscript(cfg, expr, timeout=420)
    if rc != 0:
        return False, first_line(out), "R 中文渲染失败，见 references/fonts.md"
    dims = png_dims(png)
    if not dims or 0 in dims:
        return False, f"PNG 尺寸异常：{dims}", "R 渲染产物无效"
    return True, f"中文 PNG {dims[0]}x{dims[1]}", None


def probe_r_lib_isolation(cfg):
    """确认独立库排在用户库前面 —— 否则同名包可能被用户那份抢先加载。

    复用用户的 R 时，用户库仍然在 .libPaths() 里（那是他自己的 R），
    只要我们的独立库排在它前面就没有遮蔽风险。
    """
    if not os.path.isfile(cfg["rscript"]):
        return None, "R 缺失，跳过", None
    rc, out = run([cfg["rscript"], "-e", "cat(.libPaths(), sep='|')"],
                  env_extra={"R_LIBS": cfg.get("r_lib", "")})
    if rc != 0:
        return None, first_line(out), None
    paths = [p.strip() for p in first_line(out, 400).split("|") if p.strip()]

    def norm(p):
        return p.replace("\\", "/").lower()

    lib = norm(cfg.get("r_lib", ""))
    idx = next((i for i, p in enumerate(paths) if lib and norm(p).startswith(lib)), None)
    risky = [
        p for i, p in enumerate(paths)
        if ("appdata" in norm(p) or "/win-library" in norm(p) or "/r/" in norm(p) + "/")
        and (idx is None or i < idx)
    ]
    if risky:
        return False, f"用户库排在独立库前面：{risky}", \
            f"设 R_LIBS={cfg['r_lib']}，或清空 R_LIBS_USER"
    first = paths[0] if paths else "?"
    return True, f"独立库优先（{first}）", None


def probe_omicverse(cfg):
    py = cfg["omicverse_python"]
    if not os.path.isfile(py):
        return False, f"不存在：{py}", "bash scripts/install_omicverse.sh"
    rc, out = run([py, "-c",
                   "import omicverse as ov;print(ov.__version__)"], timeout=300)
    if rc == 0:
        return True, f"omicverse {first_line(out)}", None
    return False, first_line(out), "bash scripts/install_omicverse.sh"


def probe_cjk_font(cfg):
    path = (cfg.get("fonts") or {}).get("cjk")
    if path and os.path.isfile(path):
        return True, path, None
    return False, f"缺字体：{path}", "改用存在的字体文件，见 references/fonts.md"


def probe_mpl_cap(cfg):
    """哨兵：matplotlib 升到 3.11 会直接弄坏 cnsplots（它要求 <3.11）。"""
    py = cfg["figkit_python"]
    if not os.path.isfile(py):
        return None, "figkit 缺失，跳过", None
    rc, out = run([py, "-c",
                   "import matplotlib;print(matplotlib.__version__)"])
    if rc != 0:
        return None, first_line(out), None
    ver = first_line(out)
    try:
        major, minor = (int(x) for x in ver.split(".")[:2])
    except Exception:
        return None, f"版本号无法解析：{ver}", None
    if (major, minor) >= (3, 11):
        return False, f"matplotlib {ver} 已越过 cnsplots 的 <3.11 上限", \
            f"{py} -m pip install 'matplotlib==3.10.8'"
    return True, f"matplotlib {ver} < 3.11", None


def probe_mods(cfg):
    """已装载 mod 的一致性。

    装了但坏掉的 mod 必须在这里暴露出来 —— 否则 AI 会在 Step 1 的路由表里
    选中它，然后在 Step 5 才炸。探针走 mod.py verify 的子进程，
    绝不在本进程 import 被诊断对象（和本文件其它探针同一条纪律）。
    """
    state_p = os.path.join(cfg.get("mods_vendor") or f"{ROOT}/envs/_mods",
                           "_state.json")
    if not os.path.isfile(state_p):
        return None, "没有已装载的 mod", None
    modpy = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mod.py")
    if not os.path.isfile(modpy):
        return None, "找不到 scripts/mod.py", None
    rc, out = run([sys.executable, modpy, "verify"], timeout=900)
    summary = ""
    for line in (out or "").splitlines():
        if line.startswith("RESULT:"):
            summary = line.strip()
    if rc == 0:
        return True, summary or "全部通过", None
    return False, summary or first_line(out), \
        "python scripts/mod.py verify  看是哪个 mod 坏了"


PROBES = [
    ("conda",           probe_conda,            True),
    ("figkit 导入",      probe_figkit_import,    True),
    ("figkit 渲染",      probe_figkit_render,    True),
    ("R 核心包",         probe_r_core,           True),
    ("R 编译包",         probe_r_compiled,       True),
    ("R 中文渲染",       probe_r_render_cjk,     True),
    ("R 库隔离",         probe_r_lib_isolation,  False),
    ("omicverse",       probe_omicverse,        True),
    ("中文字体",         probe_cjk_font,         True),
    ("matplotlib 上限",  probe_mpl_cap,          False),
    ("mods 一致性",      probe_mods,             False),
]


def discover(cfg):
    """探测真实路径并打印可粘贴的 JSON。"""
    found = dict(cfg)
    for c in (f"{ROOT}/R/bin/Rscript.exe", f"{ROOT}/R/bin/x64/Rscript.exe",
              f"{ROOT}/R/Lib/R/bin/Rscript.exe", f"{ROOT}/R/lib/R/bin/Rscript.exe"):
        if os.path.isfile(c):
            found["rscript"] = c
            break
    for c in (f"{ROOT}/R/library", f"{ROOT}/R/Lib/R/library", f"{ROOT}/R/lib/R/library"):
        if os.path.isdir(c):
            found["r_lib"] = c
            break
    for c in (f"{ROOT}/envs/figkit/Scripts/python.exe", f"{ROOT}/envs/figkit/python.exe"):
        if os.path.isfile(c):
            found["figkit_python"] = c
            found["figkit_mode"] = "venv" if "Scripts" in c else "conda"
            break
    print(json.dumps(found, indent=2, ensure_ascii=False))


def main():
    args = set(sys.argv[1:])
    cfg, src = load_config()

    if "--discover" in args:
        discover(cfg)
        return 0

    as_json = "--json" in args
    strict = "--strict" in args

    if not as_json:
        print("sci-figure-kit 环境自检")
        print("=" * 68)
        print(f"配置来源：{src}")
        print(sources.describe(sources.resolve(cfg)))
        print()

    results = []
    for i, (name, fn, core) in enumerate(PROBES, 1):
        try:
            ok, detail, fix = fn(cfg)
        except Exception as exc:
            ok, detail, fix = False, f"探针自身异常：{exc}", None
        results.append({"probe": name, "ok": ok, "core": core,
                        "detail": detail, "fix": fix})
        if not as_json:
            tag = "PASS" if ok else ("SKIP" if ok is None else "FAIL")
            print(f"[{i:2}/{len(PROBES)}] {name:<18} {tag:<4} {detail}")
            if fix and ok is not True:
                print(f"{'':<28}fix: {fix}")

    n_pass = sum(1 for r in results if r["ok"] is True)
    n_fail = sum(1 for r in results if r["ok"] is False)
    n_skip = sum(1 for r in results if r["ok"] is None)
    blocked = [r for r in results
               if r["ok"] is False and (r["core"] or strict)]

    if as_json:
        print(json.dumps({"results": results, "pass": n_pass,
                          "fail": n_fail, "skip": n_skip}, ensure_ascii=False, indent=2))
    else:
        print()
        print(f"RESULT: {n_pass} PASS / {n_fail} FAIL / {n_skip} SKIP")
        if blocked:
            print("未通过的核心项：" + ", ".join(r["probe"] for r in blocked))

    return 1 if blocked else 0


if __name__ == "__main__":
    sys.exit(main())
