/** @type {import('next').NextConfig} */
const nextConfig = {
  // Disable Turbopack for Windows compatibility
  experimental: {
    turbo: undefined
  },
  // Transpile Supabase packages
  transpilePackages: ['@supabase/supabase-js'],
  // Image optimization
  images: {
    domains: ['localhost'],
  },
}

export default nextConfig
