<template>
  <div class="landing">
    <!-- ── Background ── -->
    <div class="bg-layer">
      <div class="bg-gradient"></div>
      <div class="bg-grid"></div>
      <div class="bg-orb orb-1"></div>
      <div class="bg-orb orb-2"></div>
      <div class="bg-orb orb-3"></div>
    </div>
    <canvas ref="particleCanvas" class="particles"></canvas>

    <!-- ── Hero content ── -->
    <div class="hero">
      <div class="hero-badge">
        <span class="badge-dot"></span> AI 驱动的劳动法智能问答
      </div>

      <h1 class="hero-title">
        <span class="title-line">劳动法</span>
        <span class="title-highlight">RAG 智能咨询系统</span>
      </h1>
      <p class="hero-desc">
        融合检索增强生成、知识图谱与时效感知，<br/>为您提供有法可依、有据可循的专业法律问答
      </p>

      <!-- CTA -->
      <button class="cta-btn" @click="$router.push('/login')">
        <span>进入系统</span>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <line x1="5" y1="12" x2="19" y2="12"></line>
          <polyline points="12 5 19 12 12 19"></polyline>
        </svg>
      </button>

      <!-- Stats -->
      <div class="hero-stats">
        <div class="h-stat">
          <span class="hs-num">8</span>
          <span class="hs-lbl">部法律</span>
        </div>
        <div class="h-stat">
          <span class="hs-num">720</span>
          <span class="hs-lbl">条条文</span>
        </div>
        <div class="h-stat">
          <span class="hs-num">70</span>
          <span class="hs-lbl">个案例</span>
        </div>
        <div class="h-stat">
          <span class="hs-num">279</span>
          <span class="hs-lbl">条KG关系</span>
        </div>
      </div>
    </div>

    <!-- ── Scroll hint ── -->
    <div class="scroll-hint" @click="scrollToFeatures">
      <span>探索功能</span>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="6 9 12 15 18 9"></polyline>
      </svg>
    </div>

    <!-- ── Features section ── -->
    <div class="features" ref="featuresRef">
      <h2 class="section-title">核心技术能力</h2>
      <div class="feature-grid">
        <div class="feature-card" v-for="(f, i) in features" :key="i"
             :style="{ animationDelay: (i * 0.1) + 's' }">
          <div class="fc-icon" :style="{ background: f.gradient }">
            <span>{{ f.icon }}</span>
          </div>
          <h3>{{ f.title }}</h3>
          <p>{{ f.desc }}</p>
        </div>
      </div>
    </div>

    <!-- ── Bottom CTA ── -->
    <div class="bottom-cta">
      <h2>准备好体验智能法律咨询了吗？</h2>
      <button class="cta-btn secondary" @click="$router.push('/login')">
        <span>免费开始使用</span>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <line x1="5" y1="12" x2="19" y2="12"></line>
          <polyline points="12 5 19 12 12 19"></polyline>
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const featuresRef = ref(null)

const features = [
  {
    icon: '🔍', title: 'BM25 关键词检索',
    desc: '字符级 Bigram 分词 + Okapi BM25 排序，精准匹配法律条文关键词',
    gradient: 'linear-gradient(135deg, #DBEAFE, #BFDBFE)'
  },
  {
    icon: '🧠', title: '向量语义检索',
    desc: 'text2vec-base-chinese 中文模型 + FAISS 索引，理解自然语言法律问题',
    gradient: 'linear-gradient(135deg, #D1FAE5, #A7F3D0)'
  },
  {
    icon: '🔗', title: '知识图谱增强',
    desc: 'Neo4j 图数据库，7类实体 279条关系，揭示法律概念间的深层关联',
    gradient: 'linear-gradient(135deg, #EDE9FE, #DDD6FE)'
  },
  {
    icon: '⏳', title: '时效感知过滤',
    desc: '自动标注法条生效/修订/废止状态，优先推荐现行有效的法律依据',
    gradient: 'linear-gradient(135deg, #FEF3C7, #93C5FD)'
  }
]

function scrollToFeatures() {
  featuresRef.value?.scrollIntoView({ behavior: 'smooth' })
}

// ── Particles ──
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

  const particles = Array.from({ length: 40 }, () => ({
    x: Math.random() * w, y: Math.random() * h,
    vx: (Math.random() - 0.5) * 0.3,
    vy: (Math.random() - 0.5) * 0.3,
    r: Math.random() * 2 + 0.5,
    alpha: Math.random() * 0.4 + 0.08,
  }))

  function draw() {
    ctx.clearRect(0, 0, w, h)
    for (const p of particles) {
      p.x += p.vx; p.y += p.vy
      if (p.x < 0) p.x = w; if (p.x > w) p.x = 0
      if (p.y < 0) p.y = h; if (p.y > h) p.y = 0
      ctx.beginPath()
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(148, 163, 184, ${p.alpha})`
      ctx.fill()
    }
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x
        const dy = particles[i].y - particles[j].y
        const dist = Math.sqrt(dx * dx + dy * dy)
        if (dist < 130) {
          ctx.beginPath()
          ctx.moveTo(particles[i].x, particles[i].y)
          ctx.lineTo(particles[j].x, particles[j].y)
          ctx.strokeStyle = `rgba(148, 163, 184, ${0.05 * (1 - dist / 130)})`
          ctx.lineWidth = 0.5
          ctx.stroke()
        }
      }
    }
    animId = requestAnimationFrame(draw)
  }
  draw()
})

onUnmounted(() => { if (animId) cancelAnimationFrame(animId) })
</script>

<style scoped>
/* ══════ Full page scroll ══════ */
.landing {
  min-height: 100vh;
  background: #0B1120;
  color: #E2E8F0;
  position: relative;
  overflow-x: hidden;
}

/* ══════ Background ══════ */
.bg-layer { position: fixed; inset: 0; pointer-events: none; z-index: 0; }
.bg-gradient {
  position: absolute; inset: 0;
  background:
    radial-gradient(ellipse 70% 50% at 30% 0%, rgba(3,105,161,0.18) 0%, transparent 60%),
    radial-gradient(ellipse 50% 40% at 70% 80%, rgba(56,189,248,0.08) 0%, transparent 60%),
    radial-gradient(ellipse 40% 30% at 50% 50%, rgba(16,185,129,0.05) 0%, transparent 60%),
    #0B1120;
}
.bg-grid {
  position: absolute; inset: 0;
  background-image:
    linear-gradient(rgba(255,255,255,0.015) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.015) 1px, transparent 1px);
  background-size: 80px 80px;
  mask-image: radial-gradient(ellipse 50% 50% at 50% 50%, black 20%, transparent 70%);
}
.bg-orb { position: absolute; border-radius: 50%; filter: blur(100px); opacity: 0.12; }
.orb-1 { width: 500px; height: 500px; background: #0369A1; top: -15%; left: -10%; animation: orbFloat1 14s ease-in-out infinite; }
.orb-2 { width: 350px; height: 350px; background: #10B981; bottom: -10%; right: -5%; animation: orbFloat2 16s ease-in-out infinite; }
.orb-3 { width: 250px; height: 250px; background: #6366F1; top: 60%; left: 60%; animation: orbFloat3 12s ease-in-out infinite; }

@keyframes orbFloat1 {
  0%,100% { transform: translate(0,0) scale(1); }
  33% { transform: translate(40px,-50px) scale(1.1); }
  66% { transform: translate(-30px,30px) scale(0.9); }
}
@keyframes orbFloat2 {
  0%,100% { transform: translate(0,0) scale(1); }
  50% { transform: translate(-50px,-40px) scale(1.15); }
}
@keyframes orbFloat3 {
  0%,100% { transform: translate(0,0) scale(1); }
  33% { transform: translate(30px,40px) scale(1.2); }
  66% { transform: translate(-40px,-20px) scale(0.85); }
}

.particles { position: fixed; inset: 0; pointer-events: none; z-index: 1; }

/* ══════ Hero ══════ */
.hero {
  position: relative; z-index: 10;
  min-height: 100vh;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  text-align: center;
  padding: 80px 24px;
  animation: heroIn 0.8s cubic-bezier(0.22,1,0.36,1) both;
}
@keyframes heroIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.hero-badge {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 6px 16px; border-radius: 20px;
  background: rgba(3,105,161,0.15);
  border: 1px solid rgba(3,105,161,0.25);
  font-size: 13px; color: #7DD3FC;
  margin-bottom: 28px;
  letter-spacing: 0.5px;
}
.badge-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: #38BDF8; animation: dotPulse 2s ease infinite;
}
@keyframes dotPulse {
  0%,100% { opacity: 0.4; }
  50% { opacity: 1; }
}

.hero-title {
  margin: 0 0 20px;
  display: flex; flex-direction: column; gap: 4px;
}
.title-line {
  font-size: 20px; font-weight: 400; color: #94A3B8;
  letter-spacing: 4px;
}
.title-highlight {
  font-size: 52px; font-weight: 800;
  letter-spacing: 2px;
  background: linear-gradient(135deg, #38BDF8 0%, #7DD3FC 40%, #FFF 70%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1.2;
}

.hero-desc {
  font-size: 16px; color: #64748B;
  line-height: 1.8; margin: 0 0 40px;
  max-width: 500px;
}

/* CTA */
.cta-btn {
  display: inline-flex; align-items: center; gap: 10px;
  padding: 14px 36px; border-radius: 14px;
  border: none;
  background: linear-gradient(135deg, #0369A1, #38BDF8);
  color: #FFF; font-size: 17px; font-weight: 600;
  letter-spacing: 2px; cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
  box-shadow: 0 4px 30px rgba(3,105,161,0.35), 0 0 60px rgba(56,189,248,0.1);
  font-family: inherit;
}
.cta-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 40px rgba(3,105,161,0.5), 0 0 80px rgba(56,189,248,0.2);
  background: linear-gradient(135deg, #0284C7, #7DD3FC);
}
.cta-btn.secondary {
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.12);
  box-shadow: 0 4px 20px rgba(0,0,0,0.2);
}
.cta-btn.secondary:hover {
  background: rgba(255,255,255,0.1);
  border-color: rgba(255,255,255,0.2);
  box-shadow: 0 8px 30px rgba(0,0,0,0.3);
}

/* Stats */
.hero-stats {
  display: flex; gap: 40px; margin-top: 60px;
}
.h-stat { text-align: center; }
.hs-num {
  font-size: 32px; font-weight: 700;
  color: #38BDF8;
}
.hs-lbl {
  font-size: 12px; color: #64748B;
  letter-spacing: 1px; text-transform: uppercase;
  margin-top: 4px; display: block;
}

/* Scroll hint */
.scroll-hint {
  position: absolute; bottom: 32px; left: 50%; transform: translateX(-50%);
  z-index: 10;
  display: flex; flex-direction: column; align-items: center; gap: 4px;
  color: #475569; font-size: 12px; cursor: pointer;
  transition: color 0.3s;
  animation: bounceHint 2s ease infinite;
}
.scroll-hint:hover { color: #94A3B8; }
@keyframes bounceHint {
  0%,100% { transform: translateX(-50%) translateY(0); }
  50% { transform: translateX(-50%) translateY(6px); }
}

/* ══════ Features ══════ */
.features {
  position: relative; z-index: 10;
  padding: 100px 24px 80px;
  max-width: 1000px; margin: 0 auto;
}
.section-title {
  text-align: center; font-size: 28px; font-weight: 700;
  color: #F1F5F9; margin: 0 0 48px;
}
.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 20px;
}
.feature-card {
  padding: 32px 24px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 16px;
  transition: all 0.3s ease;
  animation: cardUp 0.5s ease both;
}
.feature-card:hover {
  background: rgba(255,255,255,0.06);
  border-color: rgba(255,255,255,0.12);
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(0,0,0,0.3);
}
@keyframes cardUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
.fc-icon {
  width: 48px; height: 48px; border-radius: 14px;
  display: flex; align-items: center; justify-content: center;
  font-size: 22px; margin-bottom: 16px;
}
.feature-card h3 {
  font-size: 16px; font-weight: 600; color: #E2E8F0;
  margin: 0 0 8px;
}
.feature-card p {
  font-size: 13px; color: #64748B;
  line-height: 1.7; margin: 0;
}

/* ══════ Bottom CTA ══════ */
.bottom-cta {
  position: relative; z-index: 10;
  text-align: center; padding: 80px 24px 100px;
}
.bottom-cta h2 {
  font-size: 24px; font-weight: 600; color: #F1F5F9;
  margin: 0 0 28px;
}

/* ══════ Responsive ══════ */
@media (max-width: 768px) {
  .title-highlight { font-size: 34px; }
  .hero-stats { gap: 24px; flex-wrap: wrap; justify-content: center; }
  .hs-num { font-size: 24px; }
  .feature-grid { grid-template-columns: 1fr; }
}
</style>
