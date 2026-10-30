#!/usr/bin/env bash
# 只装 R 环境。薄壳，转给 install/bootstrap.py --only r。
#
# 注意：默认 --r-mode auto —— 机器上已有 Rscript 就复用它，只把包装进独立库，
# 不会再下载一套 R。想强制装一套新的用 --r-mode install。
#
# 用法：bash scripts/install_r.sh --root ~/sci-fig --source tuna
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
SKILL="$(cd "$HERE/.." && pwd)"
PY="${PYTHON:-python}"
exec "$PY" "$SKILL/install/bootstrap.py" --only r "$@"
