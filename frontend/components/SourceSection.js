/**
 * 信源分组 Section
 * 每个信源在该赛道下的独立展示区块：信源评分 + LLM解读 + 信号卡片列表
 */

import SignalDetailCard from './SignalDetailCard'

const SOURCE_COLORS = {
  github:     'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300 border-gray-200 dark:border-gray-700',
  hackernews: 'bg-orange-50 text-orange-700 dark:bg-orange-950 dark:text-orange-300 border-orange-200 dark:border-orange-800',
  techcrunch: 'bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300 border-green-200 dark:border-green-800',
  arxiv:      'bg-purple-50 text-purple-700 dark:bg-purple-950 dark:text-purple-300 border-purple-200 dark:border-purple-800',
  '36kr':     'bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300 border-red-200 dark:border-red-800',
  wechat:     'bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800',
  astock:     'bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-300 border-blue-200 dark:border-blue-800',
}

export default function SourceSection({ sourceKey, sourceData, trackName }) {
  const { display_name, score, summary, signals = [] } = sourceData
  const colorClass = SOURCE_COLORS[sourceKey] || SOURCE_COLORS.github

  return (
    <section id={`source-${sourceKey}`} className="rounded-xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900 overflow-hidden">
      {/* Section 标题 */}
      <div className={`flex items-center justify-between px-5 py-3 border-b ${colorClass}`}>
        <div className="flex items-center gap-2">
          <span className="font-semibold text-sm">{display_name}</span>
          <span className="text-xs opacity-70">— {trackName}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs opacity-70">信源分</span>
          <span className="font-bold text-base">{score?.toFixed(1)}</span>
          <span className="text-xs opacity-50">({signals.length}条)</span>
        </div>
      </div>

      <div className="p-5 space-y-4">
        {/* LLM 解读摘要 */}
        {summary && (
          <div className="rounded-lg bg-gray-50 dark:bg-gray-800/50 px-4 py-3">
            <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
              {summary}
            </p>
          </div>
        )}

        {/* 信号卡片列表 */}
        {signals.length > 0 ? (
          <div className="space-y-3">
            {signals.map((signal, i) => (
              <SignalDetailCard key={signal.source_url || i} signal={signal} index={i} />
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-400 text-center py-4">暂无信号数据</p>
        )}
      </div>
    </section>
  )
}
