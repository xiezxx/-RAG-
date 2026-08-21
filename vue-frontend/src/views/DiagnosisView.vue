<template>
  <div class="diag-page">
    <div class="page-head">
      <div>
        <h2 class="page-title">智能案情诊断</h2>
        <p class="page-subtitle">输入案情要素，系统检索相关法条并生成诊断报告（问题清单 / 法律依据 / 风险等级 / 赔偿估算 / 行动建议）</p>
      </div>
      <button class="history-btn" @click="openHistory">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
        <span>历史报告</span>
      </button>
    </div>

    <div class="diag-layout">
      <!-- ── 左栏：案情输入 ── -->
      <section class="panel form-panel">
        <div class="panel-head"><span class="panel-index">壹</span><h3>案情信息</h3></div>

        <div class="form-item">
          <label>纠纷类型</label>
          <el-select v-model="form.reason" style="width:100%">
            <el-option v-for="r in reasonOptions" :key="r" :value="r" :label="r" />
          </el-select>
        </div>

        <div class="form-row">
          <div class="form-item">
            <label>工龄（年）</label>
            <el-input-number v-model="form.years" :min="0" :max="50" :step="0.5" :precision="1" style="width:100%" />
          </div>
          <div class="form-item">
            <label>月工资（元）</label>
            <el-input-number v-model="form.monthlyWage" :min="0" :max="1000000" :step="500" style="width:100%" />
          </div>
        </div>

        <div class="form-item switch-item">
          <label>已签订书面劳动合同</label>
          <el-switch v-model="form.hasContract" />
        </div>

        <div class="form-item">
          <label>案情描述 <span class="req">*</span></label>
          <el-input v-model="form.description" type="textarea" :rows="7" maxlength="2000" show-word-limit
                    placeholder="尽量写清楚：入职时间、岗位、工资构成、公司做了什么、有没有书面通知、你有什么证据……" />
        </div>

        <button class="gen-btn" @click="generate" :disabled="loading || !form.description.trim() || form.description.trim().length < 5">
          <span v-if="!loading">⚖️ 生成诊断报告</span>
          <span v-else class="gen-loading"><span class="dot-flow"></span> 检索法条 + 生成报告中…（约 30-60 秒）</span>
        </button>

        <div class="presets">
          <div class="presets-label">示例案情（一键填充）：</div>
          <button v-for="p in presets" :key="p.name" class="preset-chip" @click="fillPreset(p)">{{ p.name }}</button>
        </div>
      </section>

      <!-- ── 右栏：诊断报告 ── -->
      <section class="panel report-panel" v-loading="loading" element-loading-text="检索法条并生成诊断报告，请稍候…">
        <template v-if="report">
          <div class="panel-head"><span class="panel-index">贰</span><h3>诊断报告</h3>
            <span class="report-query" v-if="report.search_query">检索词：{{ report.search_query }}</span>
            <span class="report-query" v-if="report.createdAt">生成于 {{ report.createdAt }}</span>
            <button class="download-btn" @click="downloadReport" title="下载 HTML 格式报告，可在浏览器中打印 / 保存为 PDF">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              <span>下载报告</span>
            </button>
          </div>

          <div class="report-summary">{{ report.summary }}</div>

          <!-- 赔偿估算 -->
          <div class="est-card">
            <div class="est-head">💰 赔偿估算（按《劳动合同法》第47条程序化计算）</div>
            <div class="est-grid">
              <div class="est-item">
                <div class="est-num">¥{{ fmt(report.estimation?.N) }}</div>
                <div class="est-label">经济补偿金 N<br/><small>{{ report.estimation?.months }} 个月工资</small></div>
              </div>
              <div class="est-item">
                <div class="est-num">¥{{ fmt(report.estimation?.N_plus_1) }}</div>
                <div class="est-label">代通知金情形 N+1<br/><small>未提前30日书面通知</small></div>
              </div>
              <div class="est-item">
                <div class="est-num">¥{{ fmt(report.estimation?.['2N']) }}</div>
                <div class="est-label">违法解除赔偿金 2N<br/><small>违法解除/终止</small></div>
              </div>
            </div>
            <div class="est-note">{{ report.estimation?.note }}</div>
          </div>

          <!-- 问题清单 -->
          <div class="sec-title">① 问题清单（{{ report.issues?.length || 0 }} 项，按重要性排序）</div>
          <div class="issue-card" v-for="(it, i) in report.issues" :key="i">
            <div class="issue-head">
              <span class="issue-no">{{ i + 1 }}</span>
              <span class="issue-name">{{ it.issue }}</span>
              <span class="risk-tag" :class="riskClass(it.risk)">{{ it.risk || '—' }}风险</span>
            </div>
            <div class="issue-analysis">{{ it.analysis }}</div>
            <div class="issue-foot">
              <span v-for="b in it.basis" :key="b" class="basis-chip">{{ b }}</span>
            </div>
            <div class="issue-suggestion">💡 {{ it.suggestion }}</div>
          </div>

          <!-- 风险提示 -->
          <div class="sec-title">② 风险提示</div>
          <ul class="warn-list">
            <li v-for="(w, i) in report.warnings" :key="i">{{ w }}</li>
          </ul>

          <!-- 行动建议 -->
          <div class="sec-title">③ 行动建议</div>
          <ol class="step-list">
            <li v-for="(s, i) in report.next_steps" :key="i">{{ s }}</li>
          </ol>

          <!-- 参考来源 -->
          <div class="sec-title">④ 参考来源（RAG 检索）</div>
          <div class="src-cards">
            <div v-for="(s, j) in report.sources" :key="j" class="src-card" :class="'src-' + s.type">
              <div class="src-head">
                <el-tag :type="srcTypeTag(s.type)" size="small" effect="dark" round>{{ srcTypeLabel(s.type) }}</el-tag>
                <el-tag v-if="s.status" size="small" :type="statusTagType(s.status)" effect="plain" round>{{ s.status }}</el-tag>
              </div>
              <div class="src-title-text">{{ s.title }}</div>
              <div class="src-snippet" v-if="s.snippet">{{ s.snippet.substring(0, 120) }}…</div>
            </div>
          </div>

          <div class="disclaimer">⚠️ 本报告由 AI 基于知识库初步生成，仅供参考，不构成正式法律意见。涉及实际纠纷请咨询执业律师或劳动仲裁机构。</div>
        </template>

        <div v-else-if="!loading" class="report-empty">
          <svg width="52" height="52" viewBox="0 0 24 24" fill="none" stroke="#CBD5E1" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 3v18" /><path d="M8 21h8" /><path d="M5 7h14" />
            <path d="M5 7l-3.5 6a3 3 0 0 0 6 0L5 7z" /><path d="M19 7l-3.5 6a3 3 0 0 0 6 0L19 7z" />
          </svg>
          <p>填写左侧案情信息后生成诊断报告</p>
          <span>系统将自动检索相关法律条文，结合您的工龄、工资计算赔偿金额</span>
        </div>
      </section>
    </div>

    <!-- 历史报告抽屉 -->
    <el-drawer v-model="historyVisible" title="诊断报告历史" size="440px">
      <div v-loading="historyLoading" class="history-list">
        <div v-if="!history.length && !historyLoading" class="history-empty">
          <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="#CBD5E1" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          <p>暂无历史诊断报告</p>
          <span>生成一次诊断后会自动保存到这里</span>
        </div>
        <div v-for="h in history" :key="h.id" class="history-item" @click="loadReport(h.id)">
          <div class="history-item-head">
            <span class="history-reason">{{ h.reason }}</span>
            <span class="history-time">{{ h.createdAt }}</span>
          </div>
          <div class="history-summary">{{ h.summary }}</div>
          <div class="history-meta">
            <span v-if="h.estimation?.N != null" class="history-est">补偿金约 ¥{{ fmt(h.estimation.N) }}</span>
            <span>工龄 {{ h.years }} 年 · 月薪 ¥{{ fmt(h.monthlyWage) }} · {{ h.hasContract ? '已签合同' : '未签合同' }}</span>
          </div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const reasonOptions = ['被辞退', '协商解除', '被迫离职', '主动离职', '拖欠工资', '加班纠纷', '工伤', '试用期纠纷', '孕期纠纷', '未签合同', '其他']

const form = ref({
  reason: '被辞退',
  years: 3,
  monthlyWage: 8000,
  hasContract: true,
  description: ''
})

const presets = [
  { name: '突然被辞退', reason: '被辞退', years: 3, monthlyWage: 8000, hasContract: true, description: '我在公司干了3年，月薪8000元，签了合同。上周公司突然口头通知我被辞退，没有给书面通知，也没有说明辞退原因。' },
  { name: '加班不给钱', reason: '加班纠纷', years: 2, monthlyWage: 6000, hasContract: true, description: '公司长期要求周末加班，一年约有30个周末在上班，但从没发过加班费。我离职时能要求补发加班费吗？' },
  { name: '一直没签合同', reason: '未签合同', years: 0.8, monthlyWage: 5500, hasContract: false, description: '入职快一年了，公司一直没跟我签劳动合同，现在我想离职，能要求双倍工资差额吗？' }
]

const loading = ref(false)
const report = ref(null)
let activeRequest = null

const historyVisible = ref(false)
const historyLoading = ref(false)
const history = ref([])

async function openHistory() {
  historyVisible.value = true
  historyLoading.value = true
  try {
    const res = await api.get('/diagnosis/history')
    history.value = res.code === 200 ? (res.data || []) : []
    if (res.code !== 200) ElMessage.error(res.message || '历史记录加载失败')
  } catch (e) {
    history.value = []
    ElMessage.error('历史记录加载失败')
  } finally {
    historyLoading.value = false
  }
}

async function loadReport(id) {
  try {
    const res = await api.get(`/diagnosis/history/${id}`)
    if (res.code === 200 && res.data) {
      report.value = res.data
      // 回填表单，方便基于历史案情再次生成
      form.value = {
        reason: res.data.reason || '被辞退',
        years: res.data.years ?? 3,
        monthlyWage: res.data.monthlyWage ?? 8000,
        hasContract: res.data.hasContract !== false,
        description: res.data.description || ''
      }
      historyVisible.value = false
      ElMessage.success('已加载历史报告')
    } else {
      ElMessage.error(res.message || '报告加载失败')
    }
  } catch (e) {
    ElMessage.error('报告加载失败')
  }
}

function fillPreset(p) {
  form.value = { reason: p.reason, years: p.years, monthlyWage: p.monthlyWage, hasContract: p.hasContract, description: p.description }
}

async function generate() {
  if (loading.value) return
  loading.value = true
  activeRequest = new AbortController()
  // 注意：不在页面失活时中断请求——MainLayout 的 keep-alive 会让本页保持挂载，
  // 切到其它页面后生成照常进行（后端也会把报告落库到诊断历史）；
  // 切回来时加载状态与最终报告直接可见，由 180s 超时兜底。
  try {
    const res = await api.post('/diagnosis', {
      description: form.value.description.trim(),
      reason: form.value.reason,
      years: form.value.years,
      monthly_wage: form.value.monthlyWage,
      has_contract: form.value.hasContract
    }, { timeout: 180000, signal: activeRequest.signal })
    if (res.code === 200) {
      report.value = res.data
      ElMessage.success('诊断报告已生成')
    } else {
      ElMessage.error(res.message || '生成失败')
    }
  } catch (e) {
    if (e?.name === 'CanceledError' || e?.name === 'AbortError') return
    ElMessage.error('生成失败：RAG 服务暂不可用，请稍后重试')
  } finally {
    loading.value = false
    activeRequest = null
  }
}

function fmt(n) { return n == null ? '0' : Number(n).toLocaleString('zh-CN', { maximumFractionDigits: 2 }) }

/* ══════ 下载报告：生成自包含 HTML（内嵌打印按钮，可打印/另存为 PDF） ══════ */
function esc(s) {
  return String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
}

function downloadReport() {
  if (!report.value) return
  const r = report.value
  const est = r.estimation || {}
  const srcType = { statute: '法条', interpretation: '司法解释', case: '案例' }

  const issues = (r.issues || []).map((it, i) => `
    <div class="issue">
      <div class="issue-head"><span class="no">${i + 1}</span><span class="name">${esc(it.issue)}</span><span class="risk risk-${esc(it.risk || '中')}">${esc(it.risk || '—')}风险</span></div>
      <div class="analysis">${esc(it.analysis)}</div>
      <div class="chips">${(it.basis || []).map(b => `<span class="chip">${esc(b)}</span>`).join('')}</div>
      ${it.suggestion ? `<div class="sugg">💡 ${esc(it.suggestion)}</div>` : ''}
    </div>`).join('')
  const warnings = (r.warnings || []).map(w => `<li>${esc(w)}</li>`).join('')
  const steps = (r.next_steps || []).map(s => `<li>${esc(s)}</li>`).join('')
  const sources = (r.sources || []).map(s => `
    <div class="src"><span class="tag">${srcType[s.type] || '资料'}</span>${s.status ? `<span class="st">${esc(s.status)}</span>` : ''}<div class="t">${esc(s.title)}</div>${s.snippet ? `<div class="sn">${esc(s.snippet).substring(0, 120)}…</div>` : ''}</div>`).join('')

  const html = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>劳动法 AI 诊断报告</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: "Microsoft YaHei", "PingFang SC", sans-serif; color: #1E293B; background: #F8FAFC; padding: 32px 16px; }
  .page { max-width: 820px; margin: 0 auto; background: #FFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 40px 44px; }
  h1 { font-size: 22px; color: #0F172A; letter-spacing: 1px; }
  .sub { color: #94A3B8; font-size: 12px; margin-top: 6px; }
  .bar { height: 2px; background: linear-gradient(90deg, #0369A1, #38BDF8); margin: 16px 0 24px; }
  .print-btn { display: block; margin: 0 0 24px auto; padding: 9px 18px; border: 1px solid #BAE6FD; background: #F0F9FF; color: #0369A1; border-radius: 8px; font-size: 13px; cursor: pointer; font-family: inherit; }
  h2 { font-size: 15px; color: #0F172A; margin: 26px 0 10px; padding-left: 10px; border-left: 3px solid #0369A1; }
  .meta { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; background: #F8FAFC; border-radius: 10px; padding: 14px 16px; font-size: 13px; color: #475569; }
  .desc { font-size: 13.5px; line-height: 1.8; color: #334155; margin-top: 12px; }
  .summary { background: linear-gradient(135deg, #EFF6FF, #F0F9FF); border: 1px solid #BAE6FD; border-radius: 10px; padding: 14px 16px; font-size: 14px; font-weight: 600; color: #1E40AF; line-height: 1.8; }
  .est { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 10px; }
  .est div { text-align: center; border: 1px solid #FDE68A; background: #FFFBEB; border-radius: 10px; padding: 12px 6px; }
  .est .num { font-size: 18px; font-weight: 700; color: #B45309; }
  .est .lab { font-size: 11px; color: #92400E; margin-top: 4px; }
  .est-note { font-size: 11.5px; color: #A16207; line-height: 1.7; }
  .issue { border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px 14px; margin-bottom: 10px; }
  .issue-head { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
  .issue .no { width: 20px; height: 20px; border-radius: 50%; background: #EFF6FF; color: #0369A1; font-size: 11px; font-weight: 700; display: flex; align-items: center; justify-content: center; }
  .issue .name { font-size: 13.5px; font-weight: 600; }
  .risk { font-size: 10.5px; padding: 2px 8px; border-radius: 20px; }
  .risk-高 { background: #FEF2F2; color: #DC2626; border: 1px solid #FECACA; }
  .risk-中 { background: #FFFBEB; color: #D97706; border: 1px solid #FDE68A; }
  .risk-低 { background: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; }
  .analysis { font-size: 12.5px; line-height: 1.8; color: #475569; }
  .chips { margin-top: 6px; }
  .chip { display: inline-block; font-size: 10.5px; color: #0369A1; background: #F0F9FF; border: 1px solid #BAE6FD; border-radius: 5px; padding: 1px 7px; margin: 2px 4px 0 0; }
  .sugg { margin-top: 8px; padding: 8px 10px; background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 7px; font-size: 12px; color: #166534; }
  ol, ul { padding-left: 20px; font-size: 13px; line-height: 2; color: #334155; }
  ul li { color: #B45309; }
  .src { border: 1px solid #E2E8F0; border-radius: 8px; padding: 8px 10px; margin-bottom: 6px; }
  .src .tag { font-size: 10.5px; color: #0369A1; background: #F0F9FF; border-radius: 5px; padding: 1px 7px; margin-right: 6px; }
  .src .st { font-size: 10.5px; color: #64748B; border: 1px solid #E2E8F0; border-radius: 5px; padding: 1px 7px; }
  .src .t { font-size: 12px; color: #334155; margin-top: 4px; }
  .src .sn { font-size: 11px; color: #94A3B8; margin-top: 2px; }
  .foot { margin-top: 26px; padding: 12px 14px; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; font-size: 11.5px; color: #64748B; line-height: 1.7; }
  @media print {
    body { background: #FFF; padding: 0; }
    .page { border: none; padding: 0; max-width: 100%; }
    .print-btn { display: none; }
    .issue, .src { break-inside: avoid; }
  }
</style>
</head>
<body>
<div class="page">
  <button class="print-btn" onclick="window.print()">🖨️ 打印 / 保存为 PDF</button>
  <h1>⚖️ 劳动法 AI 诊断报告</h1>
  <div class="sub">生成时间：${esc(r.createdAt || '刚刚')}　|　本报告由「劳动法 RAG 智能咨询系统」生成，仅供参考</div>
  <div class="bar"></div>

  <div class="meta">
    <span>纠纷类型：${esc(r.reason || '—')}</span>
    <span>工龄：${esc(r.years ?? '—')} 年</span>
    <span>月工资：¥${fmt(r.monthlyWage)}</span>
    <span>书面合同：${r.hasContract ? '已签订' : '未签订'}</span>
  </div>
  <div class="desc"><b>案情描述：</b>${esc(r.description)}</div>

  <h2>一、诊断结论</h2>
  <div class="summary">${esc(r.summary)}</div>

  <h2>二、赔偿估算（按《劳动合同法》第47条）</h2>
  <div class="est">
    <div><div class="num">¥${fmt(est.N)}</div><div class="lab">经济补偿金 N<br>${esc(est.months)} 个月工资</div></div>
    <div><div class="num">¥${fmt(est.N_plus_1)}</div><div class="lab">代通知金情形 N+1<br>未提前30日书面通知</div></div>
    <div><div class="num">¥${fmt(est['2N'])}</div><div class="lab">违法解除赔偿金 2N<br>违法解除/终止</div></div>
  </div>
  ${est.note ? `<div class="est-note">${esc(est.note)}</div>` : ''}

  <h2>三、问题清单（${(r.issues || []).length} 项）</h2>
  ${issues}

  <h2>四、风险提示</h2>
  <ul>${warnings}</ul>

  <h2>五、行动建议</h2>
  <ol>${steps}</ol>

  <h2>六、参考来源（RAG 检索）</h2>
  ${sources}

  <div class="foot">⚠️ 本报告由 AI 基于劳动法知识库初步生成，赔偿金额为按法定规则的程序化估算，不构成正式法律意见。涉及实际纠纷请咨询执业律师或向劳动仲裁机构申请仲裁。</div>
</div>
</body>
</html>`

  const dateStr = new Date().toISOString().slice(0, 10)
  const blob = new Blob([html], { type: 'text/html;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `劳动法AI诊断报告_${r.reason || '诊断'}_${dateStr}.html`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
  ElMessage.success('报告已下载，打开后可按右上角按钮打印 / 保存为 PDF')
}
function riskClass(r) { return { '高': 'high', '中': 'mid', '低': 'low' }[r] || 'mid' }
function srcTypeTag(t) { const m = { statute: 'success', interpretation: 'primary', case: 'warning' }; return m[t] || 'info' }
function srcTypeLabel(t) { const m = { statute: '法条', interpretation: '司法解释', case: '案例' }; return m[t] || '资料' }
function statusTagType(s) { const m = { '现行有效': 'success', '已被修订': 'warning', '已废止': 'danger', '尚未生效': 'info' }; return m[s] || 'info' }
</script>

<style scoped>
.diag-page { max-width: 1200px; margin: 0 auto; padding-bottom: 40px; }
.page-head { margin-bottom: 28px; display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
.page-title { margin: 0; font-size: 24px; font-weight: 700; color: var(--text-primary); }
.page-subtitle { margin: 4px 0 0; font-size: 13px; color: var(--text-muted); }

.history-btn {
  display: inline-flex; align-items: center; gap: 7px;
  padding: 9px 16px; border-radius: 10px; border: 1px solid #E2E8F0;
  background: #FFF; color: #475569; font-size: 13px; font-weight: 500;
  cursor: pointer; transition: all .2s; font-family: inherit; flex-shrink: 0;
}
.history-btn:hover { border-color: #38BDF8; color: #0369A1; box-shadow: 0 3px 10px rgba(56, 189, 248, .15); transform: translateY(-1px); }

.diag-layout { display: grid; grid-template-columns: 340px minmax(0, 1fr); gap: 24px; }

.panel { background: #FFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 22px 24px; min-width: 0; }
.panel-head { display: flex; align-items: center; flex-wrap: wrap; gap: 10px; margin-bottom: 18px; padding-bottom: 12px; border-bottom: 1px solid #F1F5F9; }
.panel-index { font-size: 11px; font-weight: 700; color: #0369A1; padding: 2px 8px; border: 1px solid #BAE6FD; border-radius: 6px; background: #F0F9FF; font-family: 'Noto Serif SC', serif; }
.panel-head h3 { margin: 0; font-size: 15px; font-weight: 700; color: #1E293B; flex: 1; min-width: 0; }

/* ── 表单 ── */
.form-panel { position: sticky; top: 20px; align-self: start; }
.form-item { margin-bottom: 16px; }
.form-item label { display: block; font-size: 13px; color: #475569; font-weight: 500; margin-bottom: 6px; }
.form-item .req { color: #EF4444; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.switch-item { display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; background: #F8FAFC; border-radius: 10px; }
.switch-item label { margin: 0; }

.gen-btn { width: 100%; padding: 13px 0; border: none; border-radius: 12px; background: linear-gradient(135deg, #0369A1, #38BDF8); color: #FFF; font-size: 15px; font-weight: 600; cursor: pointer; transition: all .25s; font-family: inherit; box-shadow: 0 6px 20px rgba(3, 105, 161, .25); }
.gen-btn:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 10px 28px rgba(3, 105, 161, .35); }
.gen-btn:disabled { opacity: .55; cursor: not-allowed; }
.gen-loading { display: inline-flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 500; }
.dot-flow { width: 8px; height: 8px; border-radius: 50%; background: #FFF; animation: dotFlow 1.2s infinite; }
@keyframes dotFlow { 0%,100% { opacity: .3; } 50% { opacity: 1; } }

.presets { margin-top: 18px; border-top: 1px dashed #E2E8F0; padding-top: 14px; }
.presets-label { font-size: 12px; color: #94A3B8; margin-bottom: 8px; }
.preset-chip { padding: 5px 12px; margin: 0 6px 6px 0; border: 1px solid #E2E8F0; border-radius: 20px; background: #FFF; color: #64748B; font-size: 12px; cursor: pointer; transition: all .2s; font-family: inherit; }
.preset-chip:hover { border-color: #38BDF8; color: #0369A1; transform: translateY(-1px); box-shadow: 0 3px 10px rgba(56, 189, 248, .15); }

/* ── 报告 ── */
.report-panel { min-height: 480px; display: flex; flex-direction: column; overflow-wrap: break-word; }
.report-query { font-size: 11px; color: #94A3B8; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 32%; }
.download-btn {
  display: inline-flex; align-items: center; gap: 6px; flex-shrink: 0; margin-left: auto;
  padding: 6px 12px; border-radius: 8px; border: 1px solid #BAE6FD;
  background: #F0F9FF; color: #0369A1; font-size: 12px; font-weight: 500;
  cursor: pointer; transition: all .2s; font-family: inherit;
}
.download-btn:hover { background: #E0F2FE; border-color: #38BDF8; }
.report-summary { padding: 14px 18px; background: linear-gradient(135deg, #EFF6FF, #F0F9FF); border: 1px solid #BAE6FD; border-radius: 12px; color: #1E40AF; font-size: 14.5px; font-weight: 600; line-height: 1.7; margin-bottom: 18px; }

.est-card { border: 1px solid #FDE68A; background: linear-gradient(135deg, #FFFBEB, #FEF3C7); border-radius: 14px; padding: 16px 18px; margin-bottom: 22px; }
.est-head { font-size: 13px; font-weight: 700; color: #92400E; margin-bottom: 12px; }
.est-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; }
.est-item { text-align: center; background: rgba(255, 255, 255, .75); border-radius: 10px; padding: 12px 8px; border: 1px solid #FDE68A; min-width: 0; }
.est-num { font-size: clamp(16px, 1.6vw, 22px); font-weight: 700; color: #B45309; font-family: 'Space Grotesk', sans-serif; font-variant-numeric: tabular-nums; overflow-wrap: anywhere; }
.est-label { font-size: 12px; color: #92400E; margin-top: 6px; line-height: 1.5; }
.est-label small { color: #A16207; font-size: 11px; }
.est-note { font-size: 11px; color: #A16207; margin-top: 10px; line-height: 1.6; }

.sec-title { font-size: 14px; font-weight: 700; color: #1E293B; margin: 24px 0 12px; }
.issue-card { border: 1px solid #E2E8F0; border-radius: 12px; padding: 14px 16px; margin-bottom: 12px; transition: all .2s; }
.issue-card:hover { box-shadow: 0 4px 14px rgba(0, 0, 0, .05); }
.issue-head { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.issue-no { width: 22px; height: 22px; border-radius: 50%; background: #EFF6FF; color: #0369A1; font-size: 12px; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.issue-name { font-size: 14px; font-weight: 600; color: #1E293B; flex: 1; min-width: 0; }
.risk-tag { font-size: 11px; font-weight: 600; padding: 2px 10px; border-radius: 20px; flex-shrink: 0; }
.risk-tag.high { background: #FEF2F2; color: #DC2626; border: 1px solid #FECACA; }
.risk-tag.mid { background: #FFFBEB; color: #D97706; border: 1px solid #FDE68A; }
.risk-tag.low { background: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; }
.issue-analysis { font-size: 13.5px; color: #475569; line-height: 1.8; }
.issue-foot { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
.basis-chip { font-size: 11px; color: #0369A1; background: #F0F9FF; border: 1px solid #BAE6FD; border-radius: 6px; padding: 2px 8px; }
.issue-suggestion { margin-top: 10px; padding: 9px 12px; background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 8px; font-size: 12.5px; color: #166534; line-height: 1.6; }

.warn-list { margin: 0; padding-left: 20px; }
.warn-list li { color: #B45309; font-size: 13px; line-height: 1.9; }
.step-list { margin: 0; padding-left: 22px; }
.step-list li { color: #334155; font-size: 13.5px; line-height: 2; }

.src-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 8px; }
.src-card { padding: 10px 12px; border-radius: 10px; border: 1px solid #E2E8F0; background: #FFF; min-width: 0; }
.src-statute { border-left: 3px solid #22C55E; }
.src-interpretation { border-left: 3px solid #3B82F6; }
.src-case { border-left: 3px solid #F59E0B; }
.src-head { display: flex; gap: 6px; margin-bottom: 6px; }
.src-title-text { font-size: 12px; font-weight: 500; color: #334155; }
.src-snippet { font-size: 11px; color: #94A3B8; margin-top: 4px; line-height: 1.5; }

.disclaimer { margin-top: 24px; padding: 12px 16px; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; font-size: 12px; color: #64748B; line-height: 1.7; }

.report-empty { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 90px 20px; text-align: center; gap: 12px; }
.report-empty p { margin: 0; color: #64748B; font-size: 15px; font-weight: 500; }
.report-empty span { color: #94A3B8; font-size: 12.5px; }

/* ── 历史报告抽屉 ── */
.history-list { min-height: 200px; }
.history-item { border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px 14px; margin-bottom: 10px; cursor: pointer; transition: all .2s; }
.history-item:hover { border-color: #38BDF8; box-shadow: 0 3px 10px rgba(56, 189, 248, .12); transform: translateY(-1px); }
.history-item-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }
.history-reason { font-size: 13px; font-weight: 600; color: #1E293B; }
.history-time { font-size: 11px; color: #94A3B8; flex-shrink: 0; margin-left: 8px; }
.history-summary { font-size: 12.5px; color: #475569; line-height: 1.7; margin-bottom: 8px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.history-meta { display: flex; align-items: center; gap: 10px; font-size: 11px; color: #94A3B8; flex-wrap: wrap; }
.history-est { color: #B45309; font-weight: 600; background: #FFFBEB; border: 1px solid #FDE68A; padding: 1px 8px; border-radius: 20px; }
.history-empty { display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 70px 0; text-align: center; }
.history-empty p { margin: 0; color: #64748B; font-size: 14px; font-weight: 500; }
.history-empty span { color: #94A3B8; font-size: 12px; }

@media (max-width: 1000px) {
  .diag-layout { grid-template-columns: 1fr; }
  .form-panel { position: static; }
}
</style>
