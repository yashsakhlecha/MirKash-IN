import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  serverExternalPackages: ["apify-client", "@google/genai", "@prisma/adapter-libsql", "@libsql/client"],
};

export default nextConfig;
