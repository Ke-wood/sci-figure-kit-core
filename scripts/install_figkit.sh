#!/usr/bin/env bash
# 只装 figkit（Python 绘图环境）。薄壳，转给 install/bootstrap.py --only figkit。
# 用法：bash scripts/install_figkit.sh --root ~/sci-fig --source tuna
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
SKILL="$(cd "$HERE/.." && pwd)"
PY="${PYTHON:-python}"
exec "$PY" "$SKILL/install/bootstrap.py" --only figkit "$@"
