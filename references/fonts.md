# 中文字体与配色配方

**铁律：画中文图必须显式设字体，不设必出方框（tofu）。** 这不是"最好设"，是"必须设"。

本机可用字体（实测存在）：

| 文件 | 字体名 |
|---|---|
| `C:/Windows/Fonts/simhei.ttf` | SimHei（黑体） |
| `C:/Windows/Fonts/msyh.ttc` | Microsoft YaHei（微软雅黑） |
| `C:/Windows/Fonts/NotoSansSC-VF.ttf` | Noto Sans SC |

---

## Python（figkit / omicverse）

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Noto Sans SC"]
plt.rcParams["axes.unicode_minus"] = False   # 关键！否则负号显示成方框
```

**`axes.unicode_minus = False` 极易漏。** 漏了的话：中文正常了，但所有 `-1`、`-2` 这类负数的减号变成方框——因为 SimHei 没有 U+2212 这个字符。

### ⚠️ cnsplots 的三个中文坑（实测踩全了）

**坑 1 —— `cnsplots.setup_matplotlib()` 会覆盖你设的字体。**
它把 `font.sans-serif` 重置成 Helvetica/Arial 那一串（无中文），还把 `axes.unicode_minus` 重置回 `True`。
**顺序必须是：先 `setup_matplotlib()`，再设 rcParams。**

```python
cnsplots.setup_matplotlib()
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei"]   # 必须在其后
plt.rcParams["axes.unicode_minus"] = False
```

**坑 2 —— 绝对不能用 `cnsplots.savefig()` 保存中文图。**
实测：同一张图，`cnsplots.savefig()` 产生 **90 处缺字警告**（中文全变方框），`fig.savefig()` 是 **0 处**。它内部会重置字体。

```python
# 错
cnsplots.savefig("out.png")
# 对
fig.savefig("out.png", dpi=300, bbox_inches="tight")
```

**坑 3 —— 不要在图里的文字中写 U+2212「−」。**
SimHei 没有这个字形。`axes.unicode_minus=False` 只管**坐标轴刻度的自动负号**，管不了你字符串里的字面量。写 `"-log10(padj)"`（ASCII 连字符），不要写 `"−log10(padj)"`。

**辅助函数**：`cnsplots.apply_unicode_font(ax, font="SimHei")` 会把 ax 上含非 ASCII 的文字切到指定字体。**它的默认值是 `DejaVu Sans`（无中文），必须显式传 `font="SimHei"`。** 在设完所有文字、savefig 之前调用。

**自检手法**：保存时捕获缺字警告，比肉眼看图可靠：

```python
import warnings
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    fig.savefig(path, dpi=300, bbox_inches="tight")
    missing = [str(x.message) for x in w if "missing from font" in str(x.message)]
assert not missing, f"中文缺字 {len(missing)} 处"
```

若用 SciencePlots，可叠加它自带的中文样式：

```python
import scienceplots
plt.style.use(["science", "nature", "no-latex", "cjk-sc-font"])
```

注意 `no-latex` 不能不写——本机没装 LaTeX，不加会直接报错。

若某个环境没装 SimHei（比如换机器），先用 `matplotlib.font_manager` 确认真实可用名，不要硬编码：

```python
from matplotlib import font_manager
names = {f.name for f in font_manager.fontManager.ttflist}
print([n for n in names if any(k in n for k in ("Sim", "YaHei", "Noto", "Hei", "Song"))])
```

---

## R（`{root}/R`）

R 出中文字体图有两条路，都要显式指定，没有"自动"。

**R 侧的中文必须在每次出图前显式调用 `showtext_auto()` + `font_add()`**，不会自动继承。实测在 `counts_tpm.tsv` 热图和 SCpubr 的 UMAP 上都工作正常。

```r
suppressMessages(library(showtext))
showtext_auto()
font_add("SimHei", "C:/Windows/Fonts/simhei.ttf")
# 之后所有 ggplot 都要 text = element_text(family = "SimHei")
```

### 路线一：`showtext`（推荐，最稳）

```r
library(showtext)
showtext_auto()
font_add("SimHei", "C:/Windows/Fonts/simhei.ttf")

library(ggplot2)
p <- ggplot(df, aes(x, y)) + geom_point() +
     labs(title = "中文标题", x = "处理组", y = "表达量") +
     theme(text = element_text(family = "SimHei"))

ggsave("out.png", p, width = 89, height = 60, units = "mm", dpi = 300)
```

### 路线二：`ragg` / `svglite` 设备

```r
library(ragg)
agg_png("out.png", width = 89, height = 60, units = "mm", res = 300)
print(p)   # p 里已设 family = "SimHei"
dev.off()
```

`svglite::svglite()` 用于出矢量 SVG/PDF 且保留可编辑文字。

### `cairo`：包不能用，**设备能用**（别搞混）

本机 conda 的 **R 包 `Cairo`** 停在 r41（R 4.1），与 R 4.6.1 不兼容，装不上。

**但内置的 cairo 设备是好的** —— 实测 `capabilities("cairo")` 为 `TRUE`，
`cairo_pdf()` 直接认 `family = "SimHei"`，出中文且**把字体嵌进 PDF**。
本文件早前写的"不要用 cairo"针对的是那个**包**，把**设备**一起否掉是错的 ——
模板因此绕道 showtext，而 showtext 恰恰会把矢量里的文字转成路径（见下）。

---

## 色盲友好与配色

### 连续色标

```python
import cmcrameri.cm as cm
cmap = cm.batlow     # 顺序（最通用）
cmap = cm.vik        # 发散（替代 RdBu）
cmap = cm.roma       # 发散
cmap = cm.oleron     # 地形
```

**禁用**：`jet`、`rainbow`、`hsv`——感知不均匀，印刷后失真，且色盲不友好。

发散型数据（正负对称）用发散色标并**把中间点钉在 0**：`vmin=-m, vmax=m, center=0`。

### 分类型配色

```r
library(ggsci)
scale_color_npg()      # Nature 系
scale_color_aaas()     # Science 系
scale_color_lancet()   # Lancet
scale_color_nejm()     # NEJM
scale_color_jco()      # JCO
scale_fill_npg()
```

ggsci 实测可用色板（20+ 套）：`npg aaas nejm lancet jama bmj jco frontiers cosmic ucscgb igv locuszoom d3 uchicago startrek tron futurama rickandmorty simpsons flatui atlassian observable` 等。

Python 侧没有 ggsci，要期刊配色就用 cnsplots 的 `palettes`，或用 `palettable`（figkit 已装）。

### 色盲安全基准盘

Okabe-Ito（八色，色盲安全通用基准）：
`#E69F00 #56B4E9 #009E73 #F0E442 #0072B2 #D55E00 #CC79A7 #999999`

---

## 期刊尺寸硬约束

这些库自己都声明"不保证投稿合规"，最终要对着目标刊的 Author Guidelines 核：

| 期刊 | 单栏 | 双栏 |
|---|---|---|
| Nature | 89 mm | 183 mm |
| Science | 55 mm | 175 mm |
| Cell | 85 mm | 178 mm |

字体：Arial / Helvetica，7–8 pt。

### 矢量导出：投稿要 PDF，进 PPT 要 SVG

下面每一条都是**实测**的，且都对应工作台的一道闸门（脚本头部声明
`# figwork: vector=pdf,svg` 后自动查，见 `references/workbench.md`）。

**matplotlib —— 两个默认值都会安静地毁掉矢量图：**

| 默认 | 后果 | 改法 |
|---|---|---|
| `pdf.fonttype = 3` | 产 **Type 3 字体**：Nature/Elsevier 的作者指南明令拒收，且字体不嵌入 | `rcParams["pdf.fonttype"] = 42` |
| `svg.fonttype = 'path'` | **所有文字被转成路径**（实测 `<text>` 元素数 = **0**），Illustrator 里一个字都改不了 | `rcParams["svg.fonttype"] = "none"` |

两者都必须在**任何 `savefig` 之前**设。

**R —— 出 PDF 必须显式写设备：**

```r
ggsave("out.pdf", p, width = 89, height = 60, units = "mm", device = cairo_pdf)  # 对
ggsave("out.pdf", p, width = 89, height = 60, units = "mm")                      # 错！
```

不写 `device=` 时 `ggsave` 按扩展名挑的是 **`pdf()`**，实测报 `invalid font type`，
中文还会 `conversion failure ... in 'mbcsToSbcs'`。`cairo_pdf` 则正常并嵌入字体。
SVG 用 `svglite::svglite`（文字是真 `<text>`，可编辑）。

**⚠️ `showtext` 与矢量不共戴天。** 它把字形画成**多边形**，于是 PDF 里没有字体、
SVG 里没有 `<text>` —— 两者都成了改不了的路径，**字体嵌入与可编辑性同时归零**。
存矢量前必须 `showtext_auto(FALSE)`；实测关掉之后 `cairo_pdf` + `family="SimHei"`
照样出中文，所以关掉无损。PNG 用 showtext、矢量不用，是完全可以并存的。

**实测产物质量对照**（同一张 89×60 mm 的图）：

| 后端 / 设置 | 外框 | 文字可编辑 | 字体嵌入 |
|---|---|---|---|
| matplotlib 默认 | 精确 | ✗（全是路径） | ✗（Type 3） |
| matplotlib 按上表设 | 精确 | ✓ | ✓ |
| R `cairo_pdf` | ±0.28 pt | ✓ | ✓ |
| R `pdf()` | ±0.28 pt | — | ✗ |
| R `svglite` | ±0.004 pt | ✓ | ✗（按字体名引用） |

**外框**：矢量没有像素截断误差，能对得很准。R 的 cairo 会把页面尺寸**取整到整数 pt**
（89 mm 出 252.0 而非 252.2835，差 0.1 mm），工作台的容差因此取 1 pt。

**SVG 的固有取舍**：文字可编辑，但字体是**按名字引用、不嵌入**的。换到没装 SimHei
的机器上打开，中文会回退成别的字体。要交给别人（或投稿），给 **PDF** —— 字体嵌在里面。

**但注意**：以上是**投稿印刷**标准。若图是要放进 PPT 投影的，7–8 pt 在屏幕上太小——PPT 用图要按观看距离另调字号，不要照搬期刊标准。矢量给 PPT 用 SVG，缩放不失真。
