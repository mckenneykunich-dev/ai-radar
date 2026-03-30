/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',  // 静态导出，部署到 Vercel
  trailingSlash: true,
}

module.exports = nextConfig
