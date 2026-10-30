#!/usr/bin/env bash
# 只装 omicverse（conda prefix）。薄壳，转给 install/bootstrap.py --only omicverse。
# 没有 conda 时这一步会跳过，不影响另外两套。
#
# 用法：bash scripts/install_omicverse.sh --root ~/sci-fig --source tuna
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
SKILL="$(cd "$HERE/.." && pwd)"
PY="${PYTHON:-python}"
exec "$PY" "$SKILL/install/bootstrap.py" --only omicverse "$@"
