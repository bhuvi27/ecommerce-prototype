/** @type {import('next').NextConfig} */
const isGithubPages = process.env.GITHUB_PAGES === 'true';
const repoName = process.env.GITHUB_REPOSITORY?.split('/')[1]
  || process.env.NEXT_PUBLIC_BASE_PATH?.replace(/^\//, '')
  || '';
const basePath = isGithubPages && repoName ? `/${repoName}` : '';

const nextConfig = {
  output: isGithubPages ? 'export' : undefined,
  basePath,
  assetPrefix: basePath ? `${basePath}/` : undefined,
  trailingSlash: isGithubPages,
  images: {
    unoptimized: isGithubPages,
    remotePatterns: [
      { protocol: 'https', hostname: 'images.unsplash.com' },
      { protocol: 'http', hostname: 'localhost', port: '9000' },
    ],
  },
};

module.exports = nextConfig;
