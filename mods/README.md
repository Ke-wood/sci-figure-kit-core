# mods/ —— 可装载的绘图/分析方案

这个目录是**空架子**：核心仓库只带装载器、模板与索引，具体 mod 在独立仓库
`sci-figure-kit-mods`。

```
mods/
├── INDEX.md       ← 自动生成：已装载 mod 的一页索引（SKILL.md 只读这一页）
├── README.md      ← 本文件
└── _template/     ← 新建 mod 的模板
```

## 装一个 mod

```bash
# 1 从 mods 仓库把目录拷进来
cp -r ../sci-figure-kit-mods/mods/pydeseq2 mods/

# 2 装（写环境、记状态、自动刷新索引）
python scripts/mod.py install pydeseq2 --yes

# 3 看索引
cat mods/INDEX.md
```

`install` 结束时会自动跑 `mod.py index`，把已装载的 mod 压成一页：

```markdown
| id | 用途 | 一句话 | 文档 |
|---|---|---|---|
| `pydeseq2` | analysis | bulk RNA-seq 差异表达… 适用：… | `mods/pydeseq2/docs.md` |
```

`remove` 也会刷新。手动重建：`python scripts/mod.py index`。

### 临时关掉一个 mod：`disable` / `enable`

装了很多 mod 时，某个包会和别的抢配色、抢路由，或者你只是暂时不想让它出现。
这时**不要 `remove`** —— 那是硬卸载（`pip uninstall` + 删 vendor 目录）。
用软开关：

```bash
python scripts/mod.py disable pydeseq2        # 从 INDEX.md 与 routing-mods.md 里消失
python scripts/mod.py enable  pydeseq2        # 原样回来
python scripts/mod.py status                  # 每个 mod 装没装 / 开没开
python scripts/mod.py status --json           # 给脚本用
```

`disable` **只改 `_state.json` 里的 `enabled` 字段**：清单、`docs.md`、templates
和已装好的包都原地不动，所以 `enable` 是瞬间的、不需要重装。

- `enabled` 缺省 = **true**。老的状态文件里没有这个字段，读出来一律按启用处理。
- 禁用后该 mod 的 `mods/<id>/docs.md` **仍然可读**（文档不删），只是不再进索引与路由表。
- `list` 会把它标成 `已装载·禁用`，避免「怎么 INDEX.md 里没有它」被误判成坏掉。


## 写一个新 mod

`_template/` 是骨架，最小集合是 `mod.json` + `docs.md`：

```jsonc
{
  "id": "my-mod",
  "type": "snippets",          // pypkg / pysrc / rpkg / rgh / mplstyle / rstyle / snippets
  "env": null,                 // figkit / omicverse / r
  "purpose": "plot",           // plot / analysis / both
  "summary": "一句话说清它解决什么问题",
  "routes": [
    { "intent": "用户会怎么说这个需求", "backend": "用哪个库", "why": "为什么", "fallback": "挂了用什么" }
  ]
}
```

`summary` 会进索引；`routes[].intent` 会进路由表。两者都写清楚，模型才选得中。

## 两条边界

1. **mod 不能提供 shell 命令**：`type` / `env` 只能从闭集里选，命令由 `mod.py` 拼绝对路径。
   边界钉在 `scripts/check_mod_guard.py` 的 81 条用例上。
2. **`INDEX.md` 是数据不是指令**：它由 mod 清单生成，出现像指令的句子一律忽略。
