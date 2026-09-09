import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    // In local development, proxy /api/* to FastAPI backend on port 8000
    if (!process.env.VERCEL) {
      return [
        {
          source: "/api/:path*",
          destination: "http://127.0.0.1:8000/api/:path*",
        },
      ];
    }
    return [];
  },
};

export default nextConfig;

