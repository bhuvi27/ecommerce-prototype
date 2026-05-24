/** @type {import('next').NextConfig} */
const isGithubPages = process.env.GITHUB_PAGES === 'true';
const isStaticExport = isGithubPages || process.env.STATIC_EXPORT === 'true';
const repoName = process.env.GITHUB_REPOSITORY?.split('/')[1]
  || process.env.NEXT_PUBLIC_BASE_PATH?.replace(/^\//, '')
  || '';
const basePath = isGithubPages && repoName ? `/${repoName}` : '';

const nextConfig = {
  output: isStaticExport ? 'export' : undefined,
  basePath,
  assetPrefix: basePath ? `${basePath}/` : undefined,
  trailingSlash: isStaticExport,
  images: {
    unoptimized: isStaticExport,
    remotePatterns: [
      { protocol: 'https', hostname: 'images.unsplash.com' },
      { protocol: 'http', hostname: 'localhost', port: '9000' },
    ],
  },
};

module.exports = nextConfig;
