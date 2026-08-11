<template>
  <el-container class="layout">
    <!-- ── Header ── -->
    <el-header class="header">
      <div class="header-left">
        <!-- Logo：天平 SVG -->
        <div class="logo-wrapper">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 3v18" />
            <path d="M8 21h8" />
            <path d="M5 7h14" />
            <path d="M5 7l-3.5 6a3 3 0 0 0 6 0L5 7z" />
            <path d="M19 7l-3.5 6a3 3 0 0 0 6 0L19 7z" />
          </svg>
        </div>
        <div class="brand-text">
          <span class="title">劳动法 RAG</span>
          <span class="subtitle">智能咨询系统</span>
        </div>
      </div>

      <!-- 检索状态指示 -->
      <div class="header-status">
        <span class="status-dot"></span>
        <span class="status-text">检索引擎在线</span>
      </div>

      <div class="header-right">
        <span class="username">{{ username }}</span>
        <span class="role-badge" :class="role === 'ADMIN' ? 'is-admin' : ''">
          {{ role === 'ADMIN' ? '管理员' : '用户' }}
        </span>
        <button class="logout-btn" @click="logout" title="退出登录">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
            <polyline points="16 17 21 12 16 7" />
            <line x1="21" y1="12" x2="9" y2="12" />
          </svg>
          <span>退出</span>
        </button>
      </div>
    </el-header>

    <el-container>
      <!-- ── Sidebar ── -->
      <el-aside
        :width="(sidebarCollapsed && !sidebarHover) ? '60px' : '230px'"
        class="aside"
        :class="{ collapsed: sidebarCollapsed }"
        @mouseenter="sidebarHover = true"
        @mouseleave="sidebarHover = false"
      >
        <div class="sidebar-inner">
          <!-- Toggle -->
          <div class="sidebar-toggle" @click="sidebarCollapsed = !sidebarCollapsed" :class="{ active: !sidebarCollapsed }">
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
              <rect x="3" y="3" width="18" height="18" rx="2" />
              <line x1="15" y1="3" x2="15" y2="21" />
            </svg>
          </div>

          <el-menu router :default-active="route.path" class="menu" :collapse="sidebarCollapsed && !sidebarHover">
            <!-- 导航分组 -->
            <div v-show="!(sidebarCollapsed && !sidebarHover)" class="menu-group-label">导航</div>
            <el-menu-item index="/app/dashboard">
              <el-icon><Odometer /></el-icon>
              <span>系统概览</span>
            </el-menu-item>
            <el-menu-item index="/app/chat">
              <el-icon><ChatDotRound /></el-icon>
              <span>智能问答</span>
            </el-menu-item>
            <el-menu-item index="/app/history">
              <el-icon><Clock /></el-icon>
              <span>问答记录</span>
            </el-menu-item>
            <el-menu-item index="/app/cases">
              <el-icon><Document /></el-icon>
              <span>案例库</span>
            </el-menu-item>
            <el-menu-item index="/app/statutes">
              <el-icon><Collection /></el-icon>
              <span>法律法规</span>
            </el-menu-item>
            <el-menu-item index="/app/kg">
              <el-icon><Connection /></el-icon>
              <span>知识图谱</span>
            </el-menu-item>

            <!-- 管理分组 -->
            <template v-if="role === 'ADMIN'">
              <div v-show="!(sidebarCollapsed && !sidebarHover)" class="menu-group-label admin">管理</div>
              <el-menu-item index="/app/statutes/manage">
                <el-icon><EditPen /></el-icon>
                <span>法规管理</span>
              </el-menu-item>
              <el-menu-item index="/app/admin/users">
                <el-icon><UserFilled /></el-icon>
                <span>用户管理</span>
              </el-menu-item>
            </template>
          </el-menu>

          <!-- Sidebar stats -->
          <div class="sidebar-footer" v-if="stats" v-show="!(sidebarCollapsed && !sidebarHover)">
            <div class="stats-grid">
              <div class="stat-cell">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
                <b>{{ stats.statutes || 0 }}</b>
                <span>法律</span>
              </div>
              <div class="stat-cell">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/></svg>
                <b>{{ stats.articles || 0 }}</b>
                <span>条文</span>
              </div>
              <div class="stat-cell">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v18"/><path d="M8 21h8"/><path d="M5 7h14"/><path d="M5 7l-3.5 6a3 3 0 0 0 6 0L5 7z"/><path d="M19 7l-3.5 6a3 3 0 0 0 6 0L19 7z"/></svg>
                <b>{{ stats.cases || 0 }}</b>
                <span>案例</span>
              </div>
              <div class="stat-cell">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
                <b>279</b>
                <span>关系</span>
              </div>
            </div>
          </div>
        </div>
      </el-aside>

      <!-- ── Main Content ── -->
      <el-main class="main">
        <router-view v-slot="{ Component }">
          <keep-alive>
            <component :is="Component" />
          </keep-alive>
        </router-view>
      </el-main>
    </el-container>

    <!-- 语音助手（左下角） -->
    <VoiceAssistant />
  </el-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { SwitchButton } from '@element-plus/icons-vue'
import VoiceAssistant from '../components/VoiceAssistant.vue'

const router = useRouter()
const route = useRoute()
const username = localStorage.getItem('username') || ''
const role = localStorage.getItem('role') || 'USER'
const stats = ref(null)
const sidebarCollapsed = ref(false)
const sidebarHover = ref(false)

onMounted(async () => {
  try {
    const res = await fetch('/api/chat/stats')
    if (res.ok) {
      const data = await res.json()
      if (data.neo4j) stats.value = data.neo4j
    }
  } catch {}
})

function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('username')
  localStorage.removeItem('role')
  router.push('/')
}
</script>

<style scoped>
.layout { height: 100vh; }
.layout > .el-container { flex: 1; min-height: 0; overflow: hidden; }

/* ══════ Header ══════ */
.header {
  background: linear-gradient(90deg, #080D16 0%, #0B1322 45%, #0F172A 100%);
  color: #FFF;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 60px;
  z-index: 10;
  position: relative;
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.3);
}

/* 签名元素：法条流动光束 */
.header::after {
  content: '';
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 2px;
  background: linear-gradient(90deg,
    transparent,
    rgba(56,189,248,0) 20%,
    rgba(56,189,248,0.9) 50%,
    rgba(56,189,248,0) 80%,
    transparent);
  animation: beamFlow 5s linear infinite;
  opacity: 0.7;
}
@keyframes beamFlow {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.header-left { display: flex; align-items: center; gap: 14px; }
.logo-wrapper {
  width: 38px; height: 38px;
  display: flex; align-items: center; justify-content: center;
  color: #38BDF8;
  background: rgba(56,189,248,0.08);
  border: 1px solid rgba(56,189,248,0.2);
  border-radius: 10px;
  transition: all 0.2s;
}
.logo-wrapper:hover { background: rgba(56,189,248,0.15); }
.brand-text { display: flex; flex-direction: column; line-height: 1.2; }
.title {
  font-size: 16px; font-weight: 700;
  letter-spacing: 0.5px;
  color: #F1F5F9;
}
.subtitle { font-size: 10px; color: #64748B; letter-spacing: 2px; }

/* 检索状态 */
.header-status {
  position: absolute; left: 50%; transform: translateX(-50%);
  display: flex; align-items: center; gap: 7px;
  padding: 4px 12px;
  border-radius: 20px;
  background: rgba(34,197,94,0.08);
  border: 1px solid rgba(34,197,94,0.15);
  font-size: 11px; color: #4ADE80;
}
.status-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: #22C55E;
  animation: statusPulse 2s ease infinite;
}
@keyframes statusPulse {
  0%,100% { box-shadow: 0 0 0 0 rgba(34,197,94,0.4); }
  50% { box-shadow: 0 0 0 5px rgba(34,197,94,0); }
}

.header-right { display: flex; align-items: center; gap: 12px; }
.username {
  font-size: 13px; color: #CBD5E1;
  max-width: 100px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.role-badge {
  font-size: 11px; padding: 3px 10px;
  border-radius: 20px;
  background: rgba(148,163,184,0.12);
  color: #94A3B8;
  border: 1px solid rgba(148,163,184,0.15);
}
.role-badge.is-admin {
  background: rgba(56,189,248,0.1);
  color: #38BDF8;
  border-color: rgba(56,189,248,0.2);
}
.logout-btn {
  display: flex; align-items: center; gap: 5px;
  padding: 6px 10px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 8px;
  color: #64748B; font-size: 12px; cursor: pointer;
  transition: all 0.2s;
  font-family: inherit;
}
.logout-btn:hover {
  color: #F87171;
  border-color: rgba(239,68,68,0.25);
  background: rgba(239,68,68,0.08);
}

/* ══════ Sidebar ══════ */
.aside {
  background: linear-gradient(180deg, #0B1120 0%, #080D16 100%);
  border-right: 1px solid rgba(255,255,255,0.04);
  display: flex; flex-direction: column;
  position: relative; overflow: hidden;
  transition: width 0.3s cubic-bezier(0.4,0,0.2,1);
}
.aside::before {
  content: '';
  position: absolute; top: 0; right: 0;
  width: 1px; height: 60px;
  background: linear-gradient(180deg, rgba(56,189,248,0.3), transparent);
}

.sidebar-inner {
  display: flex; flex-direction: column;
  height: 100%; position: relative; z-index: 1;
}
.sidebar-toggle {
  display: flex; align-items: center; justify-content: center;
  height: 34px; margin: 10px 14px 6px;
  border-radius: 8px; cursor: pointer;
  color: #475569; transition: all 0.2s;
}
.collapsed .sidebar-toggle { margin: 10px 14px; justify-content: center; }
.sidebar-toggle:hover { background: rgba(255,255,255,0.06); color: #94A3B8; }
.sidebar-toggle.active { color: #64748B; }

.menu {
  border-right: none;
  background: transparent;
  flex: 1; padding: 0 8px;
}
.menu :deep(.el-menu-item) {
  color: #94A3B8;
  font-size: 13.5px;
  height: 42px; line-height: 42px;
  margin: 2px 0;
  border-radius: 9px;
  padding-left: 14px !important;
  transition: all 0.2s cubic-bezier(0.4,0,0.2,1);
  position: relative;
}
.menu :deep(.el-menu-item .el-icon) {
  font-size: 17px;
  transition: transform 0.2s;
}
.menu :deep(.el-menu-item:hover) {
  background: rgba(255,255,255,0.05);
  color: #E2E8F0;
}
.menu :deep(.el-menu-item:hover .el-icon) {
  transform: translateX(2px);
}
.menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(135deg, rgba(56,189,248,0.14), rgba(56,189,248,0.05));
  color: #38BDF8;
  font-weight: 600;
}
.menu :deep(.el-menu-item.is-active::before) {
  content: '';
  position: absolute; left: 0; top: 10px; bottom: 10px;
  width: 3px;
  background: #38BDF8;
  border-radius: 0 2px 2px 0;
  box-shadow: 0 0 8px rgba(56,189,248,0.5);
}

.menu-group-label {
  padding: 14px 14px 6px;
  font-size: 10px; color: #475569;
  letter-spacing: 2px; text-transform: uppercase;
  font-weight: 600;
}
.menu-group-label.admin { margin-top: 6px; padding-top: 14px; border-top: 1px solid rgba(255,255,255,0.05); }

/* Sidebar footer stats */
.sidebar-footer { padding: 0 12px 16px; flex-shrink: 0; }
.stats-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 6px;
}
.stat-cell {
  display: flex; flex-direction: column; align-items: center; gap: 3px;
  padding: 10px 6px;
  background: rgba(255,255,255,0.025);
  border-radius: 10px;
  border: 1px solid rgba(255,255,255,0.04);
  backdrop-filter: blur(8px);
  transition: all 0.2s;
}
.stat-cell:hover {
  background: rgba(255,255,255,0.05);
  border-color: rgba(56,189,248,0.15);
}
.stat-cell svg { color: #64748B; margin-bottom: 1px; }
.stat-cell b { color: #38BDF8; font-size: 14px; font-weight: 700; }
.stat-cell span {
  color: #64748B; font-size: 9px;
  text-transform: uppercase; letter-spacing: 1px;
}

/* ══════ Main ══════ */
.main {
  background:
    radial-gradient(ellipse 70% 60% at 20% 0%, rgba(56,189,248,0.02) 0%, transparent 50%),
    radial-gradient(ellipse 50% 40% at 80% 100%, rgba(3,105,161,0.03) 0%, transparent 50%),
    #F1F5F9;
  padding: 24px;
  overflow-y: auto;
}
</style>
