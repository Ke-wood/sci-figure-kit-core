# 路由表（意图 → 后端）与回退链

本文件是 `SKILL.md` 里那张表的展开版。SKILL.md 只放精简表（要在上下文里），细节在这里。

## 三个后端

| 代号 | 环境 | 位置 | 装了什么 |
|---|---|---|---|
| **figkit** | Python 3.14 venv | `{root}/envs/figkit` | cnsplots、SciencePlots、cmcrameri、marsilea（+ 被 cnsplots 带进来的 scanpy/anndata/gseapy/lifelines/statannotations/pycomplexheatmap/upsetplot/matplotlib-venn/adjustText/umap-learn） |
| **R** | **官方 CRAN 安装**（直调 `Rscript.exe`，无需激活） | `{root}/R` | ggplot2、ggsci、gggenomes、SCpubr、Seurat、ComplexHeatmap、中文字体包 |
| **omicverse** | conda prefix | `{root}/envs/omicverse` | omicverse（组学分析全流程） |

三者互不可见，只通过**文件**交换数据（TSV / h5ad / PNG / PDF）。

## 完整路由表

| 用户意图（触发词） | 调用 | 为什么 | 回退 |
|---|---|---|---|
| 顶刊风格单图、「CNS 风格」「Nature 风格」「像正刊那样」 | **cnsplots**（figkit） | 专为 Cell/Nature/Science 版式设计，图型齐全 | `plt.style.use(['science','nature'])`（SciencePlots） |
| 多面板拼图、「拼图」「一张图多个 panel」「a/b/c 面板」 | **marsilea**（figkit） | 声明式拼版，比手工 subplot 好排 | `cnsplots.multipanel()`，或 `r-patchwork`（R） |
| 期刊配色、「Lancet/NEJM/JCO/NPG 配色」 | **ggsci**（R） | 期刊官方色板，20+ 套 | figkit 的 `cmcrameri`；或 cnsplots 自带 `palettes` |
| 精致统计图（箱线/散点/带显著性标注） | **cnsplots**（figkit） | 一行出带统计检验的图 | `statannotations`（figkit 已装） |
| 色盲友好 / 连续色标 / 感知均匀色图 / 地形色 | **cmcrameri**（figkit） | Scientific colour maps，色盲安全、印刷友好 | `cmap='viridis'` |
| 单细胞图（UMAP/tSNE/dotplot/violin/featureplot） | **SCpubr**（R） | 输出即 publication-ready | `scanpy`（figkit 已装）+ cnsplots |
| 组学分析（单细胞流程/差异表达/富集/细胞通讯/轨迹/反卷积） | **omicverse**（omicverse） | 一体化流程 | figkit 的 `scanpy` + `gseapy`（只覆盖部分环节） |
| 热图（聚类/相关性/带注释/分割） | **ComplexHeatmap**（R） | 注释与分割能力无可替代 | `pycomplexheatmap`（figkit 已装） |
| oncoprint / 突变瀑布图 | **ComplexHeatmap**（R） | `oncoPrint()` 是唯一成熟实现 | 无（matplotlib 手绘质量差太多） |
| UpSet / Venn / 集合交集 | **cnsplots**（figkit） | 已含 `upsetplot` + `matplotlib-venn` | marsilea 的 `Upset` |
| 基因/基因组结构图、质粒图、基因簇比对 | **gggenomes**（R） | 基因箭头 + 轨道图 | 无 |
| 火山图 / 森林图 / ROC / 生存曲线 / GSEA | **cnsplots**（figkit） | 招牌图型，直接吃 DataFrame | ggplot2 手写（R） |
| 中文字体图 | 任一后端 + **显式设字体** | 不设必出方框 | 见 `fonts.md` |
| 「给我 R 代码」「写段 ggplot 代码」（不要求出图） | **不调用环境**，只交付代码 | 代码交付模式 | — |
| 「给我 Python 代码」 | **不调用环境**，只交付代码 | 同上 | — |
| 不确定 / 只要一张通用图 | **figkit**（cnsplots 默认主题） | 默认落 figkit，再按上表升级 | — |

## 单向升级原则

1. 先按**最具体**的一行匹配。匹配不到才走默认行（figkit）。
2. **一次只选一个后端**，不在一个脚本里混两个环境。
3. 跨环境只通过文件传递。
4. 上表每一行的"回退"列都是**已装好**的，不是设想——失败时直接切，不需要装新东西。

## 两条硬约束

### 1. 不凭记忆写 API 名

`cnsplots` 与 `omicverse` 的 API 随版本变动，且都不是广为人知的库。**用前必须实测枚举**：

```bash
# cnsplots / marsilea / cmcrameri
{root}/envs/figkit/Scripts/python.exe -c "import cnsplots; print([x for x in dir(cnsplots) if not x.startswith('_')])"

# omicverse
{root}/envs/omicverse/python.exe -c "import omicverse as ov; print([x for x in dir(ov.pp) if not x.startswith('_')])"

# R 包函数（官方 CRAN 版 R，直调即可）
{root}/R/bin/Rscript.exe -e "print(ls('package:SCpubr'))"
```

**注意**：`Rscript -e` 的表达式里不能出现 `| < > &` 这类 shell 元字符 ——
Windows 上 Rscript 会把表达式再过一遍 shell，然后报一句莫名其妙的
「系统找不到指定的路径」。多行或含元字符的 R 代码一律写成 `.R` 文件再传文件名。
详见 `troubleshooting.md §1.3`。

`figkit-api.md` / `r-api.md` / `omicverse-api.md` 里的名字都是**装完后实测写入的**，可以直接用；但若某函数报 `AttributeError`，先 `dir()` 再改，不要臆造变体名。

### 2. gggenomes 需要 GFF3 + FASTA

`gggenomes` 的输入是 **GFF3（基因坐标）+ FASTA（序列）**两个文件，缺一不可。项目里 `载荷设计/sequences/candidates_v1.fa` 只有 FASTA，**没有 GFF3**。要画基因结构图，得先根据 `parts_table.tsv` 生成一份 GFF3（GFF3 是 9 列制表符分隔：`seqid / source / type / start / end / score / strand / phase / attributes`）。这是画图之外的一步准备工作，要提前跟用户说。
