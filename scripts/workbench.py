#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""sci-figure-kit 绘图工作台 —— 无界面渲染核心。

**它做什么**：把一个「项目目录」渲染成图，并在出图那一刻把 `fonts.md` 里的投稿
硬约束变成闸门 —— 尺寸必须等于声明宽度×300/25.4、缺字、字面量 U+2212。

**闸门查的到底是什么**：查的是「声明与产物是否一致」，不是「你有没有违反 Nature
的规定」。最真实的失败模式是：你把 front-matter 改成双栏，却忘了改 `ggsave()` 的
width，于是图和自己的声明对不上。宽度不在期刊常用值上只给提醒，不给失败。

**它是给谁用的**：给 AI 用（headless），也给 P2 的静态报告与 P3 的界面用。
**界面永不在 AI 的关键路径上** —— AI 的循环仍然是「写脚本 → 跑 → 读 PNG 头」。

**为什么不并进 mod.py**：mod.py 的姿态是「加载器绝不执行第三方代码」，而这里
执行的是**用户自己写的**代码。两个域，保持边界。这里只 import mod.py 的纯函数
（配置、子进程、校验器、png_dims）。

项目 = 一个目录，文件即状态（无数据库、无服务端会话）：

    data.csv           源数据的不变副本（new 时拷入，之后**永不写**）
    data.working.csv   可编辑工作副本（首次编辑才产生）
    plot.R / plot.py   绘图脚本（模板落下来的起点，之后随便改）
    out.png            产物（预览 + 尺寸闸门的依据）
    out.pdf / out.svg  矢量产物（脚本自己存；投稿要 PDF、进 PPT 要 SVG）
    render.log         脚本的合并输出
    project.json       项目状态与溯源
    data.edits.jsonl   编辑审计（append-only，可 grep，崩溃安全）

退出码：0 成功 / 1 失败 / 2 用法或前置缺失 / 3 需要确认
"""

import base64
import csv
import html
import importlib.util
import io
import json
import os
import re
import sys
import zlib

# 注意 import codecs 刻意不用：编码往返靠 str 的 encode/decode 就够，
# 多一层 codecs 只会让 utf-8-sig 的 BOM 处理多一个出错的地方。

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)


def _load_mod():
    """import 兄弟脚本 mod.py，只为复用它的纯函数。"""
    p = os.path.join(HERE, "mod.py")
    spec = importlib.util.spec_from_file_location("sci_fig_mod", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


mod = _load_mod()
VError = mod.VError

# ---------------------------------------------------------------- 常量

# 期刊印刷宽度（mm）—— 与 references/fonts.md 的硬约束表一一对应。
# 这里硬编码一份，另有一个单测用正则回读 fonts.md 核对，防两处漂移。
JOURNAL_PRESETS = {
    "nature1":  {"label": "Nature 单栏",  "w": 89,  "h": 60},
    "nature2":  {"label": "Nature 双栏",  "w": 183, "h": 60},
    "science1": {"label": "Science 单栏", "w": 55,  "h": 60},
    "science2": {"label": "Science 双栏", "w": 175, "h": 60},
    "cell1":    {"label": "Cell 单栏",    "w": 85,  "h": 60},
    "cell2":    {"label": "Cell 双栏",    "w": 178, "h": 60},
}
JOURNAL_WIDTHS_MM = (89, 183, 55, 175, 85, 178)

DEFAULT_DPI = 300
DEFAULT_PRESET = "nature1"
DEFAULT_OUT = "out.png"

# 矢量产物。两个格式各为一个真实去处：**投稿要 PDF**（字体嵌入，跨机器不掉字），
# **进 PPT 要 SVG**（PowerPoint 2016+ 直接插、可缩放不失真）。
VECTOR_EXTS = (".pdf", ".svg")
PT_PER_MM = 72.0 / 25.4
# 外框容差（pt）。cairo_pdf 把页面尺寸取整到整 pt —— 实测 89mm 出 252.0 而非
# 252.2835（差 0.28pt ≈ 0.1mm），matplotlib 则是精确值。1pt 既放得过取整，
# 又抓得住「改成双栏却忘了改 ggsave」那种几百 pt 的偏差。
VEC_TOL_PT = 1.0

# 色盲安全分类色板基线（Okabe-Ito）。fonts.md 里也有一份，同样有单测核对。
OKABE_ITO = ("#E69F00", "#56B4E9", "#009E73", "#F0E442",
             "#0072B2", "#D55E00", "#CC79A7", "#999999")

U2212 = "−"          # 真减号 —— SimHei 没有这个字形，图里绝不能出现

PROJECT_SCHEMA = 1
SCRIPT_EXTS = (".R", ".r", ".py")

# 允许的源数据扩展名
DATA_EXTS = (".csv", ".tsv", ".txt")


def mm_px(mm, dpi=DEFAULT_DPI):
    """毫米 -> 像素。**截断而非四舍五入**：matplotlib 就是这么算的，
    89mm@300dpi 实测 1051、60mm 实测 708（round 会给出 709）。"""
    return int(mm * dpi / 25.4)


# ---------------------------------------------------------------- 矢量产物读取
# 全是纯 stdlib 的字节扫描 —— 不引入任何 PDF/SVG 库。三个后端写出来的东西
# 各有怪癖，下面每一条都是实测出来的，不是照 RFC 抄的：
#   · cairo_pdf 会把页面对象塞进**压缩的对象流**，明文里搜不到 MediaBox，
#     得先把流 zlib 解压再找（不这么做就只能读 matplotlib 的 PDF）。
#   · SVG 的引号两种都有：matplotlib 写 width="252.283465pt"，
#     svglite 写 width='252.28pt'。只认一种就会漏掉一半的 SVG。

RE_PDF_BOX = re.compile(
    rb"/MediaBox\s*\[\s*(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s*\]")
RE_SVG_TAG = re.compile(rb"<svg[^>]*>", re.S | re.I)


def _box_of(m):
    x0, y0, x1, y1 = (float(g) for g in m.groups())
    return x1 - x0, y1 - y0


def pdf_box(path):
    """PDF 的 (宽, 高)，单位 pt。读不到返回 None。"""
    try:
        with open(path, "rb") as f:
            b = f.read()
    except OSError:
        return None
    m = RE_PDF_BOX.search(b)
    if m:
        return _box_of(m)
    for sm in re.finditer(rb"stream\r?\n", b):
        s = sm.end()
        e = b.find(b"endstream", s)
        if e < 0:
            continue
        try:
            d = zlib.decompress(b[s:e])
        except Exception:          # 不是 zlib 流（图片、字体）就跳过
            continue
        m = RE_PDF_BOX.search(d)
        if m:
            return _box_of(m)
    return None


def svg_size(path):
    """SVG 根元素的 (宽, 高)，单位 pt。读不到返回 None。"""
    try:
        with open(path, "rb") as f:
            b = f.read(4096)       # 根标签就在开头，没必要读整个文件
    except OSError:
        return None
    tag = RE_SVG_TAG.search(b)
    if not tag:
        return None
    t = tag.group(0)

    def attr(name):
        m = re.search(rb"\b%s\s*=\s*[\"']\s*([\d.]+)\s*(pt|px|mm)?\s*[\"']" % name,
                      t, re.I)
        if not m:
            return None
        v = float(m.group(1))
        u = m.group(2)
        if u == b"mm":
            return v * PT_PER_MM
        if u == b"px":
            return v * 72.0 / 96.0         # CSS px
        return v                            # pt 或缺单位

    w, h = attr(b"width"), attr(b"height")
    return None if (w is None or h is None) else (w, h)


def vector_box(path):
    return pdf_box(path) if path.lower().endswith(".pdf") else svg_size(path)


def vector_font_verdict(path):
    """矢量文件里的文字「能不能改、换台机器会不会掉字」。

    返回 (ok, is_problem, detail, fix)；ok 为 None 表示只给提醒不判失败。
    判据全是实测出来的：
      · PDF 含 /Type3 —— matplotlib 的默认（pdf.fonttype=3）。Type 3 是
        位图式字形，**Nature/Elsevier 的作者指南明令拒收**，且必然不嵌字体。
      · PDF 无 /FontFile —— 字体没嵌进去，换台没装该字体的机器就掉字。
        6 个中文字体里任何一个换机器都会出问题。
      · SVG 里 <text> 数为 0 —— matplotlib 的默认（svg.fonttype='path'）把
        **所有文字转成路径**，Illustrator/Inkscape 里一个字都改不了。
    """
    try:
        with open(path, "rb") as f:
            b = f.read()
    except OSError:
        return None, False, "读不到文件", None

    if path.lower().endswith(".pdf"):
        if b"/Type3" in b:
            return False, True, "含 Type 3 字体（期刊普遍拒收，且文字不可编辑）", \
                "matplotlib 在 savefig 前设 rcParams['pdf.fonttype'] = 42；" \
                "R 出 PDF 用 ggsave(..., device = cairo_pdf)，别用默认的 pdf() 设备"
        # 一个字体资源都没有 = 文字早被转成了路径（showtext 就干这个）。
        # 注意这**不等于**「掉字」：路径在任何机器上都长得一样，它只是改不了。
        # 先判 /Font 再判 /FontFile —— 后者是前者的子串，顺序反了会漏掉这一支。
        if b"/Font" not in b:
            return False, True, "文字已转成路径（换机器不会掉字，但改不了）", \
                "R 侧通常是 showtext 干的 —— 它把字形画成多边形，矢量里就不再是文字。" \
                "实测 cairo_pdf + family='SimHei' 不靠 showtext 也能出中文，" \
                "存矢量前 showtext_auto(FALSE) 即可"
        if b"/FontFile" not in b:
            return False, True, "有字体但没嵌入，换台机器会掉字", \
                "R 的默认 pdf() 设备不嵌字体、中文还会 mbcsToSbcs 失败 —— " \
                "改用 device = cairo_pdf；matplotlib 设 pdf.fonttype = 42"
        return True, False, "字体已嵌入，无 Type 3", None

    n_text = b.count(b"<text")
    if n_text:
        # 文字是真 <text>，可编辑。但**字体是按名字引用的，没有嵌入** ——
        # 换台没装 SimHei 的机器，中文会回退成别的字体。这是 SVG 的固有取舍。
        return True, False, f"{n_text} 个 <text>（文字可编辑；字体按名字引用未嵌入）", None
    return False, True, "没有 <text>，文字全被转成了路径，改不了", \
        "matplotlib 在 savefig 前设 rcParams['svg.fonttype'] = 'none'"


# ---------------------------------------------------------------- 小工具

def sha256(path_or_bytes):
    return mod.sha256_file(path_or_bytes)


def now_stamp():
    return mod.now_stamp()


def read_text(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def write_text(path, text):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    os.replace(tmp, path)


def write_json(path, obj):
    write_text(path, json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def read_json(path, default=None):
    if not os.path.isfile(path):
        return default
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return default


# ---------------------------------------------------------------- 编码与分隔符

def sniff_bytes(path):
    """读一个数据文件，返回 (文本, 编码名, 是否带 BOM, 换行符)。

    Windows 上的中文 CSV 通常是 GBK，直接按 utf-8 读会**静默**乱码 ——
    不报错，只是列名和内容全变成问号/怪字，然后整条链路都跟着错。
    所以先试 utf-8（含 BOM 变体），最后才退 gb18030。
    """
    with open(path, "rb") as fh:
        raw = fh.read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    for enc in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = raw.decode("utf-8", errors="replace")
        enc = "utf-8(replace)"
    newline = "\r\n" if b"\r\n" in raw else "\n"
    return text, enc, bom, newline


def sniff_delim(text):
    """数第一行里各候选分隔符的个数，取最多的。不用 csv.Sniffer：它对
    中文表头与单列文件经常猜错，而猜错的后果是整张表变成一个字段。"""
    line = next((l for l in text.splitlines() if l.strip()), "")
    counts = {",": line.count(","), "\t": line.count("\t"), ";": line.count(";")}
    best = max(counts, key=lambda k: counts[k])
    return best if counts[best] > 0 else ","


def read_table(path):
    """读成 (表头, 行列表, 元信息)。元信息进 project.json，供报告与审计用。"""
    text, enc, bom, newline = sniff_bytes(path)
    delim = sniff_delim(text)
    rows = list(csv.reader(io.StringIO(text), delimiter=delim))
    rows = [r for r in rows if any(c.strip() for c in r)]
    if not rows:
        raise VError(f"数据文件是空的：{path}")
    header, body = rows[0], rows[1:]
    width = len(header)
    body = [(r + [""] * width)[:width] for r in body]     # 补齐/截齐参差行
    return header, body, {"encoding": enc, "bom": bom, "delimiter": delim,
                          "newline": newline}


def _write_enc(meta):
    """写回的编码名。带 BOM 的走 utf-8-sig —— **由 codec 自己写 BOM**，
    绝不手工前置，否则会写出两个 BOM。"""
    enc = meta.get("encoding", "utf-8")
    if enc.endswith("(replace)"):
        enc = "utf-8"
    if meta.get("bom") and enc in ("utf-8", "utf-8-sig"):
        return "utf-8-sig"
    return enc


def write_table(path, header, body, meta):
    """按读进来的编码与换行写回 —— 往返不改变用户在 Excel 里看到的样子。"""
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=meta.get("delimiter", ","),
                   lineterminator=meta.get("newline", "\n"))
    w.writerow(header)
    w.writerows(body)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding=_write_enc(meta), newline="") as fh:
        fh.write(buf.getvalue())
    os.replace(tmp, path)


# ---------------------------------------------------------------- 模板 front-matter

# `# figwork: key=value` —— 注释前缀允许 # / // / ; / -- 四种，好让 R、Python、
# SQL 风格的模板都能用同一套契约。**所有键都可选**：第三方模板（例如 ggpubfigs
# 声明的 templates/theme-demo.R）不会有 front-matter，缺省必须能跑。
RE_FRONTMATTER = re.compile(r"^\s*(?:#|//|;|--)+\s*figwork\s*:\s*([A-Za-z_]+)\s*=\s*(.+?)\s*$")

FM_KEYS = ("name", "data", "backend", "env", "size", "width", "height",
           "dpi", "out", "cjk", "u2212", "vector")


def parse_frontmatter(text):
    """读脚本头部若干个 `figwork:` 键。返回 dict（可能为空）。"""
    fm = {}
    for line in text.splitlines()[:60]:
        m = RE_FRONTMATTER.match(line)
        if m:
            fm[m.group(1).lower()] = m.group(2)
    return fm


def resolve_spec(fm, project_dir):
    """把 front-matter 解析成规范渲染参数。每一项都有缺省值。"""
    preset = (fm.get("size") or "").strip().lower()
    w = h = None
    if preset in JOURNAL_PRESETS:
        w, h = JOURNAL_PRESETS[preset]["w"], JOURNAL_PRESETS[preset]["h"]
    elif re.match(r"^\d+\s*x\s*\d+\s*mm?$", preset):
        a, b = re.split(r"x", preset.replace("mm", "").strip())
        w, h = int(a.strip()), int(b.strip())
    if fm.get("width"):
        w = int(re.sub(r"[^\d]", "", fm["width"]) or 0) or w
    if fm.get("height"):
        h = int(re.sub(r"[^\d]", "", fm["height"]) or 0) or h
    if w is None:
        w, h = JOURNAL_PRESETS[DEFAULT_PRESET]["w"], JOURNAL_PRESETS[DEFAULT_PRESET]["h"]

    dpi = int(re.sub(r"[^\d]", "", fm.get("dpi") or "") or DEFAULT_DPI)

    # vector=pdf,svg / vector=on（=两个都要）/ 不写（=不管）。
    # **不写就不查**：脚本没存矢量文件的工作台也无从查验，硬要求等于凭空失败。
    vec_raw = (fm.get("vector") or "").strip().lower()
    if vec_raw in ("", "off", "no", "none", "0"):
        vector, vector_bad = (), ()
    else:
        if vec_raw in ("on", "yes", "all", "1"):
            vec_raw = "pdf,svg"
        want = tuple(e if e.startswith(".") else "." + e
                     for e in re.split(r"[,\s]+", vec_raw) if e)
        vector = tuple(e for e in want if e in VECTOR_EXTS)
        vector_bad = tuple(e for e in want if e not in VECTOR_EXTS)

    return {
        "preset": preset if preset in JOURNAL_PRESETS else None,
        "width_mm": w, "height_mm": h, "dpi": dpi,
        "out": (fm.get("out") or DEFAULT_OUT).strip(),
        "name": (fm.get("name") or "").strip(),
        "env": (fm.get("env") or "").strip() or None,
        "cjk_check": (fm.get("cjk") or "").strip().lower() not in ("off", "no", "0"),
        "u2212_allow": (fm.get("u2212") or "").strip().lower() in ("allow", "off", "1"),
        "data": (fm.get("data") or "").strip() or None,
        "vector": vector, "vector_bad": vector_bad,
    }


# ---------------------------------------------------------------- 项目

def wb_root(cfg, override=None):
    default_root = os.environ.get("SCI_FIG_ROOT") or (
        "D:/app" if os.name == "nt" else os.path.expanduser("~/.sci-fig"))
    root = (override or os.environ.get("FIGWORK_ROOT")
            or cfg.get("workbench_root") or f"{default_root}/workbench")
    root = os.path.abspath(root).replace("\\", "/")
    # 工作台是机器本地资产，绝不写进 skill 树 —— 那会脏了分享档
    if os.path.abspath(root).lower().startswith(os.path.abspath(SKILL_DIR).lower()):
        raise VError(f"工作台根目录不得落在 skill 树里：{root}")
    return root


def project_dir(cfg, name, override=None):
    return os.path.join(wb_root(cfg, override), "projects", mod.v_project(name))


def load_project(pdir):
    p = os.path.join(pdir, "project.json")
    prj = read_json(p)
    if not prj:
        raise VError(f"不是工作台项目（没有 project.json）：{pdir}")
    return prj


def resolve_project(cfg, name, override=None):
    """name 可以是项目名，也可以是一个已有的项目目录路径。"""
    if os.path.isdir(name) and os.path.isfile(os.path.join(name, "project.json")):
        return os.path.abspath(name)
    return project_dir(cfg, name, override)


def find_script(pdir, script=None):
    if script:
        return os.path.join(pdir, mod.v_relpath(script, SCRIPT_EXTS))
    for cand in ("plot.R", "plot.r", "plot.py"):
        p = os.path.join(pdir, cand)
        if os.path.isfile(p):
            return p
    return None


def active_data(pdir, prj):
    """当前生效的数据文件：改过就是工作副本，没改过就是源副本。"""
    d = prj.get("data") or {}
    w = d.get("working")
    if w and os.path.isfile(os.path.join(pdir, w)):
        return os.path.join(pdir, w), True
    return os.path.join(pdir, d.get("source") or "data.csv"), False


def new_project(cfg, name, data_src=None, from_spec=None, preset=None, root=None):
    """建项目：拷一份源数据进来（**原始文件从此不再被碰**），可选落一个模板。"""
    pdir = project_dir(cfg, name, root)
    if os.path.isdir(pdir) and os.path.isfile(os.path.join(pdir, "project.json")):
        raise VError(f"项目已存在：{pdir}")
    os.makedirs(pdir, exist_ok=True)

    from_info = None
    script = None
    if from_spec:
        script, from_info = _place_template(from_spec, pdir)

    data_meta, src_name = None, None
    if data_src:
        if not os.path.isfile(data_src):
            raise VError(f"数据文件不存在：{data_src}")
        ext = os.path.splitext(data_src)[1].lower()
        if ext not in DATA_EXTS:
            raise VError(f"数据文件扩展名须是 {DATA_EXTS} 之一：{data_src}")
        src_name = "data" + ext
        header, body, data_meta = read_table(data_src)
        write_table(os.path.join(pdir, src_name), header, body,
                    dict(data_meta, newline="\n"))
    elif not from_info:
        raise VError("建项目至少要给 --data <csv> 或 --from <mod>:<template>")

    prj = {
        "schema": PROJECT_SCHEMA,
        "name": name,
        "created": now_stamp(),
        "from": from_info,
        "script": os.path.basename(script) if script else None,
        "preset": preset or DEFAULT_PRESET,
        "data": None,
        "last_render": None,
    }
    if src_name:
        header, body, meta = read_table(os.path.join(pdir, src_name))
        prj["data"] = {
            "source": src_name,
            "source_origin": os.path.abspath(data_src),
            "source_sha256": sha256(os.path.join(pdir, src_name)),
            "working": None,
            "working_sha256": None,
            "diverged": False,
            "rows": len(body), "cols": len(header), "header": header,
            "encoding": meta["encoding"], "delimiter": meta["delimiter"],
            "bom": meta["bom"], "newline": meta["newline"],
            "edits": 0,
        }
    write_json(os.path.join(pdir, "project.json"), prj)
    return pdir, prj


def _place_template(from_spec, pdir):
    """`<mod>:<相对路径>` / `<mod>` / 直接给一个 .R/.py 文件路径。

    支持直接给路径，是为了「拿我自己的脚本当模板」以及让核心仓库的回归测试
    不依赖另一个仓库的 mod（核心仓库的 mods/ 是空的）。
    """
    # 先按文件路径判定：Windows 的 "D:" 里也有冒号，不能靠冒号区分两种写法
    if from_spec.lower().endswith((".r", ".py")) and os.path.isfile(from_spec):
        src = os.path.abspath(from_spec)
        dst = os.path.join(pdir, os.path.basename(src))
        with open(src, "rb") as a, open(dst, "wb") as b:
            b.write(a.read())
        return dst, {"mod": None, "template": os.path.basename(src),
                     "sha256": sha256(dst)}

    if ":" in from_spec:
        mid, rel = from_spec.split(":", 1)
    else:
        mid, rel = from_spec, None
    mid = mod.v_id(mid)
    mdir = mod.mod_dir(mid)
    if not os.path.isdir(mdir):
        raise VError(f"没有这个 mod：{mid}")
    tdir = os.path.join(mdir, "templates")
    if rel:
        rel = mod.v_relpath(rel, mod.TEMPLATE_EXTS)
        src = os.path.join(mdir, *rel.split("/"))
        if not os.path.isfile(src):
            raise VError(f"模板不存在：mods/{mid}/{rel}")
    else:
        cands = sorted(f for f in os.listdir(tdir)) if os.path.isdir(tdir) else []
        cands = [f for f in cands if f.lower().endswith((".r", ".py"))]
        if not cands:
            raise VError(f"mods/{mid}/templates/ 下没有可用的模板（.R / .py）")
        rel, src = f"templates/{cands[0]}", os.path.join(tdir, cands[0])
    dst = os.path.join(pdir, os.path.basename(src))
    with open(src, "rb") as a, open(dst, "wb") as b:
        b.write(a.read())
    return dst, {"mod": mid, "template": rel, "sha256": sha256(dst)}


# ---------------------------------------------------------------- 编辑与偏离

def ensure_working(pdir, prj):
    """首次编辑才把源副本拷成工作副本。**源副本从此不再被写。**"""
    d = prj["data"]
    wpath = os.path.join(pdir, d.get("working") or "data.working.csv")
    if not os.path.isfile(wpath):
        header, body, meta = read_table(os.path.join(pdir, d["source"]))
        write_table(wpath, header, body, meta)
    return wpath


def record_edit(pdir, op):
    """审计行是 append-only 的 —— 只加不改，崩溃也不会丢历史。"""
    p = os.path.join(pdir, "data.edits.jsonl")
    with open(p, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(op, ensure_ascii=False) + "\n")


def refresh_divergence(pdir, prj):
    """**推导** diverged，绝不手工置位。判据是工作副本与源副本的哈希是否相等。"""
    d = prj["data"]
    w = d.get("working")
    if not w:
        d["diverged"] = False
        d["working_sha256"] = None
        return False
    wpath = os.path.join(pdir, w)
    if not os.path.isfile(wpath):
        d["diverged"] = False
        return False
    d["working_sha256"] = sha256(wpath)
    d["diverged"] = d["working_sha256"] != d["source_sha256"]
    return d["diverged"]


def edit_cell(cfg, pdir, row, col, value):
    """改一个单元格。row 是数据行号（0 起，不含表头），col 是列名。"""
    prj = load_project(pdir)
    d = prj["data"]
    if not d:
        raise VError("这个项目没有数据（建项目时没给 --data）")
    wpath = ensure_working(pdir, prj)
    d["working"] = os.path.basename(wpath)
    header, body, meta = read_table(wpath)
    if col not in header:
        raise VError(f"没有这一列：{col!r}（有：{', '.join(header)}）")
    if not (0 <= row < len(body)):
        raise VError(f"行号越界：{row}（共 {len(body)} 行数据，0 起）")
    ci = header.index(col)
    before = body[row][ci]
    body[row][ci] = value
    write_table(wpath, header, body, meta)
    record_edit(pdir, {"ts": now_stamp(), "op": "set", "row": row,
                       "col": col, "before": before, "after": value})
    d["edits"] = int(d.get("edits", 0)) + 1
    d["rows"], d["cols"], d["header"] = len(body), len(header), header
    diverged = refresh_divergence(pdir, prj)
    write_json(os.path.join(pdir, "project.json"), prj)
    return before, value, diverged


def revert(cfg, pdir):
    """丢掉工作副本，回到源副本。"""
    prj = load_project(pdir)
    d = prj["data"]
    w = d.get("working")
    if w:
        p = os.path.join(pdir, w)
        if os.path.isfile(p):
            os.remove(p)
    record_edit(pdir, {"ts": now_stamp(), "op": "revert"})
    d["working"] = None
    d["edits"] = 0
    refresh_divergence(pdir, prj)
    write_json(os.path.join(pdir, "project.json"), prj)
    return d["diverged"]


# ---------------------------------------------------------------- 渲染

def run_render(cfg, pdir, timeout=900):
    """跑脚本、收日志、做出图后的各项闸门。返回 results（房屋风格的列表）。"""
    prj = load_project(pdir)
    results = []
    script = find_script(pdir, prj.get("script"))
    if not script:
        return [{"probe": "脚本", "ok": False, "core": True,
                 "detail": f"项目里找不到绘图脚本（{'/'.join(SCRIPT_EXTS)}）",
                 "fix": "用 workbench.py new --from <mod>:<template> 建项目，"
                        "或自己放一个 plot.R / plot.py"}]
    code = read_text(script)
    fm = parse_frontmatter(code)
    spec = resolve_spec(fm, pdir)
    ext = os.path.splitext(script)[1].lower()

    # ---- 1. 数据
    # 项目没有数据、脚本也没声明 data= 时**跳过而不是失败**：像 theme-demo
    # 这种自带示例数据的模板本来就该能在空项目里出图。
    data_path, is_working = active_data(pdir, prj)
    if not (prj.get("data") or spec["data"]):
        results.append({"probe": "数据", "ok": None, "core": False,
                        "detail": "项目里没有数据文件，脚本自带示例数据",
                        "fix": None})
    elif os.path.isfile(data_path):
        header, body, meta = read_table(data_path)
        which = "工作副本（已偏离源）" if is_working else "源副本"
        results.append({"probe": "数据", "ok": True, "core": True,
                        "detail": f"{which} {os.path.basename(data_path)}："
                                  f"{len(body)} 行 × {len(header)} 列，"
                                  f"编码 {meta['encoding']}", "fix": None})
    else:
        results.append({"probe": "数据", "ok": False, "core": True,
                        "detail": f"数据文件不存在：{data_path}",
                        "fix": "把数据放到项目目录，或在 front-matter 里指定 data="})

    # ---- 2. 字面量 U+2212（渲染前拒绝，别等出图才发现缺字）
    if not spec["u2212_allow"] and U2212 in code:
        n = code.count(U2212)
        results.append({"probe": "U+2212", "ok": False, "core": True,
                        "detail": f"脚本里有 {n} 处 U+2212 减号字符",
                        "fix": "改用 ASCII 连字符 '-'（如 \"-log10(padj)\"）。"
                               "SimHei 没有 U+2212 字形；axes.unicode_minus=False "
                               "只管自动刻度负号，管不了字符串字面量。"
                               "**扫描是纯文本的，注释里的也算** —— 在注释里描述它时"
                               "别把字符本身写出来。详见 references/fonts.md"})
        return results
    results.append({"probe": "U+2212", "ok": True, "core": True,
                    "detail": "无字面量 U+2212", "fix": None})

    # ---- 2b. 上一轮的矢量产物是不是被手工改过（本次渲染会盖掉它）
    # 矢量文件是唯一「你会拿去手工编辑」的产物，所以它也是唯一会被渲染静默
    # 覆盖掉成果的地方。这里在动手**之前**说一声。
    stem = os.path.splitext(spec["out"])[0]
    prev_vec = (prj.get("last_render") or {}).get("vector") or {}
    clobbered = [stem + e for e in spec["vector"]
                 if os.path.isfile(os.path.join(pdir, stem + e))
                 and prev_vec.get(stem + e)
                 and sha256(os.path.join(pdir, stem + e)) != prev_vec[stem + e]]
    if clobbered:
        results.append({"probe": "手工改动", "ok": None, "core": False,
                        "detail": f"{'、'.join(clobbered)} 与上次渲染的哈希不符"
                                  f"（手改过），本次渲染会覆盖",
                        "fix": "要留住手改的那版，先把它另存一份再 render。"
                               "矢量文件是脚本的产物，改它就等于与脚本分叉 —— "
                               "工作台不禁止，但会一直告诉你"})

    # ---- 3. 执行
    if ext == ".r":
        # 走 r_script 的临时 .R 文件路径，**永不 -e**：Windows 上 Rscript 会把
        # -e 的表达式再过一遍 shell，`| < > &` 会炸成一句误导性的报错。
        rc, out = mod.r_script(cfg, code, timeout=timeout, cwd=pdir)
    else:
        env = spec["env"] or "figkit"
        try:
            py = mod.env_python(cfg, env)
        except VError:
            py = cfg["figkit_python"]
        rc, out = mod.run([py, os.path.basename(script)], timeout=timeout, cwd=pdir)
    write_text(os.path.join(pdir, "render.log"),
               f"# {now_stamp()}\n# {os.path.basename(script)}  rc={rc}\n\n{out}")
    if rc != 0:
        results.append({"probe": "执行", "ok": False, "core": True,
                        "detail": f"脚本退出码 {rc}：{mod.first_line(out, 160)}",
                        "fix": f"看项目里的 render.log 全文"})
        return results
    results.append({"probe": "执行", "ok": True, "core": True,
                    "detail": f"{os.path.basename(script)} rc=0", "fix": None})

    # ---- 4. 产物与尺寸
    out_png = os.path.join(pdir, spec["out"])
    dims = mod.png_dims(out_png) if os.path.isfile(out_png) else None
    if not dims:
        results.append({"probe": "产物", "ok": False, "core": True,
                        "detail": f"没拿到可解析的 PNG：{spec['out']}",
                        "fix": "确认脚本真的把图存到了这个文件名（R 用 ggsave，"
                               "Python 用 fig.savefig；**不要用 cnsplots.savefig**，"
                               "它会毁掉中文）"})
        return results
    w, h = dims
    ew, eh = mm_px(spec["width_mm"], spec["dpi"]), mm_px(spec["height_mm"], spec["dpi"])
    ok_size = abs(w - ew) <= 1 and abs(h - eh) <= 1
    results.append({"probe": "尺寸", "ok": ok_size, "core": True,
                    "detail": f"产物 {w}×{h} px，声明 {spec['width_mm']}×"
                              f"{spec['height_mm']} mm @ {spec['dpi']}dpi = {ew}×{eh} px",
                    "fix": None if ok_size else
                           f"图上写着 {spec['width_mm']}mm，实际却出了 {w}px。"
                           f"去改脚本里的 width/height（R: ggsave 的 width/height/units，"
                           f"Python: figsize=({spec['width_mm']}/25.4, "
                           f"{spec['height_mm']}/25.4)），或改 front-matter"})

    if spec["width_mm"] not in JOURNAL_WIDTHS_MM:
        results.append({"probe": "期刊宽度", "ok": None, "core": False,
                        "detail": f"{spec['width_mm']}mm 不是常用栏宽"
                                  f"（{'/'.join(str(x) for x in JOURNAL_WIDTHS_MM)}）",
                        "fix": "若目标是投稿，按 target 期刊的 Author Guidelines 核对"
                               "（references/fonts.md 有 Nature/Science/Cell 的表）"})

    # ---- 4b. 矢量产物：投稿要 PDF、进 PPT 要 SVG
    if spec["vector_bad"]:
        results.append({"probe": "矢量格式", "ok": False, "core": True,
                        "detail": "front-matter 声明了不支持的矢量格式："
                                  + "、".join(spec["vector_bad"]),
                        "fix": f"目前只支持 {'/'.join(VECTOR_EXTS)}；"
                               "两个都要就写 vector=pdf,svg"})

    if not spec["vector"]:
        here = [stem + e for e in VECTOR_EXTS
                if os.path.isfile(os.path.join(pdir, stem + e))]
        results.append({"probe": "矢量", "ok": None, "core": False,
                        "detail": ("出了 " + "、".join(here) + "，但脚本没声明 vector=")
                                  if here else "只出了 PNG，没有矢量图",
                        "fix": "投稿要 PDF（字体嵌入）、进 PPT 要 SVG（可缩放）。"
                               "脚本头部加 `# figwork: vector=pdf,svg` 并让脚本存这两个格式，"
                               "字体设置见 references/fonts.md"})

    for ext in spec["vector"]:
        name = stem + ext
        vp = os.path.join(pdir, name)
        if not os.path.isfile(vp):
            results.append({"probe": f"矢量{ext}", "ok": False, "core": True,
                            "detail": f"声明了 vector={ext.lstrip('.')}，但没产出 {name}",
                            "fix": "让脚本真的存这个格式。**R 出 PDF 必须显式 "
                                   "device = cairo_pdf** —— ggsave 按扩展名默认挑的 "
                                   "pdf() 会报 invalid font type，中文还会 mbcsToSbcs "
                                   "失败；R 出 SVG 用 svglite::svglite"})
            continue

        box = vector_box(vp)
        ew_pt, eh_pt = spec["width_mm"] * PT_PER_MM, spec["height_mm"] * PT_PER_MM
        if box is None:
            results.append({"probe": f"矢量{ext}尺寸", "ok": False, "core": True,
                            "detail": f"{name} 的外框读不出来"
                                      f"（可能并不是真正的 {ext.lstrip('.').upper()}）",
                            "fix": "确认脚本真的把图按这个格式存了出来，而不是只改了扩展名"})
        else:
            ok_v = (abs(box[0] - ew_pt) <= VEC_TOL_PT
                    and abs(box[1] - eh_pt) <= VEC_TOL_PT)
            results.append({"probe": f"矢量{ext}尺寸", "ok": ok_v, "core": True,
                            "detail": f"{name} 外框 {box[0]:.2f}×{box[1]:.2f} pt，"
                                      f"声明 {spec['width_mm']}×{spec['height_mm']} mm "
                                      f"= {ew_pt:.2f}×{eh_pt:.2f} pt",
                            "fix": None if ok_v else
                                   "矢量没有截断误差，所以这一关比 PNG 更严。"
                                   "去改脚本存矢量时的 width/height（R 的 ggsave 要带 "
                                   "units=\"mm\"，Python 用同一个 figsize）"})

        ok_f, _bad, det_f, fix_f = vector_font_verdict(vp)
        results.append({"probe": f"矢量{ext}字体", "ok": ok_f, "core": True,
                        "detail": det_f, "fix": fix_f})

    # ---- 5. 缺字
    results.append(_check_glyphs(code, out, spec))

    # ---- 6. 记账
    # 矢量产物的哈希也记下来 —— 下次渲染前就能知道它有没有被手工改过。
    vec_rec = {stem + e: sha256(os.path.join(pdir, stem + e))
               for e in spec["vector"]
               if os.path.isfile(os.path.join(pdir, stem + e))}
    prj["last_render"] = {
        "at": now_stamp(),
        "script": os.path.basename(script),
        "script_sha256": sha256(script),
        "data_used": os.path.basename(data_path),
        "data_sha256": sha256(data_path) if os.path.isfile(data_path) else None,
        "diverged_at_render": bool(is_working),
        "out": spec["out"],
        "dims": [w, h],
        "spec": {k: spec[k] for k in ("preset", "width_mm", "height_mm", "dpi")},
        "vector": vec_rec,
        "vector_declared": list(spec["vector"]),
    }
    prj["script"] = os.path.basename(script)
    write_json(os.path.join(pdir, "project.json"), prj)
    results.append({"probe": "记账", "ok": True, "core": False,
                    "detail": f"project.json 记下 {spec['out']} {w}×{h}"
                              + (f" 与矢量 {'、'.join(sorted(vec_rec))}" if vec_rec else "")
                              + " 及数据哈希",
                    "fix": None})
    return results


GLYPH_SIGNALS = ("missing from font", "Glyph", "font family not found",
                 "no font could be found", "invalid font", "字体")
FONT_MARKERS = ("simhei", "yahei", "noto sans", "font.sans-serif", "font_add",
                "showtext", "family =", "family=", "cjk", "systemfonts", "agg_png")


def _has_cjk(text):
    return any("一" <= ch <= "鿿" for ch in text)


def _check_glyphs(code, render_out, spec):
    """缺字两路查：① 渲染日志里的已知信号（确定性）；② 「有中文但没设字体」
    的启发式（可能误报，故可用 front-matter `cjk=off` 关掉）。"""
    hits = [s for s in GLYPH_SIGNALS if s.lower() in (render_out or "").lower()]
    if hits:
        return {"probe": "缺字", "ok": False, "core": True,
                "detail": f"渲染日志里出现缺字信号：{', '.join(hits[:3])}",
                "fix": "中文必须显式设字体。Python: plt.rcParams['font.sans-serif']="
                       "['SimHei','Microsoft YaHei'] 且 axes.unicode_minus=False，"
                       "**且必须在 cnsplots.setup_matplotlib() 之后设**（它会重置）；"
                       "R: showtext + theme(text=element_text(family='SimHei'))。"
                       "详见 references/fonts.md"}
    if spec["cjk_check"] and _has_cjk(code):
        low = code.lower()
        if not any(m in low for m in FONT_MARKERS):
            return {"probe": "缺字", "ok": False, "core": True,
                    "detail": "脚本里有中文，却找不到任何设字体的痕迹",
                    "fix": "加字体设置，或若字体是在别处设的，在 front-matter 写 "
                           "`# figwork: cjk=off` 关掉这条检查。详见 references/fonts.md"}
    return {"probe": "缺字", "ok": True, "core": True,
            "detail": "无缺字信号", "fix": None}


# ---------------------------------------------------------------- 静态报告（P2）

def write_report(cfg, pdir, anon=False, out_dir=None):
    """一份自包含 HTML：表格 + 代码 + 内嵌图。零 JS、零端口、零攻击面。"""
    prj = load_project(pdir)
    # **不要写 prj.get("data", {})** —— 项目没有数据时 "data" 这个键是存在的、
    # 值是 None，默认值根本不会生效，于是下面每个 .get 都炸在 None 上。
    dmeta = prj.get("data") or {}
    script = find_script(pdir, prj.get("script"))
    code = read_text(script) if script else ""
    spec = resolve_spec(parse_frontmatter(code), pdir)
    data_path, is_working = active_data(pdir, prj)
    header, body, meta = (read_table(data_path) if os.path.isfile(data_path)
                          else ([], [], {}))

    def path_for(p):
        """--anon 时只留文件名 —— 比赛材料不得出现 D:\\ 这类本地路径。"""
        p = str(p or "")
        return os.path.basename(p) if anon else p

    png_uri = ""
    png = os.path.join(pdir, spec["out"])
    if os.path.isfile(png):
        with open(png, "rb") as fh:
            png_uri = "data:image/png;base64," + base64.b64encode(fh.read()).decode()

    # 有 SVG 就优先用它：在 <img> 里按矢量缩放、打印锐利。
    # 刻意用 base64 data URI 而不是把 SVG 内联进 DOM —— 浏览器**不会执行**
    # <img> 里的 SVG 脚本，内联才会。这样「报告零 JS」这条纪律加了矢量仍成立。
    stem_out = os.path.splitext(spec["out"])[0]
    svg_uri = ""
    svg_path = os.path.join(pdir, stem_out + ".svg")
    if os.path.isfile(svg_path):
        with open(svg_path, "rb") as fh:
            svg_uri = ("data:image/svg+xml;base64,"
                       + base64.b64encode(fh.read()).decode())

    lr = prj.get("last_render") or {}
    dims = lr.get("dims")
    title = prj.get("name") or os.path.basename(pdir)
    log = ""
    lp = os.path.join(pdir, "render.log")
    if os.path.isfile(lp):
        log = read_text(lp)
    if anon:
        log = re.sub(r"[A-Za-z]:[\\/][^\s\"']*", lambda m: os.path.basename(m.group(0)), log)

    def esc(x):
        return html.escape(str(x))

    rows_html = "".join(
        "<tr>" + "".join(f"<td>{esc(c)}</td>" for c in r) + "</tr>" for r in body[:400])
    if len(body) > 400:
        rows_html += (f'<tr><td colspan="{max(1, len(header))}">'
                      f'… 另有 {len(body) - 400} 行未显示</td></tr>')
    head_html = "".join(f"<th>{esc(c)}</th>" for c in header)

    banner = ""
    if is_working:
        banner = (f'<div class="warn">⚠ 图基于<b>工作副本</b>，非源文件。'
                  f'已改动 {dmeta.get("edits", 0)} 处'
                  f'（data.edits.jsonl 有逐条记录）。</div>')

    prov = []
    if dmeta:
        prov.append(f"数据：{esc(path_for(dmeta.get('source')))}")
        if not anon and dmeta.get("source_origin"):
            prov.append(f"原始来源：{esc(dmeta['source_origin'])}")
    else:
        prov.append("数据：脚本自带示例数据（项目里没有数据文件）")
    prov.append(f"活动数据：{esc(path_for(data_path))}"
                + ("（工作副本）" if is_working else "（源副本）"))
    prov.append(f"脚本：{esc(os.path.basename(script) if script else '—')}")
    if dims:
        prov.append(f"产物：{dims[0]}×{dims[1]} px @ {spec['dpi']}dpi "
                    f"（声明 {spec['width_mm']}×{spec['height_mm']} mm）")
    vec_files = [stem_out + e for e in VECTOR_EXTS
                 if os.path.isfile(os.path.join(pdir, stem_out + e))]
    if vec_files:
        prov.append("矢量：" + "、".join(vec_files)
                    + ("（可编辑）" if any(f.endswith(".svg") for f in vec_files) else ""))
    src = prj.get("from") or {}
    if src.get("mod"):
        prov.append(f"起点：mod {esc(src['mod'])} / {esc(src.get('template', '—'))}")
    prov.append(f"生成：{esc(lr.get('at') or now_stamp())}")

    doc = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>{esc(title)} — 绘图工作台</title>
<style>
 body{{font:14px/1.6 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif;
      margin:0;background:#f6f7f9;color:#1c1e21}}
 header{{background:#fff;border-bottom:1px solid #dfe1e5;padding:14px 22px}}
 h1{{font-size:18px;margin:0 0 6px}}
 .prov{{font-size:12px;color:#5f6368}} .prov div{{margin:1px 0}}
 .warn{{background:#fff4e5;border-left:4px solid #f0a020;padding:9px 14px;
       margin:14px 22px 0;border-radius:3px}}
 main{{padding:14px 22px 40px;display:grid;gap:16px}}
 section{{background:#fff;border:1px solid #dfe1e5;border-radius:6px;padding:14px}}
 h2{{font-size:13px;margin:0 0 10px;color:#5f6368;text-transform:uppercase;
    letter-spacing:.06em}}
 table{{border-collapse:collapse;font-size:12.5px;width:100%}}
 th,td{{border:1px solid #e3e5e8;padding:3px 8px;text-align:left;
       white-space:nowrap}}
 th{{background:#f1f3f4;position:sticky;top:0}}
 pre{{margin:0;font:12.5px/1.55 "Cascadia Mono",Consolas,monospace;
     white-space:pre-wrap;word-break:break-word}}
 .scroll{{max-height:430px;overflow:auto}}
 img{{max-width:100%;height:auto;display:block}}
 .empty{{color:#80868b;font-style:italic}}
 .log{{background:#1f2226;color:#d6d9dd;border-radius:4px;padding:10px;
      max-height:260px;overflow:auto}}
</style></head><body>
<header><h1>{esc(title)}</h1>
<div class="prov">{''.join(f'<div>{p}</div>' for p in prov)}</div></header>
{banner}
<main>
 <section><h2>图</h2>
  {f'<img src="{svg_uri or png_uri}" alt="figure">' if (svg_uri or png_uri)
     else '<p class="empty">还没有产物 —— 跑一次 workbench.py render</p>'}
 </section>
 <section><h2>数据（{len(body)} 行 × {len(header)} 列，编码 {esc(meta.get('encoding','—'))}{'，工作副本' if is_working else ''}）</h2>
  <div class="scroll"><table><thead><tr>{head_html}</tr></thead>
  <tbody>{rows_html}</tbody></table></div>
 </section>
 <section><h2>脚本 {esc(os.path.basename(script) if script else '')}</h2>
  <pre>{esc(code)}</pre></section>
 <section><h2>渲染日志</h2>
  <div class="log"><pre>{esc(log[-6000:] if log else '（无）')}</pre></div>
 </section>
</main></body></html>
"""
    dest_dir = out_dir or pdir
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, f"报告_{prj.get('name') or 'project'}.html")
    write_text(dest, doc)
    return dest, pdir


# ---------------------------------------------------------------- CLI

def _print_results(results, as_json=False):
    if as_json:
        p = sum(1 for r in results if r["ok"] is True)
        f = sum(1 for r in results if r["ok"] is False)
        s = sum(1 for r in results if r["ok"] is None)
        print(json.dumps({"results": results, "pass": p, "fail": f, "skip": s},
                         ensure_ascii=False, indent=2))
        return 0 if f == 0 else 1
    print("=" * 68)
    n = len(results)
    for i, r in enumerate(results, 1):
        tag = "PASS" if r["ok"] else ("SKIP" if r["ok"] is None else "FAIL")
        print(f"[{i:2}/{n}] {r['probe']:<22} {tag:<4} {r['detail']}")
        if r.get("fix") and r["ok"] is not True:
            print(f"{'':<30}fix: {r['fix']}")
    print()
    p = sum(1 for r in results if r["ok"] is True)
    f = sum(1 for r in results if r["ok"] is False)
    s = sum(1 for r in results if r["ok"] is None)
    print(f"RESULT: {p} PASS / {f} FAIL / {s} SKIP")
    return 0 if f == 0 else 1


def cmd_new(cfg, rest):
    pos, opts = _split(rest)
    if not pos:
        print("用法：workbench.py new <项目名> [--data <csv>] "
              "[--from <mod>:<template>] [--preset nature1] [--root <dir>]",
              file=sys.stderr)
        return 2
    name = pos[0]
    try:
        pdir, prj = new_project(cfg, name, data_src=opts.get("data"),
                                from_spec=opts.get("from"),
                                preset=opts.get("preset"), root=opts.get("root"))
    except VError as exc:
        print(f"拒绝：{exc}", file=sys.stderr)
        return 1
    print("=" * 68)
    print(f"建好项目 {name}")
    print(f"  {pdir}")
    for k, v in (("数据", (prj.get("data") or {}).get("source")),
                 ("脚本", prj.get("script")),
                 ("起点", ((prj.get("from") or {}).get("template")))):
        if v:
            print(f"  {k}：{v}")
    print()
    print(f"下一步：改 plot.R 的 front-matter 与绘图参数，然后")
    print(f"  python {os.path.abspath(__file__)} render {pdir}")
    return 0


def cmd_render(cfg, rest):
    pos, opts = _split(rest)
    if not pos:
        print("用法：workbench.py render <项目名|目录> [--json] [--timeout N]",
              file=sys.stderr)
        return 2
    try:
        pdir = resolve_project(cfg, pos[0], opts.get("root"))
    except VError as exc:
        print(f"拒绝：{exc}", file=sys.stderr)
        return 1
    try:
        results = run_render(cfg, pdir, timeout=int(opts.get("timeout") or 900))
    except VError as exc:
        print(f"拒绝：{exc}", file=sys.stderr)
        return 1
    if not opts.get("json"):
        print("=" * 68)
        print(f"渲染 {os.path.basename(pdir)}")
    return _print_results(results, as_json=bool(opts.get("json")))


def cmd_report(cfg, rest):
    pos, opts = _split(rest)
    if not pos:
        print("用法：workbench.py report <项目名|目录> [--anon] [--no-open]",
              file=sys.stderr)
        return 2
    try:
        pdir = resolve_project(cfg, pos[0], opts.get("root"))
        dest, _ = write_report(cfg, pdir, anon=bool(opts.get("anon")),
                               out_dir=opts.get("out"))
    except VError as exc:
        print(f"拒绝：{exc}", file=sys.stderr)
        return 1
    print(f"报告已生成：{dest}")
    if not opts.get("no-open") and hasattr(os, "startfile"):
        try:
            os.startfile(dest)
        except Exception as exc:
            print(f"  （没能自动打开：{exc}）")
    return 0


def cmd_edit(cfg, rest):
    pos, opts = _split(rest)
    if not pos:
        print("用法：workbench.py edit <项目> --row N --col 列名 --value 值",
              file=sys.stderr)
        return 2
    try:
        pdir = resolve_project(cfg, pos[0], opts.get("root"))
        before, after, diverged = edit_cell(
            cfg, pdir, int(opts["row"]), opts["col"], opts.get("value", ""))
    except KeyError as exc:
        print(f"缺参数：{exc}", file=sys.stderr)
        return 2
    except (VError, ValueError) as exc:
        print(f"拒绝：{exc}", file=sys.stderr)
        return 1
    print(f"已改 {opts['col']}[{opts['row']}]：{before!r} -> {after!r}")
    print(f"  偏离源文件：{'是' if diverged else '否'}")
    return 0


def cmd_revert(cfg, rest):
    pos, opts = _split(rest)
    if not pos:
        print("用法：workbench.py revert <项目>", file=sys.stderr)
        return 2
    try:
        pdir = resolve_project(cfg, pos[0], opts.get("root"))
        diverged = revert(cfg, pdir)
    except VError as exc:
        print(f"拒绝：{exc}", file=sys.stderr)
        return 1
    print(f"已丢弃工作副本，回到源副本。偏离：{'是' if diverged else '否'}")
    return 0


def cmd_list(cfg, rest):
    _, opts = _split(rest)
    root = wb_root(cfg, opts.get("root"))
    base = os.path.join(root, "projects")
    if not os.path.isdir(base):
        print(f"（还没有项目）{base}")
        return 0
    names = sorted(d for d in os.listdir(base)
                   if os.path.isfile(os.path.join(base, d, "project.json")))
    if not names:
        print(f"（还没有项目）{base}")
        return 0
    print("=" * 68)
    for d in names:
        prj = read_json(os.path.join(base, d, "project.json"), {})
        data = prj.get("data") or {}
        lr = prj.get("last_render") or {}
        flags = []
        if data.get("diverged"):
            flags.append(f"偏离 {data.get('edits', 0)} 处")
        if lr.get("dims"):
            flags.append(f"{lr['dims'][0]}×{lr['dims'][1]}")
        print(f"  {d:<26} {prj.get('script') or '—':<10} "
              f"{'  '.join(flags) if flags else '未渲染'}")
    print(f"\n共 {len(names)} 个项目，在 {base}")
    return 0


# 这些 flag 会**吃掉下一个参数作为自己的值**。必须显式列出：否则
# `new --data x.csv 我的项目` 会把 x.csv 当成项目名，而 --json 这类开关
# 后面若跟着位置参数，又会被误吞。
VALUED_FLAGS = {"data", "from", "preset", "root", "out", "timeout",
                "row", "col", "value"}


def _split(args):
    """把 [--k=v | --k v | 位置参数] 拆成 (位置参数列表, 选项字典)。"""
    pos, opts, i = [], {}, 0
    while i < len(args):
        a = args[i]
        if a.startswith("--"):
            k = a[2:]
            if "=" in k:
                k, v = k.split("=", 1)
                opts[k.replace("-", "_")] = v
            elif k in VALUED_FLAGS and i + 1 < len(args):
                opts[k.replace("-", "_")] = args[i + 1]
                i += 1
            else:
                opts[k.replace("-", "_")] = True
        else:
            pos.append(a)
        i += 1
    return pos, opts


USAGE = """sci-figure-kit 绘图工作台（无界面核心）

  workbench.py list                        列出项目
  workbench.py new <项目名> --data <csv> [--from <mod>:<template>] [--preset nature1]
  workbench.py render <项目名|目录> [--json]
  workbench.py report <项目名|目录> [--anon] [--no-open]
  workbench.py edit <项目> --row N --col 列名 --value 值
  workbench.py revert <项目>

项目默认在 <root>/workbench/projects/（机器本地，不进分享 zip）。
可用 --root <dir> 或环境变量 FIGWORK_ROOT 改。

模板契约见 mods/README.md；运行期规则见 references/workbench.md。
"""


def main():
    argv = sys.argv[1:]
    cfg, _ = mod.load_config()
    try:
        pos, _ = _split(argv)
        if not pos or pos[0] in ("-h", "--help", "help"):
            print(USAGE)
            return 0
        cmd = pos[0]
        # 子命令**之前**的 flag 也归它：`--root X render p` 与 `render p --root X` 等价
        rest = argv[argv.index(cmd) + 1:]
        if cmd == "list":
            return cmd_list(cfg, rest)
        if cmd == "new":
            return cmd_new(cfg, rest)
        if cmd == "render":
            return cmd_render(cfg, rest)
        if cmd == "report":
            return cmd_report(cfg, rest)
        if cmd == "edit":
            return cmd_edit(cfg, rest)
        if cmd == "revert":
            return cmd_revert(cfg, rest)
        print(f"未知子命令：{cmd}\n", file=sys.stderr)
        print(USAGE, file=sys.stderr)
        return 2
    except VError as exc:
        print(f"拒绝执行：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
