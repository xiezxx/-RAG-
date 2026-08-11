<template>
  <div class="cases-page">
    <div class="page-head">
      <div>
        <h2 class="page-title">案例库</h2>
        <p class="page-subtitle">劳动争议裁判文书 · 共 {{ cases.length }} 件</p>
      </div>
    </div>

    <!-- 案卷检索栏 -->
    <div class="search-drawer">
      <el-select v-model="category" placeholder="按争议类型筛选" clearable @change="loadCases" class="filter-select">
        <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
      </el-select>
      <el-input v-model="keyword" placeholder="搜索案号 / 法院 / 关键词" @keyup.enter="loadCases" clearable class="filter-input">
        <template #append>
          <el-button @click="loadCases">检索</el-button>
        </template>
      </el-input>
    </div>

    <!-- 案卷列表 -->
    <div class="docket-list" v-loading="loading">
      <div class="docket-item" v-for="row in cases" :key="row.id" @click="goDetail(row)">
        <div class="docket-no">{{ formatCaseNo(row.caseNumber) }}</div>
        <div class="docket-body">
          <div class="docket-court">{{ row.court }}</div>
          <div class="docket-content">{{ snippet(row.caseContent) }}</div>
        </div>
        <div class="docket-meta">
          <span class="docket-date">{{ row.judgeDate }}</span>
          <span class="cat-chip" :class="'cat-' + catIndex(row.category)">{{ row.category }}</span>
        </div>
        <div class="docket-arrow">→</div>
      </div>
      <div v-if="!cases.length && !loading" class="docket-empty">
        没有检索到匹配的案例，试试调整筛选条件
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'

const router = useRouter()
const cases = ref([]), category = ref(''), keyword = ref('')
const loading = ref(false)
const categories = ['劳动合同解除','劳动报酬','工伤赔偿','社会保险','竞业限制','确认劳动关系','女职工权益','其他']

const CAT_COLORS = ['#0369A1','#0D9488','#D97706','#7C3AED','#DB2777','#16A34A','#DC2626','#64748B']

function catIndex(cat) {
  const i = categories.indexOf(cat)
  return i >= 0 ? i : 7
}
function formatCaseNo(no) {
  return no || '—'
}
function snippet(text) {
  if (!text) return ''
  return text.replace(/\s+/g, ' ').substring(0, 90) + (text.length > 90 ? '…' : '')
}

async function loadCases() {
  loading.value = true
  const params = {}
  if (category.value) params.category = category.value
  if (keyword.value) params.keyword = keyword.value
  try {
    const res = await api.get('/cases', { params })
    if (res.code === 200) cases.value = res.data
  } catch {}
  loading.value = false
}
function goDetail(row) { router.push(`/app/cases/${row.id}`) }
onMounted(loadCases)
</script>

<style scoped>
.cases-page { max-width: 1100px; margin: 0 auto; padding-bottom: 40px; }

.page-head { margin-bottom: 28px; }
.page-title { margin: 0; font-size: 24px; font-weight: 700; color: var(--text-primary); }
.page-subtitle { margin: 4px 0 0; font-size: 13px; color: var(--text-muted); }

/* ── 检索栏 ── */
.search-drawer {
  display: flex; gap: 12px; margin-bottom: 24px;
  padding: 14px 18px;
  background: #FFF;
  border: 1px solid #E2E8F0;
  border-radius: 12px;
}
.filter-select { width: 200px; }
.filter-input { flex: 1; max-width: 420px; }

/* ── 案卷列表 ── */
.docket-list {
  display: flex; flex-direction: column;
  border-top: 1px solid #E2E8F0;
}
.docket-item {
  display: flex; align-items: center; gap: 20px;
  padding: 18px 8px;
  border-bottom: 1px solid #F1F5F9;
  cursor: pointer;
  position: relative;
  transition: background 0.18s, padding-left 0.18s;
}
.docket-item:hover { background: #F8FAFC; padding-left: 16px; }
.docket-item:hover .docket-arrow { opacity: 1; transform: translateX(0); }

.docket-no {
  flex-shrink: 0; min-width: 170px;
  font-family: 'Space Grotesk', 'Inter', monospace;
  font-size: 13px; font-weight: 600; color: #0369A1;
}
.docket-body { flex: 1; min-width: 0; }
.docket-court { font-size: 14px; font-weight: 600; color: #334155; margin-bottom: 4px; }
.docket-content { font-size: 13px; color: #94A3B8; line-height: 1.6; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.docket-meta {
  display: flex; flex-direction: column; align-items: flex-end; gap: 6px;
  flex-shrink: 0;
}
.docket-date { font-size: 12px; color: #94A3B8; font-family: 'Space Grotesk', sans-serif; }
.cat-chip {
  font-size: 11px; padding: 3px 10px;
  border-radius: 20px; font-weight: 500;
  color: #FFF;
}
.cat-0 { background: #0369A1; } .cat-1 { background: #0D9488; }
.cat-2 { background: #D97706; } .cat-3 { background: #7C3AED; }
.cat-4 { background: #DB2777; } .cat-5 { background: #16A34A; }
.cat-6 { background: #DC2626; } .cat-7 { background: #64748B; }

.docket-arrow {
  flex-shrink: 0; font-size: 16px; color: #0369A1;
  opacity: 0; transform: translateX(-6px);
  transition: all 0.18s;
}
.docket-empty { padding: 60px 20px; text-align: center; color: var(--text-muted); font-size: 14px; }

@media (max-width: 768px) {
  .docket-item { flex-wrap: wrap; gap: 8px; }
  .docket-no { min-width: 100%; }
  .docket-meta { flex-direction: row; }
}
</style>
