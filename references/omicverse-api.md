# omicverse API 速查（实测自本机已装版本）

环境：`{root}/envs/omicverse` · Python 3.13.15 · omicverse 2.3.2
（scanpy 1.12.4 / anndata 0.13.4 / matplotlib 3.11.2 随包安装）

**所有名字都是装完后 `dir()` 实测的，不是凭记忆写的。**
omicverse API 版本相关性强，若某名字报 `AttributeError` 先重新 `dir()` 再改。

## 调用方式

```bash
# 直接调 exe
{root}/envs/omicverse/python.exe "<脚本.py>"
```

### ⚠️ 必须先解决 Windows GBK 控制台问题

omicverse 内部会 print emoji，Windows 控制台默认 GBK 编码会让它在 `ov.pp.*` 调用中直接抛
`UnicodeEncodeError: 'gbk' codec can't encode character` 并中断流程。

**脚本最前面（必须在 `import omicverse` 之前）：**

```python
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
```

**或调用时加环境变量**：`PYTHONIOENCODING=utf-8 .../python.exe script.py`

---

## 顶层模块（实测 49 个公开名）

```
数据/IO   : read  io  concat  datasets  datacollect
预处理    : pp
绘图      : pl  plot_set  ov_plot_set  palette  style
分析      : tl  single  bulk  bulk2single  space  micro  metabol  protein
            airr  epi  genetics  flow  mol  alignment  synbio
工具      : utils  report  settings  external
Agent     : Agent  agent  llm  mcp
          list_functions  find_function  get_function_help
          recommend_function  list_supported_models
          load_package  export_registry  import_registry
```

**注意 `list_functions` / `get_function_help`** —— omicverse 自带函数检索，比翻文档快：

```python
import omicverse as ov
ov.list_functions()                    # 列出全部
ov.find_function("umap")               # 按关键词找
ov.get_function_help("ov.pp.qc")       # 看某个函数的用法
ov.recommend_function("聚类")           # 按自然语言推荐
```

---

## `ov.pp` —— 预处理（实测 34 个公开函数）

```
QC      : qc  qc_metrics  filter_cells  filter_genes  identify_robust_genes
归一化  : normalize_total  log1p  scale  regress  regress_and_scale
          normalize_pearson_residuals  recover_counts
特征    : highly_variable_genes  highly_variable_features  select_hvf_pegasus
降维    : pca  tsne  umap  mde  sude  neighbors
聚类    : leiden  louvain
去双胞  : scrublet  scrublet_simulate_doublets
细胞周期: score_genes_cell_cycle  remove_cc_genes
其他    : ambient  champ  load_pumap  anndata_to_GPU  anndata_to_CPU
```

### 实测签名（2.3.2，直接抄即可）

```python
ov.pp.pca(adata, n_pcs=50, layer='scaled', inplace=True, random_state=...)
ov.pp.neighbors(adata, n_neighbors=15, n_pcs=None, use_rep=None, knn=True, method='umap', metric='euclidean', ...)
ov.pp.umap(adata, *, min_dist=0.5, spread=1.0, n_components=2, ...)
ov.pp.scale(adata, max_value=10, layers_add='scaled', to_sparse=False, ...)
ov.pp.preprocess(adata, mode='shiftlog|pearson', target_sum=500000.0, n_HVGs=2000, organism='human', ...)
ov.pp.qc(adata, *, mode='seurat', min_cells=3, min_genes=200, nmads=5, doublets=True, ...)
ov.pp.highly_variable_genes(adata, n_top_genes=2000)
```

### ⚠️ 三个实测踩到的坑

**1. 参数名是 `n_pcs`，不是 scanpy 的 `n_comps`。**

```python
ov.pp.pca(adata, n_comps=10)   # 错：TypeError: got multiple values for 'n_comps'
ov.pp.pca(adata, n_pcs=10)     # 对
```

**2. `ov.pp.pca` 默认读 `layer='scaled'`**，所以要先 `ov.pp.scale(adata)`（它写入 `layer='scaled'`），否则报找不到 layer。

**3. 不要在全部基因上直接做 PCA。** 实测在 38 x 26695 的完整矩阵上 `ov.pp.pca` 抛 **MemoryError**。
标准做法是先筛高变基因：

```python
ov.pp.highly_variable_genes(adata, n_top_genes=2000)
adata = adata[:, adata.var["highly_variable"]].copy()
ov.pp.scale(adata)
ov.pp.pca(adata, n_pcs=10)
```

### 完整可跑流程（已实测通过）

```python
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # 见上面的 GBK 说明

import omicverse as ov
import numpy as np, pandas as pd

X = pd.read_csv("counts_tpm.tsv", sep="\t", index_col=0).T.astype("float32")
adata = ov.AnnData(X=X, var=pd.DataFrame(index=X.columns))

ov.pp.normalize_total(adata, target_sum=1e4)
ov.pp.log1p(adata)
ov.pp.highly_variable_genes(adata, n_top_genes=2000)
adata = adata[:, adata.var["highly_variable"]].copy()
ov.pp.scale(adata)
ov.pp.pca(adata, n_pcs=10, layer="scaled")
ov.pp.neighbors(adata, n_neighbors=10, n_pcs=10)
ov.pp.umap(adata)
# 结果在 adata.obsm["X_umap"] / ["X_pca"]，adata.uns["pca"]["variance_ratio"]
```

**注意**：`scanpy` 的绘图函数签名与 omicverse 的不完全兼容。实测 `sc.pl.pca_variance_ratio(..., ax=...)` 不接受 `ax` 参数——要用子图就手动画（`adata.uns["pca"]["variance_ratio"]` 自己 bar）。

**通用原则**：`ov.pp` 的函数签名随版本变化较大，用前先 `ov.get_function_help("ov.pp.preprocess")` 或 `inspect.signature()` 确认真实参数名，不要凭 scanpy 的习惯写。

---

## `ov.pl` —— 绘图（体量很大）

实测包含通用绘图 + 期刊版面常量：

```
期刊相关 : JOURNAL_WIDTH_MM  EDITABLE_TEXT_RCPARAMS  PanelFlow  add_panel_label
通用     : barplot  boxplot  cellproportion  adjust_text  add_stat_annotation
          add_density_contour  add_arrow  ObsView  ConvexHull
单细胞   : ccc_heatmap  ccc_network_plot  cell_cor_heatmap  cell_fate
          cellrank_macrostate  Streamlines  branch_streamplot
配色     : palette  blue_color  Forbidden_Cmap  Forbiddencity
```

`JOURNAL_WIDTH_MM` 是个**期刊栏宽常量表**，配合 `PanelFlow`（多面板编排）使用，是 omicverse 里最接近"顶刊版式"的部分。

风格设置：

```python
ov.plot_set()          # 应用 omicverse 的绘图主题
# 或
ov.ov_plot_set()
```

---

## 组学分析模块

| 模块 | 用途 |
|---|---|
| `ov.single` | 单细胞：降维聚类、细胞通讯、轨迹、拟时序、代谢 |
| `ov.bulk` | 转录组差异表达与富集分析 |
| `ov.space` | 空间转录组 |
| `ov.bulk2single` | bulk 反卷积到单细胞 |
| `ov.micro` | 微生物组 |
| `ov.metabol` | 代谢组 |
| `ov.protein` | 蛋白组 |
| `ov.genetics` | 遗传/变异 |

各模块内部函数未逐一实测，用前先 `dir()`：

```python
import omicverse as ov
print([x for x in dir(ov.single) if not x.startswith("_")])
```

---

## 与 figkit 的分工

omicverse 环境里**也有 scanpy / anndata / matplotlib**，所以它本身就能画单细胞图。但：

- **要"顶刊风格单图"** → 用 figkit 的 cnsplots（版式更贴期刊，图型更全）
- **要做单细胞分析流程 + 顺带出图** → 用 omicverse（分析出图一条龙）
- **要 SCpubr 那种 publication-ready 单细胞图** → 用 R 环境

三个环境都装着 anndata 生态，**数据通过 `.h5ad` 文件在环境间传递**，不要在同一个脚本里跨环境 import。

---

## 未验证项（诚实标注）

以下**未做端到端实测**，用前先自测：

- `ov.single` / `ov.space` / `ov.bulk` 等子模块的具体函数行为
- `load_pumap`（需要额外下载模型）
- Agent / llm / mcp 相关功能（需要 API key）
- GPU 相关函数（`anndata_to_GPU` 等，本机是 CPU 环境）

已实测可用：`import omicverse`、`ov.pp` 的 34 个函数可枚举、版本正常。
