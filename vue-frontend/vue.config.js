const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: [],
  lintOnSave: false,
  devServer: {
    port: 8081,
    client: {
      overlay: false
    },
    proxy: {
      '/api': {
        target: 'http://localhost:8089',
        changeOrigin: true
      }
    }
  }
})
