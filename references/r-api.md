# R 环境 API 速查（实测自本机已装版本）

环境：`{root}/R` · **R 4.6.1（CRAN 官方安装器）** · 库路径 `{root}/R/library`

**所有函数名都是装完后用 `getNamespaceExports()` 实测得到的，不是凭记忆写的。**

## 调用方式

```bash
# 单行表达式
{root}/R/bin/Rscript.exe -e 'library(ggsci); print(pal_npg()(5))'

# 多行代码 —— 必须落 .R 文件
{root}/R/bin/Rscript.exe "分析.R"
```

**不需要激活，不需要 `conda run`。** 两条约束：

1. **`-e` 只放单行。** 多行塞进 `-e` 会被 shell 与 R 的引号处理吃掉。
2. **装包必须带 `lib="{root}/R/library"`**，否则可能落到用户 AppData 目录。

（**历史**：R 曾用 conda 装，那时必须走 `conda run -p` 且 `-e` 完全不接受多行。改用官方 R 后两条约束都消失了。原因见 `envs.md`。）

---

## ggplot2 4.0.3

标准用法。注意 ggplot2 4.x 相比 3.x 有破坏性变更（如 `linewidth` 取代 `size`、`theme()` 元素继承规则变化），若报错先查是否为 3.x 的老写法。

```r
library(ggplot2)
p <- ggplot(df, aes(x, y, color = group)) +
  geom_point(size = 2) +
  labs(title = "标题", x = "X 轴", y = "Y 轴") +
  theme_classic(base_size = 9)
ggsave("out.png", p, width = 89, height = 60, units = "mm", dpi = 300)
```

**中文必须显式设字体**，见 `fonts.md`。

---

## ggsci 5.2.0 —— 期刊配色

实测 31 个色板函数：

```r
library(ggsci)
pal_npg()      # Nature 系
pal_aaas()     # Science 系
pal_lancet()   # Lancet
pal_nejm()     # NEJM
pal_jama()     # JAMA
pal_bmj()      # BMJ
pal_jco()      # JCO
pal_frontiers()# Frontiers
pal_cosmic()   # COSMIC
```

完整列表（实测）：`pal_npg pal_aaas pal_nejm pal_lancet pal_jama pal_bmj pal_jco pal_frontiers pal_cosmic pal_ucscgb pal_igv pal_locuszoom pal_d3 pal_uchicago pal_startrek pal_tron pal_futurama pal_rickandmorty pal_simpsons pal_flatui pal_atlassian pal_observable pal_material pal_gephi pal_primer pal_gsea pal_iterm pal_bs5 pal_tw3`

用于 ggplot：

```r
scale_color_npg()        # 或 scale_fill_npg()
scale_color_aaas()
```

取色值：

```r
pal_npg()(5)             # 取 5 个颜色的十六进制值
```

---

## ComplexHeatmap 2.26.1 —— 热图 / oncoprint

实测主要导出：

```
Heatmap  HeatmapAnnotation  rowAnnotation  columnAnnotation
oncoPrint  draw  anno_*（20+ 种：anno_barplot anno_boxplot anno_density
anno_points anno_simple anno_summary anno_oncoprint_barplot ...）
```

基本用法：

```r
library(ComplexHeatmap)
set.seed(1)
mat <- matrix(rnorm(200), 20, 10)
Heatmap(mat, name = "value",
        cluster_rows = TRUE, cluster_columns = TRUE,
        row_split = rep(c("A","B"), 10))   # 行分割
```

带注释：

```r
ha <- HeatmapAnnotation(group = c("ctrl","trt"))
Heatmap(mat, name = "value", top_annotation = ha)
```

oncoprint（突变瀑布图，唯一成熟实现）：

```r
oncoPrint(mat_of_mutations, alter_fun = alter_fun, col = col)
```

**注意**：ComplexHeatmap 必须 `draw()` 才渲染；`ggsave` 不适用于它，要用设备函数包裹：

```r
ragg::agg_png("out.png", width = 178, height = 120, units = "mm", res = 300)
draw(ht)
dev.off()
```

---

## SCpubr 3.0.1 —— 单细胞出版级图

实测 **34 个 `do_*` 函数**：

| 类别 | 函数 |
|---|---|
| 降维 | `do_DimPlot` `do_FeaturePlot` `do_NebulosaPlot` |
| 表达 | `do_ViolinPlot` `do_DotPlot` `do_BoxPlot` `do_BarPlot` `do_RidgePlot` `do_BeeSwarmPlot` `do_StripPlot` |
| 热图 | `do_ExpressionHeatmap` `do_CorrelationHeatmap` `do_MetadataHeatmap` `do_SCExpressionHeatmap` `do_GroupwiseDEHeatmap` `do_LoadingsHeatmap` `do_CNVHeatmap` `do_ActivityHeatmap` `do_TFActivityHeatmap` |
| 富集 | `do_TermEnrichmentPlot` `do_EnrichmentHeatmap` `do_RankedEnrichmentHeatmap` `do_SCEnrichmentHeatmap` `do_PathwayActivityHeatmap` |
| 其他 | `do_AlluvialPlot` `do_ChordDiagramPlot` `do_LigandReceptorPlot` `do_WafflePlot` `do_CellularStatesPlot` `do_VolcanoPlot` |
| 工具 | `do_ColorPalette` `do_ColorBlindCheck` `do_PackageReport` |

典型流程：

```r
library(Seurat)
library(SCpubr)

obj <- NormalizeData(obj) |> FindVariableFeatures() |> ScaleData() |>
       RunPCA() |> RunUMAP(dims = 1:20)

p <- SCpubr::do_DimPlot(obj, reduction = "umap", group.by = "celltype")
ggsave("umap.png", p, width = 89, height = 80, units = "mm", dpi = 300)
```

**重要：SCpubr 的 CRAN DESCRIPTION 把 Seurat、ggplot2、ComplexHeatmap 等都放在 `Suggests:` 而非 `Imports:`**，所以 `library(SCpubr)` 能成功但调用具体函数可能报 `there is no package called 'X'`。常用路径的依赖已装齐；遇到没覆盖的按 `troubleshooting.md` §1.4 补装。

**函数签名以实测为准**（SCpubr 2.x→3.x 有过破坏性重命名）：

```bash
{root}/R/bin/Rscript.exe -e "print(args(SCpubr::do_DimPlot))"
```

`do_PackageReport` 可以用来一次性检查 SCpubr 的依赖完整性。

---

## gggenomes 1.1.2 —— 基因组/基因结构图

**输入必须是 GFF3 + FASTA（或 GenBank）两个文件，缺一不可。**

实测主要导出：

```
读取：read_gff3  read_seqs  read_fai  read_gbk  read_bed  read_paf  read_blast  read_vcf
主函数：gggenomes
几何：geom_gene  geom_gene_label  geom_gene_text  geom_seq  geom_seq_label
      geom_link  geom_link_curved  geom_link_label  geom_feat  geom_coverage  geom_wiggle
轨道：track  feats  genes  seqs  links  bins  track_ids
主题：theme_gggenomes_clean
工具：flip  flip_seqs  focus  add_seqs  add_feats  add_links  pick  pick_seqs  qc
```

基本用法：

```r
library(gggenomes)
s <- read_seqs("genome.fna")       # FASTA
g <- read_gff3("genes.gff3")       # GFF3

gggenomes(seqs = s, genes = g) +
  geom_seq() +
  geom_gene(aes(fill = type)) +
  geom_gene_label(aes(label = name)) +
  theme_gggenomes_clean()
```

**注意：`gggenomes` 需要 GFF3。** 只有 FASTA 时必须先生成 GFF3。GFF3 是 9 列制表符分隔：
`seqid / source / type / start / end / score / strand / phase / attributes`

`read_fai` 可读 `.fai` 索引；若只有 FASTA，`read_seqs` 也能直接读并推算长度。

---

## Seurat 5.5.1

单细胞标准流程。注意本机装的是 **CRAN 二进制版本**（conda 的构建有 mingw 缺陷，已替换，见 `envs.md`）。

```r
library(Seurat)
obj <- CreateSeuratObject(counts = mat)
obj <- NormalizeData(obj) |> FindVariableFeatures() |> ScaleData() |>
       RunPCA() |> FindNeighbors(dims = 1:20) |> RunUMAP(dims = 1:20)
```

---

## 其他已装的常用包

`patchwork`（拼图）· `cowplot` · `ggpubr` · `ggrepel`（标签避让）· `ggh4x` · `ggbeeswarm` · `ggdist` · `ggalluvial` · `ggsignif`（显著性标注）· `scattermore`（散点栅格化）· `viridis` · `RColorBrewer` · `circlize` · `ggplotify` · `dplyr` / `tidyr` / `stringr` / `purrr` / `forcats`（数据处理）

**未安装**：`ggrastr`（依赖 `r-cairo`，而 conda 的 r-cairo 停在 r41，装不上）。需要散点栅格化请用 `scattermore`。
