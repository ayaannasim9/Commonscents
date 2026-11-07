import type { NextConfig } from 'next';
const nextConfig: NextConfig = { turbopack: { root: process.cwd() }, outputFileTracingIncludes: { "/": ["./Overview/index.html"], "/overview/*": ["./Overview/app.js", "./Overview/styles.css"] } };
export default nextConfig;
