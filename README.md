# sci-figure-kit（核心）

> 三套隔离的绘图/分析后端 + 分层阅读 + 可装载 mod。
> 本仓库**只含内核**：路由、API 文档、工作台、装载器、安装器。
> 具体能力（差异表达、剂量反应、配色包、Prism/SPSS…）在
> [`sci-figure-kit-mods`](https://github.com/<you>/sci-figure-kit-mods)。

**不碰你的全局 Python，不改 PATH。**

## 为什么分两个仓库

| 仓库 | 内容 | 为什么分开 |
|---|---|---|
| **sci-figure-kit**（本仓） | SKILL.md · references · scripts · install · `mods/` 空架子 | 内核要小、要稳定、要被信任 |
| **sci-figure-kit-mods** | 每个 mod 的清单、文档、模板 | mod 更新频繁，且第三方内容多 |

好处是三条：

1. **内核不带 mod 内容** —— `SKILL.md` 不会因为多装一个 mod 而变长；
2. **mod 可以独立更新** —— `mod.py update` 只动 mod 目录；
3. **信任边界清楚** —— 内核只有装载器，mod 永远不能提供 shell 命令。

## 分层阅读

模型不会一次读完全部文档，而是按层展开：

```
SKILL.md            内置后端 + 工作流（不含任何具体 mod）
  └─ mods/INDEX.md  已装载 mod 的一页索引，每个 1–2 句（自动生成）
      └─ mods/<id>/docs.md   命中后才读，含实测调用块
          └─ references/<backend>-api.md   最后才读
```

`INDEX.md` 由 `python scripts/mod.py index` 生成，**装 / 卸 mod 时自动刷新**；
写新 mod 时只需要把 `summary` 和 `routes[].intent` 写好，索引就自动成型。

## 安装

```bash
git clone <this repo> && cd sci-figure-kit
python install/bootstrap.py --root ~/sci-fig      # 或 D:/app
python scripts/check_envs.py                      # 期望 11 PASS
```

只要绘图、不装 R 与单细胞：

```bash
python install/bootstrap.py --root ~/sci-fig --only figkit
```

### 已经有 R / Python？不会重复装

默认 `--r-mode auto` 先找机器上已有的 `Rscript`（`RSCRIPT` / `R_HOME` / PATH / 常见目录），
找到就**复用**——不下载安装器、不装第二套 R，只把包装进 `<root>/R/library` 这个独立库。

```bash
# 没找到时会提示：
#   没检测到已有 R，将安装一套。若你其实已经装了 R，加 --r-mode reuse --r-path <Rscript> 复用即可。
python install/bootstrap.py --root X --r-mode reuse --r-path "C:/Program Files/R/R-4.6.1/bin/Rscript.exe"
```

Python 只用来建 venv（不下载解释器）；conda 用你现有的、建一个 prefix，不动 base 环境。
细节见 [`install/README.md`](install/README.md)。

### 下载源自己选

默认官方源，国内或内网一条命令换镜像：

```bash
python install/bootstrap.py --root X --source tuna      # 清华；还有 ustc / aliyun
python install/bootstrap.py --list-sources              # 看全部预设
```

单项也能换（`--pip-index` / `--cran-mirror` / `--bioc-mirror` / `--conda-channel`），
或者 `--offline-dir` 完全离线。选择会写进 `envs.json`，之后装 mod 沿用同一套源。

> R 版本不写死在代码里：CRAN 只保留最新一版安装器，写死会 404
> （`R-4.6.1-win.exe` 已经 404，现在只有 4.6.2），所以装的时候现查目录。

## 装 mod

```bash
# 1 从 mods 仓库取一个 mod 目录
cp -r ../sci-figure-kit-mods/mods/pydeseq2 mods/

# 2 装载（写环境 + 记状态 + 自动刷新索引）
python scripts/mod.py install pydeseq2 --yes

# 3 看索引
cat mods/INDEX.md
```

其他命令：

```bash
python scripts/mod.py list
python scripts/mod.py update --check      # 上游有新版本吗
python scripts/mod.py update --yes        # 更新全部（或指定 id）
python scripts/mod.py verify [id]
python scripts/mod.py remove <id> --yes
python scripts/mod.py routes              # 重建 routing-mods.md
```

## 内置能力（不需要 mod）

| 领域 | 能力 |
|---|---|
| 图型 | 火山 / 森林 / ROC / 生存 / 热图 / UMAP / UpSet / 多面板 / 基因结构 |
| 配色 | 期刊色板（ggsci）、感知均匀色标（cmcrameri）、viridis |
| 分析 | 单细胞流程（omicverse）、富集（gseapy）、生存（lifelines）、统计检验与回归 |
| 工作台 | 项目目录 + 六道出图闸门（尺寸 / 缺字 / U+2212 / 矢量字体） |

## 已验证

- `check_envs.py` **11/11**（三套环境 + 中文渲染 + mod 一致性）
- `check_mod_guard.py` **81/81**（装载器对抗用例，CI 每次跑）
- `check_workbench.py` **20/20**（工作台闸门；**clone 下来就能跑**，不依赖 mods 仓库）
- `check_repo_hygiene.py`：无本机路径 + 把 `SCI_FIG_ROOT` 指到临时目录跑一遍
  `bootstrap --dry-run`，输出里不许出现别的根目录
- `mod.py index` 在空 `mods/` 下生成「当前没有已装载的 mod」；装一个 mod 后自动出表

## 目录

```
SKILL.md              代理入口：内置路由 + 工作流 + 纪律
mods/INDEX.md         已装载 mod 索引（自动生成）
mods/README.md        怎么装 / 怎么写 mod
mods/_template/       新 mod 骨架
references/           路由、API 实测、配色、图型配方、工作台、排错
scripts/              check_envs · mod.py · workbench.py · sources.py · installers
install/              跨机器安装器（自选安装根目录）
.github/workflows/    CI：编译 + 卫生 + 81 条安全用例 + 清单可加载
```

## 许可

MIT（见 `LICENSE`）。mod 与其指向的第三方库保留各自许可证。
