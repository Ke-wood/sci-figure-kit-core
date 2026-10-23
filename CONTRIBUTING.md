# Contributing

## 加一个新 mod

1. 在 `mods/<id>/` 下建 `mod.json` + `docs.md`（可参考 `mods/_template/`）。
2. `mod.json` 必须写清 `type` / `env` / `purpose` / `routes`。
3. `docs.md` 里要有**实测过**的调用块，不要凭记忆写 API。
4. 本地验证：

```bash
python scripts/mod.py install <id> --yes
python scripts/mod.py verify <id>
python scripts/mod.py routes
```

5. 如果 mod 带 Python 模板，请附带一份合成数据的冒烟测试结果（数字对账写在 docs 里）。

## 改加载器

`mod.py` 的安全边界钉在 `scripts/check_mod_guard.py` 的 81 条用例上。改完必须：

```bash
python scripts/check_mod_guard.py     # 81/81
```

**不要**让 mod 能自带命令、路径穿越、pip 选项注入。

## 风格

- 文档中文为主，代码注释中文；API 名保持原样。
- 提交信息：`mod(<id>): …` / `fix(loader): …` / `docs: …`。
