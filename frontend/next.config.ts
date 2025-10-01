import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Let TypeScript handle path mapping via tsconfig.json
  outputFileTracingRoot: __dirname,
};

export default nextConfig;
