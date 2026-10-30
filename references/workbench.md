# 绘图工作台：给 AI 的运行期规则

工作台是**给用户看的界面**（三栏：数据 / 代码 / 图），但它的执行核心是
**headless** 的。这一条很关键：**界面永不在你的关键路径上** —— 你照旧是
「写脚本 → 跑 → 读 PNG 头」，只是现在跑的是 `workbench.py render`，
它顺手把 `fonts.md` 里的投稿硬约束执行成了闸门。

## 你什么时候用它

| 时机 | 动作 |
|---|---|
| 用户说"打开工作台""用界面画" | 告诉他跑到 P3 才有界面，现在可以 `render` + `report` |
| 用户要一张图且给了 CSV/TSV | `workbench.py new` 建项目 → 改脚本 → `render` |
| 已有的工作台项目要改图 | 直接 `Read` / `Edit` 那个项目的 `plot.R`，然后 `render` |
| 用户要"看看数据长什么样" | `workbench.py report <项目>`，自包含 HTML |
| 用户说"改一个值重画" | `workbench.py edit` 或直接改 CSV，然后 `render` |

**别自己起服务、别自己写 HTML。** 界面的实现是 `scripts/workbench_server.py`
（P3 才有），不是你要现搭的东西。

## 项目 = 一个目录，文件即状态

```
data.csv           源数据的不变副本（new 时拷入，**永不写**）
data.working.csv   可编辑工作副本（首次编辑才产生）
plot.R / plot.py   绘图脚本
out.png            产物（预览 + 尺寸闸门的依据）
out.pdf / out.svg  矢量产物（**脚本自己存**，工作台只查验）
render.log         脚本的合并输出
project.json       项目状态与溯源
data.edits.jsonl   编辑审计（append-only）
```

默认落在 `<root>/workbench/projects/`（机器本地，**不进分享 zip**）。
`--root` 或 `FIGWORK_ROOT` 可改。

## 命令

```bash
python "<skill>/scripts/workbench.py" list
python "<skill>/scripts/workbench.py" new <项目名> --data <csv> [--from <mod>:<template>] [--preset nature1]
python "<skill>/scripts/workbench.py" render <项目名|目录> [--json]
python "<skill>/scripts/workbench.py" report <项目名|目录> [--anon]
python "<skill>/scripts/workbench.py" edit <项目> --row N --col 列名 --value 值
python "<skill>/scripts/workbench.py" revert <项目>
```

`render` 的退出码与 `check_envs.py` 同族（0/1/2），`--json` 信封也是同一个形状。

## 模板契约（`mods/<id>/templates/`）

`templates[]` 在 `mod.json` 里声明，落点是 `<skill>/mods/<id>/templates/`。
文件头部用注释写 `figwork:` 键，**全部可选**：

```
# figwork: name=画廊里显示的标题
# figwork: data=data.csv        # 默认：项目目录里任意 data.*
# figwork: size=nature1         # 或 89x60mm、或 width=89mm height=60mm
# figwork: dpi=300
# figwork: out=out.png
# figwork: vector=pdf,svg       # 矢量产物；不写就不查（工作台只验「声明了却没产出」）
# figwork: env=figkit           # Python 脚本用哪个环境
# figwork: cjk=off              # 关掉「有中文却没设字体」那条检查
```

**脚本必须能独立手跑**：默认值写在脚本里，不要变成只能靠工作台启动。

## 偏离源数据（这条是纪律，不是功能）

- **源副本 `data.csv` 永不被写。** 编辑只作用于 `data.working.csv`。
- `project.json` 的 `diverged` 由「工作副本哈希 != 源副本哈希」**推导**，
  绝不手工置位。
- 每次渲染把 `data_sha256` 与 `diverged_at_render` 记进 `project.json`，
  于是每张图都能追到确切的字节。
- **图基于工作副本时，交付报告里必须写明这一点**，并给出修改处数。

## 出图后的闸门（FAIL 就按 fix 行处理）

| 闸门 | 查什么 |
|---|---|
| 尺寸 | 产物像素是否等于声明宽度 × dpi / 25.4（89mm@300dpi = 1051px） |
| U+2212 | 脚本里有没有字面量 U+2212。**纯文本扫描，注释里的也算** |
| 矢量尺寸 | 声明 `vector=` 的每个格式，外框是否等于声明的毫米（容差 1pt） |
| 矢量字体 | PDF 不得含 Type 3；SVG 必须有 `<text>`（纯路径 = Illustrator 改不了） |
| 缺字 | 渲染日志里的缺字信号；以及「有中文却没设字体」的启发式 |
| 期刊宽度 | SKIP 级提醒：声明的宽度是否落在常用栏宽上 |
| 矢量 | 没声明 `vector=` 时提醒一句（非核心，不判失败） |
| 手工改动 | 矢量文件与上次渲染的哈希不符 → 提醒**本次渲染会覆盖它**（非核心） |

**矢量那两道闸门查的是「能不能改、投稿收不收」**，判据全在
`references/fonts.md` 的矢量一节 —— Type 3 字体与路径化的 SVG 都**看起来完全正常**，
不主动去查就永远发现不了。工作台只查验，**不改写产物**：矢量文件是脚本存的，
工作台不会替你补一个（补了就等于伪造「脚本能出矢量」）。

矢量产物的哈希记在 `project.json.last_render.vector`。你在 Illustrator 里改过
`out.pdf` 之后，下次 `render` 会在动手**之前**告诉你这一版要被覆盖 ——
**不禁止手改，但让它可见**（与数据偏离是同一条纪律）。

尺寸闸门查的是**声明与产物是否一致**，不是「你有没有违反 Nature 的规定」。
最常见的触发方式是改了 front-matter 的 `size=` 却忘了改 `ggsave(width=)`。

## 三条别做的事

1. **不写进 skill 目录。** 项目和产物都在项目目录里；工作台自己也会拒绝把
   根目录设在 skill 树内。
2. **不覆盖用户的图。** `report` 落在项目目录，验证产物去 `_figkit_verify/`。
3. **不用 `cnsplots.savefig()`。** 它会毁掉中文（实测 90 处缺字），用
   `fig.savefig()`；R 侧用 `ggsave()`。理由见 `references/fonts.md`。

## 常见故障

| 症状 | 原因 | 修法 |
|---|---|---|
| 尺寸闸门 FAIL | front-matter 的 `size=` 与脚本里的 width/height 不一致 | 改一处，或两处都改 |
| 尺寸差几像素 | 用了 `bbox_inches="tight"` | 去掉它；tight 会裁窄，投稿要的是精确栏宽 |
| 矢量字体 FAIL：`Type 3` | matplotlib 默认 `pdf.fonttype=3` | `rcParams["pdf.fonttype"]=42`，见 `fonts.md` |
| 矢量字体 FAIL：`没有 <text>` | matplotlib 默认 `svg.fonttype='path'`，或 R 侧 showtext 开着 | 设 `svg.fonttype="none"`；R 存矢量前 `showtext_auto(FALSE)` |
| 矢量字体 FAIL：`已转成路径` | R 侧 showtext 把字形画成了多边形 | 同上；`cairo_pdf` 不靠 showtext 也出中文 |
| R 报 `invalid font type` / `mbcsToSbcs` | `ggsave("x.pdf")` 没写 `device=`，默认挑了 `pdf()` | 显式 `device = cairo_pdf` |
| 矢量尺寸差 0.28pt | cairo 把页面尺寸取整到整 pt | 正常，容差 1pt 之内，不用管 |
| 中文变方框 | 没显式设字体，或 `cnsplots.setup_matplotlib()` 之后才设 | 见 `references/fonts.md` 的顺序陷阱 |
| 表头变成 `X1`/带点 | R 的 `read.csv` 默认 `check.names=TRUE` | 加 `check.names = FALSE` |
| `unused argument` | 猜了 API | `args()` 实测；ggpubfigs 的主题函数**不接受任何参数** |
| 中文乱码 | 源是 GBK，按 utf-8 读了 | 工作台会嗅探并记进 `project.json`；手写脚本要显式指定 |
