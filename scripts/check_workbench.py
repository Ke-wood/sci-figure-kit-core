#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""sci-figure-kit 绘图工作台回归测试（W1–W8、W11–W14、W16–W23）。

为什么单独一个脚本：工作台的闸门（尺寸必须等于声明宽度×300/25.4、字面量
U+2212、缺字启发式、矢量外框与字体）与偏离追踪（源文件永不写、diverged 由
哈希推导）都是**很容易在后续改动里被无声放宽**的东西。这个脚本把每条都钉成
一条用例 —— 尤其是矢量那两条：Type 3 字体与路径化的 SVG 都「看起来完全正常」，
不主动去查就永远不会发现。

全部在 `D:/app/envs/_wb_check` 里跑，**不碰 skill 树、不碰用户项目**。
跑完自动清理（`--keep` 可保留现场）。

只依赖标准库，用全局 Python 跑：
    python scripts/check_workbench.py [--keep]

退出码：0 全部通过 / 1 有失败
"""

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
WB = os.path.join(HERE, "workbench.py")
ROOT = "D:/app/envs/_wb_check"
SRC = os.path.join(ROOT, "_src")


def _load_workbench():
    spec = importlib.util.spec_from_file_location("sci_fig_wb", WB)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


W = _load_workbench()

# 这个字符不能以字面量出现在本文件里被渲染的脚本中；用转义写，读起来也更明确
U2212 = "−"

# 单栏 89mm、双栏 183mm，都是 Nature 的栏宽（references/fonts.md）
PX_89 = int(89 * 300 / 25.4)      # 1051
PX_183 = int(183 * 300 / 25.4)    # 2161
PX_60 = int(60 * 300 / 25.4)      # 708


def wb(*args, cwd=None):
    """跑 workbench.py，返回 (rc, stdout+stderr)。"""
    env = dict(os.environ)
    env["FIGWORK_ROOT"] = ROOT
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    p = subprocess.run([sys.executable, WB, *args], capture_output=True,
                       timeout=900, encoding="utf-8", errors="replace",
                       env=env, cwd=cwd)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def render_json(name):
    rc, out = wb("render", name, "--json")
    try:
        return rc, json.loads(out)
    except Exception:
        return rc, {"_raw": out}


def gate(data, probe):
    """从 --json 信封里取某一条闸门。"""
    for r in data.get("results", []):
        if r["probe"] == probe:
            return r
    return None


def sha(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


# ---------------------------------------------------------------- 准备

def setup():
    if os.path.isdir(ROOT):
        shutil.rmtree(ROOT, ignore_errors=True)
    os.makedirs(SRC, exist_ok=True)

    with open(os.path.join(SRC, "bar.csv"), "w", encoding="utf-8", newline="") as f:
        f.write("group,value\n")
        for g, base in (("对照组", 1.0), ("处理组", 2.3), ("恢复组", 1.5)):
            for i in range(8):
                f.write(f"{g},{base + i * 0.09:.3f}\n")
    with open(os.path.join(SRC, "scatter.csv"), "w", encoding="utf-8", newline="") as f:
        f.write("x,y,group\n")
        for g, k in (("甲组", 1.7), ("乙组", 0.8)):
            for i in range(14):
                f.write(f"{i * 0.5:.2f},{k * i * 0.5 + 1.0:.3f},{g}\n")
    # GBK 源：Windows 上中文 CSV 的常态，按 utf-8 读会静默乱码
    with open(os.path.join(SRC, "bar_gbk.csv"), "w", encoding="gbk", newline="") as f:
        f.write("group,value\n对照组,1.0\n处理组,2.3\n")


def write_script(project, text):
    """覆写项目**当前那个**绘图脚本。

    必须读 project.json 拿脚本名，不能写死 plot.R —— 从模板建的项目里，
    脚本叫模板的文件名（theme-demo.R 等），写 plot.R 会造出一个渲染器根本
    不会去读的文件，用例于是「通过」得毫无意义。
    """
    pd = os.path.join(ROOT, "projects", project)
    prj = json.load(open(os.path.join(pd, "project.json"), encoding="utf-8"))
    p = os.path.join(pd, prj.get("script") or "plot.R")
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return p


# ---------------------------------------------------------------- 用例

def main():
    keep = "--keep" in sys.argv
    setup()
    cases = []

    def add(name, fn):
        try:
            ok, detail = fn()
        except Exception as exc:
            ok, detail = False, f"用例自身抛异常：{type(exc).__name__}: {exc}"
        cases.append((name, ok, detail))

    # ---- W1/W3：自带数据的模板能在空项目里出图，且尺寸精确 ----
    def w1():
        rc, _ = wb("new", "demo", "--from", "ggpubfigs:templates/theme-demo.R")
        if rc != 0:
            return False, "建项目失败"
        rc, d = render_json("demo")
        if rc != 0:
            return False, f"渲染非 0 退出：{d.get('_raw', '')[:200]}"
        g = gate(d, "尺寸")
        if not g or g["ok"] is not True:
            return False, f"尺寸闸门：{g}"
        return True, f"空项目渲染成功，尺寸 {PX_89}×{PX_60}（{g['detail'][:60]}）"
    add("W1/W3 自带数据模板 + 89mm 尺寸", w1)

    # ---- W3b：双栏 183mm ----
    def w3b():
        rc, _ = wb("new", "scat", "--data", os.path.join(SRC, "scatter.csv"),
                   "--from", "sci-figure:templates/scatter-groups.py")
        if rc != 0:
            return False, "建项目失败"
        rc, d = render_json("scat")
        g = gate(d, "尺寸")
        if rc != 0 or not g or g["ok"] is not True:
            return False, f"双栏尺寸闸门：{g}"
        png = os.path.join(ROOT, "projects", "scat", "out.png")
        return True, f"183mm → {g['detail'][:44]}"
    add("W3b 双栏 183mm 尺寸", w3b)

    # ---- W2：R 元字符不炸（证明走临时 .R 文件，没用 -e）----
    def w2():
        rc, _ = wb("new", "meta", "--from", "ggpubfigs:templates/theme-demo.R")
        if rc != 0:
            return False, "建项目失败"
        p = os.path.join(ROOT, "projects", "meta", "theme-demo.R")
        with open(p, encoding="utf-8") as fh:
            code = fh.read()
        # | 与 < 都是 Windows Rscript 在 -e 路径下会被 shell 吃掉的元字符
        code += '\ncat("meta | < > & ok\\n")\n'
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(code)
        rc, d = render_json("meta")
        g = gate(d, "执行")
        if rc != 0 or not g or g["ok"] is not True:
            return False, f"含 | 与 < 的 R 脚本失败：{g}"
        log = open(os.path.join(ROOT, "projects", "meta", "render.log"),
                   encoding="utf-8").read()
        if "meta | < > & ok" not in log:
            return False, "脚本跑了但 cat 的输出没进日志"
        return True, "含 | < > & 的 R 表达式正常执行（未走 -e）"
    add("W2 R 元字符不炸", w2)

    # ---- W5：字面量 U+2212 在渲染前被拒，且不产出图 ----
    def w5():
        rc, _ = wb("new", "u2212", "--from", "ggpubfigs:templates/theme-demo.R")
        if rc != 0:
            return False, "建项目失败"
        png = os.path.join(ROOT, "projects", "u2212", "out.png")
        if os.path.isfile(png):
            os.remove(png)
        write_script("u2212",
                     'library(ggplot2)\n'
                     f'p <- ggplot(data.frame(x=1,y=1), aes(x,y)) + geom_point() +'
                     f' labs(x="{U2212}log10(p)")\n'
                     'ggsave("out.png", p, width=89, height=60, units="mm", dpi=300)\n')
        rc, d = render_json("u2212")
        g = gate(d, "U+2212")
        if rc == 0 or not g or g["ok"] is not False:
            return False, f"应拒绝却放行：{g}"
        if os.path.isfile(png):
            return False, "拒绝之后仍然产出了 PNG"
        return True, "渲染前拒绝，且未产出图"
    add("W5 字面量 U+2212 拒绝", w5)

    # ---- W4：有中文却没设字体 -> 缺字闸门 FAIL ----
    def w4():
        rc, _ = wb("new", "cjk", "--from", "ggpubfigs:templates/theme-demo.R")
        if rc != 0:
            return False, "建项目失败"
        write_script("cjk",
                     'library(ggplot2)\n'
                     'df <- data.frame(x=1:5, y=1:5)\n'
                     'p <- ggplot(df, aes(x,y)) + geom_point() +'
                     ' labs(x="中文轴标签", y="量")\n'
                     'ggsave("out.png", p, width=89, height=60, units="mm", dpi=300)\n')
        rc, d = render_json("cjk")
        g = gate(d, "缺字")
        if not g or g["ok"] is not False:
            return False, f"应报缺字却没有：{g}"
        if "fonts.md" not in (g.get("fix") or ""):
            return False, "fix 没有指向 fonts.md"
        return True, "有中文未设字体 -> FAIL，fix 指向 fonts.md"
    add("W4 缺字启发式", w4)

    # ---- W6/W7：偏离可审计，且源文件全程不被写 ----
    state = {}

    def w6():
        rc, _ = wb("new", "edit", "--data", os.path.join(SRC, "bar.csv"),
                   "--from", "sci-figure:templates/bar-with-points.py")
        if rc != 0:
            return False, "建项目失败"
        pd = os.path.join(ROOT, "projects", "edit")
        src = os.path.join(pd, "data.csv")
        state["src_sha"] = sha(src)
        state["src_mtime"] = os.path.getmtime(src)

        rc, out = wb("edit", "edit", "--row", "0", "--col", "value", "--value", "9.99")
        if rc != 0:
            return False, f"改单元格失败：{out[:200]}"
        prj = json.load(open(os.path.join(pd, "project.json"), encoding="utf-8"))
        d = prj["data"]
        if not d.get("diverged"):
            return False, "diverged 应为 true"
        if not d.get("working") or not os.path.isfile(os.path.join(pd, d["working"])):
            return False, "工作副本没有落盘"
        jl = os.path.join(pd, "data.edits.jsonl")
        if not os.path.isfile(jl) or len(open(jl, encoding="utf-8").readlines()) != 1:
            return False, "data.edits.jsonl 应恰好 1 行"
        return True, f"diverged=true，工作副本已建，审计 1 行"
    add("W6 偏离可审计", w6)

    def w7():
        pd = os.path.join(ROOT, "projects", "edit")
        src = os.path.join(pd, "data.csv")
        if sha(src) != state.get("src_sha"):
            return False, "源文件内容被改了"
        if os.path.getmtime(src) != state.get("src_mtime"):
            return False, "源文件 mtime 变了"
        rc, d = render_json("edit")
        g = gate(d, "数据")
        if not g or "工作副本" not in g["detail"]:
            return False, f"渲染应记录用的是工作副本：{g}"
        prj = json.load(open(os.path.join(pd, "project.json"), encoding="utf-8"))
        if not prj["last_render"].get("diverged_at_render"):
            return False, "last_render 未记录 diverged_at_render"
        return True, "源文件 sha 与 mtime 全程未变；渲染记录了用的是工作副本"
    add("W7 源文件不被写", w7)

    # ---- W6b：revert 回到源副本 ----
    def w6b():
        rc, _ = wb("revert", "edit")
        if rc != 0:
            return False, "revert 失败"
        pd = os.path.join(ROOT, "projects", "edit")
        prj = json.load(open(os.path.join(pd, "project.json"), encoding="utf-8"))
        if prj["data"].get("diverged"):
            return False, "revert 后 diverged 应为 false"
        if os.path.isfile(os.path.join(pd, "data.working.csv")):
            return False, "工作副本文件应被删除"
        if sha(os.path.join(pd, "data.csv")) != state.get("src_sha"):
            return False, "revert 动了源文件"
        return True, "revert 后 diverged=false，工作副本已删，源文件未动"
    add("W6b revert 回到源副本", w6b)

    # ---- W8：GBK 源往返不掉编码 ----
    def w8():
        rc, _ = wb("new", "gbk", "--data", os.path.join(SRC, "bar_gbk.csv"))
        if rc != 0:
            return False, "建项目失败"
        pd = os.path.join(ROOT, "projects", "gbk")
        prj = json.load(open(os.path.join(pd, "project.json"), encoding="utf-8"))
        enc = prj["data"].get("encoding", "")
        if "gb" not in enc.lower():
            return False, f"编码没认出来：{enc!r}"
        rc, out = wb("edit", "gbk", "--row", "0", "--col", "value", "--value", "7.7")
        if rc != 0:
            return False, f"改单元格失败：{out[:200]}"
        # 用 GBK 重读工作副本：若写成 utf-8，这里会抛解码错误或出乱码
        raw = open(os.path.join(pd, "data.working.csv"), "rb").read()
        try:
            text = raw.decode("gbk")
        except UnicodeDecodeError:
            return False, "改完之后工作副本不再是 GBK"
        if "对照组" not in text:
            return False, "GBK 重读后中文丢失"
        return True, f"encoding={enc}，改完仍以 GBK 写回且中文完好"
    add("W8 编码往返", w8)

    # ---- W13/W14：报告匿名，且不覆盖用户成果 ----
    def w13():
        pd = os.path.join(ROOT, "projects", "scat")
        rc, out = wb("report", "scat", "--anon", "--no-open")
        if rc != 0:
            return False, f"报告失败：{out[:200]}"
        dest = os.path.join(pd, f"报告_scat.html")
        if not os.path.isfile(dest):
            return False, f"报告不在预期位置：{dest}"
        text = open(dest, encoding="utf-8").read()
        if ROOT.replace("/", "\\") in text or ROOT in text:
            return False, "匿名的报告里仍然出现工作台本地路径"
        has_png = "data:image/png;base64," in text
        has_svg = "data:image/svg+xml;base64," in text
        if not (has_png or has_svg):
            return False, "报告没把图内嵌进去"
        # 项目里有 out.svg 时，报告**必须**优先用它：矢量在浏览器里缩放不糊、
        # 打印也锐利。用 <img> 装 SVG 而不是内联进 DOM —— 前者不执行脚本。
        if os.path.isfile(os.path.join(pd, "out.svg")) and not has_svg:
            return False, "有 out.svg 却没用它（报告应当优先矢量）"
        if "<svg" in text and "data:image/svg+xml" not in text:
            return False, "SVG 被内联进了 DOM（会执行脚本），应当走 <img> data URI"
        if "散点" not in text and "scatter-groups.py" not in text:
            return False, "报告里没有脚本内容"
        return True, ("报告自包含、图已内嵌"
                      + ("（矢量 SVG）" if has_svg else "（位图 PNG）")
                      + "、无本地路径")
    add("W13 报告匿名且自包含", w13)

    def w14():
        pd = os.path.join(ROOT, "projects", "scat")
        before = {f: os.path.getmtime(os.path.join(pd, f))
                  for f in os.listdir(pd) if f.endswith(".png")}
        rc, _ = wb("report", "scat", "--no-open")
        after = {f: os.path.getmtime(os.path.join(pd, f))
                 for f in os.listdir(pd) if f.endswith(".png")}
        if before != after:
            return False, "生成报告动了已有的图"
        return True, "报告没有改动任何已有的产物文件"
    add("W14 报告不覆盖成果", w14)

    # ---- W11/W12：模板随 mod 落盘，且不覆盖用户改过的 ----
    def w11():
        pkg = os.path.join(ROOT, "_fixture", "src")
        dest = os.path.join(ROOT, "_fixture", "mods", "fakemod")
        tdir = os.path.join(pkg, "templates")
        os.makedirs(tdir, exist_ok=True)
        with open(os.path.join(tdir, "a.R"), "w", encoding="utf-8") as f:
            f.write("# upstream v1\n")

        mj = {"templates": ["templates/a.R", "templates/absent.R"]}
        # ① 首次落盘：有源的拷进来，没源的记进 missing（多半是手写模板）
        copied, kept, missing = W.mod.install_templates(mj, None, "fakemod", pkg, {},
                                                        dest_root=dest)
        if copied != ["templates/a.R"] or kept or missing != ["templates/absent.R"]:
            return False, f"首装结果不对：copied={copied} kept={kept} missing={missing}"
        dst = os.path.join(dest, "templates", "a.R")
        if not os.path.isfile(dst):
            return False, "模板没有落到 mods/<id>/templates/ 下"
        rec = {"templates/a.R": sha(dst)}

        # ② 用户改了它，随后上游也更新 —— 必须保留用户的，不覆盖
        with open(dst, "w", encoding="utf-8") as f:
            f.write("# 用户改过的\n")
        with open(os.path.join(tdir, "a.R"), "w", encoding="utf-8") as f:
            f.write("# upstream v2\n")
        copied, kept, _ = W.mod.install_templates(mj, None, "fakemod", pkg, rec,
                                                  dest_root=dest)
        if kept != ["templates/a.R"] or copied:
            return False, f"应保留用户改过的：copied={copied} kept={kept}"
        if "用户改过" not in open(dst, encoding="utf-8").read():
            return False, "用户改过的模板被覆盖了"

        # ③ 用户没动过、上游更新了 —— 应当跟着更新。
        #    判据是「磁盘哈希 == 记录哈希」：把磁盘还原成上次写下去的那份，
        #    再带着记录重装，才是在考「没动过」这个情形。
        with open(dst, "w", encoding="utf-8") as f:
            f.write("# upstream v1\n")
        copied, kept, _ = W.mod.install_templates(mj, None, "fakemod", pkg, rec,
                                                  dest_root=dest)
        if "upstream v2" not in open(dst, encoding="utf-8").read():
            return False, "用户没动过时，上游更新应当能落下来"

        # ④ 没有记录、磁盘上却已存在 —— 视为手写模板，绝不覆盖。
        #    这正是「zip 里手写的 templates/」的情形，不能被上游顺手冲掉。
        with open(dst, "w", encoding="utf-8") as f:
            f.write("# 手写的\n")
        copied, kept, _ = W.mod.install_templates(mj, None, "fakemod", pkg, {},
                                                  dest_root=dest)
        if kept != ["templates/a.R"] or "手写" not in open(dst, encoding="utf-8").read():
            return False, "没有记录时应当按手写模板保留，不被上游覆盖"
        return True, "首装落实、用户改过的保住、没动过的跟随上游、手写的永不被覆盖"
    add("W11/W12 模板随 mod 落盘", w11)

    # ---- W16：期刊尺寸与色板取值不得与 fonts.md 漂移 ----
    def w16():
        p = os.path.join(SKILL_DIR, "references", "fonts.md")
        if not os.path.isfile(p):
            return False, "references/fonts.md 不见了"
        text = open(p, encoding="utf-8").read()
        widths = {int(m) for m in re.findall(r"(\d+)\s*mm", text)}
        miss = sorted(set(W.JOURNAL_WIDTHS_MM) - widths)
        if miss:
            return False, f"fonts.md 里找不到这些栏宽：{miss}"
        low = text.lower()
        miss_hex = [h for h in W.OKABE_ITO if h.lower() not in low]
        if miss_hex:
            return False, f"fonts.md 里找不到这些 Okabe-Ito 色值：{miss_hex}"
        if len(W.OKABE_ITO) != 8 or len(set(W.OKABE_ITO)) != 8:
            return False, "Okabe-Ito 基线应当是 8 个互不相同的色值"
        return True, (f"{len(W.JOURNAL_WIDTHS_MM)} 个栏宽 + {len(W.OKABE_ITO)} 个 "
                      f"Okabe-Ito 色值都与 fonts.md 对得上")
    add("W16 预设不漂移", w16)

    # ---- W17：没有数据的项目（脚本自带示例数据）也要能出报告 ----
    # 这条是补的：W13 当初只在一个**有数据**的项目上试过报告，于是漏掉了
    # 「project.json 里 data 是 None」这条路径 —— 而 .get("data", {}) 的默认值
    # 对「键存在、值是 None」是不生效的，实测就炸在 None.get 上。
    def w17():
        rc, out = wb("report", "demo", "--no-open")
        if rc != 0:
            return False, f"无数据项目报告失败：{out[-300:]}"
        pd = os.path.join(ROOT, "projects", "demo")
        dest = os.path.join(pd, "报告_demo.html")
        if not os.path.isfile(dest):
            return False, "报告没生成"
        t = open(dest, encoding="utf-8").read()
        if "自带示例数据" not in t:
            return False, "报告没有说明数据来自脚本自带"
        if ("data:image/png;base64," not in t
                and "data:image/svg+xml;base64," not in t):
            return False, "报告没内嵌图"
        return True, "无数据项目也能出报告，并说明了数据来源"
    add("W17 无数据项目的报告", w17)

    # ---- W18：模板自带矢量产物，且两道矢量闸门都过 ----
    def w18():
        rc, d = render_json("demo")
        if rc != 0:
            return False, f"渲染失败：{str(d.get('_raw', ''))[:200]}"
        pd = os.path.join(ROOT, "projects", "demo")
        missing = [f for f in ("out.pdf", "out.svg")
                   if not os.path.isfile(os.path.join(pd, f))]
        if missing:
            return False, f"模板没有产出 {'、'.join(missing)}"
        for probe in ("矢量.pdf尺寸", "矢量.pdf字体", "矢量.svg尺寸", "矢量.svg字体"):
            g = gate(d, probe)
            if not g or g["ok"] is not True:
                return False, f"{probe} 未通过：{g}"
        return True, "PDF/SVG 的外框、字体嵌入、文字可编辑四条闸门全过"
    add("W18 矢量产物与两道闸门", w18)

    def vec_project(name, key, tail):
        """极简项目：只画一条线，用来单独考矢量闸门。
        key=None 表示不写 vector= 那一行。"""
        rc, _ = wb("new", name, "--data", os.path.join(SRC, "bar.csv"),
                   "--from", "sci-figure:templates/bar-with-points.py")
        if rc != 0:
            return 2, {"_raw": "建项目失败"}
        fm = ("# figwork: data=data.csv\n# figwork: size=nature1\n"
              + (f"# figwork: vector={key}\n" if key else ""))
        write_script(name, fm +
                     "import matplotlib\n"
                     "matplotlib.use('Agg')\n"
                     "import matplotlib.pyplot as plt\n"
                     "fig, ax = plt.subplots(figsize=(89/25.4, 60/25.4))\n"
                     "ax.plot([1, 2, 3], [1, 4, 9])\n"
                     "ax.set_xlabel('x')\n"
                     "fig.savefig('out.png', dpi=300)\n" + tail)
        return render_json(name)

    # ---- W19：matplotlib 的默认 pdf.fonttype=3 -> Type 3，必须判 FAIL ----
    # 这是最阴的一条：产物看起来完全正常，投稿时才被作者指南打回。
    def w19():
        rc, d = vec_project("v_type3", "pdf", "fig.savefig('out.pdf')\n")
        g = gate(d, "矢量.pdf字体")
        if not g or g["ok"] is not False:
            return False, f"Type 3 的 PDF 应当判 FAIL：{g}"
        if "Type 3" not in g["detail"]:
            return False, f"detail 没点出 Type 3：{g['detail']}"
        return True, "默认 pdf.fonttype=3 的产物被判 Type 3 字体"
    add("W19 Type3 PDF 判失败", w19)

    # ---- W20：matplotlib 的默认 svg.fonttype='path' -> 文字全变路径，判 FAIL ----
    def w20():
        rc, d = vec_project("v_pathsvg", "svg", "fig.savefig('out.svg')\n")
        g = gate(d, "矢量.svg字体")
        if not g or g["ok"] is not False:
            return False, f"纯路径 SVG 应当判 FAIL：{g}"
        if "路径" not in g["detail"]:
            return False, f"detail 没点出「转成了路径」：{g['detail']}"
        return True, "默认 svg.fonttype='path' 的产物被判不可编辑"
    add("W20 路径化 SVG 判失败", w20)

    # ---- W21：声明了 vector=svg 却没存 SVG -> FAIL（声明与产物必须一致）----
    def w21():
        rc, d = vec_project("v_missing", "pdf,svg", "fig.savefig('out.pdf')\n")
        g = gate(d, "矢量.svg")
        if not g or g["ok"] is not False:
            return False, f"声明了 svg 却没产出，应当 FAIL：{g}"
        return True, "声明 vector=svg 却没存 SVG -> FAIL"
    add("W21 声明未产出判失败", w21)

    # ---- W22：没声明 vector 时只给非核心提醒，不判失败 ----
    def w22():
        rc, d = vec_project("v_none", None, "")
        g = gate(d, "矢量")
        if not g or g["ok"] is not None or g["core"] is not False:
            return False, f"未声明 vector 时应给非核心提醒：{g}"
        return True, "未声明 vector= 时只提醒不失败（脚本没存矢量，工作台无从查验）"
    add("W22 未声明只提醒", w22)

    # ---- W23：手工改过的矢量文件，在下次渲染覆盖它之前被识别出来 ----
    # 矢量是唯一「你会拿去手工编辑」的产物，也是唯一会被渲染静默盖掉成果的地方。
    def w23():
        rc, _ = wb("new", "v_touch", "--from", "ggpubfigs:templates/theme-demo.R")
        if rc != 0:
            return False, "建项目失败"
        rc, _ = render_json("v_touch")
        if rc != 0:
            return False, "首次渲染失败"
        pdf = os.path.join(ROOT, "projects", "v_touch", "out.pdf")
        with open(pdf, "ab") as f:          # 模拟在 Illustrator 里改了一笔
            f.write(b"\n% touched\n")
        rc, d = render_json("v_touch")
        g = gate(d, "手工改动")
        if not g:
            return False, "手改过的矢量没有被识别出来"
        if "out.pdf" not in g["detail"]:
            return False, f"没点名是哪个文件：{g['detail']}"
        return True, "重渲染前识别出手改过的 out.pdf 并告警"
    add("W23 手工改动被发现", w23)

    # ---- 收尾
    n = len(cases)
    print("sci-figure-kit 绘图工作台回归测试")
    print("=" * 74)
    bad = 0
    for i, (name, ok, detail) in enumerate(cases, 1):
        tag = "PASS" if ok else "FAIL"
        if not ok:
            bad += 1
        print(f"[{i:2}/{n}] {name:<30} {tag:<4} {detail}")
    print()
    if not keep:
        shutil.rmtree(ROOT, ignore_errors=True)
    else:
        print(f"（--keep：现场留在 {ROOT}）")
    print(f"RESULT: {n - bad}/{n} 通过" + ("" if bad == 0 else f" —— {bad} 条失败"))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
