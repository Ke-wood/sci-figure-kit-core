# 装环境

这个 skill 不自带 Python/R，也不要求装到固定盘符。**装到哪里由你在第一条命令里定**，
而且**能复用你已有的 R / Python / conda 时就不重复装**。

## 一条命令

```bash
python install/bootstrap.py --root <你选的位置>      # 默认 D:/app（POSIX 是 ~/.sci-fig）
```

它做三件事：建 figkit 的 venv、准备 R、建 omicverse 环境。三套互相独立，
哪套失败只影响哪套，可以 `--only figkit|r|omicverse` 单独补。

## 已经有 R 怎么办（不会重复装）

默认 `--r-mode auto`：**先找机器上已有的 Rscript**（`RSCRIPT` / `R_HOME` / PATH /
常见安装目录），找到就复用它 —— 不下载安装器、不装第二套 R。
只是把包装进一个**独立库**（`<root>/R/library`），不动你原来的 library。

```bash
# 它找到了，就会这样打印
#   复用已有 R：C:/Program Files/R/R-4.6.1/bin/Rscript.exe（不下载、不安装第二套 R）
#   包只装到独立库：<root>/R/library（不写你原有的 library）
```

显式指定或强制：

```bash
python install/bootstrap.py --root X --r-mode reuse --r-path "C:/Program Files/R/R-4.6.1/bin/Rscript.exe"
python install/bootstrap.py --root X --r-mode install    # 我就想要一套独立的
```

复用的实现方式：所有 R 调用都带 `R_LIBS=<root>/R/library`，于是 `.libPaths()` 里
独立库排在用户库前面，同名包不会被你个人装的那份抢先。

## 下载源：自己选，不用改代码

三套环境都要联网拉东西。默认走官方源，国内或内网一条命令换镜像：

```bash
python install/bootstrap.py --root ~/sci-fig --source tuna     # 清华
python install/bootstrap.py --root ~/sci-fig --source ustc     # 中科大
python install/bootstrap.py --root ~/sci-fig --source aliyun   # 阿里云
python install/bootstrap.py --list-sources                     # 看全部预设
```

| 预设 | pip | CRAN（R 包） | Bioconductor | conda |
|---|---|---|---|---|
| `official` | pip 自己的配置 | cloud.r-project.org | bioconductor.org | conda-forge |
| `tuna` | 清华 PyPI | 清华 CRAN | 清华 Bioc | 清华 conda-forge |
| `ustc` | 中科大 PyPI | 中科大 CRAN | 中科大 Bioc | conda-forge |
| `aliyun` | 阿里云 PyPI | 阿里云 CRAN | 官方（阿里云没有 Bioc 镜像） | conda-forge |

只想换其中一项：

```bash
--pip-index https://...        # 只换 pip 索引
--cran-mirror https://...      # 只换 CRAN
--bioc-mirror https://...      # 只换 BiocManager 的镜像根
--conda-channel conda-forge    # 只换 conda 频道（可重复）
--offline-dir D:/bundle        # 完全离线，见下
```

也可以用环境变量，命令一个字不用改：

```
SCI_FIG_SOURCE=tuna
SCI_FIG_PIP_INDEX / SCI_FIG_CRAN / SCI_FIG_BIOC / SCI_FIG_CONDA_CHANNELS
SCI_FIG_OFFLINE_DIR
```

你选的结果会写进 `envs.json`（`source_preset` + `sources`），**重跑时沿用**；
装 mod 时也用同一套源（`python scripts/mod.py sources` 查看，`mod.py sources tuna` 切换）。

> `official` 预设对 pip 是「不传 `--index-url`」，也就是**尊重你自己的
> `PIP_INDEX_URL` / `pip.ini`**。只有你显式选了镜像，我们才覆盖。

### R 版本不写死

CRAN 的 `bin/windows/base/` 只保留**最新一版**安装器，写死版本号隔几周就 404
（`R-4.6.1-win.exe` 已经 404 了，目录里现在只有 4.6.2）。所以默认**现查目录取最新**，
查不到才退回内置兜底值；要钉版本用 `--r-version 4.6.2`。

### 离线 / 自包含

`--offline-dir <dir>` 之后不联网，目录要长这样：

```
<dir>/wheels/*.whl     pip 用 --no-index --find-links
<dir>/cran/            一个 CRAN 仓库：bin/windows/contrib/4.x/ 与 src/contrib/
```

准备方法（**在目标平台上跑**，否则 `pip download` 会抓到别的平台的 wheel）：

```bash
pip download -r requirements-figkit.txt -d <dir>/wheels
# R：
#   download.packages(c("ggplot2","Seurat"), destdir="<dir>/cran/src/contrib",
#                     repos="https://cloud.r-project.org", type="win.binary")
```

## Python 与 conda

- **Python**：只用来建 venv，不下载解释器（用你现有的 `python`）；
- **conda**：用你现有的 conda 建一个 prefix，不覆盖 base 环境；
- 没有 conda 就跳过 omicverse，`--only omicverse` 之后补。

## 落点

```
<root>/envs/figkit       Python venv（cnsplots / SciencePlots / cmcrameri / marsilea）
<root>/R                 官方 CRAN R + 包（复用模式下只有 library/ 是自己的）
<root>/envs/omicverse    conda prefix + omicverse
<root>/envs/_mods        mod 拉下来的第三方代码
<root>/envs/envs.json    机器本地注册表
```

同时会在 **skill 目录**写一份 `envs.json`，所以 skill 搬到哪台机器都认这套路径。

## 装完

```bash
python scripts/check_envs.py      # 期望 11 PASS / 0 FAIL
```

`R 库隔离` 那项检查的是「独立库是否排在用户库前面」，不是「你有没有装过 R」。

## 常见失败

| 症状 | 处理 |
|---|---|
| `找不到 Python ≥3.10` | 装官方 Python 并勾选 Add to PATH |
| `WinError 5 ... pip\cache` 或 `failed-wheel-build-for-install` | pip 的缓存目录不可写（受控机器、只读 profile、沙箱）。`PIP_NO_CACHE_DIR=1` 重跑即可 |
| R 复用后包找不到 | 确认 `envs.json` 里 `r_lib` 指向独立库；所有 R 调用都应带 `R_LIBS` |
| 没有 conda | 跳过 omicverse，或装 Miniconda 后 `--only omicverse` |
| 想彻底重来 | 删掉 `<root>` 与 skill 目录下的 `envs.json`，重跑 |

## 非 Windows

`figkit` 在 Linux/macOS 同样可用。R 用系统包管理器装好后：

```bash
python install/bootstrap.py --root ~/sci-fig --r-mode reuse --r-path "$(which Rscript)"
```
