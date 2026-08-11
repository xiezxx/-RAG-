<template>
  <div class="statutes-page">
    <div class="page-head">
      <div>
        <h2 class="page-title">法律法规</h2>
        <p class="page-subtitle">劳动法体系全文 · {{ statutes.length }} 部 / 司法解释</p>
      </div>
    </div>

    <!-- 法规总览 — 一列式登记表 -->
    <div class="registry">
      <div class="registry-row" v-for="s in summary" :key="s.label">
        <div class="registry-num" :style="{ color: s.accent }">{{ s.num }}</div>
        <div class="registry-label">{{ s.label }}</div>
        <div class="registry-line"><span :style="{ background: s.accent }"></span></div>
      </div>
    </div>

    <!-- 法规清单 -->
    <div class="law-list" v-loading="loading">
      <div class="law-row" v-for="law in statutes" :key="law.id">
        <div class="law-marker" :class="'status-' + statusKey(law.status)"></div>
        <div class="law-main">
          <div class="law-name">{{ law.name }}</div>
          <div class="law-sub">{{ law.category }} · {{ law.articleCount || 0 }} 条条文</div>
        </div>
        <div class="law-articles">{{ law.articleCount }}</div>
        <div class="law-status">
          <span class="status-text" :class="'st-' + statusKey(law.status)">{{ law.statusText }}</span>
        </div>
      </div>
      <div v-if="!statutes.length && !loading" class="law-empty">暂无法规数据</div>
    </div>

    <!-- 版本演进时间线 -->
    <div class="evolve-section">
      <div class="evolve-head">
        <span class="evolve-label">版本演进</span>
        <h3>法律修订时间线</h3>
      </div>
      <div class="evolve-list">
        <div class="evolve-item" v-for="item in timeline" :key="item.name" :class="'ev-'+item.type">
          <div class="ev-year">{{ yearOf(item.date) }}</div>
          <div class="ev-line"><span></span></div>
          <div class="ev-card">
            <div class="ev-name">{{ item.name }}</div>
            <div class="ev-desc">{{ item.desc }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '../api'

const loading = ref(false), statutes = ref([])

const summary = computed(() => {
  const laws = statutes.value.filter(s => s.category === '法律').length
  const interp = statutes.value.filter(s => s.category !== '法律').length
  const arts = statutes.value.reduce((s, i) => s + (i.articleCount || 0), 0)
  const valid = statutes.value.filter(s => s.status === '现行有效').length
  return [
    { num: laws, label: '部法律', accent: '#3B82F6' },
    { num: interp, label: '部司法解释', accent: '#10B981' },
    { num: arts, label: '条条文', accent: '#0369A1' },
    { num: valid + '/' + statutes.value.length, label: '现行有效', accent: '#22C55E' }
  ]
})

const timeline = computed(() => {
  return [...statutes.value]
    .sort((a, b) => (a.effectiveDate || '').localeCompare(b.effectiveDate || ''))
    .map(s => ({
      name: s.name,
      date: (s.effectiveDate || '?'),
      desc: `发布 ${s.publishDate || '?'} · ${s.articleCount || 0} 条 → ${s.status || '现行有效'}`,
      type: s.status === '现行有效' ? 'success' : s.status === '已被修订' ? 'warning' : 'info'
    }))
})

function statusKey(s) {
  return s === '现行有效' ? 'current' : s === '已被修订' ? 'revised' : s === '已废止' ? 'expired' : 'pending'
}
function yearOf(date) {
  return (date || '').substring(0, 4) || '—'
}

onMounted(async () => {
  loading.value = true
  try {
    const res = await api.get('/statutes')
    if (res.code === 200) {
      statutes.value = (res.data || []).map(s => ({
        ...s,
        statusText: s.status || '现行有效'
      }))
    }
  } catch {}
  loading.value = false
})
</script>

<style scoped>
.statutes-page { max-width: 1000px; margin: 0 auto; padding-bottom: 40px; }
.page-head { margin-bottom: 32px; }
.page-title { margin: 0; font-size: 24px; font-weight: 700; color: var(--text-primary); }
.page-subtitle { margin: 4px 0 0; font-size: 13px; color: var(--text-muted); }

/* ── 登记表 ── */
.registry {
  display: grid; grid-template-columns: repeat(4, 1fr);
  border-top: 1px solid #E2E8F0;
  border-bottom: 1px solid #E2E8F0;
  margin-bottom: 40px;
}
.registry-row {
  padding: 24px 20px;
  border-left: 1px solid #E2E8F0;
  display: flex; flex-direction: column; gap: 6px;
}
.registry-row:first-child { border-left: none; }
.registry-num { font-size: 36px; font-weight: 700; font-family: 'Space Grotesk', sans-serif; }
.registry-label { font-size: 13px; color: var(--text-muted); letter-spacing: 1px; }
.registry-line span { display: block; width: 24px; height: 2px; border-radius: 2px; }

/* ── 法规清单 ── */
.law-list { margin-bottom: 48px; }
.law-row {
  display: flex; align-items: center; gap: 16px;
  padding: 16px 4px;
  border-bottom: 1px solid #F1F5F9;
  transition: background 0.15s, padding-left 0.15s;
}
.law-row:hover { background: #FAFBFD; padding-left: 12px; }
.law-marker { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.status-current { background: #22C55E; box-shadow: 0 0 0 3px rgba(34,197,94,0.15); }
.status-revised { background: #F59E0B; box-shadow: 0 0 0 3px rgba(245,158,11,0.15); }
.status-expired { background: #EF4444; box-shadow: 0 0 0 3px rgba(239,68,68,0.15); }
.status-pending { background: #3B82F6; box-shadow: 0 0 0 3px rgba(59,130,246,0.15); }
.law-main { flex: 1; min-width: 0; }
.law-name { font-size: 14.5px; font-weight: 600; color: #334155; }
.law-sub { font-size: 12px; color: #94A3B8; margin-top: 3px; }
.law-articles {
  flex-shrink: 0; width: 48px; text-align: center;
  font-size: 20px; font-weight: 700; color: #CBD5E1;
  font-family: 'Space Grotesk', sans-serif;
}
.law-status { flex-shrink: 0; min-width: 76px; text-align: right; }
.status-text { font-size: 12px; font-weight: 500; padding: 3px 10px; border-radius: 20px; }
.st-current { color: #16A34A; background: #F0FDF4; }
.st-revised { color: #D97706; background: #FFFBEB; }
.st-expired { color: #DC2626; background: #FEF2F2; }
.st-pending { color: #2563EB; background: #EFF6FF; }

/* ── 时间线 ── */
.evolve-section { margin-top: 8px; }
.evolve-label {
  font-size: 11px; color: var(--text-muted);
  letter-spacing: 3px; text-transform: uppercase; font-weight: 600;
}
.evolve-head h3 { margin: 6px 0 28px; font-size: 20px; font-weight: 700; color: var(--text-primary); }
.evolve-list { position: relative; padding-left: 20px; }
.evolve-list::before {
  content: ''; position: absolute; left: 7px; top: 0; bottom: 0;
  width: 2px; background: #E2E8F0; border-radius: 1px;
}
.evolve-item { position: relative; padding-left: 28px; margin-bottom: 16px; display: flex; gap: 20px; align-items: center; }
.evolve-item::before {
  content: ''; position: absolute; left: -5px; top: 6px;
  width: 12px; height: 12px; border-radius: 50%;
  background: #CBD5E1; border: 2px solid #FFF; box-shadow: 0 0 0 2px #E2E8F0;
}
.ev-success::before { background: #22C55E; box-shadow: 0 0 0 3px rgba(34,197,94,0.15); }
.ev-warning::before { background: #F59E0B; box-shadow: 0 0 0 3px rgba(245,158,11,0.15); }
.ev-info::before { background: #3B82F6; box-shadow: 0 0 0 3px rgba(59,130,246,0.15); }
.ev-year { flex-shrink: 0; width: 48px; font-size: 20px; font-weight: 700; color: #CBD5E1; font-family: 'Space Grotesk', sans-serif; }
.ev-line { flex-shrink: 0; width: 2px; height: 100%; background: #F1F5F9; }
.ev-card { flex: 1; padding: 14px 18px; background: #F8FAFC; border: 1px solid #F1F5F9; border-radius: 10px; transition: all 0.2s; }
.ev-card:hover { background: #FFF; box-shadow: 0 4px 16px rgba(0,0,0,0.04); }
.ev-name { font-size: 14px; font-weight: 600; color: #334155; }
.ev-desc { font-size: 12px; color: #94A3B8; margin-top: 4px; }

@media (max-width: 768px) {
  .registry { grid-template-columns: repeat(2, 1fr); }
  .registry-row:nth-child(3) { border-left: none; }
  .law-row { flex-wrap: wrap; }
  .law-status { text-align: left; }
}
</style>
