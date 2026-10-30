# figwork: name=示例（183mm 双栏）
# figwork: size=183x60mm
# figwork: dpi=300
# figwork: out=out.png
#
# Python 后端的模板样例（R 的在同目录 example.R）。front-matter 规则完全一致，
# 见 mods/README.md。**自带示例数据**：项目里不需要 data.csv，建完直接出图。
#
# 换成自己的数据：把下面 df 的构造换成 pd.read_csv("data.csv")，
# 并在 front-matter 补一行 `# figwork: data=data.csv`。

import matplotlib
matplotlib.use("Agg")          # 无显示环境必须有；工作台不需要窗口
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import pandas as pd

# 中文必须先设字体，否则出图是方框（工作台的「缺字」闸门就是在查这个）。
# 按可用性挑一个，找不到就保持默认并关掉 unicode_minus（U+2212 那条闸门）。
for _name in ("SimHei", "Microsoft YaHei", "Noto Sans CJK SC", "Source Han Sans SC"):
    if any(f.name == _name for f in fm.fontManager.ttflist):
        plt.rcParams["font.sans-serif"] = [_name]
        break
plt.rcParams["axes.unicode_minus"] = False

# 自带示例数据（两列数值，够画散点）
rng = np.random.default_rng(0)
df = pd.DataFrame({
    "x": np.arange(1, 21),
    "y": 1.6 * np.arange(1, 21) + rng.normal(0, 2, 20),
})

# 尺寸按 front-matter 的 183×60mm 折算成英寸（同栏宽表）
fig, ax = plt.subplots(figsize=(183 / 25.4, 60 / 25.4))
ax.scatter(df["x"], df["y"], s=8)
ax.set_xlabel("x")
ax.set_ylabel("y")
fig.tight_layout()
fig.savefig("out.png", dpi=300)
