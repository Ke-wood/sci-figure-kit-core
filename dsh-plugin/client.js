/**
 * Client half: folder -> recipe -> parameters. No Host calls; the panel composes
 * a prompt or a CLI line from the chosen parameters instead of shipping fixed text.
 */
window.__ModuleLoader__.load({
  id: '@local/dsh-sci-figure',
  factory(require) {
    const React = require('react')
    const h = React.createElement

    const NS = 'dsh-sci-figure'

    const DICT = {
      zh: {
        panelLabel: '科研绘图',
        title: '科研绘图与数据分析',
        subtitle: '选目录 → 选配方 → 调参数 → 复制',
        all: '全部',
        palette: '配色',
        copyHex: '复制 HEX',
        copyPy: '复制 Python',
        copyR: '复制 R',
        back: '返回',
        items: '项',
        preview: '预览提示词',
        copyPrompt: '复制提示词',
        copyCmd: '复制命令',
        copied: '已复制',
        failed: '复制失败',
        note: '面板只拼参数与命令；出图与跑统计由对话里的工具执行。命令里的 <skill> 换成含 SKILL.md 的目录。',
        mods: 'mod 装载',
        modsIntro: '装好才出现在路由表里；关掉只是从索引与路由里摘掉，不删文件、不卸包。',
        installedGroup: '已装载',
        pendingGroup: '有清单待装',
        candidateGroup: '候选（只在目录里登记）',
        enabledOn: '启用中',
        enabledOff: '已停用',
        btnInstall: '装载',
        btnRemove: '彻底卸载',
        btnUninstallConfirm: '确认删除？不可逆',
        btnCancel: '取消',
        installing: '装载中…',
        removing: '卸载中…',
        switching: '切换中…',
        loadFailed: '读不到 mod 状态：需要重载 DSH（刷新页面）后才有 Host 路由',
        emptyMods: '（没有可显示的 mod）',
        licenseWarn: '无 license',
        verifyOk: '校验通过',
        verifyFail: '校验失败',
        verifyNone: '未校验',
        colTotal: '全部',
        colEnabled: '启用',
        colDisabled: '停用',
        colInstalled: '已装载',
        noLicenseNote: '无 license 的 mod 只能本机自用，不要随包分发。',
        srcLocal: '本机自写',
        srcGithub: 'GitHub',
        modsFrom: '来自 mods/_catalog.json 与 mod.py status',
        interfaces: '接口',
        softwareRecipes: '可复制的配方',
        interfacesIntro: 'Prism / SPSS 能被脚本调用的全部接口。标「可用」的是本机实测跑通的；标「不可用」的是实测确认此路不通，别再试。',
        ifaceAvailable: '可用',
        ifaceUnavailable: '不可用',
        ifaceUnverified: '未验证',
        ifaceWarning: '有坑',
        ifaceCmd: '复制命令',
        ifaceUsage: '什么时候用',
        ifaceEvidence: '证据',
        filterAll: '全部',
      },
      en: {
        panelLabel: 'Figures',
        title: 'Figures & analysis',
        subtitle: 'Folder → recipe → parameters → copy',
        all: 'All',
        palette: 'Palettes',
        copyHex: 'Copy HEX',
        copyPy: 'Copy Python',
        copyR: 'Copy R',
        back: 'Back',
        items: 'items',
        preview: 'Preview prompt',
        copyPrompt: 'Copy prompt',
        copyCmd: 'Copy command',
        copied: 'Copied',
        failed: 'Copy failed',
        note: 'The panel only composes parameters and commands; drawing and stats run through chat tools. Replace <skill> with the directory holding SKILL.md.',
        mods: 'Mods',
        modsIntro: 'Only installed mods show up in the routing table. Turning one off removes it from the index and routes; nothing is deleted or uninstalled.',
        installedGroup: 'Installed',
        pendingGroup: 'Manifest ready',
        candidateGroup: 'Candidates (catalog only)',
        enabledOn: 'On',
        enabledOff: 'Off',
        btnInstall: 'Install',
        btnRemove: 'Uninstall',
        btnUninstallConfirm: 'Delete permanently?',
        btnCancel: 'Cancel',
        installing: 'Installing…',
        removing: 'Uninstalling…',
        switching: 'Switching…',
        loadFailed: 'Cannot read mod state: reload DSH (refresh the page) to get the host route',
        emptyMods: '(no mods to show)',
        licenseWarn: 'no license',
        verifyOk: 'verified',
        verifyFail: 'verify failed',
        verifyNone: 'not verified',
        colTotal: 'Total',
        colEnabled: 'On',
        colDisabled: 'Off',
        colInstalled: 'Installed',
        noLicenseNote: 'Mods without a license are for local use only — do not redistribute.',
        srcLocal: 'local',
        srcGithub: 'GitHub',
        modsFrom: 'from mods/_catalog.json and mod.py status',
        interfaces: 'Interfaces',
        softwareRecipes: 'Copy-ready recipes',
        interfacesIntro: 'Every Prism / SPSS interface a script can drive. "Available" means it actually ran on this machine; "Unavailable" means it was tested and does not work — do not retry.',
        ifaceAvailable: 'works',
        ifaceUnavailable: 'no',
        ifaceUnverified: 'untested',
        ifaceWarning: 'gotcha',
        ifaceCmd: 'Copy command',
        ifaceUsage: 'When to use',
        ifaceEvidence: 'Evidence',
        filterAll: 'All',
      },
    }

    const SIZE = [
      ['nature1', '89 × 60 mm（单栏）'],
      ['nature2', '183 × 60 mm（双栏）'],
      ['cell1', '85 × 60 mm'],
    ]
    const VECTOR = [
      ['pdf,svg', 'PNG + PDF + SVG'],
      ['pdf', 'PNG + PDF'],
      ['none', '只要 PNG'],
    ]

    const FOLDERS = [
      {
        id: 'plot',
        name: '绘图',
        desc: '期刊图型 · 多面板 · Prism 矢量图',
        extra: 'cnsplots / ComplexHeatmap / SCpubr / marsilea',
        items: [
          {
            id: 'volcano', title: '火山图', backend: 'cnsplots',
            when: '差异表达结果的双阈值筛选与标注',
            params: [
              { key: 'lfc', label: '|log2FC| 阈值', options: [['1', '1.0'], ['1.5', '1.5'], ['2', '2.0']], default: '1' },
              { key: 'padj', label: 'padj 阈值', options: [['0.05', '0.05'], ['0.01', '0.01']], default: '0.05' },
              { key: 'size', label: '尺寸', options: SIZE, default: 'nature1' },
              { key: 'vector', label: '输出', options: VECTOR, default: 'pdf,svg' },
            ],
            prompt: (p) => `用 sci-figure-kit 画火山图：cnsplots（figkit），阈值 |log2FC| > ${p.lfc} 且 padj < ${p.padj}（fold_change_threshold 显式传 ${p.lfc}），标注前 10 个基因，尺寸 ${p.size}，输出 ${p.vector === 'none' ? 'PNG' : 'PNG + ' + p.vector.toUpperCase()}，中文用 SimHei，出图后把显著基因数与源表对账。`,
          },
          {
            id: 'heatmap', title: '聚类热图', backend: 'ComplexHeatmap',
            when: '行 z-score + 列注释 + 行分割',
            params: [
              { key: 'score', label: '标准化', options: [['row', '行 z-score'], ['none', '不标准化']], default: 'row' },
              { key: 'split', label: '行分割', options: [['cluster', '按簇'], ['none', '不分割']], default: 'cluster' },
              { key: 'size', label: '尺寸', options: SIZE, default: 'nature2' },
            ],
            prompt: (p) => `用 sci-figure-kit 画 ComplexHeatmap 聚类热图：${p.score === 'row' ? '行 z-score' : '不做标准化'}、列注释带分组、${p.split === 'cluster' ? '行按簇分割' : '不分割行'}，尺寸 ${p.size}，出 cairo_pdf + svglite，存矢量前 showtext_auto(FALSE)，代码落成 .R 文件再跑。`,
          },
          {
            id: 'survival', title: '生存曲线', backend: 'lifelines / survival',
            when: 'KM 曲线、风险人数、log-rank',
            params: [
              { key: 'risk', label: '风险人数表', options: [['yes', '要'], ['no', '不要']], default: 'yes' },
              { key: 'size', label: '尺寸', options: SIZE, default: 'nature1' },
            ],
            prompt: (p) => `用 sci-figure-kit 画 Kaplan-Meier 生存曲线：${p.risk === 'yes' ? '图下带风险人数表，' : ''}图上标 log-rank p 值，色盲友好配色，尺寸 ${p.size}，PNG + PDF。`,
          },
          {
            id: 'umap', title: 'UMAP / dotplot', backend: 'SCpubr',
            when: '单细胞降维图与 marker 表达',
            params: [
              { key: 'panel', label: '组合', options: [['both', 'UMAP + dotplot'], ['umap', '只要 UMAP']], default: 'both' },
              { key: 'size', label: '尺寸', options: SIZE, default: 'nature2' },
            ],
            prompt: (p) => `用 sci-figure-kit 画单细胞图：SCpubr（R），${p.panel === 'both' ? 'UMAP 按细胞类型着色并配 dotplot 展示 marker 基因' : '只出 UMAP，按细胞类型着色'}，尺寸 ${p.size}，PNG + PDF。`,
          },
          {
            id: 'multipanel', title: '多面板拼图', backend: 'marsilea',
            when: 'a/b/c 面板，统一字号',
            params: [
              { key: 'layout', label: '排布', options: [['1x2', '1 × 2'], ['1x3', '1 × 3'], ['2x2', '2 × 2']], default: '1x2' },
              { key: 'size', label: '总尺寸', options: SIZE, default: 'nature2' },
            ],
            prompt: (p) => `用 sci-figure-kit 把这几张图拼成 ${p.layout.replace('x', '×')} 多面板：marsilea（figkit），统一字体字号，面板标签放左上角，总尺寸 ${p.size}，PNG + PDF。`,
          },
          {
            id: 'fit', title: '拟合曲线', backend: 'scipy + matplotlib',
            when: '散点 + 趋势线：线性带 95% CI，或 4PL 剂量反应求 EC50',
            params: [
              { key: 'kind', label: '类型', options: [['linear', '线性 + CI'], ['4pl', '4PL / EC50']], default: 'linear' },
              { key: 'label', label: '标注', options: [['eq', '方程 + R²'], ['ec50', 'EC50 ± SE'], ['none', '不标']], default: 'eq' },
            ],
            prompt: (p) => `用 sci-figure-kit 画${p.kind === '4pl' ? ' 4PL 剂量反应曲线（log 轴、EC50 ± SE）' : '线性拟合曲线（散点 + 拟合线 + 95% 预测带 + 方程与 R²）'}，标注${p.label === 'none' ? '省略' : p.label === 'ec50' ? ' EC50' : '方程与 R²'}；按 references/plot-recipes.md 第 ${p.kind === '4pl' ? 2 : 1} 条的写法，注意对数轴刻度不要用 mathtext。`,
          },
          {
            id: 'sig-bar', title: '显著性柱状图', backend: 'statannotations',
            when: '柱 + 误差棒 + 散点 + 显著性括号；多组比较要校正',
            params: [
              { key: 'test', label: '检验', options: [['t-test_ind', 't 检验'], ['Mann-Whitney', 'Mann-Whitney']], default: 't-test_ind' },
              { key: 'corr', label: '多重校正', options: [['none', '不校正'], ['bonferroni', 'Bonferroni'], ['benjamini-hochberg', 'BH']], default: 'bonferroni' },
            ],
            prompt: (p) => `用 sci-figure-kit 画柱状图 + 误差棒 + 个体散点 + 显著性括号：statannotations，检验 ${p.test}，多重校正 ${p.corr === 'none' ? '关闭（并在图注注明）' : p.corr}，按 references/plot-recipes.md 第 3 条。`,
          },
          {
            id: 'violin', title: '小提琴图', backend: 'seaborn / ggpubr',
            when: '看分布形状：小提琴 + 内嵌箱线 + 散点',
            params: [
              { key: 'lang', label: '后端', options: [['py', 'Python (seaborn)'], ['r', 'R (ggpubr)']], default: 'py' },
              { key: 'inner', label: '内层', options: [['box', '箱线'], ['quart', '四分位']], default: 'box' },
            ],
            prompt: (p) => `用 sci-figure-kit 画小提琴图${p.lang === 'r' ? '（R + ggpubr，显著性用 geom_pwc + BH 校正）' : '（Python + seaborn：小提琴 + 内嵌箱线 + 抖动散点）'}，内层用${p.inner === 'box' ? '箱线' : '四分位线'}，按 references/plot-recipes.md 第 ${p.lang === 'r' ? 7 : 4} 条。`,
          },
          {
            id: 'corr', title: '相关性热图', backend: 'matplotlib',
            when: '多指标两两相关，下三角 + 数值 + RdBu 发散色标',
            params: [
              { key: 'method', label: '相关方法', options: [['pearson', 'Pearson'], ['spearman', 'Spearman']], default: 'pearson' },
              { key: 'value', label: '格内数值', options: [['yes', '显示 r'], ['no', '只留颜色']], default: 'yes' },
            ],
            prompt: (p) => `用 sci-figure-kit 画${p.method === 'spearman' ? ' Spearman' : ' Pearson'} 相关性热图：下三角、RdBu_r 且 vmin=-1 vmax=1、${p.value === 'yes' ? '格内标 r' : '不标数值'}，按 references/plot-recipes.md 第 5 条。`,
          },
        ],
      },
      {
        id: 'analysis',
        name: '分析',
        desc: '差异表达 · 富集 · 共表达 · 生存',
        extra: 'pydeseq2 / limma / gseapy / clusterProfiler / WGCNA',
        items: [
          {
            id: 'de-py', title: 'bulk 差异表达', backend: 'pydeseq2',
            when: '原始 counts + 分组，出 log2FC / padj',
            params: [
              { key: 'design', label: '设计式', options: [['~condition', '两组'], ['~condition + batch', '含批次协变量']], default: '~condition' },
              { key: 'lfc', label: '|log2FC| 阈值', options: [['1', '1.0'], ['0.5', '0.5']], default: '1' },
            ],
            prompt: (p) => `用 sci-figure-kit 的 pydeseq2 mod 做 bulk 差异表达：counts 行=样本、列=基因，design="${p.design}"，显著按 padj<0.05 且 |log2FC|>${p.lfc}，出 results/de.tsv 与 stats.json（含输入 sha256），显著数对账后再画火山图。`,
          },
          {
            id: 'de-r', title: '差异表达（R）', backend: 'limma',
            when: '芯片 / 已归一化数据 / 自定义对比',
            params: [
              { key: 'data', label: '数据类型', options: [['microarray', '芯片 log 表达'], ['voom', 'RNA-seq counts（voom）']], default: 'microarray' },
              { key: 'contrast', label: '对比', options: [['B-A', 'B vs A'], ['custom', '自定义 makeContrasts']], default: 'B-A' },
            ],
            prompt: (p) => `用 sci-figure-kit 的 limma mod 做差异表达：${p.data === 'voom' ? 'counts 走 voom 转换' : '芯片 log 表达直接 lmFit'}，design 矩阵 + ${p.contrast === 'custom' ? 'makeContrasts 自定义对比' : 'B-A 对比'}，topTable(number=Inf)，出 results/de.tsv 与 stats.json。`,
          },
          {
            id: 'enrich', title: '富集（离线 ORA）', backend: 'gseapy',
            when: '基因列表 + GMT + 背景，不联网',
            params: [
              { key: 'background', label: '背景', options: [['20000', '20000（全基因组）'], ['custom', '自定义基因列表']], default: '20000' },
              { key: 'cutoff', label: 'FDR 阈值', options: [['0.05', '0.05'], ['0.01', '0.01']], default: '0.05' },
            ],
            prompt: (p) => `用 sci-figure-kit 的 enrichment-gseapy mod 做 ORA：基因列表 + GMT，背景 ${p.background === 'custom' ? '用我提供的背景基因列表' : '20000'}，FDR < ${p.cutoff}，产出 results/enrichment.tsv + stats.json + analysis.md，并报告显著条数与 top 通路。`,
            cmd: (p) => `python "<skill>/mods/enrichment-gseapy/templates/ora.py" --genes sig.txt --sets h.all.gmt --background ${p.background === 'custom' ? 'bg.txt' : '20000'} --out results`,
          },
          {
            id: 'enrich-r', title: 'GO / KEGG 富集', backend: 'clusterProfiler',
            when: '要 GO 三本体或 KEGG 通路编号',
            params: [
              { key: 'ont', label: '本体', options: [['BP', 'BP'], ['CC', 'CC'], ['MF', 'MF'], ['KEGG', 'KEGG']], default: 'BP' },
              { key: 'padj', label: '校正', options: [['BH', 'BH'], ['bonferroni', 'Bonferroni']], default: 'BH' },
            ],
            prompt: (p) => `用 sci-figure-kit 的 clusterprofiler mod 做 ${p.ont} 富集：显式给 universe，pAdjustMethod=${p.padj}，输出 results/*.tsv 与 stats.json；先确认 org.Hs.eg.db 已装。`,
          },
          {
            id: 'wgcna', title: '共表达网络', backend: 'WGCNA',
            when: '≥15 样本，找模块与模块-性状关联',
            params: [
              { key: 'minmod', label: '最小模块', options: [['30', '30'], ['50', '50']], default: '30' },
              { key: 'power', label: '软阈值', options: [['auto', '自动估计'], ['12', '固定 12']], default: 'auto' },
            ],
            prompt: (p) => `用 sci-figure-kit 的 wgcna mod：goodSamplesGenes 查离群样本，${p.power === 'auto' ? 'pickSoftThreshold 自动选 power' : 'power 固定 12'}，blockwiseModules（minModuleSize=${p.minmod}）出模块，再算 module-trait 相关与 p 值，全部落 results/。`,
          },
          {
            id: 'surv-analysis', title: '生存分析', backend: 'lifelines / survival',
            when: 'KM 估计或 Cox 回归',
            params: [
              { key: 'model', label: '模型', options: [['km', 'KM + log-rank'], ['cox', 'Cox 多因素']], default: 'km' },
            ],
            prompt: (p) => `用 sci-figure-kit 做生存分析：${p.model === 'cox' ? 'Cox 比例风险模型，输出 HR 与 95% CI，检验 PH 假设' : 'KM 估计 + log-rank 检验，输出各组中位生存'}，结果落 results/（表 + stats.json + analysis.md）。`,
          },
          {
            id: 'dose-response', title: '剂量-反应 / EC50', backend: 'drc（R）',
            when: '急性毒性求 LC50/EC50 与置信区间；低剂量刺激用 hormesis',
            params: [
              { key: 'model', label: '模型', options: [['LL.4', 'LL.4（默认）'], ['LL.3', 'LL.3'], ['BC.5', 'BC.5（hormesis）']], default: 'LL.4' },
              { key: 'ed', label: 'ED 水平', options: [['10,50,90', '10/50/90'], ['50', '只要 50']], default: '10,50,90' },
            ],
            prompt: (p) => `用 sci-figure-kit 的 drc mod 拟合剂量-反应曲线：模型 ${p.model}，输出 ED${p.ed === '50' ? '50' : '10/50/90'} 及 delta 置信区间，产物落 results/（ed50.csv + 曲线图 + stats.json），选模型看 AIC。`,
          },
          {
            id: 'ssd', title: '物种敏感度分布 SSD', backend: 'ssdtools（R）',
            when: '多物种毒性值 → HC5 → PNEC（生态风险评估）',
            params: [
              { key: 'af', label: '评估因子 AF', options: [['10', '10（慢性）'], ['100', '100'], ['1000', '1000（急性）']], default: '10' },
              { key: 'dists', label: '分布', options: [['lnorm,llogis,gamma,burrIII3', '四分布加权'], ['lnorm', '仅 log-normal']], default: 'lnorm,llogis,gamma,burrIII3' },
            ],
            prompt: (p) => `用 sci-figure-kit 的 ssdtools mod 做 SSD：输入 species + Conc（单位统一 mg/L），分布 ${p.dists}，求 HC5 与 95% CI，PNEC = HC5/${p.af}，产出 hc5.csv / pnec.csv / ssd.png / stats.json。`,
          },
          {
            id: 'ppi', title: '靶点 PPI 网络', backend: 'network-tox',
            when: '网络毒理：毒物靶点取 PPI、排 hub、导出 Cytoscape',
            params: [
              { key: 'species', label: '物种', options: [['9606', '人'], ['10090', '小鼠'], ['7955', '斑马鱼']], default: '9606' },
              { key: 'score', label: '置信度', options: [['400', '400（中）'], ['700', '700（高）']], default: '400' },
            ],
            prompt: (p) => `用 sci-figure-kit 的 network-tox mod：物种 ${p.species}、STRING 阈值 ${p.score}，取 PPI 并算 degree/betweenness/clustering，排 hub 基因，导出 edges/nodes/hub_genes 与 graphml，孤立节点保留并在 stats 里报告。`,
            cmd: (p) => `python "<skill>/mods/network-tox/templates/ppi_network.py" --genes targets.txt --species ${p.species} --score ${p.score} --out results`,
          },
          {
            id: 'mixture', title: '混合物毒性', backend: 'CA / IA',
            when: '联合暴露：预测 EC50、判协同或拮抗',
            params: [
              { key: 'read', label: '判读', options: [['both', 'CA / IA 区间'], ['tu', 'TU 判定']], default: 'both' },
            ],
            prompt: (p) => `用 sci-figure-kit 的 mixture-tox mod 做联合毒性：单组分 4PL + 混合物比例，同时算 CA 与 IA 预测 EC50，${p.read === 'tu' ? '并用 TU=Σ(fi·C/EC50i) 判定协同/拮抗' : '看实测落在两个预测之间还是之外'}，产出 ec50.csv / curves.csv / stats.json 并写清判读依据。`,
            cmd: () => `python "<skill>/mods/mixture-tox/templates/mixture_ca_ia.py" --singles singles.csv --mixtures mixtures.csv --out results`,
          },
        ],
      },
      {
        id: 'software',
        name: '软件',
        desc: 'Prism / SPSS：配方 + 能力边界清单',
        extra: 'Prism ≈70 条脚本命令 · SPSS 328 条语法命令',
        items: [
          {
            id: 'prism-anova', title: 'ANOVA + 事后', backend: 'Prism',
            when: 'Tukey / Dunnett / Dunn，要显著性字母',
            params: [
              { key: 'posthoc', label: '事后检验', options: [['DUNNET', 'Dunnett'], ['TUKEY', 'Tukey'], ['DUNN', 'Dunn']], default: 'DUNNET' },
              { key: 'alpha', label: 'α', options: [['0.05', '0.05'], ['0.01', '0.01']], default: '0.05' },
            ],
            prompt: (p) => `用 sci-figure-kit 的 prism mod 跑单因素 ANOVA + ${p.posthoc}（α=${p.alpha}）：宽表 CSV 列数必须与 .prism 模板一致，Import → RecalcAll → 导出结果表与 SVG，脚本以 Exit 结尾；对照列不能删。`,
            cmd: (p) => `python "<skill>/mods/prism/templates/prism_run.py" --script job.pzc --workdir '<WORKDIR>' --timeout 180`,
          },
          {
            id: 'spss-probit', title: 'LC50 / Probit', backend: 'SPSS',
            when: '急性毒性，Prism 不做',
            params: [
              { key: 'ci', label: '置信区间', options: [['95', '95%'], ['90', '90%']], default: '95' },
              { key: 'transform', label: '剂量变换', options: [['NONE', '不转换'], ['LOG', '对数']], default: 'NONE' },
            ],
            prompt: (p) => `用 sci-figure-kit 的 spss mod 跑概率单位法估 LC50：PROBIT 连续剂量用 WITH，剂量变换 ${p.transform}，${p.ci}% 置信区间，写 .sps 后生成 .spj 生产作业，跑完解析输出，产出 lcx 表与 stats.json。`,
            cmd: () => `python "<skill>/mods/spss/templates/spss_run.py" --sps analysis.sps --workdir '<WORKDIR>' --timeout 300`,
          },
          {
            id: 'spss-mixed', title: '混合模型 / KW', backend: 'SPSS',
            when: 'MIXED、双因素简单效应、Kruskal-Wallis',
            params: [
              { key: 'cmd', label: '分析', options: [['MIXED', 'MIXED 混合模型'], ['UNIANOVA', 'UNIANOVA 简单效应'], ['KW', 'NPAR K-W']], default: 'MIXED' },
              { key: 'adj', label: '校正', options: [['BONFERRONI', 'Bonferroni'], ['SIDAK', 'Šidák']], default: 'BONFERRONI' },
            ],
            prompt: (p) => `用 sci-figure-kit 的 spss mod 跑 ${p.cmd}${p.cmd === 'KW' ? '' : '（事后校正 ' + p.adj + '）'}：语法里用 OMS 导出 OXML，跑完从 number 字段取全精度值，结果落 results/；注意别用 stats.exe foo.sps（会弹 GUI 挂死）。`,
            cmd: () => `& '<SPSS_DIR>/stats.exe' -production silent '<WORKDIR>/job.spj'`,
          },
        ],
      },
    ]

    const PALETTES = [
      {
        id: 'okabe', name: 'Okabe-Ito', note: '色盲安全 · 分类 ≤ 8 的首选 · 黑白打印也分得开',
        colors: ['#000000', '#E69F00', '#56B4E9', '#009E73', '#F0E442', '#0072B2', '#D55E00', '#CC79A7'],
      },
      {
        id: 'npg', name: 'NPG（Nature）', note: 'ggsci::scale_color_npg()',
        colors: ['#E64B35', '#4DBBD5', '#00A087', '#3C5488', '#F39B7F', '#8491B4', '#91D1C2', '#DC0000', '#7E6148', '#B09C85'],
      },
      {
        id: 'lancet', name: 'Lancet', note: 'ggsci::scale_color_lancet()',
        colors: ['#00468B', '#ED0000', '#42B540', '#0099B4', '#925E9F', '#FDAF91', '#AD002A', '#ADB6B6', '#1B1919'],
      },
      {
        id: 'nejm', name: 'NEJM', note: 'ggsci::scale_color_nejm()',
        colors: ['#BC3C29', '#0072B5', '#E18727', '#20854E', '#7876B1', '#6F99AD', '#FFDC91', '#EE4C97'],
      },
      {
        id: 'jco', name: 'JCO', note: 'ggsci::scale_color_jco()',
        colors: ['#0073C2', '#EFC000', '#868686', '#CD534C', '#7AA6DC', '#003C67', '#8F7700', '#3B3B3B', '#A73030', '#4A6990'],
      },
      {
        id: 'aaas', name: 'AAAS（Science）', note: 'ggsci::scale_color_aaas()',
        colors: ['#3B4992', '#EE0000', '#008B45', '#631879', '#008280', '#BB0021', '#5F559B', '#A20056', '#808180', '#1B1919'],
      },
      {
        id: 'tableau', name: 'Tableau 10', note: '通用、区分度高',
        colors: ['#4E79A7', '#F28E2B', '#E15759', '#76B7B2', '#59A14F', '#EDC948', '#B07AA1', '#FF9DA7', '#9C755F', '#BAB0AC'],
      },
      {
        id: 'tab10', name: 'tab10（matplotlib）', note: 'matplotlib 默认，最省事',
        colors: ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'],
      },
      {
        id: 'khroma-bright', name: 'bright（khroma）', note: '色盲友好 · Paul Tol 方案 · 最多 7 色',
        colors: ['#4477AA', '#EE6677', '#228833', '#CCBB44', '#66CCEE', '#AA3377', '#BBBBBB'],
      },
      {
        id: 'khroma-vibrant', name: 'vibrant（khroma）', note: '高饱和 · 色盲友好 · 6 色',
        colors: ['#EE7733', '#0077BB', '#33BBEE', '#EE3377', '#CC3311', '#009988'],
      },
      {
        id: 'set2', name: 'ColorBrewer Set2', note: 'palettable · 8 色定性 · 柔和',
        colors: ['#66C2A5', '#FC8D62', '#8DA0CB', '#E78AC3', '#A6D854', '#FFD92F', '#E5C494', '#B3B3B3'],
      },
      {
        id: 'carto-bold', name: 'Carto Bold', note: 'palettable · 5 色 · 对比强',
        colors: ['#7F3C8D', '#11A579', '#3969AC', '#F2B701', '#E73F74'],
      },
    ]

    const GRADIENTS = [
      { id: 'viridis', name: 'viridis', note: '默认连续量 · 感知均匀', stops: ['#440154', '#3b528b', '#21918c', '#5ec962', '#fde725'] },
      { id: 'cividis', name: 'cividis', note: '色盲安全更强的连续色标', stops: ['#00224e', '#123570', '#3b496c', '#7d7d6e', '#f1e6b2'] },
      { id: 'magma', name: 'magma', note: '热图（暗底亮高）', stops: ['#000004', '#3b0f70', '#8c2981', '#de4968', '#fe9f6d', '#fcfdbf'] },
      { id: 'inferno', name: 'inferno', note: '热图，对比更强', stops: ['#000004', '#420a68', '#932667', '#dd513a', '#fca50a', '#fcffa4'] },
      { id: 'rdbu', name: 'RdBu（发散）', note: 'z-score / log2FC：零点必须是中间色', stops: ['#67001f', '#d6604d', '#f7f7f7', '#4393c3', '#053061'] },
    ]

    /* -----------------------------------------------------------------------
     * 软件接口清单（Prism / SPSS）
     *
     * 状态纪律：status 只有三种，且每条都能追到证据。
     *   ok   = 本机实测跑通过（有产物/有数值）
     *   no   = 本机实测确认不可用（别再试，试了会挂死或静默失败）
     *   todo = 未验证（文档提到但没实测，不要当承诺）
     * 「坑」是必读的，不是备注 —— 这些坑会导致挂死或静默出错。
     * ----------------------------------------------------------------------- */
    const INTERFACES = [
      {
        id: 'prism', name: 'GraphPad Prism', version: '10.6.1',
        note: '只做分析、不出图：图样式存在二进制里，脚本改不了。出图交给 cnsplots / ggplot2。',
        entries: [
          {
            name: '.pzc 脚本', status: 'ok',
            usage: '唯一可用的调用入口。所有 Prism 自动化都从这里走。',
            cmd: '& \'<PRISM_DIR>\\prism.exe\' \'@<WORKDIR>\\job.pzc\'',
            evidence: '实测：7 组 ANOVA 的 F=70.0、p=4.97e-18，与 scipy+statsmodels 完全一致',
            gotchas: [
              '@ 后的路径必须传原生反斜杠（os.path.normpath）；用正斜杠会弹「文件无法打开」然后静默退出 rc=0',
              '脚本最后一行必须是 Exit，否则模态框永久挂死',
              '.pzc 按系统 ANSI（GBK）写，不能 UTF-8',
              '脚本与工作目录必须纯 ASCII',
            ],
          },
          {
            name: '.prism 工程文件', status: 'ok',
            usage: '模板与结果都在这。导入数据 → RecalcAll → Save → 解包读 results.json。',
            cmd: 'python "<skill>/mods/prism/templates/prism_analyze.py" --template oneway.prism --data panel.csv --out results',
            evidence: '实测：解包 .prism（zip）拿到 results.json，CLD 字母与 15/21 显著数均与 statsmodels 一致',
            gotchas: [
              'Import 用的是「按位置」导入：CSV 无表头、列数必须等于模板表的列数',
              'GoTo R n 的结果表编号推不出来，某些 view 报 No such sheet! 并挂死 —— 直接读 results.json',
            ],
          },
          {
            name: 'results.json 通用取数', status: 'ok',
            usage: '任何分析类型都能把数值叶子倒出来，不必按分析类型改代码。',
            cmd: 'python "<skill>/mods/prism/templates/prism_results.py" --results results.json --find "pValue"',
            evidence: '递归遍历整棵树，按 path 定位；--list 先摸结构，--tsv/--json 全量导出',
            gotchas: ['results.json 是 Save 之后才写进 .prism 的，模板本身里没有'],
          },
          {
            name: 'ANOVA + Tukey/Dunnett/Dunn', status: 'ok',
            usage: '要显著性字母（CLD）时用它 —— SPSS 27 拿不到这三个事后检验。',
            cmd: 'python "<skill>/mods/prism/templates/prism_analyze.py" --template oneway.prism --data panel.csv --out results',
            evidence: '实测产物：anova.csv / posthoc.csv / letters.csv / results.json',
            gotchas: ['参数锁在模板里，换数据不用改行数，但列数要一致'],
          },
          {
            name: 'COM / OLE 自动化', status: 'no',
            usage: '不可用，别再试。',
            cmd: '',
            evidence: '实测：没有 IDispatch / TypeLib，Prism.Command 的 LocalServer32 是空的',
            gotchas: [],
          },
          {
            name: '图样式脚本化', status: 'no',
            usage: '不可用。字体、柱形、误差棒、图例都在二进制里。',
            cmd: '',
            evidence: '实测：脚本无对应命令；只能靠模板预先配好样式',
            gotchas: [],
          },
        ],
      },
      {
        id: 'spss', name: 'IBM SPSS Statistics', version: '27.0.1',
        note: '无人值守只能走生产作业或进程内 Python。绝不能 stats.exe foo.sps（弹 GUI 挂死）。',
        entries: [
          {
            name: '生产作业（-production silent）', status: 'ok',
            usage: '无人值守、批量、结果落 OXML 的标准路径。',
            cmd: '& \'<SPSS_DIR>\\stats.exe\' -production silent \'<WORKDIR>\\job.spj\'',
            evidence: '实测：DESCRIPTIVES 产出 OXML，number="13.833333333333" 与源表一致',
            gotchas: [
              '.spj 里必须写 <syntax syntaxPath="..."/> 属性；写成元素文本会「作业成功」但零产物',
              '<output> 必须在 <syntax> 之前',
              '语法错时 SPSS 仍 exit 0，错误只在日志里 —— 要看日志不看退出码',
              '产物路径纯 ASCII，中文目录会静默不生成',
              'OXML 可能只写一半，解析前校验 </outputTree>',
            ],
          },
          {
            name: '进程内 Python（spss / spssdata）', status: 'ok',
            usage: '要直接读数、要快、要异常可见时优先用它 —— 比 OXML 好用。',
            cmd: '& \'<SPSS_DIR>\\Python3\\python.exe\' "<skill>/mods/spss/templates/spss_py.py" --sps analysis.sps --table agg.csv --out results',
            evidence: '实测：AGGREGATE 后读回 A=12.466666666666669、B=15.2，与源表一致',
            gotchas: ['字符串变量按声明宽度补齐（A8 读出来是 "A       "），落 CSV 前 .strip()'],
          },
          {
            name: 'PROBIT（LC50 / 概率单位）', status: 'ok',
            usage: '急性毒性求 LC50 与置信区间 —— 这是 SPSS 相对 Prism 的独有价值。',
            cmd: 'PROBIT deaths OF total WITH dose /MODEL=PROBIT /PRINT=CI.',
            evidence: '实测：/PRINT=CI 时 OXML 里 Confidence Limits 表直接给 LC50 与 95% CI（读 number 属性）',
            gotchas: [
              '连续剂量用 WITH，别用 BY',
              '/PRINT=CI 不能省：写成 NONE 会把 Confidence Limits 表一起关掉 —— 旧文档误以为「PROBIT 不进 OXML」，其实自己把表关了',
            ],
          },
          {
            name: 'OXML 取数', status: 'ok',
            usage: '把 pivotTable 倒成 tidy 表，不用每次手抠维度。',
            cmd: 'python "<skill>/mods/spss/templates/spss_ooxml.py" --list out.xml',
            evidence: '解析四类表：Confidence Limits / ChiSquareTests / Parameter Estimates / Cell Counts and Residuals',
            gotchas: [
              '每格有 number（全精度）与 text（显示值、已舍入）—— 要数字必须读 number',
              '缺失值 number 为空、text 可能是 "." —— 要落 None，不能当 0',
              '残缺 OXML 当硬错误，别返回空表冒充成功',
            ],
          },
          {
            name: 'MIXED / 简单效应 / KW', status: 'ok',
            usage: '混合模型、双因素简单效应、Kruskal-Wallis。',
            cmd: 'MIXED y BY time /FIXED=time | SSTYPE(3) /RANDOM=INTERCEPT | SUBJECT(id) COVTYPE(VC) /METHOD=REML.',
            evidence: '语法齐全（reference/commands.md 60 条）',
            gotchas: ['KW 的 H 与 scipy 逐位一致，不会像 Prism 那样挂死'],
          },
          {
            name: 'Tukey / Dunnett / Dunn', status: 'no',
            usage: 'SPSS 27 拿不到这三种事后检验，走 prism mod。',
            cmd: '',
            evidence: '实测：ADJ() 只有 Bonferroni / LSD / Šidák',
            gotchas: [],
          },
          {
            name: '显著性字母（CLD）', status: 'no',
            usage: 'SPSS 无原生输出，要自己按对比结果算；直接走 prism mod。',
            cmd: '',
            evidence: '实测：无对应过程',
            gotchas: [],
          },
          {
            name: 'COM（SPSS.Application16）', status: 'todo',
            usage: 'Excel/VBA 驱动才需要；本机 Python 没装 pywin32。',
            cmd: '',
            evidence: 'ProgID 已注册，但未装 pywin32，未跑通',
            gotchas: [],
          },
          {
            name: 'R 集成（RConsole / rcommute）', status: 'todo',
            usage: 'SPSS 调 R 或 R 调 SPSS；本机 R 独立可跑，绕这层没收益。',
            cmd: '',
            evidence: '未验证',
            gotchas: [],
          },
        ],
      },
    ]

    function safeTranslate(ctx) {
      const dict = DICT.zh
      try {
        if (ctx && ctx.locale && typeof ctx.locale.register === 'function') {
          for (const locale of Object.keys(DICT)) {
            const entries = Object.entries(DICT[locale])
              .filter(([, v]) => typeof v === 'string')
              .map(([k, v]) => [k, { message: v }])
            ctx.locale.register(NS, locale, Object.fromEntries(entries))
          }
          const bound = ctx.locale.bind(NS)
          return (key) => {
            const value = bound(key)
            return typeof value === 'string' && value && value !== key ? value : dict[key] || key
          }
        }
      } catch (error) { /* fall through */ }
      return (key) => dict[key] || key
    }

    const S = {
      page: {
        height: '100%', overflow: 'auto', padding: '26px 30px 44px',
        background: 'var(--dsw-alias-bg-base)', color: 'var(--dsw-alias-label-primary)',
        fontFamily: 'inherit', boxSizing: 'border-box',
      },
      header: { display: 'flex', alignItems: 'center', gap: 12, marginBottom: 4 },
      mark: {
        width: 34, height: 34, borderRadius: 9, display: 'flex', alignItems: 'center',
        justifyContent: 'center', background: 'var(--dsw-alias-bg-layer-2)',
        border: '1px solid var(--dsw-alias-border-l1)', color: 'var(--dsw-alias-brand-primary)',
      },
      title: { fontSize: 19, fontWeight: 600, margin: 0, lineHeight: 1.3 },
      subtitle: { fontSize: 12.5, color: 'var(--dsw-alias-label-secondary)', margin: '0 0 20px 46px' },
      grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 12 },
      folder: {
        background: 'var(--dsw-alias-bg-layer-1)', border: '1px solid var(--dsw-alias-border-l1)',
        borderRadius: 12, padding: '16px 18px', cursor: 'pointer', display: 'flex',
        flexDirection: 'column', gap: 6, minHeight: 108, textAlign: 'left',
        color: 'var(--dsw-alias-label-primary)', font: 'inherit',
      },
      folderName: { fontSize: 16, fontWeight: 600, display: 'flex', alignItems: 'center', justifyContent: 'space-between' },
      badge: { fontSize: 11, color: 'var(--dsw-alias-label-secondary)' },
      folderDesc: { fontSize: 12.5, color: 'var(--dsw-alias-label-secondary)', lineHeight: 1.5 },
      folderExtra: { fontSize: 11, color: 'var(--dsw-alias-label-secondary)', marginTop: 2 },
      back: {
        fontSize: 12.5, padding: '4px 10px', borderRadius: 7, cursor: 'pointer',
        border: '1px solid var(--dsw-alias-border-l1)', background: 'transparent',
        color: 'var(--dsw-alias-label-secondary)', fontFamily: 'inherit', marginBottom: 16,
      },
      row: {
        background: 'var(--dsw-alias-bg-layer-1)', border: '1px solid var(--dsw-alias-border-l1)',
        borderRadius: 10, padding: '12px 14px', cursor: 'pointer', display: 'flex',
        alignItems: 'baseline', justifyContent: 'space-between', gap: 12, textAlign: 'left',
        color: 'var(--dsw-alias-label-primary)', font: 'inherit', width: '100%',
      },
      rowTitle: { fontSize: 14, fontWeight: 600 },
      rowWhen: { fontSize: 12, color: 'var(--dsw-alias-label-secondary)' },
      chip: {
        fontSize: 10.5, padding: '2px 7px', borderRadius: 999,
        border: '1px solid var(--dsw-alias-border-l2)',
        color: 'var(--dsw-alias-label-secondary)', whiteSpace: 'nowrap',
      },
      card: {
        background: 'var(--dsw-alias-bg-layer-1)', border: '1px solid var(--dsw-alias-border-l1)',
        borderRadius: 12, padding: '16px 18px', display: 'flex', flexDirection: 'column', gap: 12,
      },
      label: { fontSize: 12, color: 'var(--dsw-alias-label-secondary)', display: 'block', marginBottom: 4 },
      input: {
        width: '100%', fontSize: 12.5, padding: '6px 9px', borderRadius: 7,
        border: '1px solid var(--dsw-alias-border-l1)', background: 'var(--dsw-alias-bg-base)',
        color: 'var(--dsw-alias-label-primary)', fontFamily: 'inherit', boxSizing: 'border-box',
      },
      preview: {
        margin: 0, padding: '10px 12px', borderRadius: 8, background: 'var(--dsw-alias-bg-base)',
        border: '1px solid var(--dsw-alias-border-l1)', fontSize: 12, lineHeight: 1.6,
        whiteSpace: 'pre-wrap', color: 'var(--dsw-alias-label-secondary)', maxHeight: 180, overflow: 'auto',
      },
      actions: { display: 'flex', gap: 8, flexWrap: 'wrap' },
      btn: {
        fontSize: 12, padding: '6px 12px', borderRadius: 7, cursor: 'pointer',
        color: 'var(--dsw-alias-brand-primary)', background: 'transparent',
        border: '1px solid var(--dsw-alias-border-l2)', fontFamily: 'inherit',
      },
      note: {
        marginTop: 22, paddingTop: 14, borderTop: '1px solid var(--dsw-alias-border-l1)',
        fontSize: 11.5, lineHeight: 1.7, color: 'var(--dsw-alias-label-secondary)', maxWidth: 720,
      },
    }

    function PanelIcon(props) {
      const size = (props && props.size) || 18
      return h('svg', { viewBox: '0 0 24 24', width: size, height: size, 'aria-hidden': true, style: { display: 'block' } },
        h('g', { fill: 'none', stroke: 'currentColor', strokeWidth: 1.7, strokeLinecap: 'round', strokeLinejoin: 'round' },
          h('path', { d: 'M4 3.5v17h16.5' }), h('path', { d: 'M7.5 17.5v-4.2' }),
          h('path', { d: 'M11 17.5V8.8' }), h('path', { d: 'M14.5 17.5v-6.4' }), h('path', { d: 'M18 17.5V6' })))
    }

    function copyText(event, text, t) {
      const button = event && event.currentTarget
      const label = button ? button.textContent : ''
      const settle = (msg) => {
        if (!button) return
        button.textContent = msg
        setTimeout(() => { if (button.isConnected) button.textContent = label }, 1400)
      }
      try {
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(text).then(() => settle(t('copied')), () => settle(t('failed')))
          return
        }
      } catch (error) { /* fall through */ }
      settle(t('failed'))
    }

    function makePanel(t) {
      const T = {
        tabs: { display: 'flex', gap: 6, marginBottom: 16, flexWrap: 'wrap', alignItems: 'center' },
        tab: {
          fontSize: 12.5, padding: '5px 12px', borderRadius: 999, cursor: 'pointer',
          border: '1px solid var(--dsw-alias-border-l1)', background: 'transparent',
          color: 'var(--dsw-alias-label-secondary)', fontFamily: 'inherit',
        },
        tabOn: { border: '1px solid var(--dsw-alias-brand-primary)', color: 'var(--dsw-alias-brand-primary)' },
        cardHead: { display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 10 },
        cardTitle: { fontSize: 14, fontWeight: 600 },
        when: { fontSize: 12, color: 'var(--dsw-alias-label-secondary)', lineHeight: 1.5 },
        params: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 8 },
        param: { display: 'flex', flexDirection: 'column', gap: 3 },
        paramLabel: { fontSize: 11, color: 'var(--dsw-alias-label-secondary)' },
        select: {
          width: '100%', fontSize: 12, padding: '4px 6px', borderRadius: 6,
          border: '1px solid var(--dsw-alias-border-l1)', background: 'var(--dsw-alias-bg-base)',
          color: 'var(--dsw-alias-label-primary)', fontFamily: 'inherit',
        },
        details: { fontSize: 11.5, color: 'var(--dsw-alias-label-secondary)' },
        summary: { cursor: 'pointer', userSelect: 'none' },
      }

      return function FigurePanel() {
        const [tab, setTab] = React.useState('all')
        const [values, setValues] = React.useState({})

        const groups = tab === 'all' ? FOLDERS : FOLDERS.filter((f) => f.id === tab)
        const items = []
        groups.forEach((g) => g.items.forEach((it) => items.push(it)))

        const paramValue = (item, p) => {
          const k = item.id + ':' + p.key
          return k in values ? values[k] : p.default
        }
        const setParam = (item, key, value) =>
          setValues((prev) => Object.assign({}, prev, { [item.id + ':' + key]: value }))

        // 「软件」页同时承载 Prism/SPSS 的配方与接口清单，所以不再单列一个
        // 「接口」标签 —— 两者本来就是同一件事的两种粒度（怎么调 / 能调什么）。
        const tabs = [['all', t('all')]]
          .concat(FOLDERS.map((f) => [f.id, f.name]))
          .concat([['palette', t('palette')]])
          .concat([['mods', t('mods')]])

        const card = (item) => {
          const params = item.params.reduce((acc, p) => { acc[p.key] = paramValue(item, p); return acc }, {})
          const prompt = item.prompt(params)
          const cmd = item.cmd ? item.cmd(params) : null
          return h('div', { key: item.id, style: S.card },
            h('div', { style: T.cardHead },
              h('span', { style: T.cardTitle }, item.title),
              h('span', { style: S.chip }, item.backend)),
            h('div', { style: T.when }, item.when),
            h('div', { style: T.params },
              item.params.map((p) => h('label', { key: p.key, style: T.param },
                h('span', { style: T.paramLabel }, p.label),
                h('select', {
                  style: T.select, value: paramValue(item, p),
                  onChange: (e) => setParam(item, p.key, e.target.value),
                }, p.options.map(([v, text]) => h('option', { key: v, value: v }, text)))))),
            h('details', { style: T.details },
              h('summary', { style: T.summary }, t('preview')),
              h('pre', { style: S.preview }, prompt)),
            h('div', { style: S.actions },
              h('button', { type: 'button', style: S.btn, onClick: (e) => copyText(e, prompt, t) }, t('copyPrompt')),
              cmd ? h('button', { type: 'button', style: S.btn, onClick: (e) => copyText(e, cmd, t) }, t('copyCmd')) : null))
        }

        const swatchRow = (colors, height) => h('div', {
          style: {
            display: 'flex', height: height || 34, borderRadius: 6, overflow: 'hidden',
            border: '1px solid var(--dsw-alias-border-l1)',
          },
        }, colors.map((c) => h('div', { key: c, title: c, style: { flex: '1 1 0', background: c } })))

        const mono = {
          fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
          fontSize: 10.5, color: 'var(--dsw-alias-label-secondary)', wordBreak: 'break-all',
        }

        const paletteView = () => h('div', { style: { display: 'grid', gap: 12 } },
          PALETTES.map((p) => h('div', { key: p.id, style: S.card },
            h('div', { style: T.cardHead },
              h('span', { style: T.cardTitle }, p.name),
              h('span', { style: S.chip }, p.colors.length + ' 色')),
            h('div', { style: T.when }, p.note),
            swatchRow(p.colors),
            h('div', { style: mono }, p.colors.join(' ')),
            h('div', { style: S.actions },
              h('button', { type: 'button', style: S.btn, onClick: (e) => copyText(e, p.colors.join(' '), t) }, t('copyHex')),
              h('button', { type: 'button', style: S.btn, onClick: (e) => copyText(e, 'palette = [' + p.colors.map((c) => '"' + c + '"').join(', ') + ']', t) }, t('copyPy')),
              h('button', { type: 'button', style: S.btn, onClick: (e) => copyText(e, 'pal <- c(' + p.colors.map((c) => '"' + c + '"').join(', ') + ')', t) }, t('copyR'))))),
          h('div', { style: S.card },
            h('div', { style: T.cardHead }, h('span', { style: T.cardTitle }, '连续色标'), h('span', { style: S.chip }, 'diverging / sequential')),
            GRADIENTS.map((g) => h('div', { key: g.id, style: { display: 'grid', gap: 5 } },
              h('div', { style: { display: 'flex', justifyContent: 'space-between', fontSize: 12 } },
                h('span', null, g.name),
                h('span', { style: { color: 'var(--dsw-alias-label-secondary)' } }, g.note)),
              h('div', {
                style: {
                  height: 16, borderRadius: 5, border: '1px solid var(--dsw-alias-border-l1)',
                  background: 'linear-gradient(to right, ' + g.stops.join(', ') + ')',
                },
              })))))

        /* ---------------------------------------------------------------
         * mod 装载页
         *
         * 数据来自 Host 路由 GET /dsh-sci-figure/mods（由 index.js 提供，
         * 底层是 `mod.py status --json`）。开关调 POST /dsh-sci-figure/mod-op。
         *
         * 三个刻意为之的决定：
         *  1. 软开关（enable/disable）与「彻底卸载」（remove）在 UI 上必须分开：
         *     前者可逆、后者删文件，混在一起迟早误删。
         *  2. 拿不到路由时只降级、不白屏 —— 面板的其余五个标签页照旧能用。
         *  3. 每个写操作先置 pending 再发请求，防连点重复提交。
         * ------------------------------------------------------------------- */
        const MODS_URL = '/dsh-sci-figure/mods'
        const MOD_OP_URL = '/dsh-sci-figure/mod-op'
        const CLIENT_HEADER = { 'content-type': 'application/json', 'x-sci-figure': '1' }

        const [mods, setMods] = React.useState(null)
        const [modsError, setModsError] = React.useState('')
        const [busy, setBusy] = React.useState({})
        const [confirming, setConfirming] = React.useState('')

        const loadMods = React.useCallback(() => {
          let cancelled = false
          fetch(MODS_URL, { headers: { 'x-sci-figure': '1' } })
            .then((r) => r.json())
            .then((body) => {
              if (cancelled) return
              if (body && body.ok && body.data) {
                setMods(body.data)
                setModsError('')
              } else {
                setMods(null)
                setModsError((body && body.error) || t('loadFailed'))
              }
            })
            .catch(() => {
              if (cancelled) return
              setMods(null)
              setModsError(t('loadFailed'))
            })
          return () => { cancelled = true }
        }, [t])

        // 只在第一次进这个标签页时拉一次；之后靠操作后手动刷新。
        React.useEffect(() => {
          if (tab !== 'mods' || mods !== null) return undefined
          return loadMods()
        }, [tab, mods, loadMods])

        const runModOp = (id, action) => {
          setBusy((prev) => Object.assign({}, prev, { [id]: action }))
          fetch(MOD_OP_URL, {
            method: 'POST',
            headers: CLIENT_HEADER,
            body: JSON.stringify({ action, id }),
          })
            .then((r) => r.json())
            .then((body) => {
              if (!body || !body.ok) {
                const detail = body && (body.stderr_tail || body.error)
                setModsError(`${action} ${id} 失败：${detail || '未知错误'}`)
              } else {
                setModsError('')
              }
            })
            .catch((err) => setModsError(`${action} ${id} 失败：${String(err && err.message ? err.message : err)}`))
            .finally(() => {
              setBusy((prev) => {
                const next = Object.assign({}, prev)
                delete next[id]
                return next
              })
              setConfirming('')
              // 重新拉一次，让开关状态以 Host 的真实结果为准，而不是本地猜。
              fetch(MODS_URL, { headers: { 'x-sci-figure': '1' } })
                .then((r) => r.json())
                .then((body) => { if (body && body.ok && body.data) setMods(body.data) })
                .catch(() => { /* 保留旧列表，错误已在上面提示 */ })
            })
        }

        const statusDot = (item) => {
          if (item.verify_ok === true) {
            return h('span', { title: t('verifyOk'), style: { color: '#2f9e44', fontSize: 12 } }, '●')
          }
          if (item.verify_ok === false) {
            return h('span', { title: t('verifyFail'), style: { color: '#e03131', fontSize: 12 } }, '●')
          }
          return h('span', { title: t('verifyNone'), style: { color: 'var(--dsw-alias-label-secondary)', fontSize: 12 } }, '○')
        }

        const toggle = (item) => {
          const on = Boolean(item.enabled)
          const pending = busy[item.id]
          return h('button', {
            type: 'button',
            disabled: Boolean(pending),
            title: on ? t('enabledOn') : t('enabledOff'),
            onClick: () => runModOp(item.id, on ? 'disable' : 'enable'),
            style: Object.assign({}, S.btn, {
              minWidth: 62,
              opacity: pending ? 0.55 : 1,
              cursor: pending ? 'wait' : 'pointer',
              borderColor: on ? 'var(--dsw-alias-brand-primary)' : 'var(--dsw-alias-border-l2)',
              color: on ? 'var(--dsw-alias-brand-primary)' : 'var(--dsw-alias-label-secondary)',
            }),
          }, pending === 'enable' || pending === 'disable'
            ? t('switching')
            : (on ? t('enabledOn') : t('enabledOff')))
        }

        const modCard = (item) => {
          const pending = busy[item.id]
          const noLicense = !item.license || item.license === 'none'
          const installing = pending === 'install'
          const removing = pending === 'remove'
          return h('div', { key: item.id, style: S.card },
            h('div', { style: T.cardHead },
              h('span', { style: { display: 'flex', alignItems: 'center', gap: 6 } },
                statusDot(item),
                h('span', { style: T.cardTitle }, item.name || item.id)),
              h('span', { style: S.chip }, item.purpose || 'plot')),
            h('div', { style: T.when },
              h('code', { style: { fontSize: 11, opacity: 0.8 } }, item.id),
              item.type ? ' · ' + item.type : '',
              item.env ? ' · env: ' + item.env : ''),
            h('div', { style: T.when }, item.summary || ''),
            h('div', { style: { display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' } },
              noLicense ? h('span', { style: Object.assign({}, S.chip, { color: '#e8590c', borderColor: '#e8590c' }) }, t('licenseWarn')) : null,
              item.source_kind ? h('span', { style: S.chip }, item.source_kind === 'local' ? t('srcLocal') : t('srcGithub')) : null,
              item.installed_at ? h('span', { style: { fontSize: 10.5, color: 'var(--dsw-alias-label-secondary)' } }, item.installed_at.slice(0, 10)) : null),
            item.source_url && item.source_kind !== 'local'
              ? h('a', {
                href: item.source_url, target: '_blank', rel: 'noreferrer',
                style: { fontSize: 11, color: 'var(--dsw-alias-brand-primary)', wordBreak: 'break-all' },
              }, item.source_url)
              : null,
            h('div', { style: S.actions },
              item.installed ? toggle(item) : null,
              !item.installed
                ? h('button', {
                  type: 'button', disabled: Boolean(pending),
                  onClick: () => runModOp(item.id, 'install'),
                  style: Object.assign({}, S.btn, { opacity: pending ? 0.55 : 1 }),
                }, installing ? t('installing') : t('btnInstall'))
                : null,
              // 彻底卸载：危险操作，先出内联确认条，绝不用 window.confirm
              item.installed
                ? h('button', {
                  type: 'button', disabled: Boolean(pending),
                  onClick: () => setConfirming(confirming === item.id ? '' : item.id),
                  style: Object.assign({}, S.btn, { color: '#e03131', borderColor: '#e03131', opacity: pending ? 0.55 : 1 }),
                }, removing ? t('removing') : t('btnRemove'))
                : null),
            confirming === item.id
              ? h('div', {
                style: {
                  display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap',
                  padding: '8px 10px', borderRadius: 8,
                  border: '1px solid #e03131', background: 'var(--dsw-alias-bg-base)',
                },
              },
              h('span', { style: { fontSize: 12, color: '#e03131' } }, t('btnUninstallConfirm')),
              h('button', {
                type: 'button',
                onClick: () => runModOp(item.id, 'remove'),
                style: Object.assign({}, S.btn, { color: '#e03131', borderColor: '#e03131' }),
              }, t('btnRemove')),
              h('button', {
                type: 'button', onClick: () => setConfirming(''),
                style: S.btn,
              }, t('btnCancel')))
              : null)
        }

        const modsView = () => {
          if (modsError && mods === null) {
            return h('div', { style: S.card },
              h('div', { style: T.cardHead }, h('span', { style: T.cardTitle }, t('mods'))),
              h('div', { style: T.when }, modsError))
          }
          if (mods === null) {
            return h('div', { style: T.when }, '…')
          }
          const list = Array.isArray(mods.mods) ? mods.mods : []
          const installed = list.filter((m) => m.installed)
          const pendingList = list.filter((m) => !m.installed && m.has_manifest)
          const candidates = list.filter((m) => !m.installed && !m.has_manifest)
          const counts = mods.count || mods.summary || {}
          const group = (title, arr) => arr.length === 0 ? null : h('div', { style: { display: 'grid', gap: 10 } },
            h('div', { style: { fontSize: 12.5, fontWeight: 600, marginTop: 4 } }, `${title} · ${arr.length}`),
            h('div', { style: S.grid }, arr.map(modCard)))

          return h('div', { style: { display: 'grid', gap: 14 } },
            h('div', { style: S.card },
              h('div', { style: T.cardHead },
                h('span', { style: T.cardTitle }, t('mods')),
                h('span', { style: S.chip },
                  `${t('colTotal')} ${counts.total || list.length} · ${t('colInstalled')} ${counts.installed || installed.length}`)),
              h('div', { style: T.when }, t('modsIntro')),
              h('div', { style: { display: 'flex', gap: 14, flexWrap: 'wrap', fontSize: 12 } },
                h('span', null, `${t('colEnabled')}: ${counts.enabled === undefined ? '-' : counts.enabled}`),
                h('span', null, `${t('colDisabled')}: ${counts.disabled === undefined ? '-' : counts.disabled}`),
                h('span', null, `${t('candidateGroup')}: ${counts.catalog === undefined ? candidates.length : counts.catalog}`)),
              h('div', { style: { fontSize: 11, color: 'var(--dsw-alias-label-secondary)' } }, t('noLicenseNote')),
              h('div', { style: S.actions },
                h('button', { type: 'button', style: S.btn, onClick: () => loadMods() }, '↻ 刷新'))),
            modsError ? h('div', { style: Object.assign({}, T.when, { color: '#e03131' }) }, modsError) : null,
            installed.length || pendingList.length || candidates.length
              ? null
              : h('div', { style: T.when }, t('emptyMods')),
            group(t('installedGroup'), installed),
            group(t('pendingGroup'), pendingList),
            group(t('candidateGroup'), candidates))
        }

        const STATUS_COLOR = {
          ok: { fg: '#2f9e44', bg: 'transparent' },
          no: { fg: '#e03131', bg: 'transparent' },
          todo: { fg: 'var(--dsw-alias-label-secondary)', bg: 'transparent' },
        }

        const interfacesView = () => {
          const total = INTERFACES.reduce((n, g) => n + g.entries.length, 0)
          return h('div', { style: { display: 'grid', gap: 14 } },
            h('div', { style: S.card },
              h('div', { style: T.cardHead },
                h('span', { style: T.cardTitle }, t('interfaces')),
                h('span', { style: S.chip }, `${total} 条`)),
              h('div', { style: T.when }, t('interfacesIntro')),
              h('div', { style: { display: 'flex', gap: 14, flexWrap: 'wrap', fontSize: 12 } },
                h('span', { style: { color: '#2f9e44' } }, `● ${t('ifaceAvailable')}`),
                h('span', { style: { color: '#e03131' } }, `● ${t('ifaceUnavailable')}`),
                h('span', { style: { color: 'var(--dsw-alias-label-secondary)' } }, `○ ${t('ifaceUnverified')}`))),
            INTERFACES.map((group) => h('div', { key: group.id, style: { display: 'grid', gap: 10 } },
              h('div', { style: { fontSize: 13, fontWeight: 600, marginTop: 6 } },
                `${group.name}  ·  ${group.version}`),
              h('div', { style: { fontSize: 12, color: 'var(--dsw-alias-label-secondary)', lineHeight: 1.55 } },
                group.note),
              h('div', { style: S.grid },
                group.entries.map((e) => {
                  const col = STATUS_COLOR[e.status] || STATUS_COLOR.todo
                  const label = e.status === 'ok' ? t('ifaceAvailable')
                    : (e.status === 'no' ? t('ifaceUnavailable') : t('ifaceUnverified'))
                  return h('div', { key: e.name, style: S.card },
                    h('div', { style: T.cardHead },
                      h('span', { style: { display: 'flex', alignItems: 'center', gap: 6 } },
                        h('span', { style: { color: col.fg, fontSize: 12 } }, '●'),
                        h('span', { style: T.cardTitle }, e.name)),
                      h('span', { style: Object.assign({}, S.chip, { color: col.fg, borderColor: col.fg }) }, label)),
                    h('div', { style: T.when }, e.usage),
                    e.evidence
                      ? h('div', { style: { fontSize: 11.5, color: 'var(--dsw-alias-label-secondary)', lineHeight: 1.5 } },
                        `${t('ifaceEvidence')}：${e.evidence}`)
                      : null,
                    e.gotchas && e.gotchas.length
                      ? h('div', {
                        style: {
                          borderLeft: '3px solid #e8590c', paddingLeft: 8,
                          fontSize: 11.5, lineHeight: 1.55, color: 'var(--dsw-alias-label-secondary)',
                        },
                      },
                      h('div', { style: { color: '#e8590c', fontWeight: 600, marginBottom: 2 } }, t('ifaceWarning')),
                      e.gotchas.map((g, i) => h('div', { key: i }, '· ' + g)))
                      : null,
                    e.cmd
                      ? h('pre', { style: S.preview }, e.cmd)
                      : null,
                    e.cmd
                      ? h('div', { style: S.actions },
                        h('button', { type: 'button', style: S.btn, onClick: (ev) => copyText(ev, e.cmd, t) }, t('ifaceCmd')))
                      : null)
                })))))
        }

        return h('div', { style: S.page },
          h('div', { style: S.header }, h('span', { style: S.mark }, h(PanelIcon, { size: 20 })), h('h1', { style: S.title }, t('title'))),
          h('p', { style: S.subtitle }, t('subtitle')),
          h('div', { style: T.tabs },
            tabs.map(([id, label]) => h('button', {
              key: id, type: 'button',
              style: Object.assign({}, T.tab, tab === id ? T.tabOn : null),
              onClick: () => setTab(id),
            }, label)),
            h('span', { style: { fontSize: 11.5, color: 'var(--dsw-alias-label-secondary)', marginLeft: 4 } },
              (tab === 'palette' || tab === 'mods') ? '' : items.length + ' ' + t('items'))),
          tab === 'palette'
            ? paletteView()
            : (tab === 'mods'
              ? modsView()
              : (tab === 'software'
                // 软件页：上半是可直接复制的配方，下半是能力边界清单。
                // 把两者放一起是因为它们回答同一个问题——「Prism/SPSS 我能拿来干什么」。
                ? h('div', { style: { display: 'grid', gap: 16 } },
                  h('div', { style: { display: 'grid', gap: 10 } },
                    h('div', { style: { fontSize: 13, fontWeight: 600 } },
                      t('softwareRecipes')),
                    h('div', { style: S.grid }, items.map(card))),
                  interfacesView())
                : h('div', { style: S.grid }, items.map(card)))),
          h('p', { style: S.note }, t('note')))
      }
    }

    return {
      inject: ['slots'],
      apply(ctx) {
        const t = safeTranslate(ctx)
        ctx.slots.inject('sidebar.panellist', () =>
          ctx.slots.register({ name: 'sidebar.panellist', id: 'sci-figures', order: 20, label: () => t('panelLabel') }, PanelIcon))
        ctx.slots.inject('main', () => ctx.slots.register({ name: 'main', key: 'sci-figures' }, makePanel(t)))
      },
    }
  },
})
