import Link from 'next/link'

const TREND_CONFIG = {
  up:     { icon: '↑', color: 'text-emerald-500' },
  down:   { icon: '↓', color: 'text-red-500' },
  stable: { icon: '→', color: 'text-gray-400' },
}

export default function TrackCard({ track, rank }) {
  const trend = TREND_CONFIG[track.trend] || TREND_CONFIG.stable
  const score = track.score?.toFixed(1) ?? '-'
  const slug = encodeURIComponent(track.name)

  return (
    <Link
      href={`/tracks/${slug}`}
      className="group block rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition hover:shadow-md hover:border-sky-300 dark:border-gray-800 dark:bg-gray-900 dark:hover:border-sky-700"
    >
      {/* 标题行 */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-sm font-medium text-gray-400 shrink-0">#{rank}</span>
          <h3 className="text-base font-semibold text-gray-900 dark:text-white truncate">
            {track.name}
          </h3>
          <span className={`text-sm font-medium shrink-0 ${trend.color}`}>
            {trend.icon}
          </span>
        </div>
        {/* 分数 */}
        <div className="flex flex-col items-end shrink-0">
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
          {track.top_signals.slice(0, 3).map((sig, i) => (
            <li key={i} className="flex items-start gap-2 text-sm">
              <span className="mt-0.5 shrink-0 rounded px-1.5 py-0.5 text-xs font-medium bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400">
                {sig.source}
              </span>
              <span className="line-clamp-1 text-gray-600 dark:text-gray-400 group-hover:text-gray-900 dark:group-hover:text-gray-200 transition-colors">
                {sig.entity_name || sig.summary_zh}
              </span>
            </li>
          ))}
        </ul>
      )}

      {/* 查看透视链接提示 */}
      <div className="mt-3 text-right">
        <span className="text-xs text-sky-500 opacity-0 group-hover:opacity-100 transition-opacity">
          查看透视 →
        </span>
      </div>
    </Link>
  )
}
