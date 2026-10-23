# 配色方案（带预览的都在插件面板「配色」页）

写图代码时从这里取色，别临时拼。三种来源：**期刊官方色**（ggsci 同款）、**色盲安全**、
**连续色标**。十六进制均为 sRGB。

## 期刊 / 出版风格

| 名称 | 色数 | 十六进制 |
|---|---|---|
| **NPG**（Nature 系） | 10 | `#E64B35 #4DBBD5 #00A087 #3C5488 #F39B7F #8491B4 #91D1C2 #DC0000 #7E6148 #B09C85` |
| **Lancet** | 9 | `#00468B #ED0000 #42B540 #0099B4 #925E9F #FDAF91 #AD002A #ADB6B6 #1B1919` |
| **NEJM** | 8 | `#BC3C29 #0072B5 #E18727 #20854E #7876B1 #6F99AD #FFDC91 #EE4C97` |
| **JCO** | 10 | `#0073C2 #EFC000 #868686 #CD534C #7AA6DC #003C67 #8F7700 #3B3B3B #A73030 #4A6990` |
| **AAAS**（Science 系） | 10 | `#3B4992 #EE0000 #008B45 #631879 #008280 #BB0021 #5F559B #A20056 #808180 #1B1919` |

R 里直接 `ggsci::scale_color_npg()` / `scale_fill_lancet()` 等；Python 里手填十六进制。

## 色盲安全

| 名称 | 色数 | 十六进制 |
|---|---|---|
| **Okabe-Ito** | 8 | `#000000 #E69F00 #56B4E9 #009E73 #F0E442 #0072B2 #D55E00 #CC79A7` |

红绿色盲下仍可区分，黑白打印也分得开。**分类数 ≤ 8 时的默认选择**。

## 通用分类

| 名称 | 色数 | 十六进制 |
|---|---|---|
| **Tableau 10** | 10 | `#4E79A7 #F28E2B #E15759 #76B7B2 #59A14F #EDC948 #B07AA1 #FF9DA7 #9C755F #BAB0AC` |
| **tab10**（matplotlib 默认） | 10 | `#1f77b4 #ff7f0e #2ca02c #d62728 #9467bd #8c564b #e377c2 #7f7f7f #bcbd22 #17becf` |

## 连续色标

| 名称 | 5 个采样点（近似） | 用在哪 |
|---|---|---|
| **viridis** | `#440154 #3b528b #21918c #5ec962 #fde725` | 默认连续量（感知均匀、色盲安全） |
| **cividis** | `#00224e #123570 #3b496c #7d7d6e #f1e6b2` | 更强的色盲安全版本 |
| **magma** | `#000004 #3b0f70 #8c2981 #de4968 #fe9f6d #fcfdbf` | 热图（暗底亮高） |
| **inferno** | `#000004 #420a68 #932667 #dd513a #fca50a #fcffa4` | 热图，对比更强 |
| **RdBu**（发散） | `#67001f #d6604d #f7f7f7 #4393c3 #053061` | 有正负/中心的数据（z-score、log2FC） |

Python 直接用库里的名字：`cmap="viridis"` / `cmcrameri.cm.batlow`；R 用 `scale_fill_viridis_c()`。

## 三条规矩

1. **分类 ≤ 8 用 Okabe-Ito**，再多就换期刊色板（超过 10 类考虑合并或分面）。
2. **发散数据必须用发散色标**（RdBu / coolwarm），别用 viridis —— 零点会被画成中间色而不是"无"。
3. **同一篇文章里同一分组用同一个颜色**，跨图复用同一个列表，别每张图重选。

## 色板从哪来：四个配色 mod（已装）

| mod | 语言 | 能给什么 |
|---|---|---|
| **paletteer** | R | 2545 个离散色板，`包名::色板名` 统一调用 |
| **khroma** | R | 35 套科学色板 + **色盲模拟检查** |
| **colorcet** | Python | 210 个感知均匀色图（CET 系列） |
| **palettable** | Python | ColorBrewer / CartoColors，直接给十六进制与 colormap |

**命名坑**：paletteer 里 ggsci 的色板带前缀 —— `ggsci::nrc_npg`、`ggsci::lanonc_lancet`、
`ggsci::default_nejm`、`ggsci::default_jco`、`ggsci::default_aaas`（不是 `ggsci::npg`）。
写错会报 `not found`，不会静默给错色。

面板「配色」页里的色块是构建时写死的；新装配色 mod **不会自动出现在面板里**，
但模型可以按 mod 的 `docs.md` 直接调用。要出现在面板，得改 `client.js` 后重建。
