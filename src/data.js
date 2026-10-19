// Helpers for reading and normalising public/data.json.

export const IMPACT_ORDER = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']

// generated_at is ISO 8601. v1 files have no timezone (written on a UTC
// GitHub runner) and 6-digit microseconds, which some browsers reject.
export function parseGeneratedAt(value) {
  if (typeof value !== 'string' || !value) return null
  let s = value.trim().replace(/(\.\d{3})\d+/, '$1')
  if (!/(Z|[+-]\d{2}:?\d{2})$/i.test(s)) s += 'Z'
  const d = new Date(s)
  return Number.isNaN(d.getTime()) ? null : d
}

export function formatDate(date, lang) {
  const locale = { zh: 'zh-CN', en: 'en-US', es: 'es-ES' }[lang] || 'en-US'
  return (
    new Intl.DateTimeFormat(locale, {
      dateStyle: 'long',
      timeStyle: 'short',
      timeZone: 'UTC',
      hour12: false,
    }).format(date) + ' UTC'
  )
}

export function daysSince(date, now = new Date()) {
  return Math.floor((now.getTime() - date.getTime()) / 86400000)
}

const str = (v) => (typeof v === 'string' ? v.trim() : '')

// Accept only http(s) links so data can never inject javascript: URLs.
function safeUrl(v) {
  const s = str(v)
  return /^https?:\/\//i.test(s) ? s : ''
}

export function normaliseItem(raw, index) {
  if (!raw || typeof raw !== 'object') return null
  const title = str(raw.fullTitle) || str(raw.title)
  if (!title) return null
  const inv = raw.investment && typeof raw.investment === 'object' ? raw.investment : null
  const impact = str(raw.impactLevel).toUpperCase()
  return {
    key: `${str(raw.id) || 'item'}-${index}`,
    title,
    shortTitle: str(raw.title),
    summary: str(raw.summary),
    impact: IMPACT_ORDER.includes(impact) ? impact : 'INFO',
    category: str(raw.category_label) || str(raw.category),
    points: Array.isArray(raw.analysis?.strategic)
      ? raw.analysis.strategic.map(str).filter(Boolean)
      : [],
    relations: Array.isArray(raw.relations)
      ? raw.relations
          .filter((r) => r && str(r.label))
          .map((r) => ({ label: str(r.label), type: str(r.type), desc: str(r.desc) }))
      : [],
    investment:
      inv && (str(inv.asset) || str(inv.thesis))
        ? {
            action: str(inv.action).toUpperCase(),
            asset: str(inv.asset),
            risk: str(inv.risk).toUpperCase(),
            thesis: str(inv.thesis),
          }
        : null,
    confidence: Number.isFinite(raw.confidence) ? Math.round(raw.confidence) : null,
    url: safeUrl(raw.url) || safeUrl(raw.source_url) || safeUrl(raw.link),
    source: str(raw.source) || str(raw.source_name),
  }
}

export function validateData(json) {
  if (!json || typeof json !== 'object' || !json.languages || typeof json.languages !== 'object') {
    throw new Error('Invalid data.json: missing "languages"')
  }
  return json
}
