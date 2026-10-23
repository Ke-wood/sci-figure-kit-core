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
| R 复用后包找不到 | 确认 `envs.json` 里 `r_lib` 指向独立库；所有 R 调用都应带 `R_LIBS` |
| 没有 conda | 跳过 omicverse，或装 Miniconda 后 `--only omicverse` |
| 想彻底重来 | 删掉 `<root>` 与 skill 目录下的 `envs.json`，重跑 |

## 非 Windows

`figkit` 在 Linux/macOS 同样可用。R 用系统包管理器装好后：

```bash
python install/bootstrap.py --root ~/sci-fig --r-mode reuse --r-path "$(which Rscript)"
```
