#!/usr/bin/env bash
# 建 R 环境：官方 CRAN 安装器 + CRAN/Bioconductor Windows 二进制包
#
# 为什么不用 conda：conda-forge 的 R 环境混装 m2w64（MSVCRT）与 mingw-w64-ucrt
# （UCRT）两套工具链，其 Seurat 构建加载即报 "Mingw-w64 runtime failure"。
# 详见 references/envs.md 的"为什么不用 conda 装 R"。
#
# 幂等：R 已装则跳过安装器，只补包。可安全重跑。

set -u

R_DIR="${R_DIR:-{root}/R}"
RSCRIPT="$R_DIR/bin/Rscript.exe"
R_URL="${R_URL:-https://cloud.r-project.org/bin/windows/base/R-4.6.1-win.exe}"
TMP_EXE="D:/app/envs/_R-installer.exe"

# ---- 1. 装 R 本体 ----
if [ -x "$RSCRIPT" ]; then
  echo "R 已存在：$("$RSCRIPT" -e 'cat(R.version.string)' 2>/dev/null | tr -d '\r')"
else
  echo "下载 R 安装器：$R_URL"
  mkdir -p "$(dirname "$TMP_EXE")"
  curl -sL -m 900 -o "$TMP_EXE" "$R_URL" || { echo "下载失败" >&2; exit 1; }

  echo "静默安装到 $R_DIR"
  "$TMP_EXE" /VERYSILENT /DIR="$(cygpath -w "$R_DIR" 2>/dev/null || echo "$R_DIR")" \
             /NORESTART /SUPPRESSMSGBOXES || { echo "安装失败" >&2; exit 1; }

  [ -x "$RSCRIPT" ] || { echo "安装后仍找不到 $RSCRIPT" >&2; exit 1; }
  rm -f "$TMP_EXE"
fi

# ---- 2. 装 R 包 ----
echo
echo "安装 R 包（全部用 Windows 二进制，无需编译器）"
PKG_SCRIPT="$(mktemp -t rpkg.XXXXXX.R)"
cat > "$PKG_SCRIPT" <<'RCODE'
lib <- .libPaths()[1]
repos <- c(CRAN = "https://cloud.r-project.org")
cat("目标库:", lib, "\n")

core <- c(
  "dplyr","tidyr","stringr","purrr","tibble","forcats","magrittr",
  "rlang","data.table","reshape2","matrixStats",
  "ggplot2","scales","patchwork","cowplot","viridis","RColorBrewer",
  "ggrepel","ggh4x","ggbeeswarm","ggdist","ggalluvial","ggsignif",
  "ggplotify","scattermore","ggforce","ggpubr",
  "showtext","sysfonts","ragg","svglite","systemfonts",
  "ggsci","gggenomes",
  "BiocManager","remotes","jsonlite"
)
singlecell <- c("Seurat","SeuratObject","SCpubr")

install.packages(core, lib = lib, repos = repos, dependencies = NA, type = "binary")
install.packages(singlecell, lib = lib, repos = repos, dependencies = NA, type = "binary")
BiocManager::install("ComplexHeatmap", lib = lib, ask = FALSE, update = FALSE)

all <- c(core, singlecell, "ComplexHeatmap")
miss <- all[!vapply(all, function(p) {
  !is.na(tryCatch(as.character(packageVersion(p)), error = function(e) NA))
}, logical(1))]
cat("\n缺失:", if (length(miss)) paste(miss, collapse = " ") else "无", "\n")
RCODE

"$RSCRIPT" "$PKG_SCRIPT" || { echo "R 包装载失败" >&2; rm -f "$PKG_SCRIPT"; exit 1; }
rm -f "$PKG_SCRIPT"

# ---- 3. 终检：三者共存 ----
echo
echo "终检（ComplexHeatmap + Seurat + SCpubr 共存）"
"$RSCRIPT" -e 'suppressMessages({library(ComplexHeatmap);library(Seurat);library(SCpubr)}); cat("OK\n")' \
  || { echo "三者共存失败 —— 检查 R 是否为官方 CRAN 版（见 references/envs.md）" >&2; exit 1; }

echo
echo "R 环境就绪：$R_DIR"
