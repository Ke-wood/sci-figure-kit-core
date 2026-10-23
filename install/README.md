# 装环境：给一台干净的 Windows

这个 skill 不自带 Python/R，也不要求装到固定盘符。**装到哪里由你在第一条命令里定**。

## 前提

| 依赖 | 说明 |
|---|---|
| Windows 10/11 x64 | 安装器按 Windows 写；非 Windows 见文末 |
| Python ≥ 3.10 | 用来建 figkit 的 venv；`python --version` 能跑即可 |
| 可选：Miniconda | 只有 `omicverse` 需要；没有就跳过这一套 |
| 网络 | 首次装 R 与 Python 包要下载 |

不需要管理员权限；不写系统 PATH；不碰你已有的全局 Python。

## 三步

```powershell
# 1 解压后进入 skill 目录（含 SKILL.md 的那层）
cd <解压目录>\01-skill本体

# 2 选一个你自己的位置装（默认 D:/app）
python install\bootstrap.py --root E:\tools\sci-fig

# 3 装完会自跑体检，看到 11 PASS / 0 FAIL 就好了
```

`--root` 就是**所有东西的落点**：

```
<root>\envs\figkit       Python venv（cnsplots / SciencePlots / cmcrameri / marsilea）
<root>\R                 官方 CRAN R 4.6.1 + ggplot2 / ComplexHeatmap / Seurat / SCpubr
<root>\envs\omicverse    conda prefix + omicverse
<root>\envs\_mods        mod 拉下来的第三方代码
<root>\envs\envs.json    机器本地注册表
```

同时会在 **skill 目录**写一份 `envs.json`。所以 skill 本体搬到哪台机器都认这套路径，
不用设环境变量。

## 只装一部分

三套彼此独立，缺哪套补哪套：

```powershell
python install\bootstrap.py --root E:\tools\sci-fig --only figkit
python install\bootstrap.py --root E:\tools\sci-fig --only r
python install\bootstrap.py --root E:\tools\sci-fig --only omicverse
python install\bootstrap.py --root E:\tools\sci-fig --dry-run    # 只看要做什么
```

只有 figkit 也能用：所有 matplotlib 系绘图与富集都能跑，只是用不了 R 与单细胞流程。

## 装完把 skill 放进 Claude / DSH

```powershell
# Claude Code（技能目录）
Copy-Item -Recurse . "$env:USERPROFILE\.claude\skills\sci-figure-kit"

# 或 DSH（技能目录，热加载）
Copy-Item -Recurse . "$env:USERPROFILE\.dsh\skills\sci-figure-kit"
```

（如果解压目录已经在技能目录下，跳过这步。）

## 常见失败

| 症状 | 原因 | 处理 |
|---|---|---|
| `找不到 Python ≥3.10` | 只有 Microsoft Store 的 python 别名 | 装官方 Python 并勾选 Add to PATH |
| figkit 装到一半失败 | 网络或 wheel 缺失 | 重跑同一条命令（幂等） |
| R 静默安装后仍没有 Rscript | 安装被拦或目录被占用 | 用 `--only r` 重跑；仍失败就手动装 R 4.6.x 到 `<root>\R` |
| 没有 conda | 未装 Miniconda | 装完后 `--only omicverse` |
| 体检里 `mods 一致性` FAIL | mod 声明了但没装 | `python scripts\mod.py install <id> --yes` |

## 非 Windows

`figkit` 部分在 Linux/macOS 上同样可用（venv 里是 `bin/python`）。
R 与 omicverse 需要你用系统包管理器 / conda 自己装，然后跑：

```bash
SCI_FIG_ENVS=<root>/envs/envs.json python scripts/check_envs.py
```

把报错里缺的路径补进 `envs.json` 即可。R 的包安装部分见 `scripts/install_r.sh` 里的包清单。
