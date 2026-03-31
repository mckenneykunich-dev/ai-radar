/**
 * 详情页信号卡片
 * 包含：标题链接、评分、中文摘要、赛道标签、核心指标审计
 */

const SIGNAL_TYPE_LABELS = {
  funding:       '💰 融资',
  product_launch:'🚀 产品',
  research:      '🔬 研究',
  market_trend:  '📈 趋势',
  company_news:  '📰 动态',
  regulatory:    '⚖️ 监管',
}

function getPlatformMeta(signal) {
  const { source = '', metadata = {}, published_at = '' } = signal
  const dateStr = published_at
    ? new Date(published_at).toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
    : ''

  const items = []

  switch (source) {
    case 'github':
      if (metadata.stars != null)        items.push({ label: 'Stars', value: metadata.stars.toLocaleString() })
      if (metadata.weekly_stars != null) items.push({ label: '周新增', value: `+${metadata.weekly_stars}` })
      if (metadata.forks != null)        items.push({ label: 'Forks', value: metadata.forks.toLocaleString() })
      if (metadata.language)             items.push({ label: '语言', value: metadata.language })
      break

    case 'hackernews':
      if (metadata.hn_score != null) items.push({ label: 'HN Score', value: metadata.hn_score })
      if (metadata.comments != null) items.push({ label: '评论数', value: metadata.comments })
      if (dateStr)                   items.push({ label: '发布日期', value: dateStr })
      break

    case 'techcrunch':
    case '36kr':
      if (dateStr) items.push({ label: '发布日期', value: dateStr })
      break

    case 'arxiv':
      if (dateStr)                      items.push({ label: '发表时间', value: dateStr })
      if (metadata.arxiv_id)            items.push({ label: 'ArXiv ID', value: metadata.arxiv_id })
      break

    case 'wechat':
      if (metadata.account_name) items.push({ label: '公众号', value: metadata.account_name })
      if (dateStr)               items.push({ label: '发布时间', value: dateStr })
      break

    case 'astock':
      if (metadata.stock_code)        items.push({ label: '股票代码', value: metadata.stock_code })
      if (metadata.announcement_type) items.push({ label: '公告类型', value: metadata.announcement_type })
      if (dateStr)                    items.push({ label: '发布日期', value: dateStr })
      break

    default:
      if (dateStr) items.push({ label: '发布日期', value: dateStr })
  }

  return items
}

export default function SignalDetailCard({ signal, index }) {
  const {
    entity_name = '',
    source_url = '',
    summary_zh = '',
    score_final = 0,
    signal_type = '',
  } = signal

  const typeLabel = SIGNAL_TYPE_LABELS[signal_type] || signal_type
  const platformMeta = getPlatformMeta(signal)
  const scoreColor =
    score_final >= 8 ? 'text-emerald-500' :
    score_final >= 6 ? 'text-sky-500' :
    'text-gray-400'

  return (
    <div className="rounded-lg border border-gray-100 bg-gray-50 p-4 dark:border-gray-800 dark:bg-gray-900/50">
      {/* 标题行 */}
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          {source_url ? (
            <a
              href={source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="font-medium text-gray-900 hover:text-sky-500 dark:text-white dark:hover:text-sky-400 transition-colors line-clamp-2"
            >
              {entity_name || summary_zh}
            </a>
          ) : (
            <span className="font-medium text-gray-900 dark:text-white line-clamp-2">
              {entity_name || summary_zh}
            </span>
          )}
        </div>
        {/* 评分 */}
        <div className="shrink-0 text-right">
          <span className={`text-lg font-bold ${scoreColor}`}>
            🏆 {score_final?.toFixed(1)}
          </span>
        </div>
      </div>

      {/* 中文摘要 */}
      {summary_zh && entity_name && (
        <p className="mt-2 text-sm text-gray-600 dark:text-gray-400 line-clamp-3">
          {summary_zh}
        </p>
      )}

      {/* 标签行 */}
      <div className="mt-3 flex flex-wrap items-center gap-2">
        {typeLabel && (
          <span className="rounded-full bg-white border border-gray-200 px-2 py-0.5 text-xs text-gray-600 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-400">
            {typeLabel}
          </span>
        )}
      </div>

      {/* 核心指标审计 */}
      {platformMeta.length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
          <p className="mb-2 text-xs font-medium text-gray-400 uppercase tracking-wide">🔍 核心指标</p>
          <div className="flex flex-wrap gap-x-4 gap-y-1">
            {platformMeta.map(({ label, value }) => (
              <div key={label} className="flex items-center gap-1 text-xs">
                <span className="text-gray-400">{label}:</span>
                <span className="font-medium text-gray-700 dark:text-gray-300">{value}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
