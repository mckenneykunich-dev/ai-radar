import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/router'

export default function Layout({ children, updatedAt }) {
  const [dark, setDark] = useState(false)
  const router = useRouter()

  useEffect(() => {
    const saved = localStorage.getItem('theme')
    if (saved === 'dark') {
      setDark(true)
      document.documentElement.classList.add('dark')
    }
  }, [])

  const toggleTheme = () => {
    const next = !dark
    setDark(next)
    document.documentElement.classList.toggle('dark', next)
    localStorage.setItem('theme', next ? 'dark' : 'light')
  }

  const navItems = [
    { href: '/', label: '赛道雷达' },
    { href: '/projects', label: '项目榜' },
  ]

  return (
    <div className="min-h-screen">
      {/* 顶部导航 */}
      <header className="sticky top-0 z-10 border-b border-gray-200 bg-white/80 backdrop-blur dark:border-gray-800 dark:bg-gray-950/80">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2">
            <span className="text-lg font-bold tracking-tight text-gray-900 dark:text-white">
              AI <span className="text-sky-500">Alpha</span> Radar
            </span>
          </Link>

          {/* 导航 */}
          <nav className="flex items-center gap-1">
            {navItems.map(item => {
              const active = router.pathname === item.href ||
                (item.href !== '/' && router.pathname.startsWith(item.href))
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors
                    ${active
                      ? 'bg-sky-50 text-sky-600 dark:bg-sky-950 dark:text-sky-400'
                      : 'text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white'
                    }`}
                >
                  {item.label}
                </Link>
              )
            })}

            {/* 主题切换 */}
            <button
              onClick={toggleTheme}
              className="ml-2 rounded-md p-1.5 text-gray-500 hover:bg-gray-100 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-white"
              title="切换主题"
            >
              {dark ? '☀️' : '🌙'}
            </button>
          </nav>
        </div>
      </header>

      {/* 主内容 */}
      <main className="mx-auto max-w-6xl px-4 py-8">
        {children}
      </main>

      {/* 底部 */}
      <footer className="border-t border-gray-200 py-6 dark:border-gray-800">
        <div className="mx-auto max-w-6xl px-4 text-center text-xs text-gray-400">
          {updatedAt && (
            <p>数据更新于 {new Date(updatedAt).toLocaleDateString('zh-CN')}</p>
          )}
          <p className="mt-1">多信源交叉验证 · 发现高潜力 AI 投资赛道</p>
        </div>
      </footer>
    </div>
  )
}
