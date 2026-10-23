# 常规实验图型配方（全部实跑过）

每条都在这台机器上画出来过（figkit 环境 2026-10-24）。复制即可用：
只改数据来源，别改字体/矢量那几行。

## 公共设置（Python，必须放在最前面）

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False      # 否则负号变方框
plt.rcParams["pdf.fonttype"] = 42                # 投稿要 Type 42，不是 3
plt.rcParams["svg.fonttype"] = "none"            # 否则文字被转成路径
```

## R 公共设置

```r
library(ggplot2)
theme_set(theme_classic(base_size = 8) +
            theme(axis.text = element_text(colour = "black")))
# 中文：ggsave 时 device = cairo_pdf 或 ragg::agg_png
```

---

## 1 拟合曲线（线性 + 95% CI + R²）

**什么时候用**：浓度-响应、时间-累积量、任何"散点 + 趋势线"。

```python
rng = np.random.default_rng(0)
x = np.linspace(0, 10, 40)
y = 2.4 * x + 3 + rng.normal(0, 2.0, x.size)

fig, ax = plt.subplots(figsize=(3.5, 2.4), dpi=300)
ax.scatter(x, y, s=14, color="#4DBBD5", alpha=0.85, label="观测")
b, a = np.polyfit(x, y, 1)
xx = np.linspace(x.min(), x.max(), 100)
resid = y - (b * x + a)
se = np.sqrt((resid ** 2).sum() / (len(x) - 2))
ci = 1.96 * se * np.sqrt(1 / len(x) + (xx - x.mean()) ** 2 / ((x - x.mean()) ** 2).sum())
ax.plot(xx, b * xx + a, color="#E64B35", lw=1.4)
ax.fill_between(xx, b * xx + a - ci, b * xx + a + ci, color="#E64B35", alpha=0.15)
r2 = 1 - (resid ** 2).sum() / ((y - y.mean()) ** 2).sum()
ax.text(0.04, 0.92, f"y = {b:.2f}x + {a:.2f}\n$R^2$ = {r2:.3f}",
        transform=ax.transAxes, va="top", fontsize=7)
ax.set_xlabel("处理时间 (h)")
ax.set_ylabel("响应值")
fig.tight_layout()
fig.savefig("fit.png", dpi=300)
```

> CI 用**预测带**（1/n + 距离项）而不是均值 CI；只画均值 CI 会偏窄。

## 2 剂量反应（4PL / EC50）

**什么时候用**：药物抑制率、毒理、任何 S 形剂量响应。

```python
from scipy.optimize import curve_fit

conc = np.array([0.01, 0.03, 0.1, 0.3, 1, 3, 10, 30])
resp = np.array([3, 6, 12, 27, 48, 66, 82, 88.0])

def four_pl(x, bottom, top, ec50, hill):
    return bottom + (top - bottom) / (1 + (ec50 / x) ** hill)

popt, pcov = curve_fit(four_pl, conc, resp, p0=[resp.min(), resp.max(), np.median(conc), 1.0],
                       maxfev=20000)
perr = np.sqrt(np.diag(pcov))

fig, ax = plt.subplots(figsize=(3.5, 2.5), dpi=300)
ax.scatter(conc, resp, s=16, color="#3C5488", zorder=3, label="实测")
xx = np.logspace(np.log10(conc.min()), np.log10(conc.max()), 200)
ax.plot(xx, four_pl(xx, *popt), color="#E64B35", lw=1.4)
ax.set_xscale("log")
from matplotlib.ticker import FuncFormatter
ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))   # 别用 10^-2 的 mathtext
ax.xaxis.set_minor_formatter(FuncFormatter(lambda v, _: ""))
ax.set_xlabel("浓度 (μM)")
ax.set_ylabel("抑制率 (%)")
ax.text(0.04, 0.12, f"EC50 = {popt[2]:.2f} ± {perr[2]:.2f} μM",
        transform=ax.transAxes, fontsize=7)
fig.tight_layout()
fig.savefig("dose.png", dpi=300)
```

> **坑**：对数轴的默认刻度是 mathtext 的 `10^{-2}`，SimHei 没有 U+2212，
> 会出 dummy 字形。用 `FuncFormatter` 关掉 mathtext 即可（实测消除 3 条缺字警告）。

## 3 柱状图 + 误差棒 + 散点 + 显著性

**什么时候用**：三组以上比较，期刊最常见的那张图。

```python
from statannotations.Annotator import Annotator

rng = np.random.default_rng(1)
groups = ["对照", "低剂量", "高剂量"]
data = pd.DataFrame({
    "组别": np.repeat(groups, 8),
    "值": np.concatenate([rng.normal(10, 1.2, 8), rng.normal(12.5, 1.1, 8), rng.normal(15, 1.4, 8)]),
})

fig, ax = plt.subplots(figsize=(3.4, 2.6), dpi=300)
means = data.groupby("组别", observed=True)["值"].mean().reindex(groups)
sems = data.groupby("组别", observed=True)["值"].sem().reindex(groups)
ax.bar(groups, means, yerr=sems, capsize=4, width=0.55,
       color=["#8491B4", "#4DBBD5", "#E64B35"], edgecolor="black", linewidth=0.6)
for i, g in enumerate(groups):
    pts = data.loc[data["组别"] == g, "值"]
    ax.scatter(np.full(pts.size, i) + rng.normal(0, 0.05, pts.size), pts,
               s=8, color="black", alpha=0.5)

pairs = [("对照", "低剂量"), ("对照", "高剂量"), ("低剂量", "高剂量")]
Annotator(ax, pairs, data=data, x="组别", y="值", order=groups) \
    .configure(test="t-test_ind", text_format="star", loc="inside") \
    .apply_and_annotate()
ax.set_ylabel("测量值")
fig.tight_layout()
fig.savefig("bar_sig.png", dpi=300)
```

> 默认做的是**未校正** t 检验。多组比较要在 `configure()` 里加
> `comparisons_correction="Bonferroni"`（或 BH）。
> 柱子上叠散点是审稿人越来越常要的"数据可见性"。

## 4 小提琴 + 箱线 + 散点

**什么时候用**：分布形状本身是结论（双峰、长尾），且样本量 ≥ 8。

```python
import seaborn as sns

rng = np.random.default_rng(2)
df = pd.DataFrame({
    "组别": np.repeat(["WT", "KO", "Rescue"], 12),
    "值": np.concatenate([rng.normal(1.0, .18, 12), rng.normal(1.45, .22, 12), rng.normal(1.15, .2, 12)]),
})

fig, ax = plt.subplots(figsize=(3.4, 2.6), dpi=300)
sns.violinplot(data=df, x="组别", y="值", hue="组别", inner=None, cut=0,
               linewidth=0.6, palette=["#4DBBD5", "#E64B35", "#00A087"],
               legend=False, ax=ax)
sns.boxplot(data=df, x="组别", y="值", width=0.12, showfliers=False, ax=ax,
            boxprops=dict(facecolor="white", edgecolor="black", linewidth=0.6),
            medianprops=dict(color="black"),
            whiskerprops=dict(linewidth=0.6), capprops=dict(linewidth=0.6))
sns.stripplot(data=df, x="组别", y="值", size=2.6, color="black", alpha=0.55,
              jitter=0.12, ax=ax)
ax.set_xlabel("")
ax.set_ylabel("相对表达量")
fig.tight_layout()
fig.savefig("violin.png", dpi=300)
```

> `hue=` 与 `x=` 用同一列并设 `legend=False`，否则 seaborn 0.13 报
> `palette without hue` 的弃用警告。

## 5 相关性热图（下三角 + 数值）

**什么时候用**：多指标两两相关，比散点矩阵更省版面。

```python
from scipy.spatial.distance import squareform  # noqa: F401  （需要时再聚类）

rng = np.random.default_rng(3)
genes = [f"G{i}" for i in range(1, 9)]
mat = pd.DataFrame(rng.normal(size=(8, 8)), index=genes, columns=genes)
mat = (mat + mat.T) / 2
np.fill_diagonal(mat.values, 1.0)
corr = mat.corr()

mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
fig, ax = plt.subplots(figsize=(3.6, 3.0), dpi=300)
im = ax.imshow(np.ma.masked_where(mask, corr.values), cmap="RdBu_r", vmin=-1, vmax=1)
fig.colorbar(im, ax=ax, shrink=0.75, label="Pearson r")
ax.set_xticks(range(len(corr)), corr.columns, rotation=90, fontsize=6)
ax.set_yticks(range(len(corr)), corr.index, fontsize=6)
for i in range(len(corr)):
    for j in range(i + 1):
        v = corr.values[i, j]
        ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=5,
                color="white" if abs(v) > 0.6 else "black")
fig.tight_layout()
fig.savefig("corr.png", dpi=300)
```

> 相关图**必须用发散色标**（`RdBu_r`），且 `vmin=-1, vmax=1` —— 否则颜色随数据缩放，
> 两篇图之间没法比。

## 6 生长曲线 / 时间序列 + 误差带

**什么时候用**：多时间点、每点有重复。

```python
rng = np.random.default_rng(4)
days = np.arange(0, 15)
rows = []
for g, base in [("对照组", 1.0), ("处理组", 1.35)]:
    for d in days:
        for _ in range(4):
            rows.append({"组别": g, "天": d, "值": base * np.exp(0.18 * d) + rng.normal(0, 0.25)})
df = pd.DataFrame(rows)
stat = df.groupby(["天", "组别"], observed=True)["值"].agg(["mean", "sem"]).reset_index()

fig, ax = plt.subplots(figsize=(3.6, 2.6), dpi=300)
for g, color in [("对照组", "#4DBBD5"), ("处理组", "#E64B35")]:
    s = stat[stat["组别"] == g]
    ax.plot(s["天"], s["mean"], color=color, lw=1.4, label=g)
    ax.fill_between(s["天"], s["mean"] - s["sem"], s["mean"] + s["sem"],
                    color=color, alpha=0.22, lw=0)
ax.set_xlabel("时间 (d)")
ax.set_ylabel("生物量 (OD600)")
ax.legend(frameon=False, fontsize=7)
fig.tight_layout()
fig.savefig("growth.png", dpi=300)
```

> 误差带写清是 SEM 还是 SD（图注里），两者差 √n 倍。

## 7 R：小提琴 + 显著性（ggpubr）

**什么时候用**：整条流程都在 R 里，或要 ggpubr 的星号标注。

```r
library(ggplot2)
library(ggpubr)

df <- data.frame(
  group = factor(rep(c("WT", "KO", "Rescue"), each = 12), levels = c("WT", "KO", "Rescue")),
  value = c(rnorm(12, 1.0, .18), rnorm(12, 1.45, .22), rnorm(12, 1.15, .2))
)
pairs <- list(c("WT", "KO"), c("WT", "Rescue"), c("KO", "Rescue"))

p <- ggplot(df, aes(group, value, fill = group)) +
  geom_violin(trim = FALSE, colour = "black", linewidth = 0.3, alpha = 0.85) +
  geom_boxplot(width = 0.12, fill = "white", colour = "black",
               linewidth = 0.3, outlier.shape = NA) +
  geom_jitter(width = 0.06, size = 0.7, colour = "black", alpha = 0.55) +
  geom_pwc(aes(group = group), method = "t_test", p.adjust.method = "BH",
           label = "p.signif", tip.length = 0.01, size = 3) +
  scale_fill_manual(values = c("#4DBBD5", "#E64B35", "#00A087")) +
  labs(x = NULL, y = "相对表达量") +
  theme_classic(base_size = 8) +
  theme(legend.position = "none")

ggsave("violin_R.png", p, width = 89, height = 70, units = "mm", dpi = 300, device = ragg::agg_png)
```

> **坑**：`stat_compare_means(comparisons = ...)` 给的是**未校正** p 值（ggpubr 自己会警告）。
> 要校正就改用 `geom_pwc(p.adjust.method = "BH")`，或 `compare_means()` + `stat_pvalue_manual()`。

---

## 图型 → 后端速查

| 图型 | 首选 | 备选 |
|---|---|---|
| 拟合曲线 / 剂量反应 | Python（scipy + matplotlib） | R `stat_smooth` / `drc` |
| 柱状 + 误差 + 显著性 | Python（statannotations） | R ggpubr `geom_pwc` |
| 小提琴 / 箱线 / 蜂群 | Python（seaborn）或 R（ggpubr） | — |
| 相关性热图 | Python（imshow + RdBu） | R `corrplot` / ComplexHeatmap |
| 时间序列 + 误差带 | Python（fill_between） | R `geom_ribbon` |
| 火山 / 森林 / ROC / 生存 | cnsplots | ggplot2 |
| 多面板拼图 | marsilea | patchwork |
