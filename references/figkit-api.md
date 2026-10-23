# figkit 环境 API 速查（实测自本机已装版本）

环境：`{root}/envs/figkit` · Python 3.14.5 · matplotlib 3.10.8

**本文件里所有函数名与签名都是在装完后用 `dir()` / `inspect.signature()` 实测得到的，不是凭记忆写的。**
若某个名字报 `AttributeError`，说明版本变了——先 `dir()` 实测再改，不要臆造变体名。

---

## cnsplots 0.7.0

### 主题与环境配置

```python
import matplotlib
matplotlib.use("Agg")          # 无头环境必须
import cnsplots

cnsplots.setup_matplotlib()    # 应用 CNS 风格 rcParams（字体/线宽/刻度）
# 可选：color_cycle=、color_map=、title_fontsize=、axes_linewidth=
```

`setup_ggplot()` / `setup_scanpy()` 是给对应生态用的变体。

### 图型函数（实测存在）

| 函数 | 说明 |
|---|---|
| `volcanoplot` | 火山图 |
| `forestplot` | 森林图（支持模型对象或 DataFrame） |
| `rocplot` | ROC 曲线 |
| `survivalplot` | Kaplan-Meier 生存曲线 |
| `heatmapplot` | 热图（支持 AnnData / DataFrame / ndarray，带行列注释与聚类） |
| `upsetplot` / `vennplot` | 集合交集 |
| `gseaplot` / `prerank` | GSEA |
| `boxplot` `violinplot` `stripplot` `barplot` `histplot` `kdeplot` `distplot` `ridgeplot` | 基础分布图 |
| `scatterplot` `lineplot` `regplot` `qqplot` | 关系图 |
| `lollipopplot` `dumbbellplot` `slopeplot` `stackplot` `donutplot` `pieplot` `sankeyplot` | 其他 |
| `confusionplot` `cumulativeincidenceplot` `phyloplot` `dotplot` | 专用 |
| `placeholderplot` | 占位图 |

### 关键签名（实测）

```python
volcanoplot(data: pd.DataFrame, x: str = 'log2FoldChange', y: str = '-log10(adjp)',
            symbol: str = 'symbol', show_list: list[str] | None = None, n_show: int = 10, *,
            pvalue_threshold: float = 0.05, fold_change_threshold: float = 0.5,
            transform_y: bool = False, ax: Axes | None = None) -> Axes

forestplot(model=None, bar_width=None, add_pvalue=True, *, data=None, label=None,
           estimate=None, lower=None, upper=None, pvalue=None, group=None, hue=None,
           order=None, group_order=None, hue_order=None, reference=None,
           xlabel=None, ax=None) -> Axes
```

**火山图注意两点**：
1. `y` 默认字符串是 `'-log10(adjp)'`——若你的列名是 `padj`，要么改列名，要么显式传 `y=<你的列>`。
2. `fold_change_threshold` 默认 **0.5**（不是常见的 1.0）。要按 `|log2FC| > 1` 判定显著，必须显式传 `fold_change_threshold=1.0`，否则显著数量对不上。

**森林图用 DataFrame 的路子**：`forestplot(data=df, label='名称列', estimate='点估计列', lower='下界列', upper='上界列', reference=0.5)`。

### 多面板与保存

```python
cnsplots.add_panel_label("A")     # 给当前 figure 当前 ax 打面板标（作用于当前轴）
cnsplots.multipanel(max_width=None, title=None, loc=None)   # 多面板布局辅助
cnsplots.savefig("out.png")       # 见下面的警告
```

`add_panel_label` / `multipanel` 是**模块级函数、作用于当前 figure**，不是声明式 builder——要在 `plt.subplots()` 之后逐个轴调用。

### ⚠️ 中文图不要用 `cnsplots.savefig()`

实测：同一张带中文的图，`cnsplots.savefig()` 产生 **90 处缺字警告**（中文全渲染成方框），
而 `fig.savefig()` 是 **0 处**。它内部会重置字体设置。

```python
cnsplots.savefig("out.png")                                    # 中文会烂
fig.savefig("out.png", dpi=300, bbox_inches="tight")           # 中文正常
```

另外 `cnsplots.setup_matplotlib()` 会把 `font.sans-serif` 重置成无中文的 Helvetica/Arial 串，
并把 `axes.unicode_minus` 重置回 `True`。**必须在其之后重设 rcParams**，顺序不能反。
完整配方见 `fonts.md`。

### 颜色

```python
cnsplots.BLUE, RED, GREEN, ORANGE, PURPLE, PINK, VIOLET, BROWN, CHOCOLATE, GRAY, YELLOW
cnsplots.palettes
cnsplots.get_hexcolors_from_apalette(...)
```

---

## SciencePlots 2.2.2

纯 `.mplstyle` 配置集。实测可用样式：

```python
import scienceplots
plt.style.use(['science', 'nature'])          # 组合使用
plt.style.use(['science', 'ieee'])
plt.style.use(['science', 'no-latex'])        # 没装 LaTeX 时必须加
plt.style.use(['science', 'cjk-sc-font'])     # 中文（简体）字体样式
plt.style.use(['science', 'bright'])          # 配色循环
plt.style.use(['science', 'high-vis'])
```

目录结构（实测）：`styles/journals/` 下有 `nature.mplstyle`、`ieee.mplstyle`；根下有 `science.mplstyle`；`styles/color/` 有 bright / vibrant / muted / retro / high-vis / high-contrast / light；`styles/languages/` 有 cjk-sc / cjk-tc / cjk-jp / cjk-kr 字体样式。

**没装 LaTeX 时务必加 `no-latex`**，否则 matplotlib 找不到 latex 会报错。

---

## cmcrameri 1.10（实测 __version__ 报 1.8，包版本 1.10——以 `pip show` 为准）

106 个感知均匀色图。常用：

```python
import cmcrameri.cm as cm
plt.imshow(data, cmap=cm.batlow)     # 顺序色标，印刷友好
plt.imshow(data, cmap=cm.vik)        # 发散型
plt.imshow(data, cmap=cm.roma)       # 发散型
plt.imshow(data, cmap=cm.oleron)     # 地形
plt.imshow(data, cmap=cm.batlowK)    # 黑底变体
```

带 `S` 后缀（如 `batlowS`）是"平滑"变体；带 `_r` 后缀是反序；带 `O`（如 `bamO`）是 cyclic。完整 106 个用 `dir(cm)` 枚举。

---

## marsilea 0.8.1

声明式拼图。实测类：

```
Heatmap  CatHeatmap  SizedHeatmap  Upset  UpsetData  Dendrogram  GroupDendrogram
ClusterBoard  CompositeBoard  WhiteBoard  StackBoard  Piece  Layers  Deformation
```

另有 `load_data`、`dataset` 模块（自带示例数据）。

典型用法是「建 board → 往上叠层 → 加图例 → 渲染」，具体链路以 `marsilea` 官方 gallery 为准（本项目未验证到底层细节——用前先 `help(mar.Heatmap)` 实测）。

---

## 被 cnsplots 自动带进来的（可直接用，无需另装）

实测 `pip install cnsplots` 会一并装上：

`scanpy 1.12.4` · `anndata 0.13.4` · `gseapy 1.3.1` · `lifelines 0.30.3` ·
`statannotations 0.7.2` · `pycomplexheatmap 1.8.5` · `upsetplot 0.9.0` ·
`matplotlib-venn 1.1.2` · `adjustText 1.4.0` · `umap-learn 0.5.12` · `statsmodels 0.15.0`

这些正是路由表里那些"回退"件的实体——回退不是设想，是已就位。
