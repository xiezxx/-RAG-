<template>
  <div class="login-page">
    <!-- ── Animated background layers ── -->
    <div class="bg-layer">
      <div class="bg-gradient"></div>
      <div class="bg-grid"></div>
      <div class="bg-orb orb-1"></div>
      <div class="bg-orb orb-2"></div>
      <div class="bg-orb orb-3"></div>
      <div class="bg-orb orb-4"></div>
    </div>

    <!-- ── Floating particles ── -->
    <canvas ref="particleCanvas" class="particles"></canvas>

    <!-- ── Centered login card ── -->
    <div class="login-wrapper">
      <div class="login-card">
        <!-- Brand -->
        <div class="brand-row">
          <div class="brand-icon">
            <span>⚖️</span>
          </div>
          <h1 class="brand-name">劳动法 RAG</h1>
          <p class="brand-tagline">智能咨询系统 · 有法可依</p>
        </div>

        <!-- Form -->
        <div class="form-area">
          <template v-if="isRegister">
            <div class="input-group">
              <div class="input-icon"><el-icon><User /></el-icon></div>
              <input v-model="form.name" placeholder="姓名" class="modern-input" />
            </div>
            <div class="input-group">
              <div class="input-icon"><el-icon><Phone /></el-icon></div>
              <input v-model="form.phone" placeholder="手机号（选填）" class="modern-input" />
            </div>
          </template>

          <div class="input-group">
            <div class="input-icon"><el-icon><User /></el-icon></div>
            <input
              v-model="form.username"
              placeholder="用户名"
              class="modern-input"
              @keyup.enter="submit"
            />
          </div>

          <div class="input-group">
            <div class="input-icon"><el-icon><Lock /></el-icon></div>
            <input
              v-model="form.password"
              type="password"
              placeholder="密码"
              class="modern-input"
              @keyup.enter="submit"
            />
          </div>

          <div class="input-group" v-if="isRegister">
            <div class="input-icon"><el-icon><Lock /></el-icon></div>
            <input
              v-model="form.confirmPassword"
              type="password"
              placeholder="确认密码"
              class="modern-input"
              @keyup.enter="submit"
            />
          </div>

          <button class="submit-btn" @click="submit" :disabled="loading">
            <span v-if="loading" class="btn-loading">
              <span class="loading-dot"></span>
            </span>
            <span v-else>{{ isRegister ? '创建账户' : '登 录' }}</span>
          </button>
        </div>

        <!-- Toggle -->
        <p class="toggle-row">
          {{ isRegister ? '已有账户？' : '没有账户？' }}
          <a href="javascript:void(0)" @click="toggleMode" class="toggle-link">
            {{ isRegister ? '去登录' : '立即注册' }}
          </a>
        </p>
      </div>

      <!-- Footer -->
      <p class="login-footer">
        基于检索增强生成 + 知识图谱 + 时效感知 &nbsp;|&nbsp; 8部法律 · 720条文 · 70案例
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Phone } from '@element-plus/icons-vue'
import api from '../api'

const router = useRouter()
const loading = ref(false)
const isRegister = ref(false)
const form = reactive({ username: '', password: '', name: '', phone: '', confirmPassword: '' })

function toggleMode() {
  isRegister.value = !isRegister.value
  form.username = ''
  form.password = ''
  form.name = ''
  form.phone = ''
  form.confirmPassword = ''
}

async function submit() {
  if (!form.username || !form.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  if (isRegister.value) {
    if (form.password !== form.confirmPassword) {
      ElMessage.warning('两次密码不一致')
      return
    }
    if (form.password.length < 6) {
      ElMessage.warning('密码长度不能少于6位')
      return
    }
    return await register()
  }
  return await login()
}

async function login() {
  loading.value = true
  try {
    const res = await api.post('/auth/login', form)
    if (res.code === 200) {
      localStorage.setItem('token', res.data.token)
      localStorage.setItem('username', res.data.username)
      localStorage.setItem('role', res.data.role || 'USER')
      router.push('/app/chat')
    } else {
      ElMessage.error(res.message)
    }
  } catch {
    ElMessage.error('登录失败，请检查网络连接')
  } finally {
    loading.value = false
  }
}

async function register() {
  loading.value = true
  try {
    const res = await api.post('/auth/register', {
      username: form.username,
      password: form.password,
      name: form.name || form.username,
      phone: form.phone || ''
    })
    if (res.code === 200) {
      ElMessage.success('注册成功，请登录')
      toggleMode()
    } else {
      ElMessage.error(res.message)
    }
  } catch {
    ElMessage.error('注册失败，请检查网络连接')
  } finally {
    loading.value = false
  }
}

// ── Particle animation ──
const particleCanvas = ref(null)
let animId = null

onMounted(() => {
  const canvas = particleCanvas.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  let w, h

  const resize = () => {
    w = canvas.width = window.innerWidth
    h = canvas.height = window.innerHeight
  }
  resize()
  window.addEventListener('resize', resize)

  // Create particles
  const particles = Array.from({ length: 50 }, () => ({
    x: Math.random() * w,
    y: Math.random() * h,
    vx: (Math.random() - 0.5) * 0.4,
    vy: (Math.random() - 0.5) * 0.4,
    r: Math.random() * 1.5 + 0.5,
    alpha: Math.random() * 0.4 + 0.1,
  }))

  function draw() {
    ctx.clearRect(0, 0, w, h)
    for (const p of particles) {
      p.x += p.vx
      p.y += p.vy
      if (p.x < 0) p.x = w
      if (p.x > w) p.x = 0
      if (p.y < 0) p.y = h
      if (p.y > h) p.y = 0
      ctx.beginPath()
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(148, 163, 184, ${p.alpha})`
      ctx.fill()
    }

    // Draw connections
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x
        const dy = particles[i].y - particles[j].y
        const dist = Math.sqrt(dx * dx + dy * dy)
        if (dist < 120) {
          ctx.beginPath()
          ctx.moveTo(particles[i].x, particles[i].y)
          ctx.lineTo(particles[j].x, particles[j].y)
          ctx.strokeStyle = `rgba(148, 163, 184, ${0.06 * (1 - dist / 120)})`
          ctx.lineWidth = 0.5
          ctx.stroke()
        }
      }
    }
    animId = requestAnimationFrame(draw)
  }
  draw()
})

onUnmounted(() => {
  if (animId) cancelAnimationFrame(animId)
})
</script>

<style scoped>
/* ══════ Full page ══════ */
.login-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  background: #0B1120;
}

/* ══════ Background layers ══════ */
.bg-layer { position: absolute; inset: 0; pointer-events: none; }
.bg-gradient {
  position: absolute; inset: 0;
  background:
    radial-gradient(ellipse 80% 60% at 20% 20%, rgba(3, 105, 161, 0.15) 0%, transparent 60%),
    radial-gradient(ellipse 60% 50% at 80% 80%, rgba(56, 189, 248, 0.08) 0%, transparent 60%),
    radial-gradient(ellipse 50% 40% at 50% 50%, rgba(16, 185, 129, 0.05) 0%, transparent 60%),
    #0B1120;
}
.bg-grid {
  position: absolute; inset: 0;
  background-image:
    linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px);
  background-size: 80px 80px;
  mask-image: radial-gradient(ellipse 60% 50% at 50% 50%, black 30%, transparent 70%);
  -webkit-mask-image: radial-gradient(ellipse 60% 50% at 50% 50%, black 30%, transparent 70%);
}

.bg-orb {
  position: absolute; border-radius: 50%;
  filter: blur(80px); opacity: 0.15;
}
.orb-1 { width: 400px; height: 400px; background: #0369A1; top: -10%; left: -5%; animation: orbFloat1 12s ease-in-out infinite; }
.orb-2 { width: 300px; height: 300px; background: #10B981; bottom: -8%; right: -3%; animation: orbFloat2 15s ease-in-out infinite; }
.orb-3 { width: 200px; height: 200px; background: #6366F1; top: 50%; right: 15%; animation: orbFloat3 10s ease-in-out infinite; }
.orb-4 { width: 250px; height: 250px; background: #38BDF8; bottom: 30%; left: 10%; animation: orbFloat4 14s ease-in-out infinite; }

@keyframes orbFloat1 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -40px) scale(1.1); }
  66% { transform: translate(-20px, 20px) scale(0.9); }
}
@keyframes orbFloat2 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(-40px, -30px) scale(1.15); }
}
@keyframes orbFloat3 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(20px, 30px) scale(1.2); }
  66% { transform: translate(-30px, -20px) scale(0.85); }
}
@keyframes orbFloat4 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(-25px, 35px) scale(1.1); }
}

/* Particles canvas */
.particles {
  position: absolute; inset: 0;
  pointer-events: none; z-index: 1;
}

/* ══════ Login card ══════ */
.login-wrapper {
  position: relative; z-index: 10;
  display: flex; flex-direction: column; align-items: center;
  animation: cardEnter 0.8s cubic-bezier(0.22, 1, 0.36, 1) both;
}
@keyframes cardEnter {
  from { opacity: 0; transform: translateY(30px) scale(0.96); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

.login-card {
  width: 420px;
  padding: 48px 44px 36px;
  background: rgba(15, 23, 42, 0.65);
  backdrop-filter: blur(28px);
  -webkit-backdrop-filter: blur(28px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 24px;
  box-shadow:
    0 40px 100px rgba(0, 0, 0, 0.5),
    0 0 80px rgba(3, 105, 161, 0.08),
    0 0 0 1px rgba(255, 255, 255, 0.04) inset,
    0 1px 0 0 rgba(255, 255, 255, 0.06) inset;
  position: relative;
}
/* Top light reflection stripe */
.login-card::before {
  content: '';
  position: absolute; top: 0; left: 40px; right: 40px;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.12), transparent);
}

/* Brand */
.brand-row { text-align: center; margin-bottom: 36px; }
.brand-icon {
  width: 64px; height: 64px; margin: 0 auto 16px;
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, rgba(3, 105, 161, 0.3), rgba(56, 189, 248, 0.12));
  border: 1px solid rgba(56, 189, 248, 0.25);
  border-radius: 20px;
  font-size: 30px;
  box-shadow: 0 0 40px rgba(3, 105, 161, 0.2), 0 0 80px rgba(3, 105, 161, 0.06);
  animation: iconGlow 3s ease-in-out infinite;
}
@keyframes iconGlow {
  0%, 100% { box-shadow: 0 0 40px rgba(3, 105, 161, 0.2), 0 0 80px rgba(3, 105, 161, 0.06); }
  50% { box-shadow: 0 0 60px rgba(3, 105, 161, 0.35), 0 0 100px rgba(56, 189, 248, 0.12); }
}
.brand-name {
  font-size: 28px; font-weight: 700; color: #F1F5F9;
  letter-spacing: 2px; margin: 0;
  background: linear-gradient(180deg, #F8FAFC, #94A3B8);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.brand-tagline {
  font-size: 13px; color: #64748B;
  margin: 8px 0 0; letter-spacing: 1px;
}

/* Form */
.form-area { display: flex; flex-direction: column; gap: 14px; }

.input-group {
  display: flex; align-items: center;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  transition: all 0.25s ease;
  overflow: hidden;
}
.input-group:focus-within {
  border-color: rgba(56, 189, 248, 0.4);
  background: rgba(255, 255, 255, 0.06);
  box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.08);
}
.input-icon {
  width: 44px; height: 44px;
  display: flex; align-items: center; justify-content: center;
  color: #64748B; font-size: 18px; flex-shrink: 0;
}
.modern-input {
  flex: 1; height: 44px;
  background: transparent; border: none; outline: none;
  color: #E2E8F0; font-size: 15px; font-family: inherit;
  padding-right: 16px;
}
.modern-input::placeholder { color: #475569; }
.modern-input:-webkit-autofill {
  -webkit-box-shadow: 0 0 0 30px #1E293B inset !important;
  -webkit-text-fill-color: #E2E8F0 !important;
}

.submit-btn {
  width: 100%; height: 48px; margin-top: 8px;
  border: none; border-radius: 12px;
  background: linear-gradient(135deg, #0369A1, #38BDF8);
  color: #FFF; font-size: 16px; font-weight: 600;
  letter-spacing: 3px; cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 24px rgba(3, 105, 161, 0.35), 0 0 0 0 rgba(56, 189, 248, 0.3);
  font-family: inherit;
  position: relative;
}
.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 36px rgba(3, 105, 161, 0.5), 0 0 30px rgba(56, 189, 248, 0.2);
  background: linear-gradient(135deg, #0284C7, #7DD3FC);
}
.submit-btn:active:not(:disabled) { transform: scale(0.98); }
.submit-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-loading { display: flex; align-items: center; justify-content: center; }
.loading-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: #FFF; animation: dotBounce 0.6s ease infinite alternate;
}
@keyframes dotBounce {
  from { transform: scale(1); opacity: 0.5; }
  to { transform: scale(2); opacity: 1; }
}

/* Toggle */
.toggle-row {
  text-align: center; margin: 20px 0 0;
  font-size: 13px; color: #64748B;
}
.toggle-link {
  color: #38BDF8; text-decoration: none;
  font-weight: 500; transition: color 0.2s;
}
.toggle-link:hover { color: #7DD3FC; }

/* Footer */
.login-footer {
  margin-top: 28px;
  font-size: 12px; color: #475569;
  letter-spacing: 0.5px; text-align: center;
}

/* ══════ Responsive ══════ */
@media (max-width: 480px) {
  .login-card { width: 92%; padding: 36px 24px 28px; }
}
</style>
