<template>
  <div class="chat-page">
    <aside class="chat-sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-header">
        <el-button v-if="!sidebarCollapsed" type="primary" class="new-chat-btn" @click="newChat" :disabled="!messages.length">
          <el-icon><Plus /></el-icon> 新对话
        </el-button>
        <el-button text class="toggle-btn" @click="sidebarCollapsed = !sidebarCollapsed">
          <el-icon><DArrowLeft v-if="!sidebarCollapsed" /><DArrowRight v-else /></el-icon>
        </el-button>
      </div>
      <div class="conversation-list" v-show="!sidebarCollapsed">
        <div v-for="group in conversations" :key="group.date" class="conv-group">
          <div class="conv-date">{{ group.date }}</div>
          <div v-for="conv in group.items" :key="conv.id"
               :class="['conv-item', { active: conv.id === activeConvId }]"
               @click="loadConversation(conv)">
            <el-icon class="conv-item-icon"><ChatDotRound /></el-icon>
            <span class="conv-title">{{ conv.title }}</span>
          </div>
        </div>
        <div v-if="!conversations.length" class="no-conv">
          <svg class="no-conv-icon" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
          <p>暂无对话记录</p>
        </div>
      </div>
    </aside>

    <main class="chat-main">
      <div class="chat-messages" ref="msgBox" @scroll="onMsgScroll">
        <div v-if="messages.length === 0" class="welcome">
          <div class="welcome-glow"></div>
          <div class="welcome-icon-wrap">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 3v18" /><path d="M8 21h8" /><path d="M5 7h14" />
              <path d="M5 7l-3.5 6a3 3 0 0 0 6 0L5 7z" /><path d="M19 7l-3.5 6a3 3 0 0 0 6 0L19 7z" />
            </svg>
          </div>
          <h2>劳动法智能问答</h2>
          <p>基于 8 部法律、720 条条文、70 个案例<br/>为您提供有法可依的专业回答</p>
          <div class="feature-bento">
            <div class="fb-item" v-for="f in features" :key="f.label">
              <span class="fb-dot" :style="{ background: f.color }"></span><span class="fb-label">{{ f.label }}</span>
            </div>
          </div>
        </div>

        <div v-for="(msg, i) in messages" :key="i" :class="['msg', msg.role]">
          <div class="msg-avatar">
            <svg v-if="msg.role === 'user'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v18"/><path d="M8 21h8"/><path d="M5 7h14"/><path d="M5 7l-3.5 6a3 3 0 0 0 6 0L5 7z"/><path d="M19 7l-3.5 6a3 3 0 0 0 6 0L19 7z"/></svg>
          </div>
          <div class="msg-body">
            <div v-if="msg.role === 'user'" class="msg-bubble user-bubble">{{ msg.content }}</div>
            <div v-else class="msg-bubble ai-bubble">
              <div class="answer-md" v-html="renderMarkdown(msg.content)" />
              <div v-if="msg.sources?.length" class="source-section">
                <div class="source-divider"></div>
                <p class="source-title">📚 参考来源</p>
                <div class="source-cards">
                  <div v-for="(s,j) in msg.sources" :key="j" class="source-card" :class="'source-'+s.type">
                    <div class="source-header">
                      <el-tag :type="sourceTypeTag(s.type)" size="small" effect="dark" round>{{ sourceTypeLabel(s.type) }}</el-tag>
                      <el-tag v-if="s.status" size="small" :type="statusTagType(s.status)" effect="plain" round>{{ s.status }}</el-tag>
                    </div>
                    <div class="source-title-text">{{ s.title }}</div>
                    <div class="source-snippet" v-if="s.snippet">{{ s.snippet.substring(0,150) }}...</div>
                    <button v-if="s.status === '已被修订' && s.article && (s.law || s.title !== '未知来源')"
                            class="source-diff-btn" @click="openVersionDiff(s)" title="查看该条文修订前后的内容变化">📜 修订对比</button>
                  </div>
                </div>
              </div>
              <div v-if="msg.content?.includes('无法找到明确依据')" class="confidence-warn">⚠️ 检索证据不足，建议咨询专业律师</div>
              <div v-else-if="msg.sources?.length >= 2" class="confidence-ok">✅ 基于 {{ msg.sources.length }} 个法律来源，可信度较高</div>
              <div class="action-bar">
                <button class="action-btn" @click="copyMessage(msg)" :class="{copied:msg._copied}">
                  <svg v-if="!msg._copied" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                  <svg v-else width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                  <span>{{ msg._copied?'已复制':'复制' }}</span>
                </button>
                <button class="action-btn" :class="{active:msg._speaking}" @click="toggleSpeak(msg)">
                  <svg v-if="!msg._speaking" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>
                  <svg v-else width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="20" rx="4"/><rect x="7" y="7" width="10" height="10" rx="2"/></svg>
                  <span>{{ msg._speaking?'停止':'语音' }}</span>
                </button>
                <button class="action-btn" v-if="msg._mine !== false" @click="rateMsg(msg,1)" :class="{active:msg._rating===1}">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="transform:scaleY(-1)"><path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3H10z"/></svg>
                </button>
                <button class="action-btn" v-if="msg._mine !== false" @click="rateMsg(msg,5)" :class="{active:msg._rating===5}">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14z"/></svg>
                </button>
                <button class="action-btn" v-if="msg.trace" :class="{active:msg._showTrace}" @click="toggleTrace(msg)" title="查看本次回答的检索过程">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>
                  <span>检索过程</span>
                </button>
              </div>

              <!-- ── 检索过程可视化面板 ── -->
              <div v-if="msg._showTrace && msg.trace" class="trace-panel">
                <div class="trace-head">
                  <span class="trace-title">🔍 检索过程</span>
                  <span class="trace-chip mode">{{ modeLabel(msg.trace.mode) }}</span>
                  <span class="trace-chip">总耗时 {{ msg.trace.timings?.total_ms }}ms</span>
                  <span class="trace-chip" v-if="msg.trace.timings?.rewrite_ms != null">查询改写 {{ msg.trace.timings.rewrite_ms }}ms</span>
                </div>
                <div class="trace-meta">
                  <div class="trace-row"><span class="k">原始问题</span><span class="v">{{ msg.trace.original_question }}</span></div>
                  <div class="trace-row"><span class="k">改写查询</span><span class="v">{{ msg.trace.query }}</span></div>
                  <div class="trace-row"><span class="k">时间参考</span><span class="v">{{ msg.trace.reference_date || '未指定 → 现行有效优先' }}</span></div>
                  <div class="trace-row"><span class="k">策略权重</span><span class="v">
                    <span class="w-chip bm25">BM25 ×{{ msg.trace.strategy?.bm25_weight }}</span>
                    <span class="w-chip vec">向量 ×{{ msg.trace.strategy?.vector_weight }}</span>
                    <span class="w-chip kg">图谱 ×{{ msg.trace.strategy?.graph_weight }}</span>
                  </span></div>
                </div>
                <div class="trace-channels">
                  <div v-for="ch in msg.trace.channels" :key="ch.name" class="tc-card" :class="{off:!ch.enabled}">
                    <div class="tc-head">
                      <span class="tc-dot" :style="{background:channelColor(ch.name)}"></span>
                      <b>{{ ch.label }}</b>
                      <span class="tc-w">权重 {{ ch.weight }}</span>
                      <span class="tc-lat">{{ ch.latency_ms }}ms</span>
                    </div>
                    <div class="tc-body" v-if="ch.enabled">
                      <div v-for="h in ch.hits" :key="h.rank" class="tc-hit">
                        <span class="tc-rank">#{{ h.rank }}</span>
                        <span class="tc-title" :title="h.title">{{ h.title }}</span>
                        <span class="tc-score">{{ h.score }}</span>
                      </div>
                    </div>
                    <div class="tc-empty" v-else>未启用</div>
                  </div>
                </div>
                <div class="trace-fusion">
                  <div class="tf-title">RRF 融合排序（k = {{ msg.trace.fusion?.k }}）<span class="tf-note">「✓」表示通过时效过滤、进入最终上下文</span></div>
                  <div class="tf-row head"><span>#</span><span>文档</span><span>来源通道</span><span>RRF分</span><span>时效</span><span>最终</span></div>
                  <div v-for="r in msg.trace.fusion?.rows" :key="r.rank" class="tf-row" :class="{cut:!r.in_final}">
                    <span class="tf-rank">{{ r.rank }}</span>
                    <span class="tf-doc" :title="r.title">{{ r.title }}</span>
                    <span class="tf-ch"><el-tag v-for="(pos,name) in r.channels" :key="name" size="small" effect="plain" round :style="{color:channelColor(name),borderColor:channelColor(name)+'66'}">{{ channelLabel(name) }}#{{ pos }}</el-tag></span>
                    <span class="tf-rrf">{{ r.rrf_score }}</span>
                    <span class="tf-status"><el-tag v-if="r.status" size="small" :type="statusTagType(r.status)" effect="plain" round>{{ r.status }}</el-tag><span v-else>—</span></span>
                    <span class="tf-final"><span v-if="r.in_final" class="final-ok">✓ {{ r.final_rank }}</span><span v-else class="final-cut">✗</span></span>
                  </div>
                </div>
              </div>
            </div>
            <div v-if="msg.role==='user'" class="action-bar user-action">
              <button class="action-btn" @click="copyMessage(msg)" :class="{copied:msg._copied}">
                <svg v-if="!msg._copied" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
              </button>
            </div>
          </div>
        </div>

        <div v-if="thinking" class="msg assistant">
          <div class="msg-avatar">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v18"/><path d="M8 21h8"/><path d="M5 7h14"/><path d="M5 7l-3.5 6a3 3 0 0 0 6 0L5 7z"/><path d="M19 7l-3.5 6a3 3 0 0 0 6 0L19 7z"/></svg>
          </div>
          <div class="msg-body">
            <div class="thinking-bento"><span class="dot-flow"></span><span>检索分析中...</span></div>
          </div>
        </div>
      </div>

      <div class="chat-input">
        <div class="mode-row" v-if="isAdmin">
          <span class="mode-label">检索模式</span>
          <button v-for="m in modes" :key="m.value" class="mode-chip" :class="{on:mode===m.value}"
                  :disabled="thinking" :title="m.hint" @click="mode=m.value">{{ m.label }}</button>
          <span class="mode-hint">：切换模式可对比不同检索策略的效果（对应消融实验配置）</span>
        </div>
        <div class="input-row">
          <button class="tts-toggle" :class="{on:ttsEnabled}" @click="ttsEnabled=!ttsEnabled" :title="ttsEnabled?'关闭语音播报':'开启语音播报'">
            <svg v-if="ttsEnabled" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>
            <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><line x1="23" y1="9" x2="17" y2="15"/><line x1="17" y1="9" x2="23" y2="15"/></svg>
          </button>
          <textarea v-model="question" class="chat-textarea" placeholder="输入劳动法问题，Enter 发送"
                    @keydown.enter.exact.prevent="thinking?null:send()" :disabled="thinking"
                    rows="1" ref="textareaRef" @input="autoResize"></textarea>
          <button v-if="!thinking" class="send-btn" @click="send" :disabled="!question.trim()" title="发送">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><polyline points="19 12 12 19 5 12"/></svg>
          </button>
          <button v-else class="stop-btn" @click="stopThinking" title="停止生成">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><rect x="4" y="4" width="16" height="16" rx="2"/></svg>
          </button>
        </div>
        <div class="examples">
          <span class="examples-label">试试：</span>
          <el-tag v-for="e in examples" :key="e" @click="quickAsk(e)" class="example-tag" effect="plain" round size="small">{{ e }}</el-tag>
        </div>
      </div>
    </main>

    <!-- ── 法条修订对比抽屉（模块5 时效感知·法条版本管理）── -->
    <el-drawer v-model="versionDiff.visible" direction="rtl" size="760px" class="vd-drawer">
      <template #header>
        <div class="vd-head">
          <span class="vd-title">📜 法条修订对比</span>
          <span v-if="versionDiff.data" class="vd-sub">{{ versionDiff.data.law_name }} · {{ versionDiff.data.article }}</span>
        </div>
      </template>
      <div v-loading="versionDiff.loading" class="vd-body">
        <template v-if="versionDiff.data">
          <div v-if="versionDiff.data.changed" class="vd-banner">⚠️ 该条文在本次修订中内容有变化，红色为删除、绿色为新增</div>
          <div v-else class="vd-banner ok">该条文修订前后内容一致，未发生变化</div>
          <div class="vd-cols">
            <div class="vd-col old">
              <div class="vd-col-head">
                <span class="vd-col-title">修订前版本</span>
                <el-tag type="warning" size="small" round>{{ versionDiff.data.old.status }}</el-tag>
              </div>
              <div class="vd-dates">
                公布 {{ versionDiff.data.old.publish_date || '—' }} · 施行 {{ versionDiff.data.old.effective_date || '—' }}
              </div>
              <div class="vd-text" v-html="versionDiff.oldHtml"></div>
            </div>
            <div class="vd-col new">
              <div class="vd-col-head">
                <span class="vd-col-title">修订后版本（当前有效）</span>
                <el-tag type="success" size="small" round>{{ versionDiff.data.new.status }}</el-tag>
              </div>
              <div class="vd-dates">
                公布 {{ versionDiff.data.new.publish_date || '—' }} · 施行 {{ versionDiff.data.new.effective_date || '—' }}
              </div>
              <div class="vd-text" v-html="versionDiff.newHtml"></div>
            </div>
          </div>
          <div class="vd-tip">适用提示：当前有效版本以修订后内容为准；如查询修订前时间段的法律问题，系统将按历史版本作答。</div>
        </template>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, onBeforeUnmount, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { marked } from 'marked'
import { Plus, ChatDotRound, DArrowLeft, DArrowRight } from '@element-plus/icons-vue'
import api from '../api'

const role = localStorage.getItem('role') || 'USER'
const isAdmin = computed(() => role === 'ADMIN') // 检索模式切换仅管理员可见（检索过程可视化所有用户可见）

const question = ref(''), thinking = ref(false), messages = ref([])
const msgBox = ref(null), textareaRef = ref(null)
const sidebarCollapsed = ref(false), conversations = ref([]), activeConvId = ref(null)
const ttsEnabled = ref(true)
let abortController = null
let currentUtterance = null

// ── 检索模式切换（消融演示）──
const modes = [
  { value: 'full', label: '完整混合', hint: 'BM25 + 向量 + 图谱 + 时效 + 图谱扩展（默认）' },
  { value: 'bm25', label: '仅BM25', hint: '只走关键词检索（消融基线）' },
  { value: 'vector', label: '仅向量', hint: '只走语义向量检索' },
  { value: 'graph', label: '仅图谱', hint: '只走知识图谱关联检索' },
  { value: 'bm25+vector', label: 'BM25+向量', hint: '关键词 + 语义，无图谱' },
  { value: 'bm25+vector+kg', label: '混合·无时效', hint: '关键词 + 语义 + 图谱，关闭时效过滤（消融配置）' },
  { value: 'bm25+vector+kg+time', label: '混合·无扩展', hint: '完整混合但关闭图谱关系扩展' },
]
const mode = ref('full')
const modeLabels = {
  full: '完整混合', bm25: '仅 BM25', vector: '仅向量', graph: '仅图谱',
  'bm25+vector': 'BM25+向量', 'bm25+vector+kg': '混合·无时效', 'bm25+vector+kg+time': '混合·无扩展',
}
function modeLabel(name) { return modeLabels[name] || name }
function channelColor(name) { return { bm25: '#3B82F6', vector: '#10B981', graph: '#8B5CF6' }[name] || '#64748B' }
function channelLabel(name) { return { bm25: 'BM25', vector: '向量', graph: '图谱' }[name] || name }

const examples = ['公司无故辞退员工怎么维权？','工伤认定的标准和流程是什么？','加班费的计算基数怎么确定？','试用期最长可以约定多久？','拖欠工资可以要求什么赔偿？','孕期被公司降薪调岗是否违法？']
const features = [{icon:'', label:'BM25 关键词', color:'#3B82F6'},{icon:'', label:'向量语义', color:'#10B981'},{icon:'', label:'知识图谱', color:'#8B5CF6'},{icon:'', label:'时效感知', color:'#F59E0B'}]

function toggleTrace(msg) { msg._showTrace = !msg._showTrace }

// ── 法条修订对比（模块5 时效感知·法条版本管理）──
const versionDiff = ref({visible:false, loading:false, data:null, oldHtml:'', newHtml:''})
function escHtml(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}
// 字符级 LCS 差异渲染：修订前标红删除线，修订后标绿新增
function diffRender(oldText, newText){
  const a=[...String(oldText||'')], b=[...String(newText||'')], n=a.length, m=b.length
  const dp=Array.from({length:n+1},()=>new Array(m+1).fill(0))
  for(let i=n-1;i>=0;i--)for(let j=m-1;j>=0;j--)dp[i][j]=a[i]===b[j]?dp[i+1][j+1]+1:Math.max(dp[i+1][j],dp[i][j+1])
  let oldHtml='',newHtml='',i=0,j=0
  while(i<n&&j<m){
    if(a[i]===b[j]){oldHtml+=escHtml(a[i]);newHtml+=escHtml(a[i]);i++;j++}
    else if(dp[i+1][j]>=dp[i][j+1]){oldHtml+='<del class="vd-del">'+escHtml(a[i])+'</del>';i++}
    else{newHtml+='<ins class="vd-ins">'+escHtml(b[j])+'</ins>';j++}
  }
  while(i<n){oldHtml+='<del class="vd-del">'+escHtml(a[i])+'</del>';i++}
  while(j<m){newHtml+='<ins class="vd-ins">'+escHtml(b[j])+'</ins>';j++}
  return {oldHtml,newHtml}
}
function openVersionDiff(s){
  const law = s.law || (s.title && s.title !== '未知来源' ? s.title : '')
  if(!law || !s.article){ElMessage.warning('该来源无法进行修订对比');return}
  versionDiff.value={visible:true, loading:true, data:null, oldHtml:'', newHtml:''}
  api.get('/version/compare',{params:{law, article:s.article}})
    .then(res=>{
      if(res?.code===200 && res.data){
        const d=diffRender(res.data.old.text, res.data.new.text)
        versionDiff.value.data=res.data
        versionDiff.value.oldHtml=d.oldHtml
        versionDiff.value.newHtml=d.newHtml
      }else{
        ElMessage.info(res?.message||'暂无修订对比数据')
        versionDiff.value.visible=false
      }
    })
    .catch(()=>{ElMessage.error('修订对比加载失败');versionDiff.value.visible=false})
    .finally(()=>{versionDiff.value.loading=false})
}
function copyMessage(msg) {
  const div = document.createElement('div'); div.innerHTML = renderMarkdown(msg.content)
  const txt = div.textContent||div.innerText||''
  navigator.clipboard.writeText(txt).then(()=>{msg._copied=true;ElMessage.success('已复制');setTimeout(()=>msg._copied=false,2000)}).catch(()=>ElMessage.error('复制失败'))
}
async function rateMsg(msg,rating) {
  if(msg._rating===rating){msg._rating=0;return}
  msg._rating=rating
  try{await api.post('/eval/feedback',{chatId:msg._chatId,rating,comment:''});ElMessage.success(rating===5?'感谢认可！':'感谢反馈')}catch{ElMessage.error('提交失败')}
}

async function loadConversations() {
  try{const res=await api.get('/eval/history',{params:{limit:100}});if(res.code!==200||!res.data?.length)return
    const groups={}
    for(const h of res.data){const date=h.createdAt?.split(' ')[0]||h.createdAt?.substring(0,10)||'未知日期';if(!groups[date])groups[date]=[];groups[date].push({id:h.id,title:(h.question||'新对话').substring(0,40),question:h.question,answer:h.answer,sources:h.sources,rating:h.rating,createdAt:h.createdAt,mine:h.mine})}
    conversations.value=Object.entries(groups).map(([date,items])=>({date,items})).sort((a,b)=>b.date.localeCompare(a.date))
  }catch(e){console.warn('加载失败',e)}
}
function loadConversation(conv){activeConvId.value=conv.id;messages.value=[{role:'user',content:conv.question},{role:'assistant',content:conv.answer,sources:conv.sources?tryParse(conv.sources):[],_mine:conv.mine,_showTrace:false}];nextTick(()=>scrollBottom())}
function tryParse(s){try{return JSON.parse(s.replace(/SourceItem\(/g,'{"type":').replace(/type=/g,'"type":').replace(/title=/g,'"title":').replace(/snippet=/g,'"snippet":').replace(/\)/g,'}'))}catch{return[]}}
function newChat(){messages.value=[];activeConvId.value=null;question.value=''}
function quickAsk(text){question.value=text;send()}
function autoResize(){requestAnimationFrame(()=>{const el=textareaRef.value;if(!el)return;el.style.height='auto';el.style.height=Math.min(el.scrollHeight,200)+'px'})}

async function send(){
  if(thinking.value)return
  const q=question.value.trim();if(!q)return
  messages.value.push({role:'user',content:q});question.value='';thinking.value=true
  userScrolledUp.value=false;abortController=new AbortController();await nextTick();scrollBottom()

  // 流式 SSE 请求
  const token = localStorage.getItem('token')
  const history = messages.value.slice(-8, -1).map(m => ({ role: m.role, content: m.content }))

  try {
    // 直连 Spring Boot 避免 webpack 代理缓冲导致 SSE 失效
    const streamUrl = window.location.hostname === 'localhost'
      ? 'http://localhost:8089/api/chat/ask/stream'
      : '/api/chat/ask/stream'
    const response = await fetch(streamUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : ''
      },
      body: JSON.stringify({ question: q, history, mode: isAdmin.value ? mode.value : 'full' }),
      signal: abortController.signal
    })

    if (!response.ok) {
      const errText = await response.text()
      messages.value.push({role:'assistant',content:'抱歉：' + (errText || '服务异常')})
      return
    }

    // 创建助手消息占位（_showTrace 显式初始化，保证响应式）
    const msgIdx = messages.value.length
    messages.value.push({role:'assistant',content:'',sources:[],_showTrace:false})

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''  // 保留未完成的行

      for (const rawLine of lines) {
        // Spring 代理 println 在 Windows 上会把行尾写成 \r\n，剥掉 \r 再判断
        const line = rawLine.endsWith('\r') ? rawLine.slice(0, -1) : rawLine
        if (!line.startsWith('data: ') || line === 'data: [DONE]') continue
        const payload = line.substring(6)
        try {
          const obj = JSON.parse(payload)
          if (obj.__sources__) {
            // 来源信息
            messages.value[msgIdx].sources = obj.__sources__.map(s => ({...s, status: s.status || ''}))
          } else if (obj.__trace__) {
            // 检索过程明细（可视化面板数据）
            messages.value[msgIdx].trace = obj.__trace__
          } else if (typeof obj === 'string') {
            // 文本 token，追加到消息内容
            messages.value[msgIdx].content += obj
          }
        } catch {
          // 纯文本 token（未 JSON 编码）
          messages.value[msgIdx].content += payload
        }
        if (!userScrolledUp.value) scrollBottom()
      }
    }

    // 流结束后自动播报
    const finalAnswer = messages.value[msgIdx].content
    if (window.speakAssistantText && finalAnswer) window.speakAssistantText(finalAnswer)
  }
  catch(e){
    const isCancel = e?.name === 'AbortError' || abortController?.signal?.aborted
    messages.value.push({role:'assistant',content:isCancel?'⏹ 已停止生成':'网络错误，请确保后端服务已启动。'})
  }
  finally{
    thinking.value=false;abortController=null
    await nextTick();scrollBottom()
    setTimeout(loadConversations,500)
  }
}
function stopThinking(){if(abortController){abortController.abort();abortController=null}}
const userScrolledUp = ref(false)
function scrollBottom(){if(msgBox.value){msgBox.value.scrollTop=msgBox.value.scrollHeight;userScrolledUp.value=false}}
function onMsgScroll(){const el=msgBox.value;if(!el)return;userScrolledUp.value=el.scrollHeight-el.scrollTop-el.clientHeight>80}

marked.setOptions({breaks:true,gfm:true})
function renderMarkdown(t){if(!t)return'';return marked.parse(t.replace(/<[^>]*>/g,''))}
function sourceTypeTag(t){const m={statute:'success',interpretation:'primary',case:'warning',graph_article:'success',graph_case:'warning'};return m[t]||'info'}
function sourceTypeLabel(t){const m={statute:'法条',interpretation:'司法解释',case:'案例',graph_article:'关联法条',graph_case:'相似案例'};return m[t]||'资料'}
function statusTagType(s){const m={'现行有效':'success','已被修订':'warning','已废止':'danger','尚未生效':'info'};return m[s]||'info'}

// ── TTS 语音播报 ──
function stripMarkdown(text) {
  return text
    .replace(/<[^>]*>/g, '')           // strip HTML
    .replace(/[#*_~`>\[\]|\\]/g, '')   // strip markdown syntax
    .replace(/●|🟢|🔴|🟡|🔵|📜|⚖️|📝|🔗|✅|⚠️/g, '')
    .replace(/\n{2,}/g, '。')          // double newlines → period
    .replace(/\n/g, '，')              // single newline → comma
    .replace(/\s+/g, ' ')              // collapse whitespace
    .trim()
}

function getChineseVoice() {
  return new Promise((resolve) => {
    const voices = speechSynthesis.getVoices()
    // Prefer a good zh-CN voice
    const preferred = voices.find(v => v.lang === 'zh-CN' && v.name.includes('Tingting'))  // macOS
      || voices.find(v => v.lang === 'zh-CN' && v.name.includes('Xiaoxiao'))               // Windows
      || voices.find(v => v.lang === 'zh-CN')
      || voices.find(v => v.lang.startsWith('zh'))
    if (preferred) return resolve(preferred)
    // Wait for voices to load (some browsers load them async)
    speechSynthesis.addEventListener('voiceschanged', () => {
      const v = speechSynthesis.getVoices()
      const fallback = v.find(x => x.lang === 'zh-CN') || v.find(x => x.lang.startsWith('zh')) || v[0]
      resolve(fallback)
    }, { once: true })
  })
}

function speakText(text) {
  if (!text || !window.speechSynthesis) return
  stopSpeak()
  const clean = stripMarkdown(text)
  if (!clean) return
  getChineseVoice().then(voice => {
    const utterance = new SpeechSynthesisUtterance(clean)
    utterance.voice = voice
    utterance.lang = voice?.lang || 'zh-CN'
    utterance.rate = 0.95
    utterance.pitch = 1.05
    utterance.volume = 1
    currentUtterance = utterance
    speechSynthesis.speak(utterance)
  })
}

function stopSpeak() {
  if (currentUtterance) {
    speechSynthesis.cancel()
    currentUtterance = null
  }
}

function toggleSpeak(msg) {
  if (msg._speaking) {
    stopSpeak()
    msg._speaking = false
  } else {
    // Stop any other speaking message
    for (const m of messages.value) m._speaking = false
    msg._speaking = true
    speakText(msg.content)
    // Track when speech ends
    const checkEnd = setInterval(() => {
      if (!speechSynthesis.speaking && !speechSynthesis.pending) {
        msg._speaking = false
        currentUtterance = null
        clearInterval(checkEnd)
      }
    }, 200)
  }
}

// 全局 TTS 接口（供 VoiceAssistant 和 voice-speak 事件使用）
window.speakAssistantText = function(text) {
  if (!ttsEnabled.value) return
  // Find the last assistant message and mark it as speaking
  const lastMsg = messages.value[messages.value.length - 1]
  if (lastMsg && lastMsg.role === 'assistant') {
    lastMsg._speaking = true
    speakText(text)
    const checkEnd = setInterval(() => {
      if (!speechSynthesis.speaking && !speechSynthesis.pending) {
        lastMsg._speaking = false
        currentUtterance = null
        clearInterval(checkEnd)
      }
    }, 200)
  }
}
onMounted(() => {
  loadConversations()
  window.addEventListener('voice-question', onVoiceQuestion)
  window.addEventListener('voice-speak', onVoiceSpeak)
})

onBeforeUnmount(() => {
  window.removeEventListener('voice-question', onVoiceQuestion)
  window.removeEventListener('voice-speak', onVoiceSpeak)
  stopSpeak()
})

function onVoiceQuestion(e) {
  const text = e.detail?.text
  if (!text) return
  // 若不在问答页，先跳转
  if (window.location.pathname !== '/app/chat') {
    window.location.hash = '#/app/chat'
  }
  question.value = text
  send()
}

function onVoiceSpeak(e) {
  const text = e.detail?.text
  if (text && window.speakAssistantText) window.speakAssistantText(text)
}
</script>

<style scoped>
.chat-page{display:flex;flex:1;min-height:0;max-width:1200px;margin:0 auto;width:100%;height:100%}
.chat-sidebar{width:260px;min-width:260px;background:var(--bg-card);border-right:1px solid var(--border-color);display:flex;flex-direction:column;border-radius:18px 0 0 18px;overflow:hidden;transition:width .25s ease,min-width .25s ease;box-shadow:var(--shadow-xs)}
.chat-sidebar.collapsed{width:48px;min-width:48px}
.sidebar-header{padding:14px 12px;display:flex;gap:8px;align-items:center;border-bottom:1px solid var(--border-light);flex-shrink:0}
.new-chat-btn{flex:1;border-radius:10px;font-size:13px;font-weight:500}
.toggle-btn{padding:4px;min-width:32px;flex-shrink:0;color:var(--text-muted)}
.conversation-list{flex:1;overflow-y:auto;padding:8px;min-height:0}
.conv-group{margin-bottom:12px}
.conv-date{font-size:11px;color:var(--text-muted);padding:4px 10px;font-weight:600;letter-spacing:.5px}
.conv-item{display:flex;align-items:center;gap:8px;padding:9px 12px;border-radius:10px;cursor:pointer;font-size:13px;color:var(--text-secondary);transition:all .15s}
.conv-item:hover{background:#F1F5F9}
.conv-item.active{background:linear-gradient(135deg,#EFF6FF,#F0F9FF);color:#0369A1;font-weight:500;box-shadow:0 1px 4px rgba(3,105,161,.08)}
.conv-item-icon{font-size:15px;flex-shrink:0}
.conv-title{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1}
.no-conv{text-align:center;padding:40px 16px}
.no-conv-icon{margin-bottom:8px;opacity:.5;color:#94A3B8}
.no-conv p{color:var(--text-muted);font-size:13px;margin:0}

.chat-main{flex:1;display:flex;flex-direction:column;background:var(--bg-card);border-radius:0 18px 18px 0;overflow:hidden;box-shadow:var(--shadow-xs)}

.welcome{text-align:center;padding:80px 20px;position:relative;animation:scaleIn .6s cubic-bezier(.22,1,.36,1) both}
@keyframes scaleIn{from{opacity:0;transform:scale(.9)}to{opacity:1;transform:scale(1)}}
.welcome-glow{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:300px;height:300px;border-radius:50%;background:radial-gradient(circle,rgba(3,105,161,.06),transparent 70%);pointer-events:none}
.welcome-icon-wrap{width:88px;height:88px;display:inline-flex;align-items:center;justify-content:center;color:#0369A1;background:linear-gradient(135deg,#EFF6FF,#DBEAFE);border:2px solid rgba(3,105,161,.15);border-radius:24px;margin-bottom:24px;box-shadow:0 8px 32px rgba(3,105,161,.1);animation:iconGlow 3s ease-in-out infinite}
@keyframes iconGlow{0%,100%{box-shadow:0 8px 32px rgba(3,105,161,.1)}50%{box-shadow:0 12px 48px rgba(3,105,161,.2)}}
.welcome h2{font-size:28px;font-weight:700;color:var(--text-primary);margin:0 0 12px}
.welcome p{color:var(--text-secondary);margin:0 0 28px;line-height:1.8;font-size:15px}
.feature-bento{display:inline-flex;gap:10px;flex-wrap:wrap;justify-content:center}
.fb-item{display:flex;align-items:center;gap:6px;padding:10px 18px;background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;font-size:13px;color:var(--text-secondary);transition:all .3s}
.fb-item:hover{background:#FFF;border-color:#0369A1;transform:translateY(-2px);box-shadow:0 4px 16px rgba(0,0,0,.06)}
.fb-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.fb-label{font-weight:500}

.chat-messages{flex:1;overflow-y:auto;padding:24px 28px}
.msg{display:flex;margin-bottom:28px;animation:msgIn .4s cubic-bezier(.22,1,.36,1) both}
@keyframes msgIn{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:translateY(0)}}
.msg.user{flex-direction:row-reverse}
.msg-avatar{width:38px;height:38px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:17px;margin:0 12px;flex-shrink:0}
.msg.user .msg-avatar{background:linear-gradient(135deg,#1E293B,#0F172A);color:#94A3B8}
.msg.assistant .msg-avatar{background:linear-gradient(135deg,#EFF6FF,#DBEAFE);color:#0369A1}
.msg-body{max-width:82%;min-width:0}
.msg.user .msg-body{max-width:65%}
.msg-bubble{padding:16px 20px;border-radius:18px;line-height:1.85;font-size:15px}
.user-bubble{background:linear-gradient(135deg,#F1F5F9,#E2E8F0);color:var(--text-primary);border-bottom-right-radius:6px}
.ai-bubble{background:transparent;border:none;padding:0}

.thinking-bento{display:flex;align-items:center;gap:12px;padding:14px 20px;background:#F8FAFC;border:1px solid #E2E8F0;border-radius:14px;color:var(--text-muted);font-size:14px}
.dot-flow{width:8px;height:8px;border-radius:50%;background:linear-gradient(135deg,#0369A1,#38BDF8);animation:dotFlow 1.2s infinite}
@keyframes dotFlow{0%,100%{opacity:.2;transform:scale(.8)}50%{opacity:1;transform:scale(1.2)}}

.answer-md :deep(h2){color:var(--text-primary);margin:20px 0 8px;font-size:18px;font-weight:700}
.answer-md :deep(h3){color:var(--text-primary);margin:16px 0 6px;font-size:16px;font-weight:600}
.answer-md :deep(p){margin:8px 0}
.answer-md :deep(strong){color:var(--text-primary);font-weight:600}
.answer-md :deep(ul),.answer-md :deep(ol){padding-left:24px;margin:8px 0}
.answer-md :deep(li){margin:4px 0}
.answer-md :deep(blockquote){border-left:4px solid #0369A1;padding:10px 18px;margin:14px 0;background:linear-gradient(90deg,#EFF6FF,transparent);border-radius:0 10px 10px 0;color:#1E40AF}
.answer-md :deep(code){background:#F1F5F9;padding:2px 6px;border-radius:4px;font-size:.9em;font-family:'JetBrains Mono',monospace;color:#DC2626}
.answer-md :deep(pre){background:#1E293B;color:#E2E8F0;padding:18px 22px;border-radius:14px;overflow-x:auto;margin:14px 0;font-size:13px;line-height:1.7;border:1px solid rgba(255,255,255,.06)}
.answer-md :deep(pre code){background:transparent;padding:0;color:inherit}
.answer-md :deep(table){width:100%;border-collapse:collapse;margin:14px 0;font-size:14px}
.answer-md :deep(th){background:#F8FAFC;font-weight:600;padding:10px 14px;text-align:left;border:1px solid #E2E8F0}
.answer-md :deep(td){padding:8px 14px;border:1px solid #E2E8F0}

.source-section{margin-top:20px}
.source-divider{height:1px;background:linear-gradient(90deg,#E2E8F0,transparent);margin-bottom:12px}
.source-title{color:var(--text-secondary);font-size:13px;margin-bottom:10px;font-weight:500}
.source-cards{display:flex;flex-wrap:wrap;gap:8px}
.source-card{flex:0 0 calc(50% - 4px);padding:12px 14px;border-radius:12px;border:1px solid #E2E8F0;background:#FFF;transition:all .25s}
.source-card:hover{box-shadow:0 4px 16px rgba(0,0,0,.06);transform:translateY(-2px)}
.source-statute{border-left:4px solid #22C55E}
.source-interpretation{border-left:4px solid #3B82F6}
.source-case{border-left:4px solid #F59E0B}
.source-graph_article{border-left:4px solid #8B5CF6}
.source-graph_case{border-left:4px solid #EF4444}
.source-header{display:flex;gap:6px;margin-bottom:8px}
.source-title-text{font-size:13px;font-weight:500;color:#334155}
.source-snippet{font-size:12px;color:var(--text-muted);line-height:1.5}
.source-diff-btn{margin-top:8px;padding:3px 10px;border-radius:8px;border:1px solid #FCD34D;background:#FFFBEB;color:#92400E;font-size:12px;cursor:pointer;font-family:inherit;transition:all .15s}
.source-diff-btn:hover{background:#FEF3C7;border-color:#F59E0B}
.confidence-ok,.confidence-warn{margin-top:14px;padding:10px 14px;border-radius:12px;font-size:13px;font-weight:500}

/* ── 法条修订对比抽屉 ── */
.vd-drawer .el-drawer__header{margin-bottom:0;padding-bottom:14px;border-bottom:1px solid var(--border-color)}
.vd-head{display:flex;align-items:baseline;gap:10px}
.vd-title{font-size:16px;font-weight:700;color:#0F172A}
.vd-sub{font-size:13px;color:var(--text-muted)}
.vd-body{min-height:220px}
.vd-banner{margin:4px 0 14px;padding:10px 14px;border-radius:10px;background:#FEF3C7;border:1px solid #FCD34D;color:#92400E;font-size:13px}
.vd-banner.ok{background:#ECFDF5;border-color:#6EE7B7;color:#065F46}
.vd-cols{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.vd-col{border:1px solid #E2E8F0;border-radius:12px;overflow:hidden;background:#FFF}
.vd-col.old{background:#FFFBEB}
.vd-col.new{background:#F0FDF4}
.vd-col-head{display:flex;align-items:center;justify-content:space-between;padding:10px 14px;border-bottom:1px dashed #E2E8F0}
.vd-col-title{font-size:14px;font-weight:600;color:#334155}
.vd-dates{padding:8px 14px;font-size:12px;color:var(--text-muted);border-bottom:1px dashed #E2E8F0}
.vd-text{padding:12px 14px;font-size:13px;line-height:1.9;color:#334155;white-space:pre-wrap;max-height:52vh;overflow-y:auto}
.vd-del{background:#FEE2E2;color:#B91C1C;text-decoration:line-through;border-radius:3px;padding:0 1px}
.vd-ins{background:#DCFCE7;color:#15803D;border-radius:3px;padding:0 1px;text-decoration:none}
.vd-tip{margin-top:14px;padding:10px 14px;border-radius:10px;background:#F0F9FF;border:1px solid #BAE6FD;color:#0369A1;font-size:12px;line-height:1.6}
@media (max-width:860px){.vd-cols{grid-template-columns:1fr}}
.confidence-warn{background:#FEF3C7;color:#92400E;border:1px solid #FCD34D}
.confidence-ok{background:#ECFDF5;color:#065F46;border:1px solid #6EE7B7}

.action-bar{display:flex;align-items:center;gap:4px;margin-top:14px}
.user-action{justify-content:flex-end;margin-top:6px}
.action-btn{display:inline-flex;align-items:center;gap:6px;padding:6px 12px;border-radius:10px;border:1px solid #E2E8F0;background:#FFF;color:#64748B;font-size:13px;cursor:pointer;transition:all .15s;font-family:inherit}
.action-btn:hover{background:#F8FAFC;border-color:#CBD5E1;color:#334155}
.action-btn.copied{color:#22C55E;border-color:#BBF7D0;background:#F0FDF4}
.action-btn.active{color:#0369A1;border-color:#BAE6FD;background:#F0F9FF}
.user-action .action-btn{padding:4px 10px;font-size:12px}

.chat-input{padding:16px 24px;border-top:1px solid var(--border-color);background:#FFF;flex-shrink:0}
.mode-row{display:flex;align-items:center;gap:8px;margin-bottom:10px;flex-wrap:wrap}
.mode-label{font-size:12px;color:var(--text-muted);font-weight:600;margin-right:2px}
.mode-chip{padding:4px 12px;border-radius:20px;border:1px solid #E2E8F0;background:#FFF;color:#64748B;font-size:12px;cursor:pointer;transition:all .2s;font-family:inherit}
.mode-chip:hover:not(:disabled){border-color:#7DD3FC;color:#0369A1;transform:translateY(-1px)}
.mode-chip.on{background:linear-gradient(135deg,#EFF6FF,#F0F9FF);border-color:#38BDF8;color:#0369A1;font-weight:600;box-shadow:0 2px 8px rgba(56,189,248,.18)}
.mode-chip:disabled{opacity:.5;cursor:not-allowed}
.mode-hint{margin-left:auto;font-size:11px;color:#94A3B8}

/* ── 检索过程可视化面板 ── */
.trace-panel{margin-top:16px;border:1px solid #E2E8F0;border-radius:14px;background:#F8FAFC;overflow:hidden;animation:msgIn .3s ease both}
.trace-head{display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:12px 16px;background:linear-gradient(90deg,#EFF6FF,transparent);border-bottom:1px solid #E2E8F0}
.trace-title{font-size:13px;font-weight:700;color:#0369A1}
.trace-chip{font-size:11px;color:#64748B;background:#FFF;border:1px solid #E2E8F0;border-radius:20px;padding:2px 10px}
.trace-chip.mode{color:#0369A1;border-color:#BAE6FD;background:#F0F9FF;font-weight:600}
.trace-meta{padding:10px 16px 0}
.trace-row{display:flex;gap:12px;padding:5px 0;font-size:12.5px;align-items:baseline}
.trace-row .k{flex-shrink:0;width:64px;color:#94A3B8}
.trace-row .v{color:#334155;word-break:break-all}
.w-chip{display:inline-block;padding:1px 8px;border-radius:10px;font-size:11px;margin-right:6px;font-family:'Space Grotesk',monospace}
.w-chip.bm25{background:#EFF6FF;color:#2563EB}
.w-chip.vec{background:#ECFDF5;color:#059669}
.w-chip.kg{background:#F5F3FF;color:#7C3AED}
.trace-channels{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;padding:12px 16px}
.tc-card{border:1px solid #E2E8F0;border-radius:10px;background:#FFF;overflow:hidden}
.tc-card.off{opacity:.55}
.tc-head{display:flex;align-items:center;gap:6px;padding:8px 10px;border-bottom:1px solid #F1F5F9;background:#FBFDFF}
.tc-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.tc-head b{font-size:12px;color:#1E293B}
.tc-w{font-size:10px;color:#94A3B8;margin-left:auto}
.tc-lat{font-size:10px;color:#94A3B8;font-family:'Space Grotesk',monospace}
.tc-body{padding:4px 0;max-height:170px;overflow-y:auto}
.tc-hit{display:flex;align-items:center;gap:6px;padding:5px 10px;font-size:11.5px;border-bottom:1px dashed #F1F5F9}
.tc-hit:last-child{border-bottom:none}
.tc-rank{color:#94A3B8;font-family:'Space Grotesk',monospace;flex-shrink:0}
.tc-title{flex:1;color:#475569;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.tc-score{color:#0369A1;font-family:'Space Grotesk',monospace;flex-shrink:0;font-size:11px}
.tc-empty{text-align:center;color:#CBD5E1;font-size:12px;padding:16px 0}
.trace-fusion{padding:0 16px 14px}
.tf-title{font-size:12px;font-weight:600;color:#334155;padding:10px 0 8px;border-top:1px solid #E2E8F0;margin-top:2px}
.tf-note{font-weight:400;color:#94A3B8;font-size:11px;margin-left:8px}
.tf-row{display:grid;grid-template-columns:32px 1fr 110px 70px 74px 44px;gap:8px;align-items:center;padding:6px 10px;font-size:12px;border-bottom:1px solid #F1F5F9;background:#FFF;border-radius:6px;margin-bottom:2px}
.tf-row.head{background:transparent;color:#94A3B8;font-size:11px;border:none;margin-bottom:0}
.tf-row.cut{opacity:.5}
.tf-rank{color:#94A3B8;font-family:'Space Grotesk',monospace}
.tf-doc{color:#334155;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.tf-ch{display:flex;gap:3px;flex-wrap:wrap}
.tf-rrf{color:#0369A1;font-family:'Space Grotesk',monospace}
.tf-final{text-align:center}
.final-ok{color:#059669;font-weight:700;font-size:11px}
.final-cut{color:#CBD5E1}
.examples{margin-top:10px;display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.examples-label{font-size:12px;color:var(--text-muted);font-weight:500}
.example-tag{cursor:pointer;transition:all .2s;border:1px solid #E2E8F0}
.example-tag:hover{transform:translateY(-2px);box-shadow:0 4px 12px rgba(0,0,0,.08);border-color:#0369A1;color:#0369A1}
.input-row{display:flex;align-items:flex-end;gap:10px;background:#F8FAFC;border-radius:18px;padding:10px 16px;border:2px solid #E2E8F0;transition:all .25s}
.input-row:focus-within{border-color:#0369A1;box-shadow:0 0 0 4px rgba(3,105,161,.06)}
.tts-toggle{width:36px;height:36px;border-radius:50%;border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:all .2s;background:#F1F5F9;color:#94A3B8}
.tts-toggle:hover{background:#E2E8F0;color:#64748B}
.tts-toggle.on{background:#EFF6FF;color:#0369A1}
.tts-toggle.on:hover{background:#DBEAFE}
.chat-textarea{flex:1;border:none;outline:none;resize:none;font-size:15px;line-height:1.6;font-family:inherit;color:var(--text-primary);background:transparent;padding:4px 0;max-height:200px}
.chat-textarea::placeholder{color:var(--text-muted)}
.chat-textarea:disabled{opacity:.5}
.send-btn,.stop-btn{width:42px;height:42px;border-radius:50%;border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:all .25s}
.send-btn{background:linear-gradient(135deg,#38BDF8,#7DD3FC);color:#FFF;opacity:.6;box-shadow:0 4px 16px rgba(56,189,248,.25)}
.send-btn:not(:disabled){opacity:1}
.send-btn:not(:disabled):hover{transform:scale(1.08);box-shadow:0 8px 28px rgba(56,189,248,.4)}
.send-btn:disabled{cursor:not-allowed}
.stop-btn{background:#DC2626;color:#FFF}
.stop-btn:hover{background:#B91C1C;transform:scale(1.08)}
</style>
