import Link from 'next/link'

const TREND_CONFIG = {
  up:     { icon: '↑', color: 'text-emerald-500' },
  down:   { icon: '↓', color: 'text-red-500' },
  stable: { icon: '→', color: 'text-gray-400' },
}

const SOURCE_LABELS = {
  github:     { label: 'GitHub',      color: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300' },
  hackernews: { label: 'HN',          color: 'bg-orange-50 text-orange-700 dark:bg-orange-950 dark:text-orange-300' },
  techcrunch: { label: 'TechCrunch',  color: 'bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300' },
  arxiv:      { label: 'ArXiv',       color: 'bg-purple-50 text-purple-700 dark:bg-purple-950 dark:text-purple-300' },
}

export default function TrackCard({ track, rank }) {
  const trend = TREND_CONFIG[track.trend] || TREND_CONFIG.stable
  const score = track.score?.toFixed(1) ?? '-'

  return (
    <div className="group rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition hover:shadow-md dark:border-gray-800 dark:bg-gray-900">
      {/* 标题行 */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-400">#{rank}</span>
          <h3 className="text-base font-semibold text-gray-900 dark:text-white">
            {track.name}
          </h3>
          <span className={`text-sm font-medium ${trend.color}`}>
            {trend.icon}
          </span>
        </div>
        {/* 分数 */}
        <div className="flex flex-col items-end">
          <span className="text-2xl font-bold text-sky-500">{score}</span>
          <span className="text-xs text-gray-400">{track.project_count} 条信号</span>
        </div>
      </div>

      {/* 热度条 */}
      <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-gray-100 dark:bg-gray-800">
        <div
          className="h-full rounded-full bg-gradient-to-r from-sky-400 to-sky-600 transition-all"
          style={{ width: `${((track.score - 8) / 2) * 100}%` }}
        />
      </div>

      {/* Top 信号预览 */}
      {track.top_signals?.length > 0 && (
        <ul className="mt-3 space-y-1.5">
          {track.top_signals.slice(0, 3).map((sig, i) => {
            const src = SOURCE_LABELS[sig.source] || { label: sig.source, color: 'bg-gray-100 text-gray-600' }
            return (
              <li key={i} className="flex items-start gap-2 text-sm">
                <span className={`mt-0.5 shrink-0 rounded px-1 py-0.5 text-xs font-medium ${src.color}`}>
                  {src.label}
                </span>
                <a
                  href={sig.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="line-clamp-1 text-gray-600 hover:text-sky-500 dark:text-gray-400 dark:hover:text-sky-400"
                >
                  {sig.entity_name || sig.summary_zh}
                </a>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
