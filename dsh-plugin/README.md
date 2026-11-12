# dsh-plugin —— sci-figure-kit 的可选 DSH 面板

**这是可选项。** 不装它，`SKILL.md` 那套脚本与路由照常能用；
装了才有侧栏面板与两个模型工具。

```
dsh-plugin/
├── index.js            Host 半：两个模型工具 + 一条 HTTP 路由
├── client.js           Client 半：6 个标签页的面板
├── cordis.patch.yml    loader 插入条目
├── package.json        包清单（@local/dsh-sci-figure）
├── icon.svg
└── locale/             zh / en 文案
```

## 两个模型工具

| 工具 | 作用 |
|---|---|
| `sci_figure_env` | `status` 跑 11 项环境体检；`mods` 校验已装 mod |
| `sci_figure_workbench` | `list` / `templates` / `new` / `render` / `report`，对应 `scripts/workbench.py` 的五个子命令 |

两者都只用 `execFile(file, args)` 调固定脚本，**不拼 shell 字符串**，参数走白名单。

## 面板的 6 个标签页

全部 / 绘图 / 分析 / 软件 / 配色 / **mod 装载**。

前五项是静态内容（22 个配方 + 12 套色板 + 5 个连续色标），不依赖 Host。
**只有「mod 装载」页会调 Host 路由**；拿不到路由时该页降级提示，其余照旧可用。

### mod 装载页

三组展示，靠 `installed` / `has_manifest` 区分：

| 组 | 条件 |
|---|---|
| 已装载 | `installed = true` |
| 有清单待装 | `has_manifest = true` 且未装载 |
| 候选 | 只在 `mods/_catalog.json` 里登记过 |

两种关闭方式**刻意分开**，不要混用：

| 操作 | 底层命令 | 语义 |
|---|---|---|
| 开关（软） | `mod.py disable/enable <id>` | 只改 `_state.json` 的 `enabled`，**不删文件、不卸包**，秒回可逆 |
| 彻底卸载（硬） | `mod.py remove <id> --yes` | 真删 vendor 目录 + `pip uninstall`，**不可逆**，面板上要二次确认 |

软关闭的落点是 `_installed_ids()` 与 `cmd_routes()` 的过滤：
被禁用的 mod 会从 `mods/INDEX.md` 与 `references/routing-mods.md` 消失，
但它的 `mod.json` / `docs.md` / 已装依赖原样保留。

## Host 路由

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/dsh-sci-figure/mods` | 返回 `mod.py status --json` 的解析结果（`{ok, data}` 包裹） |
| `POST` | `/dsh-sci-figure/mod-op` | body `{action, id}`，`action ∈ enable \| disable \| install \| remove` |

三道防线：

1. **自定义头** `x-sci-figure: 1` —— 插件路由绕过 web server 的 auth gate，
   跨站 `fetch` 无法在无 CORS 预检应答的情况下带自定义头，所以这个头挡住任意网页。
2. **id 白名单** —— 正则 `^[a-z0-9][a-z0-9._-]{0,63}$`，且必须出现在 `status` 返回的列表里；
   id 从不被拼进路径。
3. **固定 argv** —— 只调 `mod.py` 的固定子命令，`execFile` 而非 shell。

`install` 超时 900s（联网 + 装依赖），`remove` 300s，`enable/disable` 120s。

## 装进 DSH profile

在本机 profile 的 `package.json` 里加 link 依赖，并把包名写进 `dsh.profile.bundles`：

```json
{
  "dependencies": {
    "@local/dsh-sci-figure": "link:<本目录绝对路径>"
  },
  "dsh": {
    "profile": {
      "bundles": ["@local/dsh-sci-figure"]
    }
  }
}
```

改完**刷新页面**（Ctrl+R）才会加载新的客户端模块。
若面板没出现，先看浏览器控制台有没有 `@local/dsh-sci-figure` 相关的加载错误。

## 环境变量

| 变量 | 作用 | 缺省 |
|---|---|---|
| `SCI_FIG_KIT` | 技能根目录（含 `SKILL.md` 与 `scripts/`） | 依次尝试：上级目录、相邻 core 仓库、`~/.dsh/skills/sci-figure-kit`、`~/.claude/skills/sci-figure-kit` |
| `SCI_FIG_PROJECTS` | 工作台项目根 | 无 |
| `SCI_FIG_ROOT` | 安装根；工作台取 `<root>/workbench/projects` | 无 |
| `SCI_FIG_PYTHON` | 解释器 | PATH 上的 `python` / `py` |

技能根目录是**运行时解析**的，源码里没有任何本机绝对路径 ——
这既是为了过 `scripts/check_repo_hygiene.py`，也修掉了早期「写死旧技能目录、
结果工具跑在旧代码树上」的毛病。

## 安全边界

- 只暴露固定子命令，不接受任意脚本路径
- `project` 必须是工作台根下的合法名字，或存在的绝对目录且不含 `..`
- `data` 必须是存在的绝对路径，后缀 `.csv` / `.tsv` / `.txt`
- `template` 必须匹配 `<mod-id>:templates/<file>`，禁止 `..`
- 无 shell、无自由参数、无第三方 npm 依赖
