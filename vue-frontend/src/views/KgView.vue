<template>
  <div class="kg-page">
    <div class="page-head">
      <div>
        <h2 class="page-title">知识图谱</h2>
        <p class="page-subtitle">劳动法实体关联网络 · 7 类节点</p>
      </div>
      <el-radio-group v-model="viewMode" size="small">
        <el-radio-button label="all">全部</el-radio-button>
        <el-radio-button label="concept">法律概念</el-radio-button>
        <el-radio-button label="act">违法与责任</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 科普介绍（可折叠） -->
    <div class="kg-intro" :class="{ collapsed: !introExpanded }">
      <div class="intro-head" @click="introExpanded = !introExpanded">
        <h3>🔍 知识图谱是什么？ 怎么看懂这张图</h3>
        <span class="intro-toggle">{{ introExpanded ? '收起 ▴' : '展开 ▾' }}</span>
      </div>
      <div v-show="introExpanded" class="intro-body">
        <div class="intro-grid">
          <div class="intro-block full">
            <b>① 它是什么</b>
            <p>把劳动法里的法律、条文、概念、案例串成一张「关系网」。圆点是一个个法律知识点，连线是它们之间的关系——就像给零散的法条画了一张思维导图。</p>
            <p class="example-hint-inline">示例问题：被辞退能拿什么补偿？</p>
            <div class="example-flow">
              <template v-for="(n, i) in examplePath" :key="n.name">
                <div class="flow-node">
                  <span class="path-dot" :style="{ background: n.color }"></span>
                  <div class="path-text">
                    <b>{{ n.name }}</b>
                    <span class="path-type">{{ n.type }}</span>
                  </div>
                </div>
                <div v-if="i < examplePath.length - 1" class="flow-arrow">
                  <span class="flow-arrow-label">{{ n.relation }}</span>
                  <span class="flow-arrow-line"></span>
                </div>
              </template>
            </div>
          </div>
          <div class="intro-block">
            <b>② 怎么看颜色</b>
            <p>不同颜色代表不同类型的知识点：<span class="c-blue">蓝色=法律</span>、<span class="c-green">绿色=条文</span>、<span class="c-cyan">青色=案例</span>、<span class="c-purple">紫色=概念</span>、<span class="c-sky">天蓝=权利义务</span>、<span class="c-red">红色=违法行为</span>、<span class="c-orange">橙色=法律责任</span>。</p>
          </div>
          <div class="intro-block">
            <b>③ 它有什么用</b>
            <p>从一个法条出发，顺着连线就能找到它定义的概念、对应的违法行为和要承担的责任。比如「被辞退能拿什么补偿」，顺着 ① 里的示例链就能一路找到答案。</p>
          </div>
          <div class="intro-block">
            <b>④ 操作小技巧</b>
            <p>拖动圆点整理布局 · 滚轮缩放 · 悬停圆点高亮它和相邻节点 · 右上角按钮可只看某几类节点。</p>
          </div>
        </div>
      </div>
    </div>

    <div class="kg-layout">
      <!-- 主图 -->
      <div class="graph-panel">
        <div class="graph-panel-head">
          <h3>实体关系总览</h3>
          <span class="graph-hint">拖动节点整理布局 · 滚轮缩放 · 悬停高亮相邻节点</span>
        </div>
        <div ref="chartDom" class="chart-container"></div>
      </div>

      <!-- 侧栏 -->
      <div class="side">
        <div class="panel">
          <div class="panel-head"><span class="panel-index">壹</span><h3>图例</h3></div>
          <div class="legend-list">
            <div class="legend-item" v-for="lg in legends" :key="lg.name">
              <span class="dot" :style="{ background: lg.color }"></span>
              <div class="legend-text">
                <span class="legend-name">{{ lg.name }}</span>
                <span class="legend-desc">{{ lg.desc }}</span>
              </div>
            </div>
          </div>
        </div>
        <div class="panel">
          <div class="panel-head"><span class="panel-index">贰</span><h3>图谱统计</h3></div>
          <div class="kg-stats">
            <div class="kg-stat" v-for="s in kgStats" :key="s.label">
              <span class="kg-stat-label">{{ s.label }}</span>
              <b>{{ s.value }}</b>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 实体维护（管理员/研究人员：修正知识图谱）—— 全宽面板 -->
    <section class="entity-panel" v-if="canEdit">
      <div class="panel-head">
        <span class="panel-index">叁</span><h3>实体维护</h3>
        <span class="entity-hint">新增或删除知识图谱实体，保存后立即生效</span>
        <div class="entity-toolbar">
          <el-select v-model="entityType" size="small" style="width: 170px">
            <el-option v-for="t in entityTypes" :key="t.value" :value="t.value" :label="t.label" />
          </el-select>
          <el-button type="primary" size="small" round @click="openEntityDialog">新增实体</el-button>
        </div>
      </div>
      <div class="entity-grid" v-loading="entityLoading">
        <div class="entity-card" v-for="e in currentEntities" :key="e.type + ':' + e.name">
          <div class="entity-info">
            <span class="entity-name">{{ e.name }}</span>
            <span class="entity-desc" :title="e.description">{{ e.description || '—' }}</span>
          </div>
          <el-button size="small" type="danger" text circle @click="removeEntity(e)" title="删除实体">
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
        <div v-if="!currentEntities.length && !entityLoading" class="empty-state grid-full">该类型暂无实体</div>
      </div>
    </section>

    <!-- 新增实体 -->
    <el-dialog v-model="entityDialogVisible" title="新增图谱实体" width="440px">
      <el-form label-width="70px" @submit.prevent>
        <el-form-item label="类型">
          <el-select v-model="entityForm.type" style="width: 100%">
            <el-option v-for="t in entityTypes" :key="t.value" :value="t.value" :label="t.label" />
          </el-select>
        </el-form-item>
        <el-form-item label="名称" required>
          <el-input v-model="entityForm.name" placeholder="实体名称，如：竞业限制补偿" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="entityForm.description" type="textarea" :rows="3" placeholder="实体释义（选填）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button round @click="entityDialogVisible = false">取消</el-button>
        <el-button type="primary" round :loading="entitySaving" @click="submitEntity">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, reactive, watch, onMounted, onActivated, onDeactivated, nextTick } from 'vue'
import * as echarts from 'echarts'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'

const viewMode = ref('all')
const chartDom = ref(null)
let chart = null

// ── 实体维护（管理员/研究人员） ──
const role = localStorage.getItem('role') || 'USER'
const canEdit = role === 'ADMIN' || role === 'RESEARCHER'
const entityTypes = [
  { value: 'LegalConcept', label: '法律概念' },
  { value: 'RightObligation', label: '权利义务' },
  { value: 'IllegalAct', label: '违法行为' },
  { value: 'LegalLiability', label: '法律责任' }
]
const entityType = ref('LegalConcept')
const allTerms = ref([])
const entityLoading = ref(false)
const currentEntities = computed(() => allTerms.value.filter(t => t.type === entityType.value))
const entityDialogVisible = ref(false)
const entitySaving = ref(false)
const entityForm = reactive({ type: 'LegalConcept', name: '', description: '' })

async function loadTerms() {
  entityLoading.value = true
  try {
    const res = await api.get('/knowledge/terms')
    if (res.code === 200) allTerms.value = res.data || []
  } catch (e) {
    console.warn('实体列表加载失败', e)
  }
  entityLoading.value = false
}

function openEntityDialog() {
  entityForm.type = entityType.value
  entityForm.name = ''
  entityForm.description = ''
  entityDialogVisible.value = true
}

async function submitEntity() {
  if (!entityForm.name.trim()) {
    ElMessage.warning('请填写实体名称')
    return
  }
  entitySaving.value = true
  try {
    const res = await api.post('/kg/entities', {
      entity_type: entityForm.type,
      name: entityForm.name.trim(),
      description: entityForm.description.trim()
    })
    if (res.ok === true || res.code === 200) {
      ElMessage.success('实体已创建')
      entityDialogVisible.value = false
      entityType.value = entityForm.type
      loadTerms()
    } else {
      ElMessage.error(res.message || res.error || '创建失败')
    }
  } catch (e) {
    ElMessage.error('创建失败：' + (e?.message || '网络错误'))
  }
  entitySaving.value = false
}

async function removeEntity(e) {
  await ElMessageBox.confirm(`确定删除实体「${e.name}」？`, '确认', { type: 'warning' })
  try {
    const res = await api.delete('/kg/entities', { params: { entity_type: e.type, name: e.name } })
    if (res.ok === true) {
      ElMessage.success('已删除')
      loadTerms()
    } else {
      ElMessage.error(res.error || '删除失败')
    }
  } catch (err) {
    ElMessage.error('删除失败：' + (err?.message || '网络错误'))
  }
}

// 顶部科普介绍默认展开
const introExpanded = ref(true)

const legends = [
  { name: '法律', color: '#3b82f6', desc: '国家的法律文本' },
  { name: '条文', color: '#22c55e', desc: '法律的具体条款' },
  { name: '案例', color: '#0369A1', desc: '法院判过的案件' },
  { name: '法律概念', color: '#8b5cf6', desc: '法律术语的释义' },
  { name: '权利义务', color: '#06b6d4', desc: '法定权利和义务' },
  { name: '违法行为', color: '#ef4444', desc: '法律禁止的行为' },
  { name: '法律责任', color: '#f97316', desc: '违法的后果' }
]

// ① 内嵌示例：一条普通人都能读懂的推理链
const examplePath = [
  { name: '劳动合同法', type: '法律', color: '#3b82f6', relation: '规定了' },
  { name: '第47条 经济补偿', type: '条文', color: '#22c55e', relation: '定义了' },
  { name: '经济补偿金', type: '法律概念', color: '#8b5cf6', relation: '对应责任' },
  { name: '支付经济补偿金', type: '法律责任', color: '#f97316' }
]

const kgStats = ref([
  { label: 'Statute 法律', value: 8 },
  { label: 'Article 条文', value: 955 },
  { label: 'Case 案例', value: 71 },
  { label: 'LegalConcept', value: 27 },
  { label: 'RightObligation', value: 48 },
  { label: 'IllegalAct', value: 20 },
  { label: 'LegalLiability', value: 71 },
  { label: '关系总数', value: '283' }
])

const allNodes = [
  { id: '劳动法', category: 0, symbolSize: 40 },
  { id: '劳动合同法', category: 0, symbolSize: 45 },
  { id: '社会保险法', category: 0, symbolSize: 30 },
  { id: '工伤保险条例', category: 0, symbolSize: 28 },
  { id: '第47条\n经济补偿', category: 1, symbolSize: 18 },
  { id: '第87条\n违法解除赔偿', category: 1, symbolSize: 18 },
  { id: '第38条\n被迫解除', category: 1, symbolSize: 18 },
  { id: '第44条\n加班工资', category: 1, symbolSize: 18 },
  { id: '第19条\n试用期', category: 1, symbolSize: 16 },
  { id: '第23条\n竞业限制', category: 1, symbolSize: 16 },
  { id: '违法解除案', category: 2, symbolSize: 14 },
  { id: '工伤赔偿案', category: 2, symbolSize: 14 },
  { id: '拖欠工资案', category: 2, symbolSize: 14 },
  { id: '劳动关系', category: 3, symbolSize: 20 },
  { id: '经济补偿金', category: 3, symbolSize: 20 },
  { id: '竞业限制', category: 3, symbolSize: 18 },
  { id: '试用期', category: 3, symbolSize: 18 },
  { id: '工伤', category: 3, symbolSize: 18 },
  { id: '取得报酬权', category: 4, symbolSize: 14 },
  { id: '支付工资义务', category: 4, symbolSize: 14 },
  { id: '违法解除', category: 5, symbolSize: 16 },
  { id: '拖欠工资', category: 5, symbolSize: 16 },
  { id: '强迫劳动', category: 5, symbolSize: 14 },
  { id: '支付赔偿金', category: 6, symbolSize: 16 },
  { id: '支付双倍工资', category: 6, symbolSize: 14 },
  { id: '行政处罚', category: 6, symbolSize: 14 }
]

const allLinks = [
  { source: '劳动法', target: '第44条\n加班工资' },
  { source: '劳动合同法', target: '第47条\n经济补偿' },
  { source: '劳动合同法', target: '第87条\n违法解除赔偿' },
  { source: '劳动合同法', target: '第38条\n被迫解除' },
  { source: '劳动合同法', target: '第19条\n试用期' },
  { source: '劳动合同法', target: '第23条\n竞业限制' },
  { source: '社会保险法', target: '社保第16条\n养老保险' },
  { source: '工伤保险条例', target: '工伤第14条\n认定条件' },
  { source: '第47条\n经济补偿', target: '经济补偿金' },
  { source: '第87条\n违法解除赔偿', target: '违法解除' },
  { source: '第23条\n竞业限制', target: '竞业限制' },
  { source: '第19条\n试用期', target: '试用期' },
  { source: '第38条\n被迫解除', target: '劳动关系' },
  { source: '违法解除', target: '支付赔偿金' },
  { source: '拖欠工资', target: '支付双倍工资' },
  { source: '强迫劳动', target: '行政处罚' },
  { source: '违法解除', target: '违法解除案' },
  { source: '工伤', target: '工伤赔偿案' },
  { source: '拖欠工资', target: '拖欠工资案' }
]

// Build filtered graph data: concept (categories 3,4) and act (categories 5,6)
function filterGraph(cats) {
  const nodeIds = new Set(allNodes.filter(n => cats.includes(n.category)).map(n => n.id))
  return {
    nodes: allNodes.filter(n => nodeIds.has(n.id)),
    links: allLinks.filter(l => nodeIds.has(l.source) && nodeIds.has(l.target))
  }
}

const graphData = {
  all: { nodes: allNodes, links: allLinks },
  concept: filterGraph([3, 4]),
  act: filterGraph([5, 6])
}

const categories = [
  { name: '法律', itemStyle: { color: '#3b82f6' } },
  { name: '条文', itemStyle: { color: '#22c55e' } },
  { name: '案例', itemStyle: { color: '#0369A1' } },
  { name: '法律概念', itemStyle: { color: '#8b5cf6' } },
  { name: '权义', itemStyle: { color: '#06b6d4' } },
  { name: '违法行为', itemStyle: { color: '#ef4444' } },
  { name: '法律责任', itemStyle: { color: '#f97316' } }
]

function renderChart() {
  if (!chartDom.value) return
  if (!chart) chart = echarts.init(chartDom.value, 'light')
  const r = chartDom.value.getBoundingClientRect()
  if (r.width === 0 || r.height === 0) return
  const data = graphData[viewMode.value] || graphData.all
  chart.setOption({
    tooltip: {
      formatter: p => p.dataType === 'edge'
        ? `${p.data.source} → ${p.data.target}`
        : `<b>${p.name}</b><br/>${categories[p.data.category]?.name || ''}`
    },
    series: [{
      type: 'graph', layout: 'force',
      data: data.nodes, links: data.links,
      categories, roam: true, draggable: true,
      force: { repulsion: 300, edgeLength: [80, 200], gravity: 0.1 },
      label: { show: true, fontSize: 10, color: '#334155', formatter: p => p.name.split('\n')[0] },
      lineStyle: { color: '#cbd5e1', curveness: 0.2, opacity: 0.6 },
      emphasis: { focus: 'adjacency', lineStyle: { width: 3 } }
    }]
  })
}

// Re-render when viewMode changes
watch(viewMode, () => {
  if (chart) { chart.dispose(); chart = null }
  nextTick(renderChart)
})

onMounted(() => {
  nextTick(renderChart)
  window.addEventListener('resize', () => chart?.resize())
  if (canEdit) loadTerms()
})

onActivated(() => {
  nextTick(() => {
    if (chart) { chart.dispose(); chart = null }
    renderChart()
  })
})

onDeactivated(() => {
  if (chart) { chart.dispose(); chart = null }
})
</script>

<style scoped>
.kg-page { max-width: 1300px; margin: 0 auto; padding-bottom: 40px; }
.page-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px; }
.page-title { margin: 0; font-size: 24px; font-weight: 700; color: var(--text-primary); }
.page-subtitle { margin: 4px 0 0; font-size: 13px; color: var(--text-muted); }

/* 顶部科普介绍卡 */
.kg-intro {
  background: linear-gradient(135deg, #F0F9FF 0%, #F8FAFC 60%, #FFF 100%);
  border: 1px solid #BAE6FD;
  border-radius: 14px;
  margin-bottom: 24px;
  overflow: hidden;
}
.intro-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 20px;
  cursor: pointer; user-select: none;
}
.intro-head h3 { margin: 0; font-size: 15px; font-weight: 700; color: #0369A1; }
.intro-toggle { font-size: 12px; color: #7C8AA0; white-space: nowrap; }
.intro-head:hover { background: rgba(186, 230, 253, 0.25); }
.kg-intro.collapsed { background: #F8FAFC; }
.intro-body { padding: 0 20px 16px; border-top: 1px dashed #D7EDFA; }
.intro-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px 24px; padding-top: 14px; }
.intro-block b { display: block; font-size: 13px; color: #1E293B; margin-bottom: 6px; }
.intro-block p { margin: 0; font-size: 12.5px; color: #475569; line-height: 1.7; }
.c-blue { color: #2563EB; } .c-green { color: #16A34A; } .c-cyan { color: #0369A1; }
.c-purple { color: #7C3AED; } .c-sky { color: #0891B2; } .c-red { color: #DC2626; }
.c-orange { color: #EA580C; }

.kg-layout { display: grid; grid-template-columns: 1fr 280px; gap: 24px; align-items: start; }
.graph-panel { background: #FFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 20px 20px 14px; }
.graph-panel-head { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; margin-bottom: 12px; }
.graph-panel-head h3 { margin: 0; font-size: 15px; font-weight: 700; color: #1E293B; }
.graph-hint { font-size: 11.5px; color: #94A3B8; }
.chart-container { width: 100%; height: 620px; }

.side { display: flex; flex-direction: column; gap: 24px; }
.panel { background: #FFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 20px 22px; }
.panel-head { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid #F1F5F9; }
.panel-index { font-size: 11px; font-weight: 700; color: #0369A1; padding: 2px 8px; border: 1px solid #BAE6FD; border-radius: 6px; background: #F0F9FF; font-family: 'Noto Serif SC', serif; }
.panel-head h3 { margin: 0; font-size: 15px; font-weight: 700; color: #1E293B; }

.legend-list { display: grid; grid-template-columns: 1fr 1fr; gap: 12px 16px; }
.legend-item { display: flex; align-items: flex-start; gap: 10px; font-size: 13px; color: #475569; }
.dot { width: 12px; height: 12px; border-radius: 50%; display: inline-block; flex-shrink: 0; margin-top: 3px; }
.legend-text { display: flex; flex-direction: column; gap: 2px; }
.legend-name { letter-spacing: 0.5px; font-weight: 600; color: #334155; }
.legend-desc { font-size: 12px; color: #94A3B8; line-height: 1.5; }

.kg-stats { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.kg-stat {
  display: flex; flex-direction: column; gap: 4px;
  padding: 12px 14px;
  background: #F8FAFC; border: 1px solid #F1F5F9;
  border-radius: 10px; transition: all 0.2s;
}
.kg-stat:hover { background: #F1F5F9; }
.kg-stat-label { font-size: 11.5px; color: #94A3B8; }
.kg-stat b { color: #0369A1; font-size: 18px; font-family: 'Space Grotesk', sans-serif; }

/* 实体维护面板（全宽） */
.entity-panel {
  background: #FFF; border: 1px solid #E2E8F0; border-radius: 14px;
  padding: 20px 22px; margin-top: 24px;
}
.entity-panel .panel-head { flex-wrap: wrap; }
.entity-hint { font-size: 11.5px; color: #94A3B8; }
.entity-toolbar { display: flex; gap: 8px; margin-left: auto; }
.entity-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(270px, 1fr));
  gap: 10px; max-height: 420px; overflow-y: auto;
}
.entity-card {
  display: flex; align-items: center; justify-content: space-between; gap: 10px;
  padding: 12px 14px; border: 1px solid #F1F5F9; border-radius: 10px;
  background: #F8FAFC; transition: all 0.15s;
}
.entity-card:hover { background: #F0F9FF; border-color: #BAE6FD; }
.entity-info { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
.entity-name { font-size: 13.5px; font-weight: 600; color: #334155; }
.entity-desc {
  font-size: 11.5px; color: #94A3B8; white-space: nowrap; overflow: hidden;
  text-overflow: ellipsis;
}
.empty-state { padding: 16px 0; text-align: center; font-size: 12.5px; color: #94A3B8; }
.grid-full { grid-column: 1 / -1; }

/* ① 内嵌的示例链 */
.intro-block.full { grid-column: 1 / -1; }
.intro-block .example-hint-inline { margin: 12px 0 0; font-size: 12px; color: #94A3B8; }
.example-flow { display: flex; flex-wrap: wrap; align-items: center; margin-top: 8px; }
.flow-node { display: flex; align-items: center; gap: 10px; padding: 10px 14px; background: #FFF; border: 1px solid #E2E8F0; border-radius: 10px; }
.path-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.path-text { display: flex; flex-direction: column; gap: 1px; }
.path-text b { font-size: 13px; color: #334155; font-weight: 600; }
.path-type { font-size: 11px; color: #94A3B8; }
.flow-arrow { display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 0 6px; width: 60px; flex-shrink: 0; }
.flow-arrow-label { font-size: 11px; color: #0369A1; background: #F0F9FF; border: 1px solid #BAE6FD; border-radius: 6px; padding: 1px 8px; white-space: nowrap; }
.flow-arrow-line { width: 100%; height: 2px; background: #CBD5E1; border-radius: 1px; position: relative; }
.flow-arrow-line::after { content: ''; position: absolute; right: -1px; top: -3px; border-left: 8px solid #CBD5E1; border-top: 4px solid transparent; border-bottom: 4px solid transparent; }

@media (max-width: 900px) {
  .kg-layout { grid-template-columns: 1fr; }
  .intro-grid { grid-template-columns: 1fr; }
}
</style>
