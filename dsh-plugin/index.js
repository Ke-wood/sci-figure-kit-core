/**
 * Host half of the sci-figure-kit bridge.
 *
 * Two model-facing tools wrap the local skill's scripts with fixed, absolute
 * commands and a small argument allowlist. Nothing here takes a shell string:
 * every invocation is `execFile(file, args)` with validated values.
 */
import { execFile } from 'node:child_process'
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs'
import { dirname, isAbsolute, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

/**
 * The skill root is resolved at runtime, never baked in.
 *
 * Two reasons: this package ships inside the public core repo, whose
 * `check_repo_hygiene.py` fails the build on any author-machine path; and a
 * hard-coded root is exactly the bug that made these tools run an old tree.
 *
 * Order: SCI_FIG_KIT env var → sibling checkout (../../sci-figure-kit-core
 * relative to this file) → the user's installed DSH skill → the Claude skill.
 */
function firstExisting(candidates) {
  for (const dir of candidates) {
    if (dir && existsSync(join(dir, 'scripts'))) return dir
  }
  return null
}

/**
 * A candidate is only usable if it actually carries mod data.
 *
 * Why this exists: the sibling checkout (`../sci-figure-kit-core`) is a SOURCE
 * repo whose `mods/` holds just `_template` — no `_catalog.json`, no manifests.
 * It still has `scripts/`, so a naive "does scripts/ exist" check picks it and
 * every panel install then dies with "没有这个 mod". The installed skill, which
 * does have the real mods, sits later in the list and never gets a chance.
 *
 * So rank candidates: one with a mods/_catalog.json or any manifest wins;
 * scripts-only remains a last resort (enough for env checks and workbench).
 */
function hasModData(dir) {
  if (!dir) return false
  const modsDir = join(dir, 'mods')
  if (!existsSync(modsDir)) return false
  if (existsSync(join(modsDir, '_catalog.json'))) return true
  try {
    for (const name of readdirSync(modsDir)) {
      if (name.startsWith('_') || name.startsWith('.')) continue
      if (existsSync(join(modsDir, name, 'mod.json'))) return true
    }
  } catch {
    return false
  }
  return false
}

function pickKit(candidates) {
  const usable = candidates.filter((d) => d && existsSync(join(d, 'scripts')))
  if (usable.length === 0) return null
  const withMods = usable.find((d) => hasModData(d))
  return withMods || usable[0]
}

function resolveKit() {
  // import.meta.url is the profile's linked copy, so walk up from the REAL
  // file location only as a hint; the env var stays authoritative.
  let here = ''
  try {
    here = dirname(fileURLToPath(import.meta.url))
  } catch {
    here = ''
  }
  const home = process.env.USERPROFILE || process.env.HOME || ''
  // 注意：用户已安装的技能目录**排在兄弟 checkout 之前**。兄弟 checkout 是
  // 源码仓库，它的 mods/ 只有 _template，拿它跑 install 会全失败。
  const found = pickKit([
    process.env.SCI_FIG_KIT,
    home ? join(home, '.dsh', 'skills', 'sci-figure-kit') : '',
    home ? join(home, '.claude', 'skills', 'sci-figure-kit') : '',
    here ? resolve(here, '..', 'sci-figure-kit-core') : '',
    here ? resolve(here, '..') : '',
  ])
  if (found === null) {
    throw new Error('找不到 sci-figure-kit 技能目录；设 SCI_FIG_KIT 指向含 SKILL.md 的目录。')
  }
  return found
}

/**
 * Resolved lazily on first use, not at module load.
 *
 * Throwing here while the module is being imported would take the whole panel
 * down on a machine where the skill is missing or laid out differently — and
 * the panel's static tabs (recipes, palettes) do not need the skill at all.
 * Failing at call time instead keeps the UI usable and reports the problem as
 * a tool error the model can actually read.
 */
let kitCache = null

function kitRoot() {
  if (kitCache === null) kitCache = resolveKit()
  return kitCache
}

function kitScripts() {
  return join(kitRoot(), 'scripts')
}

/** Workbench projects root: explicit env var, else SCI_FIG_ROOT layout, else undefined. */
function resolveProjects() {
  if (process.env.SCI_FIG_PROJECTS) return process.env.SCI_FIG_PROJECTS
  const root = process.env.SCI_FIG_ROOT
  return root ? join(root, 'workbench', 'projects') : null
}

const PROJECTS = resolveProjects()

const PRESETS = ['nature1', 'nature2', 'science1', 'science2', 'cell1', 'cell2']

const PY_CANDIDATES = ['python', 'py']
let pythonPath = null

function execOnce(file, args, timeoutMs) {
  return new Promise((resolve) => {
    execFile(
      file,
      args,
      { timeout: timeoutMs, windowsHide: true, maxBuffer: 16 * 1024 * 1024, encoding: 'utf8' },
      (err, stdout, stderr) => {
        resolve({
          ok: !err,
          code: err && typeof err.code === 'number' ? err.code : 0,
          killed: Boolean(err && err.killed),
          stdout: stdout || '',
          stderr: stderr || '',
          message: err ? String(err.message || err) : '',
        })
      },
    )
  })
}

async function resolvePython() {
  if (pythonPath) return pythonPath
  for (const candidate of PY_CANDIDATES) {
    if (candidate === 'py' || candidate === 'python') {
      const probe = await execOnce(candidate, ['-c', 'import sys;print(sys.version_info[0])'], 20000)
      if (probe.ok && probe.stdout.trim().startsWith('3')) {
        pythonPath = candidate
        return pythonPath
      }
    } else if (existsSync(candidate)) {
      pythonPath = candidate
      return pythonPath
    }
  }
  throw new Error('找不到可用的 Python 解释器（尝试过 python / py）；可用 SCI_FIG_PYTHON 指定。')
}

async function runPython(args, timeoutMs) {
  const py = await resolvePython()
  return execOnce(py, args, timeoutMs)
}

function tail(text, limit = 4000) {
  const trimmed = (text || '').trim()
  return trimmed.length > limit ? `${trimmed.slice(0, limit)}\n…（截断）` : trimmed
}

function parseJson(text) {
  const raw = (text || '').trim()
  if (!raw) return null
  try {
    return JSON.parse(raw)
  } catch {
    const start = raw.indexOf('{')
    const end = raw.lastIndexOf('}')
    if (start >= 0 && end > start) {
      try {
        return JSON.parse(raw.slice(start, end + 1))
      } catch {
        return null
      }
    }
    return null
  }
}

function safeProjectName(value) {
  return typeof value === 'string' && /^[A-Za-z0-9_.\-\u4e00-\u9fff ]{1,64}$/.test(value) && !value.includes('..')
}

function resolveProject(value) {
  if (typeof value !== 'string' || value.length === 0) throw new Error('缺少 project 参数。')
  if (isAbsolute(value)) {
    if (value.includes('..') || !existsSync(value)) throw new Error(`项目目录不存在：${value}`)
    return value
  }
  if (!safeProjectName(value)) throw new Error(`项目名不合法：${value}`)
  if (PROJECTS === null) {
    throw new Error('没配置工作台根目录：设 SCI_FIG_PROJECTS，或设 SCI_FIG_ROOT 让项目落在 <root>/workbench/projects。')
  }
  const dir = join(PROJECTS, value)
  if (!existsSync(dir)) throw new Error(`工作台里没有项目「${value}」，先用 action=list 看看。`)
  return dir
}

function validateData(value) {
  if (typeof value !== 'string' || !isAbsolute(value)) throw new Error('data 必须是绝对路径。')
  if (!/\.(csv|tsv|txt)$/i.test(value)) throw new Error('data 只接受 .csv / .tsv / .txt。')
  if (!existsSync(value)) throw new Error(`数据文件不存在：${value}`)
  return value
}

function validateTemplate(value) {
  const m = /^([a-z0-9][a-z0-9-]*):([A-Za-z0-9_./-]+)$/.exec(value || '')
  if (!m || value.includes('..')) throw new Error('template 必须形如 <mod-id>:templates/xxx.py')
  return value
}

function listTemplates() {
  const out = []
  const modsDir = join(kitRoot(), 'mods')
  if (!existsSync(modsDir)) return out
  for (const id of readdirSync(modsDir)) {
    const dir = join(modsDir, id, 'templates')
    if (!existsSync(dir) || !statSync(dir).isDirectory()) continue
    for (const file of readdirSync(dir)) {
      if (file.startsWith('.')) continue
      out.push(`${id}:templates/${file}`)
    }
  }
  return out.sort()
}

function listProjects() {
  if (PROJECTS === null || !existsSync(PROJECTS)) return []
  const out = []
  for (const name of readdirSync(PROJECTS)) {
    const dir = join(PROJECTS, name)
    if (!statSync(dir).isDirectory()) continue
    let project = null
    try {
      project = JSON.parse(readFileSync(join(dir, 'project.json'), 'utf8'))
    } catch {
      project = null
    }
    const entry = { name }
    if (project && project.size) entry.preset = String(project.size)
    if (project) entry.diverged = Boolean(project.diverged)
    if (project && project.vector) entry.vector = String(project.vector)
    out.push(entry)
  }
  return out
}

async function actionStatus() {
  const script = join(kitScripts(), 'check_envs.py')
  const res = await runPython([script, '--json'], 600000)
  const parsed = parseJson(res.stdout)
  if (!parsed || !Array.isArray(parsed.results)) {
    return {
      ok: false,
      summary: `自检没能返回 JSON（exit ${res.code}）。\n${tail(res.stderr || res.stdout)}`,
      data: null,
    }
  }
  const failed = parsed.results.filter((r) => r.ok === false)
  const summary = failed.length
    ? `环境自检：${parsed.pass} PASS / ${parsed.fail} FAIL / ${parsed.skip} SKIP；未通过：${failed.map((r) => r.probe).join('、')}`
    : `环境自检：${parsed.pass} PASS / 0 FAIL / ${parsed.skip} SKIP，三个后端可用。`
  return { ok: failed.length === 0, summary, data: parsed }
}

async function actionMods() {
  const script = join(kitScripts(), 'mod.py')
  const res = await runPython([script, 'verify'], 600000)
  const text = tail(res.stdout + (res.stderr ? `\n${res.stderr}` : ''))
  return {
    ok: res.ok,
    summary: res.ok ? '已装载的 mod 全部通过 verify。' : `mod verify 失败（exit ${res.code}）。`,
    data: text,
  }
}

async function actionProjects() {
  const projects = listProjects()
  return {
    ok: true,
    summary: projects.length
      ? `工作台里有 ${projects.length} 个项目：${projects.map((p) => p.name).join('、')}`
      : '工作台里还没有项目，用 action=new 建一个。',
    data: projects,
  }
}

async function actionTemplates() {
  const templates = listTemplates()
  return {
    ok: true,
    summary: `可用起步模板 ${templates.length} 个。`,
    data: templates,
  }
}

async function actionNew(args) {
  if (!safeProjectName(args.name || '')) throw new Error('name 必须是 1–64 位的字母数字、汉字、空格、点、下划线或短横线。')
  if (!args.data && !args.template) throw new Error('new 至少需要 data 或 template 之一。')
  if (args.preset && !PRESETS.includes(args.preset)) throw new Error(`preset 只能是 ${PRESETS.join(' / ')}。`)

  const script = join(kitScripts(), 'workbench.py')
  const cmd = [script, 'new', args.name]
  if (args.data) cmd.push('--data', validateData(args.data))
  if (args.template) cmd.push('--from', validateTemplate(args.template))
  if (args.preset) cmd.push('--preset', args.preset)

  const res = await runPython(cmd, 180000)
  const text = tail(res.stdout + (res.stderr ? `\n${res.stderr}` : ''))
  return {
    ok: res.ok,
    summary: res.ok ? `已建项目「${args.name}」。` : `建项目失败（exit ${res.code}）。`,
    data: text,
  }
}

async function actionRender(args) {
  const project = resolveProject(args.project)
  const script = join(kitScripts(), 'workbench.py')
  const res = await runPython([script, 'render', project, '--json'], 600000)
  const envelope = parseJson(res.stdout)
  const text = tail(res.stdout + (res.stderr ? `\n${res.stderr}` : ''))
  if (!envelope) {
    return {
      ok: false,
      summary: `渲染没能返回 JSON（exit ${res.code}）。`,
      data: text,
    }
  }
  return {
    ok: res.ok && envelope.ok !== false,
    summary: `渲染完成：${res.ok ? '闸门见 data.gates' : `exit ${res.code}`}`,
    data: envelope,
  }
}

async function actionReport(args) {
  const project = resolveProject(args.project)
  const script = join(kitScripts(), 'workbench.py')
  const res = await runPython([script, 'report', project, '--no-open'], 300000)
  const text = tail(res.stdout + (res.stderr ? `\n${res.stderr}` : ''))
  return {
    ok: res.ok,
    summary: res.ok ? '报告已生成（自包含 HTML，路径见 data）。' : `生成报告失败（exit ${res.code}）。`,
    data: text,
  }
}

const textRender = (args, value) => {
  if (typeof value === 'string') return [{ type: 'text', text: value }]
  const summary = value && typeof value.summary === 'string' ? value.summary : ''
  const data = value && value.data !== undefined ? value.data : value
  const body = typeof data === 'string' ? data : JSON.stringify(data, null, 2)
  return [{ type: 'text', text: `${summary}\n\n${body}`.trim() }]
}

export const inject = ['tools', 'webServer']

/* ---------------------------------------------------------------------------
 * Panel ↔ Host route
 *
 * The panel used to be pure static content, so "toggle a mod" had nowhere to
 * go. These two routes give it a narrow, audited write path:
 *
 *   GET  /dsh-sci-figure/mods     → `mod.py status --json` (read)
 *   POST /dsh-sci-figure/mod-op   → enable | disable | install | remove
 *
 * Security notes, in the order they matter:
 *  1. Plugin routes bypass the web server's auth gate. A cross-site `fetch`
 *     cannot attach a custom header without a CORS preflight this host does
 *     not answer, so `x-sci-figure: 1` is what keeps arbitrary pages out.
 *  2. `id` is checked against the ids the status call actually reported —
 *     never interpolated into a path. `action` is a closed set.
 *  3. Only `execFile(file, args)` with fixed argv. No shell string anywhere.
 *  4. enable/disable are reversible; remove deletes files, so it is a separate
 *     action the panel asks twice for.
 * ------------------------------------------------------------------------- */
const ROUTE_PREFIX = '/dsh-sci-figure'
const CLIENT_HEADER = 'x-sci-figure'

/** Ops the route accepts, with their timeouts. install is slow (network + pip). */
const MOD_OPS = {
  enable: { verb: 'enable', timeoutMs: 120000 },
  disable: { verb: 'disable', timeoutMs: 120000 },
  install: { verb: 'install', timeoutMs: 900000, extra: ['--yes'] },
  remove: { verb: 'remove', timeoutMs: 300000, extra: ['--yes'] },
}

const MOD_ID_RE = /^[a-z0-9][a-z0-9._-]{0,63}$/

function sendJson(res, code, payload) {
  res.writeHead(code, { 'content-type': 'application/json; charset=utf-8' })
  res.end(JSON.stringify(payload))
}

function readJsonBody(req) {
  return new Promise((resolve) => {
    let body = ''
    req.on('data', (chunk) => {
      body += chunk
      if (body.length > 65536) req.destroy()
    })
    req.on('end', () => {
      try {
        resolve(body ? JSON.parse(body) : {})
      } catch {
        resolve({})
      }
    })
    req.on('error', () => resolve({}))
  })
}

async function modsStatus() {
  const res = await runPython([join(kitScripts(), 'mod.py'), 'status', '--json'], 180000)
  const parsed = parseJson(res.stdout)
  if (!parsed) {
    return {
      ok: false,
      error: `mod.py status --json 没能返回 JSON（exit ${res.code}）`,
      detail: tail(res.stderr || res.stdout, 1200),
    }
  }
  return { ok: true, data: parsed }
}

async function modOp(action, id) {
  const spec = MOD_OPS[action]
  if (!spec) throw new Error(`未知 action：${action}`)
  if (typeof id !== 'string' || !MOD_ID_RE.test(id) || id.includes('..'))
    throw new Error(`mod id 不合法：${id}`)

  // Refuse ids that are not actually known — a typo should fail here, not
  // become an argv element that mod.py has to interpret.
  const status = await modsStatus()
  if (!status.ok) {
    return { ok: false, action, id, error: '无法读取 mod 列表，操作已取消', detail: status.detail }
  }
  const known = (status.data.mods || []).some((m) => m.id === id)
  if (!known) {
    return { ok: false, action, id, error: `没有这个 mod：${id}` }
  }

  const args = [join(kitScripts(), 'mod.py'), spec.verb, id].concat(spec.extra || [])
  const res = await runPython(args, spec.timeoutMs)
  return {
    ok: res.ok,
    action,
    id,
    exit_code: res.code,
    stdout_tail: tail(res.stdout, 2000),
    stderr_tail: tail(res.stderr, 2000),
  }
}

async function handleRoute(req, res) {
  const url = new URL(req.url || '/', 'http://dsh')
  const path = url.pathname.slice(ROUTE_PREFIX.length) || '/'

  if (req.method === 'GET' && (path === '/mods' || path === '/')) {
    try {
      const status = await modsStatus()
      sendJson(res, status.ok ? 200 : 500, status)
    } catch (error) {
      sendJson(res, 500, { ok: false, error: String(error && error.message ? error.message : error) })
    }
    return
  }

  if (req.method === 'POST' && path === '/mod-op') {
    if (req.headers[CLIENT_HEADER] !== '1') {
      sendJson(res, 403, { ok: false, error: 'missing client header' })
      return
    }
    try {
      const body = await readJsonBody(req)
      const result = await modOp(String(body.action || ''), String(body.id || ''))
      sendJson(res, result.ok ? 200 : 400, result)
    } catch (error) {
      sendJson(res, 400, { ok: false, error: String(error && error.message ? error.message : error) })
    }
    return
  }

  sendJson(res, 404, { ok: false, error: `no route: ${path}` })
}

export function apply(ctx) {
  ctx.tools.register({
    name: 'sci_figure_env',
    description:
      'Inspect the local scientific-figure toolchain before drawing: the three isolated backends (Python figkit with cnsplots, R with ggplot2/ComplexHeatmap/SCpubr, omicverse) and the installed figure mods. Use action=status for the 11-probe health check and action=mods to verify installed plotting mods. Returns pass/fail detail with a fix hint per probe.',
    parameters: {
      type: 'object',
      properties: {
        action: {
          type: 'string',
          enum: ['status', 'mods'],
          description: 'status = environment health; mods = verify installed figure mods.',
        },
      },
      required: ['action'],
      additionalProperties: false,
    },
    output: {
      schema: { type: 'object', additionalProperties: true },
      render: textRender,
    },
    timeoutMs: 660000,
    isConcurrencySafe: () => false,
    async execute(args) {
      return args.action === 'mods' ? actionMods() : actionStatus()
    },
  })

  ctx.tools.register({
    name: 'sci_figure_workbench',
    description:
      'Drive the local figure workbench, where one figure is a project directory with source data, script, outputs, and publication gates. Use action=list to see projects, action=templates to see starter templates from installed mods, action=new to create a project from a CSV plus a template, action=render to draw it (checks size, CJK glyphs, vector font gates), and action=report for a self-contained HTML. Every path must be absolute; rendering happens on this machine.',
    parameters: {
      type: 'object',
      properties: {
        action: {
          type: 'string',
          enum: ['list', 'templates', 'new', 'render', 'report'],
          description: 'Workbench operation.',
        },
        project: {
          type: 'string',
          description: 'Project name under the workbench root, or an absolute project directory.',
        },
        name: {
          type: 'string',
          description: 'new only: project name to create (letters, digits, CJK, space, dot, dash, underscore).',
        },
        data: {
          type: 'string',
          description: 'new only: absolute path to a .csv/.tsv/.txt source file.',
        },
        template: {
          type: 'string',
          description: 'new only: starter template as <mod-id>:templates/<file>, e.g. ggpubfigs:templates/theme-demo.R.',
        },
        preset: {
          type: 'string',
          enum: PRESETS,
          description: 'new only: journal size preset.',
        },
      },
      required: ['action'],
      additionalProperties: false,
    },
    output: {
      schema: { type: 'object', additionalProperties: true },
      render: textRender,
    },
    timeoutMs: 660000,
    isConcurrencySafe: () => false,
    async execute(args) {
      switch (args.action) {
        case 'list':
          return actionProjects()
        case 'templates':
          return actionTemplates()
        case 'new':
          return actionNew(args)
        case 'render':
          return actionRender(args)
        case 'report':
          return actionReport(args)
        default:
          throw new Error(`未知 action：${args.action}`)
      }
    },
  })

  // Panel route: registered in an effect so a reload/teardown disposes it.
  ctx.effect(
    () => ctx.webServer.register({
      kind: 'prefix',
      path: ROUTE_PREFIX,
      handler: (req, res) => handleRoute(req, res),
    }),
    'dsh-sci-figure: mod routes',
  )
}
