import fs from 'fs'
import path from 'path'
import Link from 'next/link'
import Layout from '../../components/Layout'
import SourceWall from '../../components/SourceWall'
import SourceSection from '../../components/SourceSection'

const TREND_CONFIG = {
  up:     { icon: '↑', label: '上升', color: 'text-emerald-500' },
  down:   { icon: '↓', label: '下降', color: 'text-red-500' },
  stable: { icon: '→', label: '稳定', color: 'text-gray-400' },
}

export default function TrackDetail({ track, generatedAt }) {
  if (!track) {
    return (
      <Layout>
        <div className="text-center py-20 text-gray-400">赛道数据不存在</div>
      </Layout>
    )
  }

  const trend = TREND_CONFIG[track.trend] || TREND_CONFIG.stable
  const sourceBreakdown = track.source_breakdown || {}
  const sourceCount = Object.keys(sourceBreakdown).length

  const updateDate = generatedAt
    ? new Date(generatedAt).toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
    : ''

  return (
    <Layout updatedAt={generatedAt}>
      <div className="mx-auto max-w-4xl space-y-6">

        {/* 返回按钮 */}
        <Link
          href="/"
          className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-sky-500 dark:text-gray-400 dark:hover:text-sky-400 transition-colors"
        >
          ← 返回赛道列表
        </Link>

        {/* Header 卡片 */}
        <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-gray-900">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              {/* 赛道名 */}
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                🔥 {track.name}
              </h1>

              {/* 标签行 */}
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <span className="rounded-full bg-sky-50 text-sky-700 border border-sky-200 px-3 py-0.5 text-xs font-medium dark:bg-sky-950 dark:text-sky-300 dark:border-sky-800">
                  📊 全渠道综合评级
                </span>
                <span className={`text-sm font-medium ${trend.color}`}>
                  {trend.icon} {trend.label}
                </span>
                {sourceCount > 0 && (
                  <span className="text-xs text-gray-400">{sourceCount} 个信源 · {track.project_count} 条信号</span>
                )}
              </div>

              {/* 更新日期 */}
              {updateDate && (
                <p className="mt-1 text-xs text-gray-400">更新于 {updateDate}</p>
              )}
            </div>

            {/* 评分 */}
            <div className="shrink-0 text-right">
              <div className="text-5xl font-bold text-sky-500">{track.score?.toFixed(1)}</div>
              <div className="text-sm text-gray-400">/ 10</div>
            </div>
          </div>

          {/* 热度条 */}
          <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-gray-100 dark:bg-gray-800">
            <div
              className="h-full rounded-full bg-gradient-to-r from-sky-400 to-sky-600"
              style={{ width: `${((track.score - 8) / 2) * 100}%` }}
            />
          </div>

          {/* LLM 生成的赛道摘要 */}
          {track.summary_zh && (
            <div className="mt-4 rounded-lg bg-sky-50 dark:bg-sky-950/30 px-4 py-3">
              <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                {track.summary_zh}
              </p>
            </div>
          )}
        </div>

        {/* 信源证据墙 */}
        {sourceCount > 0 && (
          <SourceWall sourceBreakdown={sourceBreakdown} />
        )}

        {/* 按信源分组的信号列表 */}
        {Object.entries(sourceBreakdown).map(([sourceKey, sourceData]) => (
          <SourceSection
            key={sourceKey}
            sourceKey={sourceKey}
            sourceData={sourceData}
            trackName={track.name}
          />
        ))}

        {/* 空状态 */}
        {sourceCount === 0 && (
          <div className="rounded-xl border border-dashed border-gray-300 p-12 text-center dark:border-gray-700">
            <p className="text-gray-400">该赛道暂无详细信号数据</p>
            <p className="mt-1 text-xs text-gray-300">请运行采集脚本更新数据</p>
          </div>
        )}

        {/* 底部返回 */}
        <div className="pb-8">
          <Link
            href="/"
            className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-sky-500 dark:text-gray-400 dark:hover:text-sky-400 transition-colors"
          >
            ← 返回赛道列表
          </Link>
        </div>
      </div>
    </Layout>
  )
}

export async function getStaticPaths() {
  const dataDir = path.join(process.cwd(), '..', 'data')

  let paths = []
  try {
    const raw = fs.readFileSync(path.join(dataDir, 'tracks.json'), 'utf-8')
    const data = JSON.parse(raw)
    const tracks = data.tracks ?? []
    paths = tracks.map(t => ({
      params: { slug: t.name }
    }))
  } catch {
    // 数据文件不存在时返回空路径
  }

  return { paths, fallback: false }
}

export async function getStaticProps({ params }) {
  const dataDir = path.join(process.cwd(), '..', 'data')
  const slug = params.slug

  let track = null
  let generatedAt = null

  try {
    const raw = fs.readFileSync(path.join(dataDir, 'tracks.json'), 'utf-8')
    const data = JSON.parse(raw)
    generatedAt = data.generated_at ?? null
    track = (data.tracks ?? []).find(t => t.name === slug) ?? null
  } catch {
    // 数据文件不存在
  }

  return {
    props: { track, generatedAt }
  }
}
