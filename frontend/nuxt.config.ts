import tailwindcss from '@tailwindcss/vite'

const apiTarget = process.env.NUXT_API_PROXY_TARGET ?? 'http://localhost:8000'
const mediaTarget = process.env.NUXT_MEDIA_PROXY_TARGET ?? 'http://localhost:9010/nit-media'

export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  telemetry: false,

  modules: ['shadcn-nuxt', '@nuxtjs/color-mode', '@nuxt/eslint', '@pinia/nuxt', '@vite-pwa/nuxt'],

  css: ['~/assets/css/main.css'],

  vite: {
    plugins: [tailwindcss()],
    optimizeDeps: {
      include: [
        '@lucide/vue',
        '@vueuse/core',
        'class-variance-authority',
        'cn',
        'reka-ui',
        'vue-sonner',
        'markdown-it',
        'vue-draggable-plus',
        'uqr',
        '@tiptap/vue-3',
        '@tiptap/starter-kit',
        '@tiptap/markdown',
        '@tiptap/extension-image',
        '@tiptap/extensions',
      ],
    },
  },

  app: {
    head: {
      htmlAttrs: { lang: 'ru' },
      titleTemplate: '%s · Нить',
      title: 'Пошаговые инструкции, которые проходят до конца',
      meta: [
        { name: 'viewport', content: 'width=device-width, initial-scale=1, viewport-fit=cover' },
        {
          name: 'description',
          content: 'Нить — интерактивные пошаговые инструкции с чек-листами: проходите задачу шаг за шагом, а авторы видят, где ученики спотыкаются.',
        },
        { name: 'theme-color', content: '#f7f3ec' },
        { property: 'og:site_name', content: 'Нить' },
      ],
      link: [
        { rel: 'icon', href: '/favicon.ico', sizes: '48x48' },
        { rel: 'icon', href: '/favicon.svg', type: 'image/svg+xml' },
        { rel: 'apple-touch-icon', href: '/apple-touch-icon.png' },
        { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
        { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' },
      ],
    },
  },

  shadcn: {
    prefix: '',
    componentDir: '@/components/ui',
  },

  colorMode: {
    classSuffix: '',
    preference: 'system',
    fallback: 'light',
  },

  routeRules: {
    // все /api/* проксим в fastapi, и на ssr и в браузере
    '/api/**': { proxy: `${apiTarget}/api/**` },
    '/media/**': { proxy: `${mediaTarget}/**` },
    // личное рендерим на клиенте, там гостевой id из localStorage
    '/studio/**': { ssr: false },
    '/me/**': { ssr: false },
    '/review/**': { ssr: false },
    '/admin/**': { ssr: false },
    '/guides/*/run': { ssr: false },
    '/embed/**': { ssr: false },
  },

  pwa: {
    registerType: 'autoUpdate',
    manifest: {
      name: 'Нить — пошаговые инструкции',
      short_name: 'Нить',
      description: 'Интерактивные пошаговые инструкции с чек-листами',
      lang: 'ru',
      theme_color: '#f7f3ec',
      background_color: '#f7f3ec',
      display: 'standalone',
      start_url: '/',
      icons: [
        { src: '/icon-192.png', sizes: '192x192', type: 'image/png' },
        { src: '/icon-512.png', sizes: '512x512', type: 'image/png' },
        { src: '/icon-maskable-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
      ],
    },
    workbox: {
      navigateFallback: null,
      globPatterns: ['**/*.{js,css,webp,png,ico,svg,woff2}'],
      runtimeCaching: [
        {
          urlPattern: ({ request }) => request.mode === 'navigate',
          handler: 'NetworkFirst',
          options: { cacheName: 'nit-pages', networkTimeoutSeconds: 3 },
        },
        {
          urlPattern: ({ url, request }) => url.pathname.startsWith('/api/guides') && request.method === 'GET',
          handler: 'NetworkFirst',
          options: { cacheName: 'nit-api', networkTimeoutSeconds: 3 },
        },
        {
          urlPattern: ({ url }) => url.pathname.startsWith('/media/') || url.hostname.includes('fonts.g'),
          handler: 'CacheFirst',
          options: { cacheName: 'nit-assets', expiration: { maxEntries: 200 } },
        },
      ],
    },
    client: { installPrompt: true },
    devOptions: { enabled: false },
  },
})
