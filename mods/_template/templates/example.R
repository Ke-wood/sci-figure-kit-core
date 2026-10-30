# figwork: name=示例（89mm 单栏）
# figwork: size=nature1
# figwork: dpi=300
# figwork: out=out.png
# figwork: vector=pdf,svg
#
# 这是 Python 后端（example.py）的姊妹版：**自带示例数据**，项目里不需要
# data.csv，建完项目直接就能出图。
#
# 换成自己的数据：把下面 df 的构造整段换成
#     df <- read.csv("data.csv", check.names = FALSE)
# 并在 front-matter 里补一行 `# figwork: data=data.csv`。
# （check.names = FALSE 别省 —— R 默认会改表头，列名引用会静默失配。）

suppressPackageStartupMessages({
  library(ggplot2)
  library(showtext)
  library(sysfonts)
})

# 中文必须显式设字体。showtext 稳，但**它把字形画成多边形** —— 于是矢量图里就
# 没有文字了（PDF 无字体、SVG 无 <text>），改不了。所以存矢量前要关掉它。
if (file.exists("C:/Windows/Fonts/simhei.ttf")) {
  font_add("SimHei", "C:/Windows/Fonts/simhei.ttf")
  showtext_auto()
  cjk <- "SimHei"
} else {
  cjk <- ""            # 非 Windows：交给系统默认字体
}
theme_cjk <- function(...) theme(text = element_text(family = cjk),
                                 axis.title = element_text(family = cjk), ...)

# 自带示例数据（两列数值，够画散点）
df <- data.frame(
  x = 1:20,
  y = c(3, 5, 4, 8, 7, 11, 9, 13, 12, 16, 15, 19, 18, 22, 20, 24, 23, 27, 25, 30)
)

p <- ggplot(df, aes(x = x, y = y)) +
  geom_point(size = 1.5) +
  labs(x = "x", y = "y") +
  theme_classic(base_size = 8) +
  theme_cjk()

# 尺寸必须与 front-matter 的 size= 一致：89mm 单栏 / 183mm 双栏
ggsave("out.png", p, width = 89, height = 60, units = "mm", dpi = 300)

# ---- 矢量：投稿要 PDF，进 PPT 要 SVG ----
# ① 先关 showtext（它把字形画成多边形）② PDF 必须显式 cairo_pdf
# ③ SVG 用 svglite::svglite，不要靠默认 svg() 设备
if (nzchar(cjk)) showtext_auto(FALSE)
ggsave("out.pdf", p, width = 89, height = 60, units = "mm", device = cairo_pdf)
ggsave("out.svg", p, width = 89, height = 60, units = "mm",
       device = svglite::svglite)
