<template>
  <div class="knowledge-page">
    <div class="page-head">
      <div>
        <h2 class="page-title">法律知识科普</h2>
        <p class="page-subtitle">生成式普法专题 · 名词卡片 · 高频问答 · 互动情景剧 · 普法海报 · 科普短片</p>
      </div>
    </div>

    <el-tabs v-model="activeTab" class="knowledge-tabs">
      <!-- ═══════════ Tab 1 科普专题 ═══════════ -->
      <el-tab-pane label="科普专题" name="articles">
        <div class="category-chips">
          <el-tag
            v-for="c in categories" :key="c"
            :effect="activeCategory === c ? 'dark' : 'plain'"
            round class="category-chip" @click="activeCategory = c"
          >{{ c }}</el-tag>
        </div>
        <div v-loading="articlesLoading" class="article-grid stagger-children">
          <div
            v-for="a in filteredArticles" :key="a.id"
            class="article-card animate-fade-in-up" @click="openArticle(a)"
          >
            <div class="article-card-head">
              <span class="article-category">{{ a.category }}</span>
              <el-tag size="small" :type="a.hasContent ? 'success' : 'info'" effect="plain" round>
                {{ a.hasContent ? '已生成' : '待生成' }}
              </el-tag>
            </div>
            <h3>{{ a.title }}</h3>
            <p>{{ a.description }}</p>
            <span v-if="a.generatedAt" class="article-time">生成于 {{ fmtTime(a.generatedAt) }}</span>
          </div>
          <div v-if="!filteredArticles.length && !articlesLoading" class="docket-empty">暂无科普专题</div>
        </div>
      </el-tab-pane>

      <!-- ═══════════ Tab 2 名词卡片 ═══════════ -->
      <el-tab-pane label="名词卡片" name="terms">
        <div v-loading="termsLoading" class="terms-sections stagger-children">
          <div v-for="g in termGroups" :key="g.type" class="terms-panel animate-fade-in-up">
            <div class="panel-head">
              <span class="panel-index" :style="{ color: g.color, borderColor: g.color + '55', background: g.color + '14' }">{{ g.index }}</span>
              <h3>{{ g.label }}</h3>
              <span class="panel-count">{{ g.items.length }} 个</span>
            </div>
            <div class="term-grid">
              <div v-for="t in g.items" :key="t.name" class="term-card" @click="router.push('/app/kg')">
                <b>{{ t.name }}</b>
                <p v-if="t.description">{{ t.description }}</p>
                <p v-else class="term-no-desc">图谱实体 · 点击查看关联关系</p>
              </div>
            </div>
          </div>
          <div v-if="!terms.length && !termsLoading" class="docket-empty">
            术语数据暂不可用，请确认 RAG 服务已启动后刷新
            <el-button size="small" plain style="margin-top:10px" @click="loadTerms">重试</el-button>
          </div>
        </div>
      </el-tab-pane>

      <!-- ═══════════ Tab 3 高频问答 ═══════════ -->
      <el-tab-pane label="高频问答" name="faq">
        <div class="faq-layout">
          <aside class="faq-list">
            <div v-for="g in faqGroups" :key="g.category">
              <div class="faq-group-label">{{ g.category }}</div>
              <div
                v-for="q in g.items" :key="q" class="faq-item"
                :class="{ active: faqSelected === q }" @click="askFaq(q)"
              >{{ q }}</div>
            </div>
          </aside>
          <main class="faq-answer" v-loading="faqLoading">
            <div v-if="faqSelected" class="faq-answer-inner">
              <div class="faq-question-title">{{ faqSelected }}</div>
              <div class="answer-md" v-html="renderMarkdown(faqAnswer)" />
              <div v-if="faqSources.length" class="source-section">
                <div class="source-divider"></div>
                <p class="source-title">📚 参考来源</p>
                <div class="source-cards">
                  <div v-for="(s, j) in faqSources" :key="j" class="source-card" :class="'source-' + s.type">
                    <div class="source-title-text">{{ s.title }}</div>
                    <div class="source-snippet" v-if="s.snippet">{{ s.snippet.substring(0, 150) }}...</div>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="faq-empty">点击左侧问题开始咨询，答案由三路混合检索生成</div>
          </main>
        </div>
      </el-tab-pane>
      <!-- ═══════════ Tab 4 打工人小剧场 ═══════════ -->
      <el-tab-pane label="打工人小剧场" name="drama">
        <div class="drama-page">
          <!-- 剧本选择 -->
          <div v-if="!drama.story" class="story-picker">
            <p class="picker-sub">在剧情里做出选择，看看法律会怎么判——选错也没关系，每次选择都是一次避坑学习</p>
            <div v-loading="drama.storiesLoading" class="story-grid stagger-children">
              <div v-for="(s, i) in drama.stories" :key="s.id" class="story-card animate-fade-in-up" @click="startDrama(s)">
                <span class="story-index">{{ '壹贰叁肆伍'[i] || i + 1 }}</span>
                <h3>{{ s.title }}</h3>
                <p>{{ s.topic }}</p>
                <el-button type="primary" plain size="small" round>开始体验 →</el-button>
              </div>
              <div v-if="!drama.stories.length && !drama.storiesLoading" class="docket-empty">
                剧本加载失败，请确认 RAG 服务已启动
                <el-button size="small" plain style="margin-top:10px" @click="loadStories">重试</el-button>
              </div>
            </div>
          </div>

          <!-- 剧场 -->
          <div v-else class="theater">
            <div class="theater-top">
              <span class="theater-badge">第 {{ drama.sceneIndex }} 幕 / 共 {{ drama.totalScenes }} 幕</span>
              <h3 class="theater-title">{{ drama.story.title }}</h3>
              <el-button size="small" plain round @click="resetDrama">换个剧本</el-button>
            </div>

            <div class="stage" v-loading="drama.busy">
              <template v-if="drama.phase !== 'ending'">
                <p class="stage-text">{{ drama.sceneText }}</p>

                <!-- 选项（未作答时） -->
                <div v-if="drama.phase === 'scene'" class="stage-options">
                  <div v-for="o in drama.options" :key="o.key" class="stage-option" @click="chooseDrama(o)">
                    <span class="option-key">{{ o.key }}</span><span>{{ o.text }}</span>
                  </div>
                </div>

                <!-- 判决 -->
                <div v-if="drama.phase === 'verdict'" class="verdict-card" :class="drama.verdict.correct ? 'verdict-ok' : 'verdict-bad'">
                  <div class="verdict-head">
                    <span class="verdict-icon">{{ drama.verdict.correct ? '✔' : '✘' }}</span>
                    <b>{{ drama.verdict.correct ? '这一步走对了！' : '这一步踩坑了' }}</b>
                    <span class="verdict-key">正确答案：{{ drama.verdict.correct_key }}</span>
                  </div>
                  <p class="verdict-explain">{{ drama.verdict.explanation }}</p>
                  <div class="verdict-laws">
                    <el-tag v-for="(l, j) in drama.verdict.law_refs" :key="j" size="small" effect="plain" type="info" round>{{ l }}</el-tag>
                  </div>
                  <div class="verdict-actions">
                    <el-button type="primary" size="small" round :loading="drama.busy" @click="continueDrama">继续 →</el-button>
                  </div>
                </div>
              </template>

              <!-- 结局 -->
              <template v-else>
                <div class="ending-card">
                  <span class="ending-icon">🎓</span>
                  <h3>全剧终 · 避坑笔记</h3>
                  <p class="ending-summary">{{ drama.ending.summary }}</p>
                  <div class="ending-lessons">
                    <div v-for="(l, j) in drama.ending.lessons" :key="j" class="lesson-item">
                      <span class="lesson-no">{{ j + 1 }}</span><span>{{ l }}</span>
                    </div>
                  </div>
                  <div class="verdict-actions">
                    <el-button type="primary" size="small" round @click="replayDrama">再玩一次</el-button>
                    <el-button size="small" plain round @click="resetDrama">换个剧本</el-button>
                  </div>
                </div>
              </template>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- ═══════════ Tab 5 普法海报 ═══════════ -->
      <el-tab-pane label="普法海报" name="poster">
        <div class="poster-page">
          <div class="poster-controls">
            <div class="poster-topic-row">
              <el-tag
                v-for="t in posterTopics" :key="t"
                :effect="poster.topic === t ? 'dark' : 'plain'"
                round class="category-chip" @click="poster.topic = t"
              >{{ t }}</el-tag>
              <el-input v-model="poster.topic" placeholder="自定义主题，如：加班费" class="poster-input" clearable />
              <el-button type="primary" :loading="poster.loading" @click="makePoster">🎨 生成海报</el-button>
            </div>
            <div class="poster-theme-row">
              <span class="theme-label">海报风格：</span>
              <el-radio-group v-model="poster.theme" size="small">
                <el-radio-button label="blue">蓝色 · 权威风</el-radio-button>
                <el-radio-button label="red">红色 · 警示风</el-radio-button>
                <el-radio-button label="warm">暖色 · 关怀风</el-radio-button>
              </el-radio-group>
            </div>
          </div>
          <div class="poster-body" v-loading="poster.loading">
            <div v-if="poster.data" class="poster-preview">
              <canvas ref="posterCanvas" width="800" height="1300" class="poster-canvas"></canvas>
              <div class="poster-actions">
                <el-button type="primary" @click="downloadPoster">⬇ 下载海报 PNG</el-button>
                <span class="poster-hint">RAG 检索法条 + LLM 生成文案 + 前端渲染成图，可保存分享</span>
              </div>
            </div>
            <div v-else class="poster-empty">输入主题点击「生成海报」，系统检索法条后自动提炼成一张普法海报</div>
          </div>

          <!-- 已生成的海报图库（点击即载入主画布，可换风格下载） -->
          <div class="preset-section" v-if="posterPresets.length">
            <div class="preset-head">
              <h4>预置海报图库 · 点击任意一张载入预览</h4>
            </div>
            <div class="preset-grid">
              <div
                v-for="(p, i) in posterPresets" :key="i"
                class="preset-card poster-card" :class="{ on: poster.presetIdx === i }"
                @click="loadPosterPreset(i)"
              >
                <div class="poster-card-top" :style="posterCardStyle(i)">
                  <span class="preset-card-topic">{{ p.topic }}</span>
                  <b class="poster-card-title">{{ p.title }}</b>
                </div>
                <p class="poster-card-slogan">{{ p.slogan }}</p>
                <p class="poster-card-point" v-if="p.points && p.points.length">· {{ p.points[0].headline || p.points[0] }}</p>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- ═══════════ Tab 6 普法短片 ═══════════ -->
      <el-tab-pane label="普法短片" name="video">
        <div class="video-page">
          <div class="poster-controls">
            <div class="poster-topic-row">
              <el-tag
                v-for="t in posterTopics" :key="t"
                :effect="video.topic === t ? 'dark' : 'plain'"
                round class="category-chip" @click="video.topic = t"
              >{{ t }}</el-tag>
              <el-input v-model="video.topic" placeholder="自定义主题，如：竞业限制" class="poster-input" clearable />
              <el-button type="primary" :loading="video.loading" @click="makeVideo">🎬 生成短片</el-button>
            </div>
          </div>
          <div class="video-body" v-loading="video.loading">
            <template v-if="video.data">
              <div class="video-player">
                <div class="video-screen" :class="'video-theme-' + video.themeIdx" @click="video.playing ? pauseVideo() : playVideo()">
                  <transition name="fade" mode="out-in">
                    <div :key="video.idx" class="video-scene">
                      <span class="video-scene-no">{{ video.idx + 1 }} / {{ video.data.scenes.length }}</span>
                      <p class="video-visual">{{ video.data.scenes[video.idx].visual }}</p>
                      <p class="video-subtitle">{{ video.data.scenes[video.idx].subtitle }}</p>
                    </div>
                  </transition>
                  <div class="video-controls" @click.stop>
                    <el-button circle size="small" @click="video.playing ? pauseVideo() : playVideo()">{{ video.playing ? '⏸' : '▶' }}</el-button>
                    <div class="video-progress">
                      <div
                        v-for="(s, j) in video.data.scenes" :key="j"
                        class="video-dot" :class="{ on: j <= video.idx, active: j === video.idx }"
                        @click="jumpVideo(j)"
                      ></div>
                    </div>
                    <el-button circle size="small" @click="replayVideo">↺</el-button>
                  </div>
                </div>
                <div class="video-side">
                  <h3 class="video-title">{{ video.data.title }}</h3>
                  <div class="video-script">
                    <div
                      v-for="(s, j) in video.data.scenes" :key="j"
                      class="script-item" :class="{ active: j === video.idx }" @click="jumpVideo(j)"
                    >
                      <b>分镜{{ j + 1 }}</b><span>{{ s.subtitle }}</span>
                    </div>
                  </div>
                  <p class="poster-hint">{{ video.audioUrls.length ? '🔊 已为旁白合成语音（点击画面播放）' : '🔇 未启用语音合成，字幕自动播放' }}</p>
                </div>
              </div>
            </template>
            <div v-else class="poster-empty">输入主题点击「生成短片」，自动生成 5 个分镜的动态科普短片</div>
          </div>

          <!-- 已生成的短片列表（点击即播放，含预合成配音） -->
          <div class="preset-section" v-if="videoPresets.length">
            <div class="preset-head">
              <h4>预置短片 · 点击任意一部直接播放</h4>
            </div>
            <div class="preset-grid">
              <div
                v-for="v in videoPresets" :key="v.id"
                class="preset-card video-card" :class="{ on: video.data && video.presetId === v.id }"
                v-loading="videoPresetLoading === v.id"
                @click="loadVideoPreset(v.id)"
              >
                <div class="video-card-top">
                  <span class="preset-card-topic">{{ v.topic }}</span>
                  <span class="video-card-meta">🎬 {{ v.scene_count }} 分镜 · {{ v.has_audio ? '🔊 有配音' : '🔇 字幕' }}</span>
                </div>
                <b class="video-card-title">{{ v.title }}</b>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- ═══════════ 文章详情抽屉 ═══════════ -->
    <el-drawer v-model="articleVisible" size="720px" :title="currentArticle?.title || '科普专题'">
      <div v-loading="articleDetailLoading" class="article-detail">
        <template v-if="currentArticle">
          <div class="article-meta">
            <span class="article-category">{{ currentArticle.category }}</span>
            <span v-if="currentArticle.generatedAt" class="article-time">生成于 {{ fmtTime(currentArticle.generatedAt) }}</span>
            <el-button
              type="primary" plain size="small" :loading="regenerating" class="regen-btn"
              @click="regenerate"
            >
              {{ currentArticle.hasContent ? '重新生成' : '生成文章' }}
            </el-button>
          </div>

          <div v-if="currentArticle.content" class="answer-md" v-html="renderMarkdown(currentArticle.content)" />
          <div v-else class="faq-empty" style="padding:60px 0">
            该专题尚未生成，点击「生成文章」由 RAG 引擎检索语料并撰写（约 20-60 秒）
          </div>

          <div v-if="currentArticle.sources?.length" class="source-section">
            <div class="source-divider"></div>
            <p class="source-title">📚 参考来源（含时效状态）</p>
            <div class="source-cards">
              <div v-for="(s, j) in currentArticle.sources" :key="j" class="source-card" :class="'source-' + s.type">
                <div class="source-header">
                  <el-tag v-if="s.status" size="small" :type="statusTagType(s.status)" effect="plain" round>{{ s.status }}</el-tag>
                </div>
                <div class="source-title-text">{{ s.title }}</div>
                <div class="source-snippet" v-if="s.snippet">{{ s.snippet.substring(0, 150) }}...</div>
              </div>
            </div>
          </div>
        </template>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, reactive, watch, nextTick, onMounted, onDeactivated } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { marked } from 'marked'
import api from '../api'

const router = useRouter()
const activeTab = ref('articles')

// ── 科普专题 ──
const articles = ref([])
const activeCategory = ref('全部')
const articlesLoading = ref(false)
const articleVisible = ref(false)
const currentArticle = ref(null)
const articleDetailLoading = ref(false)
const regenerating = ref(false)

const categories = computed(() => ['全部', ...new Set(articles.value.map(a => a.category))])
const filteredArticles = computed(() => activeCategory.value === '全部'
  ? articles.value
  : articles.value.filter(a => a.category === activeCategory.value))

async function loadArticles() {
  articlesLoading.value = true
  try {
    const res = await api.get('/knowledge/articles')
    if (res.code === 200) articles.value = res.data || []
  } catch {}
  articlesLoading.value = false
}

async function openArticle(a) {
  articleVisible.value = true
  articleDetailLoading.value = true
  currentArticle.value = null
  try {
    const res = await api.get(`/knowledge/articles/${a.id}`)
    if (res.code === 200) currentArticle.value = res.data
  } catch {}
  articleDetailLoading.value = false
}

async function regenerate() {
  if (!currentArticle.value) return
  regenerating.value = true
  try {
    const res = await api.post(`/knowledge/articles/${currentArticle.value.id}/generate`, null, { timeout: 180000 })
    if (res.code === 200) {
      currentArticle.value = res.data
      ElMessage.success('文章已生成')
      loadArticles() // 刷新列表状态徽章
    } else {
      ElMessage.error(res.message || '生成失败')
    }
  } catch (e) {
    ElMessage.error(e.response?.data?.message || '生成失败，请稍后重试')
  }
  regenerating.value = false
}

function fmtTime(t) {
  if (!t) return ''
  return String(t).replace('T', ' ').substring(0, 16)
}

// ── 名词卡片 ──
const terms = ref([])
const termsLoading = ref(false)
const typeMeta = {
  LegalConcept:    { label: '法律概念', color: '#8b5cf6', index: '壹' },
  RightObligation: { label: '权利义务', color: '#06b6d4', index: '贰' },
  IllegalAct:      { label: '违法行为', color: '#ef4444', index: '叁' },
  LegalLiability:  { label: '法律责任', color: '#f97316', index: '肆' },
}
const termGroups = computed(() => Object.entries(typeMeta).map(([type, meta]) => ({
  type, label: meta.label, index: meta.index, color: meta.color,
  items: terms.value.filter(t => t.type === type),
})).filter(g => g.items.length))

async function loadTerms() {
  termsLoading.value = true
  try {
    const res = await api.get('/knowledge/terms')
    if (res.code === 200) terms.value = res.data || []
  } catch {}
  termsLoading.value = false
}

// ── 高频问答 ──
const faqGroups = [
  { category: '工资报酬', items: ['加班费怎么算？', '公司拖欠工资怎么办？'] },
  { category: '劳动合同', items: ['试用期最长可以约定多久？', '公司不签劳动合同有什么后果？', '竞业限制协议必须签吗？'] },
  { category: '解除辞退', items: ['被公司辞退能拿到多少经济补偿？', '什么情况属于违法解除劳动合同？', '主动辞职能拿经济补偿金吗？'] },
  { category: '工伤社保', items: ['工伤认定的标准和流程是什么？', '发生工伤后应该怎么维权？'] },
  { category: '女职工', items: ['孕期被公司调岗降薪合法吗？', '产假能休多少天？'] },
]
const faqSelected = ref('')
const faqAnswer = ref('')
const faqSources = ref([])
const faqLoading = ref(false)

async function askFaq(q) {
  if (faqLoading.value) return
  faqSelected.value = q
  faqLoading.value = true
  try {
    const res = await api.post('/chat/ask', { question: q })
    if (res.code === 200) {
      faqAnswer.value = res.data.answer || '未获取到回答'
      faqSources.value = res.data.sources || []
    }
  } catch {
    faqAnswer.value = '服务暂时不可用，请稍后重试。'
    faqSources.value = []
  }
  faqLoading.value = false
}

// ── 打工人小剧场（互动情景剧） ──
const drama = reactive({
  stories: [], storiesLoading: false,
  story: null,
  phase: 'scene',            // scene | verdict | ending
  sceneIndex: 1, totalScenes: 3,
  sceneText: '', options: [],
  verdict: null,
  pendingNext: null,         // 判决后待展示的下一幕/结局
  ending: { summary: '', lessons: [] },
  busy: false,
})

async function loadStories() {
  drama.storiesLoading = true
  try {
    const res = await api.get('/knowledge/stories')
    if (res.code === 200) drama.stories = res.data || []
  } catch {}
  drama.storiesLoading = false
}

async function startDrama(s) {
  drama.story = s
  drama.phase = 'scene'
  drama.sceneIndex = 1
  drama.sceneText = '正在编写剧情……'
  drama.options = []
  drama.busy = true
  try {
    const res = await api.post('/knowledge/scene/start', { story_id: s.id }, { timeout: 180000 })
    if (res.code === 200) {
      const d = res.data
      drama.sceneIndex = d.scene_index
      drama.totalScenes = d.total_scenes
      drama.sceneText = d.scene_text
      drama.options = d.options || []
    } else {
      ElMessage.error(res.message || '开场生成失败')
      resetDrama()
    }
  } catch {
    ElMessage.error('开场生成失败：RAG 服务暂不可用')
    resetDrama()
  }
  drama.busy = false
}

async function chooseDrama(o) {
  if (drama.busy || drama.phase !== 'scene') return
  drama.busy = true
  try {
    const res = await api.post('/knowledge/scene/next', {
      story_id: drama.story.id,
      scene_index: drama.sceneIndex,
      choice: o.key,
    }, { timeout: 180000 })
    if (res.code === 200) {
      drama.verdict = res.data.verdict
      drama.pendingNext = res.data.next
      drama.phase = 'verdict'
    } else {
      ElMessage.error(res.message || '剧情推进失败')
    }
  } catch {
    ElMessage.error('剧情推进失败：RAG 服务暂不可用')
  }
  drama.busy = false
}

function continueDrama() {
  const nxt = drama.pendingNext
  if (!nxt) return
  if (nxt.is_ending) {
    drama.ending = { summary: nxt.summary, lessons: nxt.lessons || [] }
    drama.phase = 'ending'
  } else {
    drama.sceneIndex = nxt.scene_index
    drama.sceneText = nxt.scene_text
    drama.options = nxt.options || []
    drama.phase = 'scene'
  }
  drama.pendingNext = null
}

function resetDrama() {
  drama.story = null
  drama.phase = 'scene'
  drama.sceneText = ''
  drama.options = []
  drama.verdict = null
  drama.pendingNext = null
  drama.ending = { summary: '', lessons: [] }
}

function replayDrama() {
  const s = drama.story
  resetDrama()
  if (s) startDrama(s) // 命中服务端进程内缓存，二次体验很快
}

// ── 普法海报（LLM 文案 + Canvas 渲染） ──
const posterTopics = ['加班费怎么算', '被辞退的经济补偿', '工伤认定与赔偿', '试用期红线', '竞业限制', '女职工特殊保护']
const poster = reactive({ topic: '加班费怎么算', theme: 'blue', loading: false, data: null, presetIdx: -1 })
const posterCanvas = ref(null)

const POSTER_THEMES = {
  blue: { bg: ['#0B3A6B', '#0369A1'], accent: '#38BDF8', sub: '#BAE6FD' },
  red:  { bg: ['#7F1D1D', '#DC2626'], accent: '#FCA5A5', sub: '#FECACA' },
  warm: { bg: ['#7C2D12', '#EA580C'], accent: '#FDBA74', sub: '#FED7AA' },
}

async function makePoster() {
  const topic = poster.topic.trim()
  if (!topic) return
  poster.loading = true
  try {
    const res = await api.post('/knowledge/poster', { topic }, { timeout: 180000 })
    if (res.code === 200) {
      poster.data = { ...res.data, topic }
      poster.presetIdx = -1
      await nextTick()
      renderPoster()
    } else {
      ElMessage.error(res.message || '海报生成失败')
    }
  } catch {
    ElMessage.error('海报生成失败：RAG 服务暂不可用')
  }
  poster.loading = false
}

watch(() => poster.theme, () => { if (poster.data) renderPoster() })

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath()
  ctx.moveTo(x + r, y)
  ctx.arcTo(x + w, y, x + w, y + h, r)
  ctx.arcTo(x + w, y + h, x, y + h, r)
  ctx.arcTo(x, y + h, x, y, r)
  ctx.arcTo(x, y, x + w, y, r)
  ctx.closePath()
}

function wrapText(ctx, text, x, y, maxW, lineH) {
  let line = ''
  let yy = y
  for (const ch of String(text || '')) {
    const test = line + ch
    if (ctx.measureText(test).width > maxW && line) {
      ctx.fillText(line, x, yy)
      line = ch
      yy += lineH
    } else {
      line = test
    }
  }
  if (line) ctx.fillText(line, x, yy)
  return yy
}

function renderPoster() {
  const cv = posterCanvas.value
  const data = poster.data
  if (!cv || !data) return
  const th = POSTER_THEMES[poster.theme] || POSTER_THEMES.blue
  const ctx = cv.getContext('2d')
  const W = 800, H = 1300

  // 背景
  const g = ctx.createLinearGradient(0, 0, W, H)
  g.addColorStop(0, th.bg[0])
  g.addColorStop(1, th.bg[1])
  ctx.fillStyle = g
  ctx.fillRect(0, 0, W, H)

  // 装饰圆
  ctx.globalAlpha = 0.12
  ctx.fillStyle = '#FFFFFF'
  ctx.beginPath(); ctx.arc(660, 150, 190, 0, Math.PI * 2); ctx.fill()
  ctx.beginPath(); ctx.arc(110, 1140, 150, 0, Math.PI * 2); ctx.fill()
  ctx.globalAlpha = 1

  // 顶部小标 + 标题 + 标语
  ctx.fillStyle = th.accent
  ctx.font = '600 26px "Microsoft YaHei", sans-serif'
  ctx.fillText('劳动法 · 打工人避坑指南', 70, 92)
  ctx.fillStyle = '#FFFFFF'
  ctx.font = 'bold 64px "Microsoft YaHei", sans-serif'
  wrapText(ctx, data.title || '', 70, 175, 660, 84)
  ctx.fillStyle = th.sub
  ctx.font = '28px "Microsoft YaHei", sans-serif'
  wrapText(ctx, data.slogan || '', 70, 295, 660, 44)

  ctx.strokeStyle = th.accent
  ctx.lineWidth = 2
  ctx.beginPath(); ctx.moveTo(70, 366); ctx.lineTo(730, 366); ctx.stroke()

  // 要点卡 ×4
  let y = 410
  for (let i = 0; i < (data.points || []).length; i++) {
    const p = data.points[i]
    ctx.fillStyle = 'rgba(255,255,255,0.10)'
    roundRect(ctx, 70, y, 660, 140, 16)
    ctx.fill()
    ctx.fillStyle = th.accent
    ctx.font = 'bold 38px "Noto Serif SC", serif'
    ctx.fillText('0' + (i + 1), 104, y + 58)
    ctx.fillStyle = '#FFFFFF'
    ctx.font = 'bold 30px "Microsoft YaHei", sans-serif'
    ctx.fillText(p.headline || '', 170, y + 56)
    ctx.fillStyle = th.sub
    ctx.font = '24px "Microsoft YaHei", sans-serif'
    wrapText(ctx, p.detail || '', 104, y + 100, 580, 36)
    y += 158
  }

  // 温馨提示
  ctx.fillStyle = 'rgba(255,255,255,0.10)'
  roundRect(ctx, 70, y + 6, 660, 116, 16)
  ctx.fill()
  ctx.fillStyle = th.accent
  ctx.font = 'bold 26px "Microsoft YaHei", sans-serif'
  ctx.fillText('温馨提示', 104, y + 56)
  ctx.fillStyle = th.sub
  ctx.font = '24px "Microsoft YaHei", sans-serif'
  wrapText(ctx, data.tip || '', 104, y + 96, 580, 36)

  // 底部：法条依据 + 脚注
  ctx.textAlign = 'center'
  ctx.fillStyle = '#FFFFFF'
  ctx.font = 'bold 26px "Microsoft YaHei", sans-serif'
  ctx.fillText('依据：' + (data.law_basis || ''), 400, 1230)
  ctx.fillStyle = th.sub
  ctx.font = '20px "Microsoft YaHei", sans-serif'
  ctx.fillText('劳动法 RAG 智能普法 · 内容由 AI 生成，仅供参考，不构成法律意见', 400, 1268)
  ctx.textAlign = 'left'
}

function downloadPoster() {
  const cv = posterCanvas.value
  if (!cv) return
  const a = document.createElement('a')
  a.href = cv.toDataURL('image/png')
  a.download = `普法海报-${poster.data?.title || '海报'}.png`
  a.click()
}

// ── 预置内容（已生成的海报图库 / 短片列表，秒开不等待 LLM） ──
const posterPresets = ref([])
const videoPresets = ref([])
const videoPresetLoading = ref(-1)

const THEME_KEYS = ['blue', 'red', 'warm']
function posterCardStyle(i) {
  const th = POSTER_THEMES[THEME_KEYS[i % 3]] || POSTER_THEMES.blue
  return { background: `linear-gradient(135deg, ${th.bg[0]}, ${th.bg[1]})` }
}

async function loadPosterPresets() {
  try {
    const res = await api.get('/knowledge/poster/presets')
    if (res.code === 200) posterPresets.value = res.data || []
  } catch { posterPresets.value = [] }
}

async function loadVideoPresets() {
  try {
    const res = await api.get('/knowledge/video/presets')
    if (res.code === 200) videoPresets.value = res.data || []
  } catch { videoPresets.value = [] }
}

function loadPosterPreset(i) {
  const p = posterPresets.value[i]
  if (!p) return
  poster.data = { ...p, topic: p.topic }
  poster.topic = p.topic
  poster.presetIdx = i
  nextTick(() => {
    renderPoster()
    document.querySelector('.poster-preview')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  })
}

async function loadVideoPreset(id) {
  if (videoPresetLoading.value !== -1) return
  videoPresetLoading.value = id
  try {
    const res = await api.get(`/knowledge/video/presets/${id}`, { timeout: 120000 })
    if (res.code === 200 && res.data) {
      video.data = res.data
      video.audioUrls = res.data.audio || []
      video.idx = 0
      video.presetId = id
      await nextTick()
      playVideo()
      document.querySelector('.video-player')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    } else {
      ElMessage.error(res.message || '预置短片加载失败')
    }
  } catch {
    ElMessage.error('预置短片加载失败：RAG 服务暂不可用')
  }
  videoPresetLoading.value = -1
}

// ── 普法短片（LLM 分镜 + 自动播放 + 可选配音） ──
const video = reactive({
  topic: '加班费怎么算', loading: false, data: null,
  idx: 0, playing: false, themeIdx: 0,
  audioUrls: [],
  audio: [],      // 当前场景的 Audio 实例
  timer: null,
  presetId: -1,
})

async function makeVideo() {
  const topic = video.topic.trim()
  if (!topic) return
  video.loading = true
  try {
    const res = await api.post('/knowledge/video', { topic }, { timeout: 180000 })
    if (res.code === 200) {
      video.data = res.data
      video.audioUrls = res.data.audio || []
      video.idx = 0
      video.presetId = -1
      await nextTick()
      playVideo()
    } else {
      ElMessage.error(res.message || '短片生成失败')
    }
  } catch {
    ElMessage.error('短片生成失败：RAG 服务暂不可用')
  }
  video.loading = false
}

function stopVideoTimer() {
  if (video.timer) { clearTimeout(video.timer); video.timer = null }
  video.audio.forEach(a => { a.pause(); a.onended = null })
  video.audio = []
}

function playVideo() {
  if (!video.data) return
  video.playing = true
  playScene(video.idx)
}

function playScene(i) {
  const data = video.data
  if (!data || !data.scenes[i]) return
  video.idx = i
  video.themeIdx = i % 4
  stopVideoTimer()
  const scene = data.scenes[i]
  const url = video.audioUrls[i]
  if (url) {
    const a = new Audio(url)
    video.audio = [a]
    a.onended = () => {
      if (video.idx < data.scenes.length - 1) playScene(video.idx + 1)
      else video.playing = false
    }
    a.onerror = () => fallbackTimer(scene)
    a.play().catch(() => fallbackTimer(scene))
  } else {
    fallbackTimer(scene)
  }
}

function fallbackTimer(scene) {
  // 无配音时按字幕长度估算停留时间
  const dur = Math.min(10000, Math.max(4000, (scene.subtitle || '').length * 180))
  video.timer = setTimeout(() => {
    if (video.idx < video.data.scenes.length - 1) playScene(video.idx + 1)
    else video.playing = false
  }, dur)
}

function pauseVideo() {
  video.playing = false
  stopVideoTimer()
}

function replayVideo() {
  video.idx = 0
  playVideo()
}

function jumpVideo(i) {
  if (!video.data) return
  if (video.playing) playScene(i)
  else { video.idx = i; video.themeIdx = i % 4 }
}

// 离开页面时停止播放（keep-alive 下组件不会卸载）
onDeactivated(() => stopVideoTimer())

// ── markdown（与 ChatView 一致，先剥原始标签防 XSS） ──
marked.setOptions({ breaks: true, gfm: true })
function renderMarkdown(t) {
  if (!t) return ''
  return marked.parse(t.replace(/<[^>]*>/g, ''))
}
function statusTagType(s) {
  const m = { '现行有效': 'success', '已被修订': 'warning', '已废止': 'danger', '尚未生效': 'info' }
  return m[s] || 'info'
}

onMounted(() => {
  loadArticles()
  loadTerms()
  loadStories()
  loadPosterPresets()
  loadVideoPresets()
})
</script>

<style scoped>
.knowledge-page { max-width: 1300px; margin: 0 auto; padding-bottom: 40px; }
.page-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.page-title { margin: 0; font-size: 24px; font-weight: 700; color: var(--text-primary); }
.page-subtitle { margin: 4px 0 0; font-size: 13px; color: var(--text-muted); }

.knowledge-tabs :deep(.el-tabs__item) { font-weight: 600; }
.knowledge-tabs :deep(.el-tabs__item.is-active) { color: #0369A1; }

/* ── 科普专题 ── */
.category-chips { display: flex; gap: 10px; flex-wrap: wrap; margin: 6px 0 20px; }
.category-chip { cursor: pointer; font-size: 12.5px; }

.article-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; min-height: 200px; }
.article-card {
  background: #FFF; border: 1px solid #E2E8F0; border-radius: 14px;
  padding: 18px 20px; cursor: pointer;
  transition: all .25s; display: flex; flex-direction: column; gap: 10px;
}
.article-card:hover { transform: translateY(-3px); box-shadow: 0 10px 26px rgba(3, 105, 161, .10); border-color: #BAE6FD; }
.article-card-head { display: flex; align-items: center; justify-content: space-between; }
.article-category {
  font-size: 11.5px; font-weight: 600; color: #0369A1;
  padding: 3px 10px; background: #F0F9FF; border: 1px solid #BAE6FD; border-radius: 999px;
}
.article-card h3 { margin: 0; font-size: 16px; font-weight: 700; color: #1E293B; }
.article-card p { margin: 0; font-size: 13px; color: #64748B; line-height: 1.7; flex: 1; }
.article-time { font-size: 12px; color: #94A3B8; }

.docket-empty { text-align: center; color: #94A3B8; font-size: 13.5px; padding: 50px 0; }

/* ── 名词卡片 ── */
.terms-sections { display: flex; flex-direction: column; gap: 24px; min-height: 200px; }
.terms-panel { background: #FFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 20px 22px; }
.panel-head { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid #F1F5F9; }
.panel-index {
  font-size: 11px; font-weight: 700; padding: 2px 8px;
  border: 1px solid; border-radius: 6px; font-family: 'Noto Serif SC', serif;
}
.panel-head h3 { margin: 0; font-size: 15px; font-weight: 700; color: #1E293B; }
.panel-count { font-size: 12px; color: #94A3B8; }

.term-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 12px; }
.term-card {
  padding: 14px 16px; border: 1px solid #F1F5F9; border-radius: 12px;
  background: #F8FAFC; cursor: pointer; transition: all .2s;
}
.term-card:hover { background: #F0F9FF; border-color: #BAE6FD; transform: translateY(-2px); }
.term-card b { display: block; font-size: 14px; color: #1E293B; margin-bottom: 6px; }
.term-card p { margin: 0; font-size: 12.5px; color: #64748B; line-height: 1.65; }
.term-card .term-no-desc { color: #94A3B8; font-style: italic; font-size: 12px; }

/* ── 高频问答 ── */
.faq-layout { display: grid; grid-template-columns: 300px 1fr; gap: 24px; min-height: 480px; }
.faq-list {
  background: #FFF; border: 1px solid #E2E8F0; border-radius: 14px;
  padding: 14px 0; max-height: 640px; overflow-y: auto;
}
.faq-group-label { font-size: 12px; font-weight: 700; color: #0369A1; padding: 12px 20px 6px; letter-spacing: 1px; }
.faq-item {
  padding: 10px 20px; font-size: 13.5px; color: #475569; cursor: pointer;
  border-left: 3px solid transparent; transition: all .2s;
}
.faq-item:hover { background: #F8FAFC; color: #0369A1; }
.faq-item.active { background: #F0F9FF; color: #0369A1; font-weight: 600; border-left-color: #0369A1; }

.faq-answer {
  background: #FFF; border: 1px solid #E2E8F0; border-radius: 14px;
  padding: 24px 28px; min-height: 480px;
}
.faq-answer-inner { animation: fadeInUp .4s ease; }
.faq-question-title { font-size: 17px; font-weight: 700; color: #1E293B; margin-bottom: 18px; padding-bottom: 14px; border-bottom: 1px solid #F1F5F9; }
.faq-empty { display: flex; align-items: center; justify-content: center; height: 100%; color: #94A3B8; font-size: 13.5px; }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }

/* ── 文章详情抽屉 ── */
.article-detail { min-height: 300px; }
.article-meta { display: flex; align-items: center; gap: 14px; margin-bottom: 20px; flex-wrap: wrap; }
.regen-btn { margin-left: auto; }

/* ── markdown 渲染（与 ChatView 一致） ── */
.answer-md { color: #334155; font-size: 14.5px; line-height: 1.85; }
.answer-md :deep(h2) { color: var(--text-primary); margin: 20px 0 8px; font-size: 18px; font-weight: 700; }
.answer-md :deep(h3) { color: var(--text-primary); margin: 16px 0 6px; font-size: 16px; font-weight: 600; }
.answer-md :deep(p) { margin: 8px 0; }
.answer-md :deep(strong) { color: var(--text-primary); font-weight: 600; }
.answer-md :deep(ul), .answer-md :deep(ol) { padding-left: 24px; margin: 8px 0; }
.answer-md :deep(li) { margin: 4px 0; }
.answer-md :deep(blockquote) { border-left: 4px solid #0369A1; padding: 10px 18px; margin: 14px 0; background: linear-gradient(90deg, #EFF6FF, transparent); border-radius: 0 10px 10px 0; color: #1E40AF; }
.answer-md :deep(code) { background: #F1F5F9; padding: 2px 6px; border-radius: 4px; font-size: .9em; font-family: 'JetBrains Mono', monospace; color: #DC2626; }
.answer-md :deep(pre) { background: #1E293B; color: #E2E8F0; padding: 18px 22px; border-radius: 14px; overflow-x: auto; margin: 14px 0; font-size: 13px; line-height: 1.7; border: 1px solid rgba(255,255,255,.06); }
.answer-md :deep(pre code) { background: transparent; padding: 0; color: inherit; }
.answer-md :deep(table) { width: 100%; border-collapse: collapse; margin: 14px 0; font-size: 14px; }
.answer-md :deep(th) { background: #F8FAFC; font-weight: 600; padding: 10px 14px; text-align: left; border: 1px solid #E2E8F0; }
.answer-md :deep(td) { padding: 8px 14px; border: 1px solid #E2E8F0; }

/* ── 来源卡片（与 ChatView 一致） ── */
.source-section { margin-top: 20px; }
.source-divider { height: 1px; background: linear-gradient(90deg, #E2E8F0, transparent); margin-bottom: 12px; }
.source-title { color: var(--text-secondary); font-size: 13px; margin-bottom: 10px; font-weight: 500; }
.source-cards { display: flex; flex-wrap: wrap; gap: 8px; }
.source-card { flex: 0 0 calc(50% - 4px); padding: 12px 14px; border-radius: 12px; border: 1px solid #E2E8F0; background: #FFF; transition: all .25s; }
.source-card:hover { border-color: #BAE6FD; box-shadow: 0 4px 12px rgba(3, 105, 161, .08); }
.source-header { display: flex; gap: 8px; margin-bottom: 6px; }
.source-title-text { font-size: 13.5px; font-weight: 600; color: #1E293B; }
.source-snippet { font-size: 12.5px; color: #64748B; margin-top: 6px; line-height: 1.7; }
.source-statute { border-left: 3px solid #0369A1; }
.source-interpretation { border-left: 3px solid #8b5cf6; }
.source-case { border-left: 3px solid #f59e0b; }
.source-unknown { border-left: 3px solid #94A3B8; }

/* ── 打工人小剧场 ── */
.picker-sub { margin: 0 0 18px; font-size: 13px; color: #94A3B8; }
.story-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 16px; min-height: 160px; }
.story-card {
  position: relative; background: #FFF; border: 1px solid #E2E8F0; border-radius: 14px;
  padding: 20px; cursor: pointer; transition: all .25s;
  display: flex; flex-direction: column; gap: 8px; align-items: flex-start;
}
.story-card:hover { transform: translateY(-3px); box-shadow: 0 10px 26px rgba(3, 105, 161, .10); border-color: #BAE6FD; }
.story-index {
  font-size: 11px; font-weight: 700; color: #0369A1; padding: 2px 8px;
  border: 1px solid #BAE6FD; border-radius: 6px; background: #F0F9FF; font-family: 'Noto Serif SC', serif;
}
.story-card h3 { margin: 4px 0 0; font-size: 17px; font-weight: 700; color: #1E293B; }
.story-card p { margin: 0; font-size: 12.5px; color: #64748B; flex: 1; }
.story-card .el-button { margin-top: 8px; }

.theater { max-width: 760px; margin: 0 auto; }
.theater-top { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.theater-badge { font-size: 12px; font-weight: 700; color: #0369A1; padding: 3px 12px; background: #F0F9FF; border: 1px solid #BAE6FD; border-radius: 999px; }
.theater-title { margin: 0; font-size: 17px; font-weight: 700; color: #1E293B; flex: 1; }
.stage {
  background: #FFF; border: 1px solid #E2E8F0; border-radius: 16px;
  padding: 32px 34px; min-height: 320px;
  background-image: radial-gradient(rgba(3, 105, 161, .045) 1px, transparent 1px);
  background-size: 22px 22px;
}
.stage-text { margin: 0 0 26px; font-size: 15px; color: #334155; line-height: 2; }
.stage-options { display: flex; flex-direction: column; gap: 12px; }
.stage-option {
  display: flex; align-items: center; gap: 14px; padding: 14px 18px;
  border: 1px solid #E2E8F0; border-radius: 12px; background: #F8FAFC;
  cursor: pointer; font-size: 14px; color: #334155; transition: all .2s;
}
.stage-option:hover { background: #F0F9FF; border-color: #BAE6FD; color: #0369A1; transform: translateX(4px); }
.option-key {
  width: 28px; height: 28px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  background: #E0F2FE; color: #0369A1; font-weight: 700; font-size: 13px;
}

.verdict-card { border-radius: 14px; padding: 22px 24px; animation: fadeInUp .4s ease; }
.verdict-ok { background: #F0FDF4; border: 1px solid #BBF7D0; }
.verdict-bad { background: #FEF2F2; border: 1px solid #FECACA; }
.verdict-head { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.verdict-icon {
  width: 34px; height: 34px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; font-size: 16px; color: #FFF;
}
.verdict-ok .verdict-icon { background: #16A34A; }
.verdict-bad .verdict-icon { background: #DC2626; }
.verdict-head b { font-size: 16px; color: #1E293B; }
.verdict-key { font-size: 12.5px; color: #94A3B8; }
.verdict-explain { margin: 14px 0 0; font-size: 14px; color: #475569; line-height: 1.9; }
.verdict-laws { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px; }
.verdict-actions { margin-top: 18px; display: flex; gap: 10px; }

.ending-card { text-align: center; animation: fadeInUp .4s ease; }
.ending-icon { font-size: 44px; }
.ending-card h3 { margin: 10px 0 6px; font-size: 20px; color: #1E293B; }
.ending-summary { margin: 0 auto; max-width: 560px; font-size: 14px; color: #475569; line-height: 1.9; }
.ending-lessons { margin: 20px 0 6px; display: flex; flex-direction: column; gap: 10px; }
.lesson-item {
  display: flex; align-items: flex-start; gap: 12px; text-align: left;
  padding: 12px 16px; background: #F0F9FF; border: 1px solid #BAE6FD; border-radius: 12px;
  font-size: 13.5px; color: #334155; line-height: 1.7;
}
.lesson-no {
  width: 24px; height: 24px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  background: #0369A1; color: #FFF; font-weight: 700; font-size: 12px; margin-top: 1px;
}
.ending-card .verdict-actions { justify-content: center; }

/* ── 普法海报 ── */
.poster-controls { background: #FFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 16px 20px; margin-bottom: 20px; }
.poster-topic-row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.poster-input { width: 240px; }
.poster-theme-row { display: flex; align-items: center; gap: 12px; margin-top: 14px; flex-wrap: wrap; }
.theme-label { font-size: 12.5px; color: #94A3B8; }
.poster-body { min-height: 320px; }
.poster-preview { display: flex; flex-direction: column; align-items: center; gap: 16px; }
.poster-canvas { width: 460px; max-width: 100%; border-radius: 14px; box-shadow: 0 14px 40px rgba(3, 105, 161, .16); }
.poster-actions { display: flex; align-items: center; gap: 14px; }
.poster-hint { font-size: 12px; color: #94A3B8; }
.poster-empty {
  display: flex; align-items: center; justify-content: center; min-height: 320px;
  color: #94A3B8; font-size: 13.5px; text-align: center; padding: 0 40px;
}

/* ── 预置图库（海报画廊 / 短片列表） ── */
.preset-section { margin-top: 22px; }
.preset-head { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.preset-head h4 { font-size: 14.5px; color: #334155; margin: 0; font-weight: 600; }
.preset-badge {
  font-size: 11.5px; font-weight: 600; color: #059669; background: #D1FAE5;
  padding: 2px 10px; border-radius: 999px; letter-spacing: .5px;
}
.preset-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 14px; }
.preset-card {
  background: #FFF; border: 1px solid #E2E8F0; border-radius: 14px; overflow: hidden;
  cursor: pointer; transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
}
.preset-card:hover { transform: translateY(-3px); box-shadow: 0 8px 20px rgba(30, 64, 175, .10); }
.preset-card.on { border-color: #2F54EB; box-shadow: 0 0 0 2px rgba(47, 84, 235, .18); }

.poster-card-top { padding: 14px 16px; min-height: 96px; display: flex; flex-direction: column; gap: 6px; }
.preset-card-topic {
  align-self: flex-start; font-size: 11px; font-weight: 600; color: #FFF;
  background: rgba(255, 255, 255, .22); border: 1px solid rgba(255, 255, 255, .35);
  padding: 1px 9px; border-radius: 999px;
}
.poster-card-title { color: #FFF; font-size: 15.5px; line-height: 1.4; }
.poster-card-slogan { margin: 10px 16px 0; font-size: 12.5px; color: #475569; line-height: 1.6; }
.poster-card-point { margin: 4px 16px 14px; font-size: 12px; color: #94A3B8; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.video-card { padding: 14px 16px; }
.video-card-top { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 10px; }
.video-card-meta { font-size: 11.5px; color: #94A3B8; white-space: nowrap; }
.video-card-title { display: block; font-size: 14.5px; color: #1E293B; line-height: 1.5; }

/* ── 普法短片 ── */
.video-body { min-height: 320px; }
.video-player { display: grid; grid-template-columns: 1fr 320px; gap: 24px; align-items: start; }
.video-screen {
  position: relative; height: 420px; border-radius: 16px; overflow: hidden;
  display: flex; align-items: center; justify-content: center; cursor: pointer;
  transition: background .6s ease;
}
.video-theme-0 { background: linear-gradient(135deg, #0B3A6B, #0369A1); }
.video-theme-1 { background: linear-gradient(135deg, #7F1D1D, #DC2626); }
.video-theme-2 { background: linear-gradient(135deg, #7C2D12, #EA580C); }
.video-theme-3 { background: linear-gradient(135deg, #064E3B, #059669); }
.video-scene { text-align: center; padding: 0 44px; animation: fadeInUp .45s ease; }
.video-scene-no {
  position: absolute; top: 18px; right: 20px; font-size: 12px; color: rgba(255,255,255,.7);
}
.video-visual { margin: 0; font-size: 40px; font-weight: 800; color: #FFF; line-height: 1.5; letter-spacing: 2px; text-shadow: 0 2px 12px rgba(0,0,0,.2); }
.video-subtitle { margin: 22px 0 0; font-size: 16px; color: rgba(255,255,255,.92); line-height: 1.9; }
.video-controls {
  position: absolute; left: 0; right: 0; bottom: 0;
  display: flex; align-items: center; gap: 14px; padding: 14px 20px;
  background: linear-gradient(transparent, rgba(0,0,0,.45));
}
.video-progress { display: flex; gap: 8px; flex: 1; }
.video-dot { flex: 1; height: 4px; border-radius: 2px; background: rgba(255,255,255,.3); cursor: pointer; transition: background .3s; }
.video-dot.on { background: rgba(255,255,255,.85); }
.video-dot.active { background: #FDBA74; }
.video-side { background: #FFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 20px; }
.video-title { margin: 0 0 14px; font-size: 17px; font-weight: 700; color: #1E293B; padding-bottom: 12px; border-bottom: 1px solid #F1F5F9; }
.video-script { display: flex; flex-direction: column; gap: 8px; }
.script-item {
  display: flex; flex-direction: column; gap: 4px; padding: 10px 14px;
  border-radius: 10px; cursor: pointer; transition: all .2s; border: 1px solid transparent;
}
.script-item b { font-size: 12px; color: #0369A1; }
.script-item span { font-size: 12.5px; color: #64748B; line-height: 1.7; }
.script-item:hover { background: #F8FAFC; }
.script-item.active { background: #F0F9FF; border-color: #BAE6FD; }
.video-side .poster-hint { display: block; margin-top: 14px; line-height: 1.7; }

/* ── 通用动画 ── */
.fade-enter-active, .fade-leave-active { transition: opacity .4s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

@media (max-width: 900px) {
  .faq-layout { grid-template-columns: 1fr; }
  .faq-list { max-height: 300px; }
  .source-card { flex: 0 0 100%; }
  .video-player { grid-template-columns: 1fr; }
  .poster-canvas { width: 100%; }
}
</style>
