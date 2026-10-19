import { useCallback, useEffect, useMemo, useState } from 'react'
import { LANGS, T } from './i18n.js'
import {
  IMPACT_ORDER,
  daysSince,
  formatDate,
  normaliseItem,
  parseGeneratedAt,
  validateData,
} from './data.js'
import './App.css'

const STALE_AFTER_DAYS = 3

function initialLang() {
  try {
    const fromUrl = new URLSearchParams(window.location.search).get('lang')
    if (LANGS.some((l) => l.code === fromUrl)) return fromUrl
    const saved = localStorage.getItem('nexus_lang')
    if (LANGS.some((l) => l.code === saved)) return saved
  } catch {
    /* storage unavailable */
  }
  const nav = (typeof navigator !== 'undefined' && navigator.language) || ''
  if (nav.startsWith('es')) return 'es'
  if (nav.startsWith('en')) return 'en'
  return 'zh'
}

function useNewsData() {
  const [state, setState] = useState({ status: 'loading', data: null, error: null })
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    const ctrl = new AbortController()
    fetch('/data.json', { cache: 'no-cache', signal: ctrl.signal })
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then((json) => setState({ status: 'ready', data: validateData(json), error: null }))
      .catch((err) => {
        if (err.name === 'AbortError') return
        console.error('Failed to load data.json:', err)
        setState({ status: 'error', data: null, error: err })
      })
    return () => ctrl.abort()
  }, [attempt])

  const retry = useCallback(() => {
    setState({ status: 'loading', data: null, error: null })
    setAttempt((n) => n + 1)
  }, [])

  return { ...state, retry }
}

function Chip({ active, onClick, children }) {
  return (
    <button type="button" className={`chip${active ? ' chip--active' : ''}`} aria-pressed={active} onClick={onClick}>
      {children}
    </button>
  )
}

function NewsCard({ item, t }) {
  const searchUrl = `https://news.google.com/search?q=${encodeURIComponent(item.shortTitle || item.title)}`
  return (
    <article className="card">
      <div className="card__meta">
        <span className={`badge badge--${item.impact.toLowerCase()}`}>
          {t.impactLabels[item.impact] || item.impact}
        </span>
        {item.category && <span className="tag">{item.category}</span>}
        {item.confidence != null && (
          <span className="muted small">
            {t.confidence} {item.confidence}%
          </span>
        )}
      </div>

      <h3 className="card__title">{item.title}</h3>
      {item.summary && <p className="card__summary">{item.summary}</p>}

      {item.points.length > 0 && (
        <div className="card__section">
          <h4>{t.keyPoints}</h4>
          <ul>
            {item.points.map((p, i) => (
              <li key={i}>{p}</li>
            ))}
          </ul>
        </div>
      )}

      {item.relations.length > 0 && (
        <div className="card__section">
          <h4>{t.related}</h4>
          <div className="relations">
            {item.relations.map((r, i) => (
              <span key={i} className={`rel rel--${r.type || 'entity'}`} title={r.desc}>
                {r.label}
              </span>
            ))}
          </div>
        </div>
      )}

      {item.investment && (
        <details className="card__section market">
          <summary>
            <h4>{t.marketView}</h4>
            {item.investment.action && (
              <span className={`action action--${item.investment.action.toLowerCase()}`}>
                {t.actionLabels[item.investment.action] || item.investment.action}
              </span>
            )}
          </summary>
          <dl>
            {item.investment.asset && (
              <>
                <dt>{t.asset}</dt>
                <dd>{item.investment.asset}</dd>
              </>
            )}
            {item.investment.risk && (
              <>
                <dt>{t.risk}</dt>
                <dd>{t.riskLabels[item.investment.risk] || item.investment.risk}</dd>
              </>
            )}
          </dl>
          {item.investment.thesis && <p>{item.investment.thesis}</p>}
          <p className="muted small">{t.disclaimer}</p>
        </details>
      )}

      <footer className="card__footer">
        {item.url ? (
          <a href={item.url} target="_blank" rel="noopener noreferrer">
            {t.source}
            {item.source ? `: ${item.source}` : ''} ↗
          </a>
        ) : (
          <>
            <span className="muted small">{t.noSource}</span>
            <a href={searchUrl} target="_blank" rel="noopener noreferrer">
              {t.searchStory} ↗
            </a>
          </>
        )}
      </footer>
    </article>
  )
}

function Status({ title, body, action }) {
  return (
    <div className="status" role="status">
      <h2>{title}</h2>
      {body && <p>{body}</p>}
      {action}
    </div>
  )
}

export default function App() {
  const [lang, setLang] = useState(initialLang)
  const [impact, setImpact] = useState('ALL')
  const [category, setCategory] = useState('ALL')
  const [query, setQuery] = useState('')
  const { status, data, retry } = useNewsData()
  const t = T[lang]

  useEffect(() => {
    document.documentElement.lang = lang === 'zh' ? 'zh-CN' : lang
    try {
      localStorage.setItem('nexus_lang', lang)
    } catch {
      /* storage unavailable */
    }
  }, [lang])

  const items = useMemo(() => {
    const list = data?.languages?.[lang]
    return Array.isArray(list) ? list.map(normaliseItem).filter(Boolean) : []
  }, [data, lang])

  const impacts = useMemo(
    () => IMPACT_ORDER.filter((lvl) => items.some((i) => i.impact === lvl)),
    [items],
  )
  const categories = useMemo(
    () => [...new Set(items.map((i) => i.category).filter(Boolean))],
    [items],
  )

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return items
      .filter((i) => impact === 'ALL' || i.impact === impact)
      .filter((i) => category === 'ALL' || i.category === category)
      .filter((i) => !q || `${i.title} ${i.shortTitle} ${i.summary}`.toLowerCase().includes(q))
  }, [items, impact, category, query])

  // Group by category when the data has categories (v2), otherwise by impact level (v1).
  const groups = useMemo(() => {
    const byCategory = categories.length > 0
    const keys = byCategory ? categories : IMPACT_ORDER
    return keys
      .map((k) => ({
        key: k,
        label: byCategory ? k : t.impactLabels[k] || k,
        items: filtered.filter((i) => (byCategory ? i.category === k : i.impact === k)),
      }))
      .concat(byCategory ? [{ key: '_none', label: '—', items: filtered.filter((i) => !i.category) }] : [])
      .filter((g) => g.items.length > 0)
  }, [filtered, categories, t])

  const generatedAt = parseGeneratedAt(data?.generated_at)
  const age = generatedAt ? daysSince(generatedAt) : null
  const otherLangs = LANGS.filter(
    (l) => l.code !== lang && Array.isArray(data?.languages?.[l.code]) && data.languages[l.code].length > 0,
  )
  const hasFilters = impact !== 'ALL' || category !== 'ALL' || query !== ''
  const clearFilters = () => {
    setImpact('ALL')
    setCategory('ALL')
    setQuery('')
  }
  const switchLang = (code) => {
    setLang(code)
    setCategory('ALL')
  }

  return (
    <div className="page">
      <header className="header">
        <div className="header__top">
          <div>
            <h1>NexusIntel</h1>
            <p className="tagline">{t.tagline}</p>
          </div>
          <nav className="langs" aria-label="Language">
            {LANGS.map((l) => (
              <Chip key={l.code} active={l.code === lang} onClick={() => switchLang(l.code)}>
                {l.label}
              </Chip>
            ))}
          </nav>
        </div>
        <p className="description">{t.description}</p>
        {generatedAt && (
          <p className="updated">
            {t.updated}: <time dateTime={generatedAt.toISOString()}>{formatDate(generatedAt, lang)}</time>
          </p>
        )}
      </header>

      {status === 'ready' && age != null && age > STALE_AFTER_DAYS && (
        <div className="notice" role="note">
          <strong>{t.staleTitle}</strong> {t.stale(age)}
        </div>
      )}

      <main>
        {status === 'loading' && <Status title={t.loading} />}

        {status === 'error' && (
          <Status
            title={t.errorTitle}
            body={t.errorBody}
            action={
              <button type="button" className="button" onClick={retry}>
                {t.retry}
              </button>
            }
          />
        )}

        {status === 'ready' && items.length === 0 && (
          <Status
            title={t.emptyTitle}
            body={t.emptyBody}
            action={
              otherLangs.length > 0 && (
                <div className="langs">
                  {otherLangs.map((l) => (
                    <Chip key={l.code} onClick={() => switchLang(l.code)}>
                      {l.label}
                    </Chip>
                  ))}
                </div>
              )
            }
          />
        )}

        {status === 'ready' && items.length > 0 && (
          <>
            <section className="filters" aria-label="Filters">
              <input
                type="search"
                className="search"
                placeholder={t.search}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                aria-label={t.search}
              />
              {categories.length > 0 && (
                <div className="filter-row">
                  <span className="filter-label">{t.category}</span>
                  <Chip active={category === 'ALL'} onClick={() => setCategory('ALL')}>
                    {t.all}
                  </Chip>
                  {categories.map((c) => (
                    <Chip key={c} active={category === c} onClick={() => setCategory(c)}>
                      {c}
                    </Chip>
                  ))}
                </div>
              )}
              {impacts.length > 1 && (
                <div className="filter-row">
                  <span className="filter-label">{t.impact}</span>
                  <Chip active={impact === 'ALL'} onClick={() => setImpact('ALL')}>
                    {t.all}
                  </Chip>
                  {impacts.map((lvl) => (
                    <Chip key={lvl} active={impact === lvl} onClick={() => setImpact(lvl)}>
                      {t.impactLabels[lvl] || lvl}
                    </Chip>
                  ))}
                </div>
              )}
              <p className="muted small">{t.items(filtered.length)}</p>
            </section>

            {groups.length === 0 ? (
              <Status
                title={t.noMatch}
                action={
                  hasFilters && (
                    <button type="button" className="button" onClick={clearFilters}>
                      {t.clear}
                    </button>
                  )
                }
              />
            ) : (
              groups.map((g) => (
                <section key={g.key} className="group">
                  <h2 className="group__title">
                    {g.label} <span className="muted">· {g.items.length}</span>
                  </h2>
                  <div className="grid">
                    {g.items.map((item) => (
                      <NewsCard key={item.key} item={item} t={t} />
                    ))}
                  </div>
                </section>
              ))
            )}
          </>
        )}
      </main>

      <footer className="page__footer muted small">{t.disclaimer}</footer>
    </div>
  )
}
