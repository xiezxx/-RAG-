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

    <div class="kg-layout">
      <!-- 主图 -->
      <div class="graph-panel">
        <div ref="chartDom" class="chart-container"></div>
      </div>

      <!-- 侧栏 -->
      <div class="side">
        <div class="panel">
          <div class="panel-head"><span class="panel-index">壹</span><h3>图例</h3></div>
          <div class="legend-list">
            <div class="legend-item" v-for="lg in legends" :key="lg.name">
              <span class="dot" :style="{ background: lg.color }"></span>
              <span class="legend-name">{{ lg.name }}</span>
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
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onActivated, onDeactivated, nextTick } from 'vue'
import * as echarts from 'echarts'

const viewMode = ref('all')
const chartDom = ref(null)
let chart = null

const legends = [
  { name: '法律(Statute)', color: '#3b82f6' },
  { name: '条文(Article)', color: '#22c55e' },
  { name: '案例(Case)', color: '#0369A1' },
  { name: '法律概念', color: '#8b5cf6' },
  { name: '权利义务', color: '#06b6d4' },
  { name: '违法行为', color: '#ef4444' },
  { name: '法律责任', color: '#f97316' }
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
    legend: [{
      data: categories.map(c => c.name),
      orient: 'vertical', right: 10, top: 20,
      textStyle: { fontSize: 11 }
    }],
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

.kg-layout { display: grid; grid-template-columns: 1fr 280px; gap: 24px; align-items: start; }
.graph-panel { background: #FFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 20px; }
.chart-container { width: 100%; height: 540px; }

.side { display: flex; flex-direction: column; gap: 24px; }
.panel { background: #FFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 20px 22px; }
.panel-head { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid #F1F5F9; }
.panel-index { font-size: 11px; font-weight: 700; color: #0369A1; padding: 2px 8px; border: 1px solid #BAE6FD; border-radius: 6px; background: #F0F9FF; font-family: 'Noto Serif SC', serif; }
.panel-head h3 { margin: 0; font-size: 15px; font-weight: 700; color: #1E293B; }

.legend-list { display: flex; flex-direction: column; gap: 10px; }
.legend-item { display: flex; align-items: center; gap: 10px; font-size: 13px; color: #475569; }
.dot { width: 12px; height: 12px; border-radius: 50%; display: inline-block; flex-shrink: 0; }
.legend-name { letter-spacing: 0.5px; }

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

@media (max-width: 900px) {
  .kg-layout { grid-template-columns: 1fr; }
}
</style>
