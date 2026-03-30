import { useState, useMemo } from 'react'
import fs from 'fs'
import path from 'path'
import Layout from '../components/Layout'
import ProjectCard from '../components/ProjectCard'

const ALL_TRACKS = [
  'AI助理', 'AI Coding', 'AI视频', 'AI医疗', 'AI金融',
  'AI营销', 'AI工业', 'AI安全', 'AI硬件', 'AI4S',
  '具身智能', '自动驾驶', '基础模型', 'AI基础设施',
]

const SOURCE_OPTIONS = [
  { value: 'github',     label: 'GitHub' },
  { value: 'hackernews', label: 'HackerNews' },
  { value: 'techcrunch', label: 'TechCrunch' },
  { value: 'arxiv',      label: 'ArXiv' },
]

export default function Projects({ signals, generatedAt }) {
  const [trackFilter, setTrackFilter] = useState('')
  const [sourceFilter, setSourceFilter] = useState('')
  const [teamFilter, setTeamFilter] = useState('')  // '' | 'chinese' | 'non-chinese'
  const [page, setPage] = useState(1)
  const PAGE_SIZE = 20

  const filtered = useMemo(() => {
    return signals.filter(s => {
      if (trackFilter && s.track !== trackFilter) return false
      if (sourceFilter && s.source !== sourceFilter) return false
      if (teamFilter && s.team_origin !== teamFilter) return false
      return true
    })
  }, [signals, trackFilter, sourceFilter, teamFilter])

  const totalPages = Math.ceil(filtered.length / PAGE_SIZE)
  const paged = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  const resetFilters = () => {
    setTrackFilter('')
    setSourceFilter('')
    setTeamFilter('')
    setPage(1)
  }

  const isEmpty = signals.length === 0

  return (
    <Layout updatedAt={generatedAt}>
      {/* 页头 */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">项目榜</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          按热度评分排列的 AI 项目与信号，共 {filtered.length} 条
        </p>
      </div>

      {/* 筛选器 */}
      {!isEmpty && (
        <div className="mb-5 flex flex-wrap items-center gap-2">
          {/* 赛道 */}
          <select
            value={trackFilter}
            onChange={e => { setTrackFilter(e.target.value); setPage(1) }}
            className="rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-sm dark:border-gray-700 dark:bg-gray-900"
          >
            <option value="">全部赛道</option>
            {ALL_TRACKS.map(t => <option key={t} value={t}>{t}</option>)}
          </select>

          {/* 信源 */}
          <select
            value={sourceFilter}
            onChange={e => { setSourceFilter(e.target.value); setPage(1) }}
            className="rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-sm dark:border-gray-700 dark:bg-gray-900"
          >
            <option value="">全部信源</option>
            {SOURCE_OPTIONS.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
          </select>

          {/* 团队来源 */}
          <select
            value={teamFilter}
            onChange={e => { setTeamFilter(e.target.value); setPage(1) }}
            className="rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-sm dark:border-gray-700 dark:bg-gray-900"
          >
            <option value="">全部团队</option>
            <option value="chinese">🇨🇳 中国团队</option>
            <option value="non-chinese">🌍 海外团队</option>
          </select>

          {(trackFilter || sourceFilter || teamFilter) && (
            <button
              onClick={resetFilters}
              className="text-sm text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
            >
              清除筛选 ×
            </button>
          )}
        </div>
      )}

      {/* 空状态 */}
      {isEmpty && (
        <div className="rounded-xl border border-dashed border-gray-300 p-12 text-center dark:border-gray-700">
          <p className="text-gray-400">暂无数据，请运行采集脚本后刷新</p>
          <code className="mt-2 block text-xs text-gray-300">python scraper/main.py</code>
        </div>
      )}

      {/* 项目列表 */}
      {!isEmpty && (
        <>
          <div className="space-y-3">
            {paged.map((signal, i) => (
              <ProjectCard
                key={signal.source_url}
                signal={signal}
                rank={(page - 1) * PAGE_SIZE + i + 1}
              />
            ))}
          </div>

          {/* 分页 */}
          {totalPages > 1 && (
            <div className="mt-6 flex items-center justify-center gap-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="rounded-lg border border-gray-200 px-3 py-1.5 text-sm disabled:opacity-40 dark:border-gray-700"
              >
                上一页
              </button>
              <span className="text-sm text-gray-500">
                {page} / {totalPages}
              </span>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="rounded-lg border border-gray-200 px-3 py-1.5 text-sm disabled:opacity-40 dark:border-gray-700"
              >
                下一页
              </button>
            </div>
          )}
        </>
      )}
    </Layout>
  )
}

export async function getStaticProps() {
  const dataDir = path.join(process.cwd(), '..', 'data')

  let signals = []
  let generatedAt = null

  try {
    const raw = fs.readFileSync(path.join(dataDir, 'signals.json'), 'utf-8')
    const data = JSON.parse(raw)
    signals = data.signals ?? []
    generatedAt = data.generated_at ?? null
  } catch {
    // 数据文件尚未生成
  }

  return {
    props: { signals, generatedAt },
  }
}
