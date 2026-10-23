# figwork: name=<这一步是画廊里显示的标题>
# figwork: data=data.csv
# figwork: size=nature1
# figwork: dpi=300
# figwork: out=out.png
# figwork: vector=pdf,svg
#
# ↑ 这些是**模板契约**的头部（front-matter）。工作台读它们来决定：绑哪个数据
#   文件、出多大、多少 dpi、产物叫什么名字、出不出矢量图。
#
# **全部键都可选** —— 没有 front-matter 的模板也能跑，缺什么用什么默认值：
#     backend  由脚本扩展名决定（.R -> R 后端，.py -> Python）
#     env      Python 脚本用哪个环境，默认 figkit
#     data     默认：项目目录里任意 data.*
#     size     默认 nature1（89×60mm）；也可写 89x60mm、或 width=89mm height=60mm
#     dpi      默认 300
#     out      默认 out.png
#     vector   矢量产物，取值 pdf / svg（vector=pdf,svg 表示两个都要）。
#              **不写就不查** —— 工作台只校验「声明了却没有」的情况
#     cjk      写 `cjk=off` 可关掉「脚本有中文却没设字体」那条检查
#     u2212    写 `u2212=allow` 可放行字面量 U+2212（一般不该放行）
#
# 完整契约与可用键见 mods/README.md。

suppressPackageStartupMessages({
  library(ggplot2)
  library(showtext)
  library(sysfonts)
})

# 数据：工作台保证脚本的工作目录就是项目目录，所以相对路径直接可用。
# check.names = FALSE 别省 —— R 默认会改表头，列名引用会静默失配。
df <- read.csv("data.csv", check.names = FALSE)

# 中文必须显式设字体。showtext 稳，但**它把字形画成多边形** —— 于是矢量图里就
# 没有文字了（PDF 无字体、SVG 无 <text>），改不了。所以存矢量前要关掉它，
# 见文件末尾「矢量」一节。实测 cairo_pdf 直接认 family="SimHei"，关掉无损。
# （早前注释里说「本机 cairo 不兼容」指的是 R 包 Cairo，不是内置的 cairo 设备。）
showtext_auto()
font_add("SimHei", "C:/Windows/Fonts/simhei.ttf")

p <- ggplot(df, aes(x = df[[1]], y = df[[2]])) +
  geom_point(size = 1.5) +
  labs(x = names(df)[1], y = names(df)[2]) +
  theme_classic(base_size = 8) +
  theme(text = element_text(family = "SimHei"),
        axis.title = element_text(family = "SimHei"))

# 尺寸必须与 front-matter 的 size= 一致：89mm 单栏 / 183mm 双栏（Nature）
ggsave("out.png", p, width = 89, height = 60, units = "mm", dpi = 300)

# ---- 矢量：投稿要 PDF，进 PPT 要 SVG ----
# ① 先关 showtext（它把字形画成多边形，矢量里就不再是文字了）
# ② PDF 必须显式写 device = cairo_pdf —— ggsave 按扩展名默认挑的 pdf() 会报
#    invalid font type，中文还会 mbcsToSbcs 失败
# ③ SVG 用 svglite::svglite，不能靠默认的 svg() 设备
showtext_auto(FALSE)
ggsave("out.pdf", p, width = 89, height = 60, units = "mm", device = cairo_pdf)
ggsave("out.svg", p, width = 89, height = 60, units = "mm",
       device = svglite::svglite)
