import fs from 'fs'
import path from 'path'
import Layout from '../components/Layout'
import TrackCard from '../components/TrackCard'

export default function Home({ tracks, generatedAt, totalSignals }) {
  const isEmpty = !tracks || tracks.length === 0

  return (
    <Layout updatedAt={generatedAt}>
      {/* 页头 */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          赛道雷达
        </h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          多信源交叉验证 · 发现高潜力 AI 投资赛道
        </p>
        {/* 数据统计 */}
        <div className="mt-4 flex flex-wrap gap-4">
          {[
            { label: '热点赛道', value: tracks?.length ?? 0 },
            { label: '信号总数', value: totalSignals ?? 0 },
            { label: '活跃信源', value: 4 },
          ].map(stat => (
            <div key={stat.label} className="rounded-lg border border-gray-200 bg-white px-4 py-2 dark:border-gray-800 dark:bg-gray-900">
              <div className="text-xl font-bold text-sky-500">{stat.value}</div>
              <div className="text-xs text-gray-500">{stat.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* 空状态 */}
      {isEmpty && (
        <div className="rounded-xl border border-dashed border-gray-300 p-12 text-center dark:border-gray-700">
          <p className="text-gray-400">暂无数据，请运行采集脚本后刷新</p>
          <code className="mt-2 block text-xs text-gray-300">python scraper/main.py</code>
        </div>
      )}

      {/* 赛道卡片网格 */}
      {!isEmpty && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {tracks.map((track, i) => (
            <TrackCard key={track.name} track={track} rank={i + 1} />
          ))}
        </div>
      )}
    </Layout>
  )
}

export async function getStaticProps() {
  const dataDir = path.join(process.cwd(), '..', 'data')

  let tracks = []
  let generatedAt = null
  let totalSignals = 0

  try {
    const tracksRaw = fs.readFileSync(path.join(dataDir, 'tracks.json'), 'utf-8')
    const tracksData = JSON.parse(tracksRaw)
    tracks = tracksData.tracks ?? []
    generatedAt = tracksData.generated_at ?? null
  } catch {
    // 数据文件尚未生成，使用空默认值
  }

  try {
    const signalsRaw = fs.readFileSync(path.join(dataDir, 'signals.json'), 'utf-8')
    const signalsData = JSON.parse(signalsRaw)
    totalSignals = signalsData.total ?? 0
  } catch {
    // 忽略
  }

  return {
    props: { tracks, generatedAt, totalSignals },
  }
}
