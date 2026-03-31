/**
 * 信源证据墙
 * 展示覆盖该赛道的所有信源及其独立评分，按分数降序排列
 */

const SOURCE_COLORS = {
  github:     'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300',
  hackernews: 'bg-orange-50 text-orange-700 dark:bg-orange-950 dark:text-orange-300',
  techcrunch: 'bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300',
  arxiv:      'bg-purple-50 text-purple-700 dark:bg-purple-950 dark:text-purple-300',
  '36kr':     'bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300',
  wechat:     'bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300',
  astock:     'bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-300',
}

export default function SourceWall({ sourceBreakdown }) {
  if (!sourceBreakdown || Object.keys(sourceBreakdown).length === 0) return null

  const sources = Object.entries(sourceBreakdown).map(([key, val]) => ({
    key,
    displayName: val.display_name || key,
    score: val.score,
    count: val.signals?.length ?? 0,
  }))

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900">
      <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">
        🔍 信源证据墙
      </h2>
      <div className="flex flex-wrap gap-3">
        {sources.map(({ key, displayName, score, count }) => {
          const colorClass = SOURCE_COLORS[key] || 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'
          return (
            <a
              key={key}
              href={`#source-${key}`}
              className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition hover:opacity-80 ${colorClass}`}
            >
              <span>{displayName}</span>
              <span className="font-bold">{score?.toFixed(1)}</span>
              <span className="opacity-60 text-xs">({count}条)</span>
            </a>
          )
        })}
      </div>
    </div>
  )
}
