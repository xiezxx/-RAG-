<template>
  <div class="history-view">
    <div class="page-head">
      <div>
        <h2 class="page-title">{{ isAdmin ? '系统评估' : '问答记录' }}</h2>
        <p class="page-subtitle">{{ isAdmin ? '全员问答数据与用户反馈' : '个人问答历史与评价' }}</p>
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

    <div class="two-col">
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

        <!-- 消融实验 -->
        <section class="panel">
          <div class="panel-head"><span class="panel-index">贰</span><h3>消融实验</h3></div>
          <div class="ablation-list">
            <div class="abl-item" v-for="a in ablationData" :key="a.config">
              <div class="abl-config">{{ a.config }}</div>
              <div class="abl-metric"><span>R@5</span><b>{{ a.r5 }}</b></div>
              <div class="abl-metric"><span>MRR</span><b>{{ a.mrr }}</b></div>
            </div>
          </div>
          <p class="table-note">* 详细数据见 src/eval/ablation_results.json</p>
        </section>
      </div>

      <!-- ── 右栏：记录 ── -->
      <section class="panel record-panel">
        <div class="panel-head">
          <span class="panel-index">叁</span><h3>问答记录</h3>
          <button class="refresh-btn" @click="loadHistory">刷新</button>
        </div>
        <div class="record-list" v-loading="loading">
          <div class="record-item" v-for="row in history" :key="row.id">
            <div class="record-q">
              <span class="record-user" v-if="isAdmin">{{ row.username || '用户' }}</span>
              {{ row.question?.substring(0, 40) }}{{ row.question?.length > 40 ? '…' : '' }}
            </div>
            <div class="record-time">{{ formatTime(row.createdAt) }}</div>
            <div class="record-rating">
              <template v-if="row.rating > 0">
                <span v-for="i in 5" :key="i" class="star" :class="{ filled: i <= row.rating }">★</span>
              </template>
              <span v-else class="unrated">未评</span>
            </div>
            <div class="record-feedback">{{ row.feedback || '—' }}</div>
            <div class="record-actions">
              <button class="mini-btn" @click="showDetail(row)">详情</button>
              <button class="mini-btn accent" @click="openRate(row)">评价</button>
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
          <span>时间 {{ formatTime(current.createdAt) }}</span>
          <span>评分 {{ current.rating > 0 ? current.rating + '分' : '未评' }}</span>
        </div>
        <div v-if="current.feedback" class="detail-feedback"><strong>用户反馈：</strong>{{ current.feedback }}</div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { marked } from 'marked'
import api from '../api'

const role = localStorage.getItem('role') || 'USER'
const isAdmin = computed(() => role === 'ADMIN')

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

const ablationData = [
  { config: 'BM25 (基线)', r5: '88%', mrr: '0.467' },
  { config: '+ 向量检索', r5: '100%', mrr: '0.502' },
  { config: '+ 知识图谱', r5: '100%', mrr: '0.502' },
  { config: '+ 时效感知', r5: '120%', mrr: '0.642' }
]

let pollTimer = null
marked.setOptions({ breaks: true, gfm: true })
function renderMd(text) { return marked.parse((text || '').replace(/<[^>]*>/g, '')) }
function formatTime(t) { if (!t) return ''; const s = typeof t === 'string' ? t : String(t); return s.substring(0, 16).replace('T', ' ') }

async function loadHistory() {
  loading.value = true
  try {
    const url = isAdmin.value ? '/eval/admin/history' : '/eval/history'
    const res = await api.get(url, { params: { limit: 100 } })
    if (res.code === 200) {
      history.value = (res.data || []).map(h => ({ ...h, _rating: h.rating || 0 }))
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
onMounted(() => { loadHistory(); pollTimer = setInterval(loadHistory, 10000) })
onUnmounted(() => { if (pollTimer) clearInterval(pollTimer) })
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

/* 消融 */
.ablation-list { display: flex; flex-direction: column; }
.abl-item { display: flex; align-items: center; gap: 16px; padding: 12px 0; border-bottom: 1px solid #F1F5F9; }
.abl-item:last-child { border-bottom: none; }
.abl-config { flex: 1; font-size: 13px; font-weight: 500; color: #334155; }
.abl-metric { display: flex; flex-direction: column; align-items: center; }
.abl-metric span { font-size: 10px; color: #94A3B8; }
.abl-metric b { font-size: 15px; color: #0369A1; font-family: 'Space Grotesk', sans-serif; }
.table-note { font-size: 11px; color: var(--text-muted); margin-top: 12px; }

/* 记录 */
.record-panel { grid-column: auto; }
.refresh-btn { border: none; background: none; color: #0369A1; font-size: 13px; cursor: pointer; font-family: inherit; }
.record-list { max-height: 640px; overflow-y: auto; }
.record-item { display: flex; align-items: center; gap: 16px; padding: 14px 0; border-bottom: 1px solid #F1F5F9; }
.record-item:last-child { border-bottom: none; }
.record-q { flex: 1; min-width: 0; font-size: 13.5px; color: #334155; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.record-user { font-size: 11px; color: #0369A1; background: #F0F9FF; border: 1px solid #BAE6FD; padding: 1px 6px; border-radius: 4px; margin-right: 6px; }
.record-time { flex-shrink: 0; font-size: 11px; color: #94A3B8; font-family: 'Space Grotesk', sans-serif; }
.record-rating { flex-shrink: 0; width: 76px; }
.star { color: #CBD5E1; font-size: 13px; }
.star.filled { color: #F59E0B; }
.unrated { color: #CBD5E1; font-size: 11px; }
.record-feedback { flex-shrink: 0; width: 130px; font-size: 11.5px; color: #94A3B8; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.record-actions { flex-shrink: 0; display: flex; gap: 4px; }
.mini-btn { padding: 4px 10px; border: 1px solid #E2E8F0; border-radius: 6px; background: #FFF; font-size: 12px; color: #64748B; cursor: pointer; font-family: inherit; transition: all 0.15s; }
.mini-btn:hover { border-color: #94A3B8; color: #334155; }
.mini-btn.accent { border-color: #BAE6FD; color: #0369A1; }
.mini-btn.accent:hover { background: #F0F9FF; }

.empty-state { text-align: center; color: var(--text-muted); padding: 40px 20px; font-size: 14px; }
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
  .two-col { grid-template-columns: 1fr; }
  .metric-ledger { grid-template-columns: repeat(2, 1fr); }
  .metric-cell:nth-child(3) { border-left: none; }
  .record-item { flex-wrap: wrap; }
}
</style>
