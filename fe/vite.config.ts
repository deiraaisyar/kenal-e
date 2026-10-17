import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [react(), tailwindcss(), VitePWA({
    registerType: 'autoUpdate',
    includeAssets: ['logo.svg', 'logo-white.svg', 'icon-192.png', 'icon-512.png'],
    manifest: {
      name: 'Kenal-E — Kenali, Pilah, Setor', short_name: 'Kenal-E', lang: 'id',
      description: 'Mulai memilah elektronik lama dari satu foto.',
      theme_color: '#286336', background_color: '#f8faf6', display: 'standalone', start_url: '/',
      icons: [{src:'/icon-192.png',sizes:'192x192',type:'image/png'}, {src:'/icon-512.png',sizes:'512x512',type:'image/png',purpose:'any maskable'}],
    },
    workbox: {
      navigateFallbackDenylist: [/^\/api/],
      globPatterns: ['**/*.{js,css,html,svg,png,webp,woff2}'],
      runtimeCaching: [{urlPattern: /\/api\/taxonomy(?:\/\d+)?$/, handler:'NetworkFirst', options:{cacheName:'eokay-catalog-v1',expiration:{maxEntries:30,maxAgeSeconds:86400},networkTimeoutSeconds:5}}],
    },
  })],
  server: {port:5173, proxy:{'/api':{target:'http://127.0.0.1:8000',changeOrigin:true}}},
})
