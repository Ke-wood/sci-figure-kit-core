#!/usr/bin/env bash
# 建 omicverse 环境：conda prefix + Python 3.13 + omicverse
# 幂等：已存在则跳过创建，只补包。可安全重跑。

set -u

CONDA="${CONDA:-{root}/ana/Scripts/conda.exe}"
ENV_DIR="${ENV_DIR:-{root}/envs/omicverse}"
OMVPY="$ENV_DIR/python.exe"
OMV_VER="${OMV_VER:-2.3.2}"

if [ ! -x "$CONDA" ]; then
  echo "找不到 conda：$CONDA" >&2
  echo "用 CONDA=<路径> 覆盖" >&2
  exit 2
fi

if [ -x "$OMVPY" ]; then
  echo "omicverse 环境已存在：$OMVPY"
else
  echo "创建 conda prefix 环境：$ENV_DIR"
  mkdir -p "$(dirname "$ENV_DIR")"
  # --override-channels 必需：{root}/ana/.condarc 里是 channels:[defaults]，
  # 不覆盖会撞上 Anaconda ToS 门槛，且求解结果不可控。
  "$CONDA" create -y --prefix "$ENV_DIR" --override-channels \
    -c conda-forge python=3.13 pip || exit 1
fi

echo "升级 pip"
"$OMVPY" -m pip install -q --upgrade pip

# 不装 extras（[full] / [easy]）—— 那些会拉 torch / squidpy / scvi-tools 等，
# 数 GB 且风险尾巴最长。按需再加：pip install "omicverse[commot]"
echo "安装 omicverse==$OMV_VER"
"$OMVPY" -m pip install "omicverse==$OMV_VER" || exit 1

echo
echo "omicverse 就绪："
"$OMVPY" -c "import omicverse as ov, sys; print('  python', sys.version.split()[0], '| omicverse', ov.__version__)"
