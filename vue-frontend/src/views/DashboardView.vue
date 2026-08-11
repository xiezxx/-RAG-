<template>
  <div class="dashboard">
    <!-- ══════ 页头 ══════ -->
    <div class="page-head">
      <div>
        <h2 class="page-title">系统概览</h2>
        <p class="page-subtitle">劳动法知识库运行状态</p>
      </div>
      <div class="live-badge">
        <span class="live-dot"></span>
        <span>运行中</span>
      </div>
    </div>

    <!-- ══════ 知识库台账 — 大数字 + 细线 ══════ -->
    <div class="ledger">
      <div class="ledger-cell" v-for="s in ledger" :key="s.label">
        <div class="ledger-num">
          <span ref="numRefs" :data-target="s.num" :data-suffix="s.suffix">0{{ s.suffix }}</span>
        </div>
        <div class="ledger-label">{{ s.label }}</div>
        <div class="ledger-rule" :style="{ background: s.accent }"></div>
      </div>
    </div>

    <!-- ══════ 检索流水线 — 签名元素 ══════ -->
    <section class="pipeline-section">
      <div class="section-label">检索流程</div>
      <h3 class="section-title">一条问题如何获得答案</h3>

      <div class="pipeline">
        <div class="pl-base"></div>
        <span class="pl-pulse p1"></span>
        <span class="pl-pulse p2"></span>

        <div class="pl-step" v-for="(s, i) in retrievalSteps" :key="s.name">
          <div class="pl-dot" :class="{ active: s.active }">
            <span class="pl-dot-inner">{{ i + 1 }}</span>
          </div>
          <div class="pl-label">
            <strong>{{ s.name }}</strong>
            <span class="pl-desc">{{ s.desc }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- ══════ 双栏：图谱结构 + 创新点 ══════ -->
    <div class="two-col">
      <!-- 知识图谱结构 -->
      <section class="panel">
        <div class="panel-head">
          <span class="panel-index">壹</span>
          <h3>知识图谱结构</h3>
        </div>
        <div class="kg">
          <div class="kg-layer" v-for="(layer, i) in kgLayers" :key="layer.name">
            <div class="kg-layer-head">
              <span class="kg-dot" :class="'kg-dot-' + i"></span>
              <span class="kg-name">{{ layer.icon }} {{ layer.name }}</span>
              <span class="kg-count">{{ layer.items.length }}</span>
            </div>
            <div class="kg-items">
              <span class="kg-tag" v-for="item in layer.items" :key="item">{{ item }}</span>
            </div>
          </div>
        </div>
        <button class="panel-link" @click="$router.push('/app/kg')">查看图谱可视化 →</button>
      </section>

      <!-- 创新点 -->
      <section class="panel">
        <div class="panel-head">
          <span class="panel-index">贰</span>
          <h3>论文创新点</h3>
        </div>
        <div class="innov-list">
          <div class="innov-item" v-for="inn in innovations" :key="inn.name">
            <div class="innov-mark" :class="{ done: inn.done }">{{ inn.done ? '✓' : '…' }}</div>
            <div class="innov-body">
              <div class="innov-name">{{ inn.name }}</div>
              <div class="innov-desc">{{ inn.description }}</div>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import api from '../api'

const numRefs = ref([])

const ledger = ref([
  { label: '法律法规', num: 8, suffix: ' 部', accent: '#3B82F6' },
  { label: '法律条文', num: 720, suffix: ' 条', accent: '#10B981' },
  { label: '劳动争议案例', num: 66, suffix: ' 个', accent: '#0369A1' },
  { label: 'KG 实体关系', num: 279, suffix: ' 条', accent: '#8B5CF6' }
])

const kgLayers = [
  { icon: '🏛️', name: '核心法律层', items: ['劳动法', '劳动合同法', '社会保险法', '工伤保险条例', '仲裁法', '工会法', '就业促进法', '安全生产法'] },
  { icon: '📜', name: '条文与概念层', items: ['720条文', '劳动关系', '劳动合同', '经济补偿金', '竞业限制', '工伤', '试用期'] },
  { icon: '⚡', name: '行为与责任层', items: ['违法解除', '拖欠工资', '强迫劳动', '就业歧视', '未签合同', '赔偿金', '双倍工资'] }
]

const retrievalSteps = [
  { name: '问题预处理', desc: '分词 · 实体识别 · 时间解析', active: true },
  { name: 'BM25 关键词', desc: '字符 Bigram · Okapi BM25', active: true },
  { name: '向量语义', desc: 'text2vec · FAISS 余弦', active: true },
  { name: '知识图谱', desc: 'Neo4j 关系遍历', active: true },
  { name: '融合 + 时效', desc: 'RRF 融合 · 状态过滤', active: true }
]

const innovations = [
  { name: '1. 知识图谱语义关联检索', description: '5类节点 + 4类扩展实体，279条关系，图扩展检索', done: true },
  { name: '2. 多策略融合检索', description: 'BM25 + 向量 + 图谱，RRF 加权融合', done: true },
  { name: '3. 时效感知检索', description: '双源日期提取，720条文状态标注，过期降权', done: true },
  { name: '4. 证据约束可追溯回答', description: 'Prompt 约束 LLM，引用校验，可信度评估', done: true }
]

function animateCount(el, target, suffix, duration = 900) {
  let start = null
  const step = (ts) => {
    if (!start) start = ts
    const p = Math.min((ts - start) / duration, 1)
    const eased = 1 - Math.pow(1 - p, 3)
    el.textContent = Math.round(target * eased) + suffix
    if (p < 1) requestAnimationFrame(step)
  }
  requestAnimationFrame(step)
}

onMounted(async () => {
  try {
    const res = await api.get('/chat/stats')
    if (res.code === 200 && res.neo4j) {
      ledger.value[0].num = res.neo4j.statutes || 8
      ledger.value[1].num = res.neo4j.articles || 720
      ledger.value[2].num = res.neo4j.cases || 66
      ledger.value[3].num = 279
    }
  } catch {}

  await nextTick()
  numRefs.value.forEach((el, i) => {
    if (el) animateCount(el, ledger.value[i].num, ledger.value[i].suffix)
  })
})
</script>

<style scoped>
.dashboard { max-width: 1000px; margin: 0 auto; padding-bottom: 40px; }

/* ══════ 页头 ══════ */
.page-head {
  display: flex; align-items: flex-start; justify-content: space-between;
  margin-bottom: 36px;
}
.page-title {
  margin: 0; color: var(--text-primary);
  font-size: 24px; font-weight: 700; letter-spacing: -0.3px;
}
.page-subtitle { margin: 4px 0 0; font-size: 13px; color: var(--text-muted); }
.live-badge {
  display: flex; align-items: center; gap: 8px;
  padding: 6px 14px; border-radius: 20px;
  background: #F0FDF4; border: 1px solid #BBF7D0;
  font-size: 12px; color: #065F46; font-weight: 500;
}
.live-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: #22C55E; animation: livePulse 2s ease infinite;
}
@keyframes livePulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(34,197,94,0.4); }
  50% { box-shadow: 0 0 0 6px rgba(34,197,94,0); }
}

/* ══════ 台账 ══════ */
.ledger {
  display: grid; grid-template-columns: repeat(4, 1fr);
  border-top: 1px solid #E2E8F0;
  border-bottom: 1px solid #E2E8F0;
  margin-bottom: 48px;
}
.ledger-cell {
  padding: 28px 20px 22px;
  border-left: 1px solid #E2E8F0;
  position: relative;
  transition: background 0.2s;
}
.ledger-cell:first-child { border-left: none; }
.ledger-cell:hover { background: #FAFBFD; }
.ledger-num {
  font-size: 42px; font-weight: 700; line-height: 1;
  color: #1E293B;
  font-family: 'Space Grotesk', 'Inter', sans-serif;
  font-variant-numeric: tabular-nums;
}
.ledger-label { font-size: 13px; color: var(--text-muted); margin-top: 12px; letter-spacing: 1px; }
.ledger-rule {
  position: absolute; top: 0; left: 24px; right: 24px;
  height: 2px; border-radius: 0 0 2px 2px;
  opacity: 0; transform: scaleX(0.6);
  transition: all 0.3s;
}
.ledger-cell:hover .ledger-rule { opacity: 1; transform: scaleX(1); }

/* ══════ 流水线 ══════ */
.pipeline-section { margin-bottom: 48px; }
.section-label {
  font-size: 11px; color: var(--text-muted);
  letter-spacing: 3px; text-transform: uppercase;
  font-weight: 600;
}
.section-title {
  margin: 6px 0 32px; font-size: 20px; font-weight: 700; color: var(--text-primary);
}

.pipeline {
  position: relative;
  display: grid; grid-template-columns: repeat(5, 1fr);
  padding-top: 40px;
}
.pl-base {
  position: absolute; top: 47px; left: 8%; right: 8%;
  height: 2px;
  background: #E2E8F0;
}
.pl-pulse {
  position: absolute; top: 44px;
  width: 8px; height: 8px; border-radius: 50%;
  background: #0369A1;
  opacity: 0; left: 8%;
  box-shadow: 0 0 8px rgba(3,105,161,0.6);
}
.pl-pulse.p1 { animation: flowAcross 4s cubic-bezier(0.4,0,0.2,1) infinite; }
.pl-pulse.p2 { animation: flowAcross 4s cubic-bezier(0.4,0,0.2,1) 2s infinite; }
@keyframes flowAcross {
  0% { left: 8%; opacity: 0; }
  8% { opacity: 1; }
  92% { opacity: 1; }
  100% { left: 92%; opacity: 0; }
}

.pl-step { display: flex; flex-direction: column; align-items: center; }
.pl-dot {
  width: 34px; height: 34px; border-radius: 50%;
  background: #FFF; border: 2px solid #CBD5E1;
  display: flex; align-items: center; justify-content: center;
  position: relative; z-index: 2;
  transition: all 0.3s;
}
.pl-dot-inner {
  font-size: 13px; font-weight: 700; color: #94A3B8;
  font-family: 'Space Grotesk', sans-serif;
}
.pl-dot.active {
  border-color: #0369A1; background: #0369A1;
  box-shadow: 0 0 0 4px rgba(3,105,161,0.12);
}
.pl-dot.active .pl-dot-inner { color: #FFF; }
.pl-step:hover .pl-dot { transform: scale(1.08); }

.pl-label {
  margin-top: 14px; text-align: center;
  display: flex; flex-direction: column; gap: 4px;
}
.pl-label strong { font-size: 13px; font-weight: 600; color: #334155; }
.pl-desc { font-size: 11px; color: #94A3B8; line-height: 1.5; }

/* ══════ 双栏 ══════ */
.two-col {
  display: grid; grid-template-columns: 3fr 2fr; gap: 24px;
  align-items: start;
}
.panel {
  background: #FFF;
  border: 1px solid #E2E8F0;
  border-radius: 14px;
  padding: 24px 26px;
}
.panel-head {
  display: flex; align-items: center; gap: 10px;
  margin-bottom: 20px;
  padding-bottom: 14px;
  border-bottom: 1px solid #F1F5F9;
}
.panel-index {
  font-size: 11px; font-weight: 700; color: #0369A1;
  font-family: 'Noto Serif SC', serif;
  padding: 2px 8px; border: 1px solid #BAE6FD; border-radius: 6px;
  background: #F0F9FF;
}
.panel-head h3 { margin: 0; font-size: 15px; font-weight: 700; color: #1E293B; }

/* 图谱 */
.kg-layer { margin-bottom: 16px; }
.kg-layer:last-child { margin-bottom: 0; }
.kg-layer-head {
  display: flex; align-items: center; gap: 8px; margin-bottom: 8px;
}
.kg-dot { width: 7px; height: 7px; border-radius: 50%; }
.kg-dot-0 { background: #3B82F6; }
.kg-dot-1 { background: #10B981; }
.kg-dot-2 { background: #0369A1; }
.kg-name { font-size: 13px; font-weight: 600; color: #475569; flex: 1; }
.kg-count { font-size: 11px; color: #94A3B8; font-family: 'Space Grotesk', sans-serif; }
.kg-items { display: flex; flex-wrap: wrap; gap: 6px; padding-left: 15px; }
.kg-tag {
  font-size: 12px; color: #64748B;
  padding: 3px 10px; border-radius: 20px;
  background: #F8FAFC; border: 1px solid #EEF2F7;
  transition: all 0.15s;
}
.kg-tag:hover { color: #0369A1; border-color: #BAE6FD; background: #F0F9FF; }
.panel-link {
  margin-top: 18px; padding: 0; border: none; background: none;
  font-size: 13px; color: #0369A1; font-weight: 500; cursor: pointer;
  font-family: inherit; transition: color 0.15s;
}
.panel-link:hover { color: #0284C7; }

/* 创新点 */
.innov-list { display: flex; flex-direction: column; }
.innov-item {
  display: flex; gap: 12px; padding: 12px 0;
  border-bottom: 1px solid #F1F5F9;
}
.innov-item:last-child { border-bottom: none; }
.innov-mark {
  width: 22px; height: 22px; border-radius: 50%;
  border: 2px solid #CBD5E1;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; color: #94A3B8; flex-shrink: 0; margin-top: 1px;
}
.innov-mark.done {
  border-color: #22C55E; background: #F0FDF4; color: #16A34A;
}
.innov-name { font-size: 13px; font-weight: 600; color: #334155; }
.innov-desc { font-size: 12px; color: #94A3B8; margin-top: 3px; line-height: 1.6; }

/* ══════ 响应式 ══════ */
@media (max-width: 900px) {
  .ledger { grid-template-columns: repeat(2, 1fr); }
  .ledger-cell:nth-child(3) { border-left: none; border-top: 1px solid #E2E8F0; }
  .ledger-cell:nth-child(4) { border-top: 1px solid #E2E8F0; }
  .two-col { grid-template-columns: 1fr; }
  .pipeline { grid-template-columns: 1fr; gap: 20px; padding-top: 0; }
  .pl-base, .pl-pulse { display: none; }
  .pl-step { flex-direction: row; justify-content: flex-start; gap: 12px; }
  .pl-dot { flex-shrink: 0; }
  .pl-label { margin-top: 0; text-align: left; }
}
</style>
