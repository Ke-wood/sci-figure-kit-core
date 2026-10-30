#!/usr/bin/env bash
# 三套环境一起装 —— 只是 install/bootstrap.py 的薄壳，参数原样透传。
#
# 为什么不留一份自己的实现：两份实现必然漂移（旧版这里写死过安装目录和 R
# 版本号，R 一升级就 404）。现在唯一的实现是 install/bootstrap.py。
#
# 用法：
#   bash scripts/install_all.sh --root ~/sci-fig
#   bash scripts/install_all.sh --root ~/sci-fig --source tuna --dry-run
#   PYTHON=/d/tools/python.exe bash scripts/install_all.sh --only figkit
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
SKILL="$(cd "$HERE/.." && pwd)"
PY="${PYTHON:-python}"
exec "$PY" "$SKILL/install/bootstrap.py" "$@"
