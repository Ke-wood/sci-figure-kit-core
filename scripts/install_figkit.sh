#!/usr/bin/env bash
# 建 figkit 环境：Python 3.14 venv + 绘图库
# 幂等：已存在则跳过，可安全重跑。

set -u

GLOBAL_PY="${GLOBAL_PY:-$(command -v python || command -v python3 || true)}"
VENV="{root}/envs/figkit"
FIGPY="$VENV/Scripts/python.exe"
REQ="$(cd "$(dirname "$0")/.." && pwd)/requirements-figkit.txt"

if [ -x "$FIGPY" ]; then
  echo "figkit 已存在：$FIGPY"
  "$FIGPY" -m pip install -q -r "$REQ" && echo "依赖已同步"
  exit 0
fi

if [ ! -x "$GLOBAL_PY" ]; then
  echo "找不到全局 Python：$GLOBAL_PY" >&2
  echo "若路径不同，用 GLOBAL_PY=<路径> 覆盖" >&2
  exit 2
fi

echo "创建 venv：$VENV"
mkdir -p "$(dirname "$VENV")"
"$GLOBAL_PY" -m venv "$VENV" || exit 1

echo "升级 pip"
"$FIGPY" -m pip install -q --upgrade pip

echo "安装绘图库（读 $REQ）"
"$FIGPY" -m pip install -r "$REQ" || exit 1

echo
echo "figkit 就绪："
"$FIGPY" -c "import sys,matplotlib,cnsplots; print('  python', sys.version.split()[0], '| matplotlib', matplotlib.__version__, '| cnsplots', cnsplots.__version__)"
