# 故障排查

按"最可能先遇到"排序。每条给症状 → 根因 → 修法。

---

## 1. R 相关

### 1.0 最重要的一条：R 必须是官方 CRAN 版，不能是 conda 版

**症状**：

```
Mingw-w64 runtime failure:
32 bit pseudo relocation at 00007FFD... out of range, targeting 00007FFC..., ...
```

加载 Seurat / SeuratObject 时报这个，**且时好时坏**（同一命令连跑 6 次可能全失败，也可能偶尔通过）。

**根因**：conda-forge 的 R 环境混装两套 mingw 工具链——`m2w64-sysroot`（MSVCRT）与 `mingw-w64-ucrt-x86_64`（UCRT）——而 R 本身是 UCRT 构建。落在错误一侧的 `.dll` 触发伪重定位溢出。

**修法**：**换官方 CRAN 安装器重装 R**。完整证据链和排查过程见 `envs.md` 的"为什么不用 conda 装 R"。

```bash
{root}/R/bin/Rscript.exe -e 'cat(R.version.string)'
# 应输出 4.6.x (ucrt) 且来自官方安装器
```

**不要试图用 CRAN 二进制去覆盖 conda R 里的坏包** —— 那会引入第二套 mingw 运行时（conda 的 `libstdc++-6.dll` 有 30 MB），冲突比原来更严重。这条路我试过，是错的。

### 1.1 `ComplexHeatmap` 在 conda 上装不上

**症状**：`conda create ... bioconductor-complexheatmap` 报
`bioconductor-iranges >=2.44.0,<2.45.0 ... does not exist`。

**根因**：bioconda 的 Bioconductor **基础设施**包没有 win-64 构建：

| 包 | 可用平台 |
|---|---|
| `bioconductor-iranges` | osx-64 / linux-64 / linux-aarch64 / osx-arm64 —— **无 win-64** |
| `bioconductor-s4vectors` | 同上 |
| `bioconductor-genomicranges` | 同上 |

**修法**：用官方 R 后，直接从 Bioconductor 装 Windows 二进制（不需要编译器）：

```r
BiocManager::install("ComplexHeatmap", lib = "{root}/R/library",
                     ask = FALSE, update = FALSE)
```

**必须带 `lib=`** —— 不带可能装到 `%LOCALAPPDATA%\R\win-library`，那是本项目的禁止污染点。

### 1.2 `library(Seurat)` 报 DLL not found

**症状**：`unable to load shared object ... libstdc++-6.dll / libwinpthread-1.dll`，
或 `api-ms-win-crt-time-l1-1-0.dll: cannot open shared object file`。

**根因**：这是 **conda 版 R 特有**的问题——编译包依赖 `<prefix>/Library/bin` 里的 DLL，不激活就不在 PATH 上。

**修法**：换官方 CRAN 版 R（见 1.0）。官方版直调 `Rscript.exe` 即可，无需任何激活。

### 1.3 `-e` 的多行不生效；含 `| < > &` 的表达式报「系统找不到指定的路径」

**症状**：
- `Rscript.exe -e '多行代码'` 输出为空或报引号错误
- 单行也会挂：`Rscript.exe -e 'cat("a|b")'` → **退出码 255、stdout 为空、
  stderr 只有一句中文「系统找不到指定的路径。」**

**根因（两条，第二条很坑）**：

1. 多行字符串经过 Git Bash 与 Windows 参数传递后被吃掉。
2. **Windows 上 `Rscript.exe` 会把 `-e` 的表达式再过一遍 shell**，表达式里的
   `|`、`<`、`>`、`&` 于是被当成 shell 元字符解释掉。注意这**不是**调用方开没开
   shell 的问题 —— 实测用 `subprocess` 的 argv 列表（`shell=False`）照样复现。
   `|` 最隐蔽：它被当成管道，右侧被当成命令去执行，于是报「找不到路径」。

**修法**：**R 代码一律写成 `.R` 文件再传文件名**，不要用 `-e`：

```bash
{root}/R/bin/Rscript.exe "分析.R"
```

写成文件一次性绕开多行、引号、元字符三类问题。若确实要用 `-e`，至少保证
表达式里不出现 `| < > & ^ %`（例如用 `"\t"` 而不是 `"|"` 当分隔符）。

本 skill 的 `scripts/mod.py` 里所有 R 调用都走 `r_script()`（写临时 `.R` 文件），
就是为了绕开这一整类问题。

### 1.4 `library(SCpubr)` 成功，但调用函数报 `there is no package called 'X'`

**症状**：`do_DimPlot()` 之类抛缺包错。

**根因**：SCpubr 的 CRAN DESCRIPTION 把 Seurat、ggplot2、ComplexHeatmap、Nebulosa、infercnv、UCell、org.Hs.eg.db 等**全放在 `Suggests:` 而非 `Imports:`**，所以它不会自动拉依赖。

**修法**：常用绘图路径的依赖（Seurat / SeuratObject / ggplot2 / ComplexHeatmap）已装齐。遇到没覆盖的，按需补装：

```r
BiocManager::install("Nebulosa", lib = "{root}/R/library", ask = FALSE, update = FALSE)
```

先确认真实函数签名，不要凭记忆：

```bash
{root}/R/bin/Rscript.exe -e 'print(args(SCpubr::do_DimPlot))'
```

`SCpubr::do_PackageReport()` 可一次性检查依赖完整性。

### 1.5 R 包装到了用户目录

**症状**：`%LOCALAPPDATA%\R\win-library` 里出现包。

**根因**：`install.packages` / `BiocManager::install` 没带 `lib=`。

**修法**：一律带 `lib = "{root}/R/library"`。自检脚本的「R 库隔离」探针专门盯这个。

### 1.6 `ggrastr` 用不了

**症状**：装 `ggrastr` 时求解失败，或加载后报错。

**根因**：`ggrastr` 依赖 `r-cairo`，而 conda 的 `r-cairo` 停在 r41（R 4.1），与新版 R 不兼容。

**修法**：改用 `scattermore`（已装）做散点栅格化。

---

## 2. Python 相关

### 2.1 `cnsplots` 导入或画图失败，报 matplotlib 版本问题

**根因**：cnsplots 要求 `matplotlib<3.11,>=3.10`。有人在这个 venv 里跑了 `pip install -U matplotlib` 就会踩到。

**修法**：

```bash
{root}/envs/figkit/Scripts/python.exe -m pip install "matplotlib==3.10.8"
```

自检第 10 号探针专门盯着这条线。

### 2.2 中文显示成方框

见 `fonts.md`。两个最常见的漏项：
- matplotlib 忘了 `plt.rcParams["axes.unicode_minus"] = False` → 中文正常但**负号**变方框
- SciencePlots 忘了加 `no-latex` → 本机没装 LaTeX，直接报错

### 2.3 omicverse 报 `UnicodeEncodeError: 'gbk' codec can't encode character`

**症状**：

```
UnicodeEncodeError: 'gbk' codec can't encode character '\U0001f50d' in position 11
```

在 `ov.pp.normalize_total(...)` 之类的调用上直接中断。

**根因**：omicverse 内部会 `print` emoji（🔍 🖥️ 📊 等），而 Windows 控制台默认是 GBK 编码，编不出来就抛异常。

**修法（两选一，推荐都做）**：

```python
# 脚本最前面，必须在 import omicverse 之前
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
```

```bash
# 或者调用时设环境变量
PYTHONIOENCODING=utf-8 {root}/envs/omicverse/python.exe script.py
```

### 2.4 裸 `pip install` 打到了全局 Python

**症状**：用户发现全局 3.14.5 里多了一堆绘图库。

**根因**：没带绝对路径的 python。

**修法**：

```bash
# 全局 Python 里卸掉
<你的全局 Python 绝对路径> -m pip uninstall <包名>
```

**预防**：任何安装都必须写全 `{root}/envs/figkit/Scripts/python.exe -m pip install ...`。

---

## 3. 安装过程

### 3.1 看起来卡死了

**这大概率不是故障。** conda 装 R + Seurat 树要 10–30 分钟，omicverse 的 190+ 个 wheel 也要 10–30 分钟。

**判据**：看日志文件大小是否还在涨，或 `tasklist | grep python` 看进程是否还在。

**预防**：三个阶段分开跑，每段结束报一次进度。

### 3.2 `conda` 命令找不到 / 报 channel ToS

**根因**：`D:\app\ana\.condarc` 里是 `channels: [defaults]`。

**修法**：所有 conda 命令都带 **`--override-channels -c conda-forge -c bioconda`**。这既避开 `defaults` 里那个很老的 R，也绕开 Anaconda 的 ToS 门槛。

### 3.3 Git Bash 里 conda/python 看不到 `/tmp`

**症状**：`conda ... > /tmp/x.json` 之后 Python 说文件不存在。

**根因**：Git Bash 的 `/tmp` 映射到 MSYS 虚拟目录，**Windows 原生的 conda.exe / python.exe 看不见**。

**修法**：临时文件一律用双方都能看见的路径，如 `<root>/envs/_tmp.json`。

---

## 4. 设计约束（不是故障，但会让人困惑）

### 4.1 为什么不能"先激活再复用"

本 harness 中 Bash 工具调用之间**不保留 shell 状态**——环境变量、`cd`、函数全部丢失。所以每次调用都必须是自包含的绝对路径命令。这不是偷懒，是机制决定的。

### 4.2 三个后端都是直接调 exe

| 后端 | 调用 |
|---|---|
| figkit（Python venv） | `{root}/envs/figkit/Scripts/python.exe` |
| omicverse（Python conda env） | `{root}/envs/omicverse/python.exe` |
| R（官方 CRAN 安装） | `{root}/R/bin/Rscript.exe` |

三个都不需要激活、不需要 `conda run`。

（**历史**：R 曾经装成 conda prefix 环境，那时必须走 `conda run -p`，因为编译包 DLL 在 `<prefix>/Library/bin`、只有激活才进 PATH。换成官方 R 后这条约束消失了。详见 `envs.md`。）

### 4.3 为什么分享的 zip 里没有环境

环境是**绝对路径的机器本地资产**（`D:\app\...`），不是可携带的东西。zip 里只有 skill 本体（SKILL.md / references / scripts / requirements），目标 2 MB 以内。别人拿到 zip 后要自己跑 `install_all.sh` 建环境。
