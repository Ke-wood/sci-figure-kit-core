#!/usr/bin/env bash
# 依次安装三套环境，每段独立可验证。
#
# 设计要点：三段分开跑，任一段失败不影响另外两段。
# figkit（快，约 3 分钟）先跑通网络与轮子假设；R 和 omicverse 慢（各 10–30 分钟）。
# 不需要 root/admin；不改动用户的全局 Python。

set -u
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "=========================================="
echo "sci-figure-kit 环境安装"
echo "=========================================="
echo

FAILED=""

echo "---------- [1/3] figkit（Python 绘图环境）----------"
if bash "$HERE/install_figkit.sh"; then
  echo "✓ figkit"
else
  echo "✗ figkit 失败" >&2; FAILED="$FAILED figkit"
fi

echo
echo "---------- [2/3] R 环境 ----------"
if bash "$HERE/install_r.sh"; then
  echo "✓ R"
else
  echo "✗ R 失败" >&2; FAILED="$FAILED R"
fi

echo
echo "---------- [3/3] omicverse（组学分析）----------"
if bash "$HERE/install_omicverse.sh"; then
  echo "✓ omicverse"
else
  echo "✗ omicverse 失败" >&2; FAILED="$FAILED omicverse"
fi

echo
echo "=========================================="
if [ -n "$FAILED" ]; then
  echo "以下环境安装失败：$FAILED"
  echo "其余环境不受影响，可单独重跑对应 install_*.sh"
fi

echo
echo "跑体检："
python "$HERE/check_envs.py"

if [ -n "$FAILED" ]; then
  exit 1
fi
echo
echo "全部就绪。"
