import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import './assets/global.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'

// 忽略 Chrome ResizeObserver 无害警告
window.addEventListener('error', e => {
  if (e.message?.includes('ResizeObserver')) {
    e.stopImmediatePropagation()
    return false
  }
})

const app = createApp(App)
app.use(ElementPlus)
app.use(router)

// 全局注册 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.mount('#app')
