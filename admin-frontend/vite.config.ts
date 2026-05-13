import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import path from 'path'

export default defineConfig({
  plugins: [
    vue(),
    AutoImport({
      resolvers: [ElementPlusResolver()],
    }),
    Components({
      resolvers: [ElementPlusResolver()],
    }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/admin/api': {
        target: 'http://localhost:5678',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: '../src/memory_mcp/admin/static',
    emptyOutDir: true,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) {
            return undefined
          }

          if (id.includes('element-plus') || id.includes('@element-plus')) {
            return 'element-plus'
          }

          if (id.includes('echarts') || id.includes('zrender') || id.includes('vue-echarts')) {
            return 'charts'
          }

          if (
            id.includes('vue-router') ||
            id.includes('pinia') ||
            id.includes('/vue/') ||
            id.includes('node_modules/vue/')
          ) {
            return 'vue-vendor'
          }

          return 'vendor'
        },
      },
    },
  },
})
