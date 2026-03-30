const SOURCE_CONFIG = {
  github:     { label: 'GitHub',     color: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300' },
  hackernews: { label: 'HN',         color: 'bg-orange-50 text-orange-700 dark:bg-orange-950 dark:text-orange-300' },
  techcrunch: { label: 'TechCrunch', color: 'bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300' },
  arxiv:      { label: 'ArXiv',      color: 'bg-purple-50 text-purple-700 dark:bg-purple-950 dark:text-purple-300' },
}

const SIGNAL_TYPE_LABELS = {
  funding:        { label: '融资',   color: 'text-emerald-600 dark:text-emerald-400' },
  product_launch: { label: '产品',   color: 'text-blue-600 dark:text-blue-400' },
  research:       { label: '研究',   color: 'text-purple-600 dark:text-purple-400' },
  market_trend:   { label: '趋势',   color: 'text-amber-600 dark:text-amber-400' },
  company_news:   { label: '动态',   color: 'text-gray-500 dark:text-gray-400' },
  regulatory:     { label: '政策',   color: 'text-red-600 dark:text-red-400' },
}

export default function ProjectCard({ signal, rank }) {
  const src = SOURCE_CONFIG[signal.source] || { label: signal.source, color: 'bg-gray-100 text-gray-600' }
  const sigType = SIGNAL_TYPE_LABELS[signal.signal_type] || SIGNAL_TYPE_LABELS.company_news
  const pubDate = signal.published_at
    ? new Date(signal.published_at).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
    : ''

  return (
    <div className="flex gap-4 rounded-xl border border-gray-200 bg-white p-4 shadow-sm transition hover:shadow-md dark:border-gray-800 dark:bg-gray-900">
      {/* 排名 + 分数 */}
      <div className="flex w-14 shrink-0 flex-col items-center justify-center">
        <span className="text-xs text-gray-400">#{rank}</span>
        <span className="text-xl font-bold text-sky-500">{signal.score_final?.toFixed(1)}</span>
      </div>

      {/* 内容 */}
      <div className="min-w-0 flex-1">
        {/* 顶行：实体名 + 赛道 + 来源 */}
        <div className="flex flex-wrap items-center gap-1.5">
          <a
            href={signal.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="font-semibold text-gray-900 hover:text-sky-500 dark:text-white dark:hover:text-sky-400"
          >
            {signal.entity_name}
          </a>
          {signal.track && (
            <span className="rounded-full bg-sky-50 px-2 py-0.5 text-xs text-sky-600 dark:bg-sky-950 dark:text-sky-400">
              {signal.track}
            </span>
          )}
          <span className={`rounded px-1.5 py-0.5 text-xs font-medium ${src.color}`}>
            {src.label}
          </span>
          {signal.team_origin === 'chinese' && (
            <span className="text-xs">🇨🇳</span>
          )}
        </div>

        {/* 摘要 */}
        {signal.summary_zh && (
          <p className="mt-1 line-clamp-2 text-sm text-gray-500 dark:text-gray-400">
            {signal.summary_zh}
          </p>
        )}

        {/* 底行：信号类型 + 日期 + 元数据 */}
        <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-gray-400">
          <span className={`font-medium ${sigType.color}`}>{sigType.label}</span>
          {pubDate && <span>{pubDate}</span>}
          {signal.source === 'github' && signal.metadata?.stars && (
            <span>⭐ {signal.metadata.stars.toLocaleString()}</span>
          )}
          {signal.source === 'hackernews' && signal.metadata?.hn_score && (
            <span>▲ {signal.metadata.hn_score}</span>
          )}
        </div>
      </div>
    </div>
  )
}
