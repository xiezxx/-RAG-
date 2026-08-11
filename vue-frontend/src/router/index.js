import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../views/MainLayout.vue'

const routes = [
  // 介绍页（无需登录）
  { path: '/', name: 'Landing', component: () => import('../views/LandingView.vue') },
  // 登录注册（无需登录）
  { path: '/login', name: 'Login', component: () => import('../views/LoginView.vue') },
  // 系统内部（需登录）
  {
    path: '/app',
    component: MainLayout,
    redirect: '/app/chat',
    children: [
      { path: 'dashboard', name: 'Dashboard', component: () => import('../views/DashboardView.vue') },
      { path: 'chat', name: 'Chat', component: () => import('../views/ChatView.vue') },
      { path: 'history', name: 'History', component: () => import('../views/HistoryView.vue') },
      { path: 'cases', name: 'Cases', component: () => import('../views/CaseListView.vue') },
      { path: 'cases/:id', name: 'CaseDetail', component: () => import('../views/CaseDetailView.vue') },
      { path: 'statutes', name: 'Statutes', component: () => import('../views/StatuteView.vue') },
      { path: 'statutes/manage', name: 'StatuteManager', component: () => import('../views/StatuteManager.vue') },
      { path: 'kg', name: 'KG', component: () => import('../views/KgView.vue') },
      { path: 'admin/users', name: 'UserManager', component: () => import('../views/UserManager.vue') },
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// chunk 加载失败 → 自动刷新
router.onError((error) => {
  if (error.message?.includes('Loading chunk')) {
    window.location.reload()
  }
})

// 登录守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  // 公开页面：介绍页 + 登录页
  if (to.path === '/' || to.path === '/login') {
    // 已登录用户访问公开页 → 跳到系统首页
    if (token && to.path !== '/') {
      next('/app/chat')
    } else {
      next()
    }
    return
  }
  // 系统内部页面需要登录
  if (!token) {
    next('/login')
  } else {
    next()
  }
})

export default router
