# Changelog

## 未发布

- **mod 软开关**：新增 `mod.py disable / enable / status [--json]`。
  `disable` 只把 `_state.json` 里的 `enabled` 写成 `false`，**不 `pip uninstall`、
  不删任何文件**；该 mod 随即从 `mods/INDEX.md` 与 `references/routing-mods.md`
  消失，`enable` 立刻恢复。`enabled` 缺省为 `true`，现有 `_state.json`
  无需迁移即可照常工作。硬卸载 `remove` 行为不变。

## 0.2.0

下载路径全部可配，仓库自身自包含。

- **下载源可选**：`--source official|tuna|ustc|aliyun`，或逐项 `--pip-index` /
  `--cran-mirror` / `--bioc-mirror` / `--conda-channel`；环境变量
  `SCI_FIG_SOURCE` 等同样生效。选择写进 `envs.json`，**装 mod 时沿用同一套源**
  （`mod.py sources`）。`official` 对 pip 是「不传 `--index-url`」，即尊重你自己的
  `PIP_INDEX_URL` / `pip.ini`。
- **离线目录**：`--offline-dir` 指向 `wheels/` + `cran/`，全程不联网。
- **R 版本不再写死**：CRAN 只保留最新一版安装器，`R-4.6.1-win.exe` 已经 404。
  现在列目录 + 逐个 HEAD 验真取最新的能下的（镜像的目录页可能过期，阿里云就是），
  下载带重试；要钉版本用 `--r-version`。
- **修好四个 `install_*.sh`**：里面是未替换的 `{root}` 占位符，照跑会建出名叫
  `{root}` 的目录。现在它们只是 `install/bootstrap.py` 的薄壳。
- **自包含审计**：`check_workbench.py`、`workbench.py` 的写死盘符改为跟着
  `SCI_FIG_ROOT` 走；`check_repo_hygiene.py` 新增两条闸门 —— shell 里不许有
  `{root}` 占位符，以及把 `SCI_FIG_ROOT` 指到临时目录跑一遍 `bootstrap --dry-run`，
  输出里不许再出现别的根目录（字符串能骗过去，行为不能）。
- 顺带：`sources.py` 会拒绝能闭合 R 字符串的 URL 字符；本地目录自动归一成
  `file://` 仓库。

## 0.1.0

首个公开版本。

- 三套隔离后端 + 路由表 + 逐后端实测 API 文档
- mod 系统：`list / available / show / add / install / verify / update / remove / routes`
- 18 个 mod：绘图风格（ggpubfigs、paperfig、sci-figure）、配色（paletteer、khroma、
  colorcet、palettable）、统计（pydeseq2、limma、clusterprofiler、wgcna、drc、
  ssdtools、mixture-tox）、软件桥（prism、spss）、网络毒理（network-tox）、
  富集模板（enrichment-gseapy）
- 绘图工作台：项目结构、模板契约、六道出图闸门、矢量字体检查
- 跨机器安装器：自选安装根目录，写 `envs.json` 供 skill 自定位
