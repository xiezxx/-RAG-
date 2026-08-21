<template>
  <div class="history-view">
    <div class="page-head">
      <div>
        <h2 class="page-title">{{ canViewEval ? '系统评估' : '问答记录' }}</h2>
        <p class="page-subtitle">{{ canViewEval ? '问答数据、用户反馈与消融实验' : '你与其他普通用户的问答记录与评价' }}</p>
      </div>
    </div>

    <!-- ── 台账式统计 ── -->
    <div class="metric-ledger">
      <div class="metric-cell" v-for="c in evalCards" :key="c.label">
        <div class="metric-num" :style="{ color: c.color }">{{ c.value }}</div>
        <div class="metric-label">{{ c.label }}</div>
        <div class="metric-sub" v-if="c.desc">{{ c.desc }}</div>
      </div>
    </div>

    <div class="two-col" :class="{ 'wide-record': !canViewEval }">
      <!-- ── 左栏 ── -->
      <div class="side-stack">
        <!-- 满意度分布 -->
        <section class="panel">
          <div class="panel-head"><span class="panel-index">壹</span><h3>满意度分布</h3></div>
          <div v-if="ratings.length" class="rating-dist">
            <div v-for="r in ratings" :key="r.rating" class="rating-row">
              <span class="rating-stars">{{ '★'.repeat(r.rating) }}</span>
              <div class="rating-track">
                <div class="rating-fill" :style="{ width: r.pct + '%', background: r.color }"></div>
              </div>
              <span class="rating-count">{{ r.count }}</span>
              <span class="rating-pct">{{ r.pct }}%</span>
            </div>
          </div>
          <div v-else class="empty-state">暂无评分数据</div>
        </section>

        <!-- 消融实验面板（管理员/研究人员） -->
        <section class="panel" v-if="canViewEval">
          <div class="panel-head"><span class="panel-index">贰</span><h3>消融实验 <span class="panel-sub">50 题 × 5 组检索配置</span></h3>
            <button class="refresh-btn" @click="loadAblation">刷新</button>
          </div>
          <div v-if="ablation.configs?.length" class="abl-wrap">
            <div class="abl-table">
              <div class="abl-row head">
                <span>配置</span><span>R@1</span><span>R@3</span><span>R@5</span><span>P@5</span><span>MRR</span><span>过期率</span><span>延迟</span>
              </div>
              <div v-for="c in ablation.configs" :key="c.name" class="abl-row" :class="{best:c.name==='full'}">
                <span class="abl-name">{{ configLabel(c.name) }}</span>
                <span>{{ pct(c.recall_at_1) }}</span>
                <span>{{ pct(c.recall_at_3) }}</span>
                <span class="abl-r5">{{ pct(c.recall_at_5) }}</span>
                <span>{{ pct(c.precision_at_5) }}</span>
                <span>{{ c.mrr?.toFixed(4) }}</span>
                <span>{{ pct(c.expired_rate) }}</span>
                <span>{{ Math.round(c.avg_latency_ms) }}ms</span>
              </div>
            </div>
            <div ref="ablChart" class="abl-chart"></div>
            <div class="abl-drill">
              <div class="drill-head">
                <span class="drill-title">逐题明细（R@5 / 单题检索耗时）</span>
                <el-select v-model="drillConfig" size="small" style="width:170px">
                  <el-option v-for="c in ablation.configs" :key="c.name" :value="c.name" :label="configLabel(c.name)" />
                </el-select>
              </div>
              <div class="drill-table" v-if="drillRows.length">
                <div v-for="r in drillRows" :key="r.id" class="drill-row">
                  <span class="drill-id">{{ r.id }}</span>
                  <span class="drill-q" :title="r.question">{{ r.question }}</span>
                  <span class="drill-m" :class="{zero:!r.recall_5}">{{ pct(r.recall_5) }}</span>
                  <span class="drill-m lat">{{ Math.round(r.latency_ms) }}ms</span>
                </div>
              </div>
            </div>
            <p class="table-note">* 数据由 src/eval/ablation.py 离线跑出（ablation_results.json）{{ ablConclusion }}</p>
          </div>
          <div v-else class="empty-state">消融数据暂不可用（请先运行 src/eval/ablation.py 生成结果）</div>
        </section>

        <!-- 测试集管理（管理员/研究人员） -->
        <section class="panel" v-if="canViewEval">
          <div class="panel-head"><span class="panel-index">肆</span><h3>测试集管理 <span class="panel-sub">{{ testQuestions.length }} 题</span></h3>
            <button class="refresh-btn" @click="loadTestset">刷新</button>
          </div>
          <div class="ts-add">
            <el-input v-model="tsQuestion" size="small" placeholder="新测试题（如：加班工资基数怎么算？）" />
            <el-input v-model="tsCategory" size="small" placeholder="分类（选填）" style="width: 140px" />
            <el-button type="primary" size="small" round :loading="tsAdding" @click="addTestQuestion">添加</el-button>
          </div>
          <div class="ts-list">
            <div class="ts-row" v-for="q in testQuestions" :key="q.id">
              <span class="ts-id">{{ q.id }}</span>
              <span class="ts-q" :title="q.question">{{ q.question }}</span>
              <el-button size="small" type="danger" text circle @click="removeTestQuestion(q)" title="删除">
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
            <div v-if="!testQuestions.length" class="empty-state">暂无测试题</div>
          </div>
        </section>
      </div>

      <!-- ── 右栏：记录 ── -->
      <section class="panel record-panel">
        <div class="panel-head">
          <span class="panel-index">叁</span><h3>问答记录</h3>
          <span class="count-badge">{{ history.length }} 条</span>
          <button class="refresh-btn" @click="loadHistory">刷新</button>
        </div>
        <div class="record-list" v-loading="loading">
          <div class="record-card" v-for="row in history" :key="row.id" :class="{ mine: row.mine }">
            <div class="rc-head">
              <span class="rc-user" :class="{ me: row.mine }">{{ row.mine ? '我' : (row.username || '用户') }}</span>
              <span class="rc-q">{{ row.question }}</span>
            </div>
            <p class="rc-answer">{{ answerPreview(row.answer) }}</p>
            <div class="rc-meta">
              <span class="rc-time">{{ formatTime(row.createdAt) }}</span>
              <template v-if="row.rating > 0">
                <span class="rc-stars"><span v-for="i in 5" :key="i" class="star" :class="{ filled: i <= row.rating }">★</span></span>
              </template>
              <span v-else class="unrated">未评</span>
              <span v-if="row.feedback" class="rc-feedback" :title="row.feedback">💬 {{ row.feedback }}</span>
              <span class="rc-actions">
                <button class="mini-btn" @click="showDetail(row)">详情</button>
                <button v-if="row.mine" class="mini-btn accent" @click="openRate(row)">评价</button>
              </span>
            </div>
          </div>
          <div v-if="!history.length && !loading" class="empty-state">暂无问答记录</div>
        </div>
      </section>
    </div>

    <!-- 评价弹窗 -->
    <el-dialog v-model="rateVisible" title="评价回答" width="480px">
      <div class="rate-content">
        <div class="rate-question">{{ ratingTarget.question?.substring(0, 80) }}{{ ratingTarget.question?.length > 80 ? '…' : '' }}</div>
        <div class="rate-stars-row">
          <span class="rate-label">满意度：</span>
          <el-rate v-model="ratingValue" :max="5" size="large" :colors="['#CBD5E1','#F59E0B','#F59E0B']" :texts="['非常差','较差','一般','满意','非常满意']" show-text />
        </div>
        <div class="rate-comment">
          <span class="rate-label">文字反馈（选填）：</span>
          <el-input v-model="ratingComment" type="textarea" :rows="3" placeholder="如：法条引用有误、回答不完整、内容已过期..." maxlength="500" show-word-limit />
        </div>
      </div>
      <template #footer>
        <el-button @click="rateVisible = false">取消</el-button>
        <el-button type="primary" @click="submitRate" :disabled="!ratingValue">提交评价</el-button>
      </template>
    </el-dialog>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="问答详情" width="720px">
      <div class="detail-content">
        <h4>问题</h4>
        <p class="detail-question">{{ current.question }}</p>
        <h4>回答</h4>
        <div v-html="renderMd(current.answer || '')" class="detail-answer" />
        <div class="detail-meta-row">
          <span v-if="current.username && !current.mine">提问者 {{ current.username }}</span>
          <span>时间 {{ formatTime(current.createdAt) }}</span>
          <span>评分 {{ current.rating > 0 ? current.rating + '分' : '未评' }}</span>
        </div>
        <div v-if="current.feedback" class="detail-feedback"><strong>用户反馈：</strong>{{ current.feedback }}</div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { marked } from 'marked'
import * as echarts from 'echarts'
import api from '../api'

const role = localStorage.getItem('role') || 'USER'
const isAdmin = computed(() => role === 'ADMIN')
const canViewEval = computed(() => role === 'ADMIN' || role === 'RESEARCHER')

const history = ref([])
const loading = ref(false)
const detailVisible = ref(false)
const current = ref({})
const ratings = ref([])
const evalCards = ref([
  { label: '总问答', value: 0, color: '#3b82f6', desc: '' },
  { label: '平均评分', value: '—', color: '#22c55e', desc: '' },
  { label: '满意率', value: '—', color: '#d97706', desc: '≥4★' },
  { label: '有反馈', value: 0, color: '#8b5cf6', desc: '含文字评价' }
])

const rateVisible = ref(false)
const ratingTarget = ref({})
const ratingValue = ref(0)
const ratingComment = ref('')

function openRate(row) {
  ratingTarget.value = row
  ratingValue.value = row.rating || 0
  ratingComment.value = row.feedback || ''
  rateVisible.value = true
}

async function submitRate() {
  try {
    await api.post('/eval/feedback', { chatId: ratingTarget.value.id, rating: ratingValue.value, comment: ratingComment.value })
    ratingTarget.value.rating = ratingValue.value
    ratingTarget.value.feedback = ratingComment.value
    ElMessage.success('评价已提交')
    rateVisible.value = false
    loadHistory()
  } catch { ElMessage.error('提交失败') }
}

// ── 消融实验面板 ──
const ablation = ref({ configs: [], per_question: {}, questions: [] })
const drillConfig = ref('full')
const ablChart = ref(null)
let ablChartInstance = null

const configLabelMap = {
  bm25: 'BM25 基线',
  'bm25+vector': '+ 向量检索',
  'bm25+vector+kg': '+ 知识图谱',
  'bm25+vector+kg+time': '+ 时效感知',
  full: '完整混合(+扩展)'
}
function configLabel(name) { return configLabelMap[name] || name }
function pct(v) { return v == null ? '—' : (v * 100).toFixed(0) + '%' }

const drillRows = computed(() => {
  const rows = ablation.value.per_question?.[drillConfig.value] || []
  const qMap = {}
  for (const q of ablation.value.questions || []) qMap[q.id] = q.question
  return rows.map(r => ({
    id: r.question_id,
    question: (qMap[r.question_id] || '').substring(0, 42) + ((qMap[r.question_id] || '').length > 42 ? '…' : ''),
    recall_5: r.recall_5,
    latency_ms: r.latency_ms
  }))
})

const ablConclusion = computed(() => {
  const cfg = ablation.value.configs || []
  const base = cfg.find(c => c.name === 'bm25')
  const full = cfg.find(c => c.name === 'full')
  if (!base || !full) return ''
  const r5 = ((full.recall_at_5 - base.recall_at_5) * 100).toFixed(1)
  const mrr = (full.mrr - base.mrr).toFixed(3)
  return `，对比结论：完整混合相对 BM25 基线 R@5 提升 ${r5}pp、MRR 提升 ${mrr}`
})

async function loadAblation() {
  try {
    const res = await api.get('/eval/ablation')
    if (res.code === 200 && res.data?.configs?.length) {
      ablation.value = res.data
      await nextTick()
      renderAblChart()
    } else {
      ablation.value = {}
      if (res.code !== 200) ElMessage.error(res.message || '消融数据加载失败')
    }
  } catch (e) { console.warn('消融数据加载失败', e) }
}

function renderAblChart() {
  if (!ablChart.value) return
  if (ablChartInstance) ablChartInstance.dispose()
  ablChartInstance = echarts.init(ablChart.value)
  const cfg = ablation.value.configs
  ablChartInstance.setOption({
    grid: { left: 44, right: 12, top: 30, bottom: 28 },
    tooltip: { trigger: 'axis' },
    legend: { top: 0, itemWidth: 10, itemHeight: 8, textStyle: { fontSize: 10 } },
    xAxis: {
      type: 'category',
      data: cfg.map(c => configLabel(c.name)),
      axisLabel: { fontSize: 9, interval: 0, rotate: 12 }
    },
    yAxis: { type: 'value', max: 100, axisLabel: { fontSize: 10, formatter: '{value}%' } },
    series: ['recall_at_1', 'recall_at_3', 'recall_at_5'].map((key, i) => ({
      name: ['Recall@1', 'Recall@3', 'Recall@5'][i],
      type: 'bar',
      barMaxWidth: 16,
      data: cfg.map(c => Math.round(c[key] * 1000) / 10),
      itemStyle: { borderRadius: [3, 3, 0, 0], color: ['#93C5FD', '#60A5FA', '#0369A1'][i] }
    }))
  })
}

let pollTimer = null
marked.setOptions({ breaks: true, gfm: true })
function renderMd(text) { return marked.parse((text || '').replace(/<[^>]*>/g, '')) }
function formatTime(t) { if (!t) return ''; const s = typeof t === 'string' ? t : String(t); return s.substring(0, 16).replace('T', ' ') }
function answerPreview(a) {
  const t = (a || '').replace(/[#>*`\-_|]/g, '').replace(/\s+/g, ' ').trim()
  if (!t) return '—'
  return t.length > 90 ? t.substring(0, 90) + '…' : t
}

async function loadHistory() {
  loading.value = true
  try {
    // 可见性由后端按角色控制：管理员=全员，普通用户=自己+其他普通用户
    const res = await api.get('/eval/history', { params: { limit: 100 } })
    if (res.code === 200) {
      history.value = res.data || []
      evalCards.value[0].value = history.value.length
      let totalRating = 0, ratedCount = 0, goodCount = 0, feedbackCount = 0
      const dist = {}
      for (const h of history.value) {
        if (h.rating > 0) { totalRating += h.rating; ratedCount++; if (h.rating >= 4) goodCount++; dist[h.rating] = (dist[h.rating] || 0) + 1 }
        if (h.feedback) feedbackCount++
      }
      if (ratedCount > 0) {
        evalCards.value[1].value = (totalRating / ratedCount).toFixed(1)
        evalCards.value[2].value = Math.round(goodCount / ratedCount * 100) + '%'
      }
      evalCards.value[3].value = feedbackCount
      ratings.value = [5,4,3,2,1].map(r => ({ rating: r, count: dist[r] || 0, pct: ratedCount > 0 ? Math.round((dist[r] || 0) / ratedCount * 100) : 0, color: r >= 4 ? '#22c55e' : r === 3 ? '#d97706' : '#ef4444' }))
    }
  } catch (error) { console.warn('加载历史记录失败', error) }
  loading.value = false
}

function showDetail(row) { current.value = row; detailVisible.value = true }

// ── 测试集管理 ──
const testQuestions = ref([])
const tsQuestion = ref('')
const tsCategory = ref('')
const tsAdding = ref(false)

async function loadTestset() {
  try {
    const res = await api.get('/eval/testset')
    if (res.code === 200) testQuestions.value = res.data || []
  } catch (e) { console.warn('测试集加载失败', e) }
}

async function addTestQuestion() {
  if (!tsQuestion.value.trim()) { ElMessage.warning('请填写测试题'); return }
  tsAdding.value = true
  try {
    const res = await api.post('/eval/testset', {
      question: tsQuestion.value.trim(),
      category: tsCategory.value.trim()
    })
    if (res.code === 200) {
      ElMessage.success('已添加')
      tsQuestion.value = ''
      tsCategory.value = ''
      loadTestset()
    } else {
      ElMessage.error(res.message || '添加失败')
    }
  } catch (e) { ElMessage.error('添加失败：' + (e?.message || '网络错误')) }
  tsAdding.value = false
}

async function removeTestQuestion(q) {
  await ElMessageBox.confirm(`确定删除测试题「${(q.question || '').substring(0, 30)}…」？`, '确认', { type: 'warning' })
  try {
    const res = await api.delete(`/eval/testset/${q.id}`)
    if (res.code === 200) {
      ElMessage.success('已删除')
      loadTestset()
    } else {
      ElMessage.error(res.message || '删除失败')
    }
  } catch (e) { ElMessage.error('删除失败：' + (e?.message || '网络错误')) }
}

onMounted(() => { loadHistory(); if (canViewEval.value) { loadAblation(); loadTestset() } pollTimer = setInterval(loadHistory, 10000) })
onUnmounted(() => { if (pollTimer) clearInterval(pollTimer); if (ablChartInstance) ablChartInstance.dispose() })
</script>

<style scoped>
.history-view { max-width: 1200px; margin: 0 auto; padding-bottom: 40px; }
.page-head { margin-bottom: 28px; }
.page-title { margin: 0; font-size: 24px; font-weight: 700; color: var(--text-primary); }
.page-subtitle { margin: 4px 0 0; font-size: 13px; color: var(--text-muted); }

/* ── 台账式统计 ── */
.metric-ledger {
  display: grid; grid-template-columns: repeat(4, 1fr);
  border-top: 1px solid #E2E8F0; border-bottom: 1px solid #E2E8F0;
  margin-bottom: 32px;
}
.metric-cell { padding: 26px 20px; border-left: 1px solid #E2E8F0; }
.metric-cell:first-child { border-left: none; }
.metric-num { font-size: 36px; font-weight: 700; font-family: 'Space Grotesk', sans-serif; }
.metric-label { font-size: 13px; color: var(--text-muted); margin-top: 8px; }
.metric-sub { font-size: 11px; color: var(--text-muted); margin-top: 2px; }

.two-col { display: grid; grid-template-columns: 3fr 2fr; gap: 24px; align-items: start; }
.two-col.wide-record { grid-template-columns: 1fr 2fr; }
.side-stack { display: flex; flex-direction: column; gap: 24px; }

.panel { background: #FFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 22px 24px; }
.panel-head { display: flex; align-items: center; gap: 10px; margin-bottom: 18px; padding-bottom: 12px; border-bottom: 1px solid #F1F5F9; }
.panel-index { font-size: 11px; font-weight: 700; color: #0369A1; padding: 2px 8px; border: 1px solid #BAE6FD; border-radius: 6px; background: #F0F9FF; font-family: 'Noto Serif SC', serif; }
.panel-head h3 { margin: 0; font-size: 15px; font-weight: 700; color: #1E293B; flex: 1; }

/* 满意度 */
.rating-dist { display: flex; flex-direction: column; gap: 12px; }
.rating-row { display: flex; align-items: center; gap: 12px; }
.rating-stars { font-size: 12px; width: 52px; color: #F59E0B; letter-spacing: 1px; }
.rating-track { flex: 1; height: 16px; background: #F1F5F9; border-radius: 8px; overflow: hidden; }
.rating-fill { height: 100%; border-radius: 8px; transition: width 0.6s ease; }
.rating-count { width: 22px; text-align: right; font-weight: 600; color: #475569; }
.rating-pct { width: 44px; text-align: right; font-size: 12px; color: #94A3B8; }

/* 消融实验面板 */
.panel-sub { font-size: 11px; color: #94A3B8; font-weight: 400; margin-left: 6px; }
.abl-wrap { display: flex; flex-direction: column; gap: 14px; }
.abl-table { width: 100%; }
.abl-row { display: grid; grid-template-columns: 1.4fr repeat(7, 1fr); gap: 4px; align-items: center; padding: 8px 6px; border-bottom: 1px solid #F1F5F9; font-size: 12px; text-align: center; color: #475569; font-family: 'Space Grotesk', sans-serif; }
.abl-row.head { color: #94A3B8; font-size: 10px; border-bottom: 1px solid #E2E8F0; font-family: inherit; }
.abl-row.best { background: #F0F9FF; border-radius: 8px; font-weight: 600; }
.abl-name { text-align: left; font-family: inherit; font-size: 12px; color: #334155; }
.abl-r5 { color: #0369A1; font-weight: 700; }
.abl-chart { width: 100%; height: 210px; }
.abl-drill { border-top: 1px solid #F1F5F9; padding-top: 12px; }
.drill-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.drill-title { font-size: 12px; color: #64748B; font-weight: 600; }
.drill-table { max-height: 230px; overflow-y: auto; border: 1px solid #F1F5F9; border-radius: 8px; }
.drill-row { display: flex; align-items: center; gap: 8px; padding: 6px 10px; font-size: 11.5px; border-bottom: 1px dashed #F1F5F9; }
.drill-row:last-child { border-bottom: none; }
.drill-id { flex-shrink: 0; color: #94A3B8; font-family: 'Space Grotesk', sans-serif; }
.drill-q { flex: 1; color: #475569; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.drill-m { flex-shrink: 0; width: 44px; text-align: right; color: #0369A1; font-family: 'Space Grotesk', sans-serif; font-weight: 600; }
.drill-m.zero { color: #CBD5E1; font-weight: 400; }
.drill-m.lat { width: 56px; color: #94A3B8; font-weight: 400; }
.table-note { font-size: 11px; color: var(--text-muted); margin-top: 12px; }

/* 记录 */
.record-panel { grid-column: auto; }
.refresh-btn { border: none; background: none; color: #0369A1; font-size: 13px; cursor: pointer; font-family: inherit; }
.count-badge { font-size: 11px; color: #64748B; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 999px; padding: 2px 10px; }
.record-list { max-height: 720px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
.record-card { border: 1px solid #F1F5F9; border-radius: 10px; padding: 12px 16px; background: #FFF; transition: border-color 0.15s, box-shadow 0.15s; }
.record-card:hover { border-color: #BAE6FD; box-shadow: 0 2px 8px rgba(3, 105, 161, 0.06); }
.record-card.mine { background: #FBFDFF; }
.rc-head { display: flex; align-items: center; gap: 8px; }
.rc-user { flex-shrink: 0; font-size: 11px; color: #0369A1; background: #F0F9FF; border: 1px solid #BAE6FD; padding: 1px 7px; border-radius: 999px; }
.rc-user.me { color: #047857; background: #ECFDF5; border-color: #A7F3D0; }
.rc-q { flex: 1; min-width: 0; font-size: 13.5px; font-weight: 600; color: #1E293B; line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.rc-answer { margin: 6px 0 0; font-size: 12.5px; color: #64748B; line-height: 1.6; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.rc-meta { display: flex; align-items: center; gap: 14px; margin-top: 10px; padding-top: 10px; border-top: 1px dashed #F1F5F9; }
.rc-time { flex-shrink: 0; font-size: 11px; color: #94A3B8; font-family: 'Space Grotesk', sans-serif; }
.rc-stars { flex-shrink: 0; }
.star { color: #CBD5E1; font-size: 12px; }
.star.filled { color: #F59E0B; }
.unrated { flex-shrink: 0; color: #CBD5E1; font-size: 11px; }
.rc-feedback { flex: 1; min-width: 0; font-size: 11.5px; color: #94A3B8; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.rc-actions { flex-shrink: 0; display: flex; gap: 6px; margin-left: auto; }
.mini-btn { padding: 4px 12px; border: 1px solid #E2E8F0; border-radius: 6px; background: #FFF; font-size: 12px; color: #64748B; cursor: pointer; font-family: inherit; transition: all 0.15s; }
.mini-btn:hover { border-color: #94A3B8; color: #334155; }
.mini-btn.accent { border-color: #BAE6FD; color: #0369A1; }
.mini-btn.accent:hover { background: #F0F9FF; }

.empty-state { text-align: center; color: var(--text-muted); padding: 40px 20px; font-size: 14px; }

/* 测试集管理 */
.ts-add { display: flex; gap: 8px; margin-bottom: 12px; }
.ts-list { max-height: 320px; overflow-y: auto; display: flex; flex-direction: column; gap: 4px; }
.ts-row {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 10px; border: 1px solid #F1F5F9; border-radius: 10px;
  background: #F8FAFC; transition: all 0.15s;
}
.ts-row:hover { background: #F0F9FF; border-color: #BAE6FD; }
.ts-id { font-size: 11px; font-weight: 700; color: #0369A1; font-family: 'Space Grotesk', sans-serif; flex-shrink: 0; }
.ts-q {
  flex: 1; font-size: 12.5px; color: #334155; white-space: nowrap;
  overflow: hidden; text-overflow: ellipsis;
}
.rate-content { display: flex; flex-direction: column; gap: 20px; }
.rate-question { padding: 12px 16px; background: #F8FAFC; border-radius: 10px; font-size: 14px; color: #475569; border-left: 3px solid #D97706; }
.rate-stars-row { display: flex; align-items: center; gap: 12px; }
.rate-label { font-size: 14px; color: #475569; font-weight: 500; white-space: nowrap; }
.rate-comment { display: flex; flex-direction: column; gap: 8px; }
.detail-content { max-height: 500px; overflow-y: auto; }
.detail-content h4 { margin: 16px 0 8px; color: var(--text-primary); }
.detail-question { color: var(--text-primary); font-weight: 500; line-height: 1.7; }
.detail-answer { line-height: 1.9; font-size: 14px; }
.detail-answer :deep(blockquote) { border-left: 4px solid #0369A1; padding: 8px 16px; background: #F0F9FF; border-radius: 0 8px 8px 0; margin: 10px 0; }
.detail-meta-row { display: flex; gap: 24px; font-size: 13px; color: var(--text-muted); margin-top: 16px; }
.detail-feedback { margin-top: 12px; padding: 10px 14px; background: #EFF6FF; border: 1px solid #93C5FD; border-radius: 10px; font-size: 13px; color: #1E40AF; line-height: 1.6; }

@media (max-width: 900px) {
  .two-col, .two-col.wide-record { grid-template-columns: 1fr; }
  .metric-ledger { grid-template-columns: repeat(2, 1fr); }
  .metric-cell:nth-child(3) { border-left: none; }
  .rc-meta { flex-wrap: wrap; }
}
</style>
