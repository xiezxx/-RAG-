<template>
  <!-- 左下角 · 法律解答宠物「法小鹰」（可拖拽） -->
  <div
    class="owl-assistant"
    :class="{ dragging }"
    :style="posStyle"
  >
    <!-- 折叠时：立体猫头鹰 -->
    <button
      v-if="!expanded"
      class="owl-fab"
      :class="{ listening }"
      @mousedown="startDrag"
      @touchstart="startDrag"
      @click="onFabClick"
      title="法小鹰 · 语音助手（可拖动）"
    >
      <div class="owl-3d" :class="{ awake: listening }">
        <!-- 猫头鹰 SVG -->
        <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
          <!-- 身体（法官袍） -->
          <path d="M14 30c0-9 8-16 18-16s18 7 18 16c0 10-5 18-10 22H24c-5-4-10-12-10-22z" fill="#1E293B" stroke="#334155" stroke-width="1.5"/>
          <!-- 腹部 -->
          <path d="M24 32c0-5 4-9 8-9s8 4 8 9c0 6-3 12-8 12s-8-6-8-12z" fill="#F1F5F9" opacity="0.9"/>
          <!-- 法袍前襟 -->
          <path d="M28 24l-6 20M36 24l6 20" stroke="#38BDF8" stroke-width="1.5" stroke-linecap="round" opacity="0.6"/>
          <!-- 翅膀 -->
          <path d="M14 30c-3-1-6-1-8 1 3 5 5 8 8 9M50 30c3-1 6-1 8 1-3 5-5 8-8 9" fill="#0F172A" stroke="#334155" stroke-width="1"/>
          <!-- 眼睛（左） -->
          <g class="owl-eye owl-eye-l">
            <circle cx="23" cy="24" r="6" fill="#FFF8DC" stroke="#1E293B" stroke-width="1"/>
            <circle cx="23" cy="24" r="2.6" class="owl-pupil" fill="#38BDF8"/>
          </g>
          <!-- 眼睛（右） -->
          <g class="owl-eye owl-eye-r">
            <circle cx="41" cy="24" r="6" fill="#FFF8DC" stroke="#1E293B" stroke-width="1"/>
            <circle cx="41" cy="24" r="2.6" class="owl-pupil" fill="#38BDF8"/>
          </g>
          <!-- 耳朵 -->
          <path d="M17 20l-4-7M21 17l-2-8" stroke="#1E293B" stroke-width="2" stroke-linecap="round" class="owl-ear owl-ear-l"/>
          <path d="M47 20l4-7M43 17l2-8" stroke="#1E293B" stroke-width="2" stroke-linecap="round" class="owl-ear owl-ear-r"/>
          <!-- 喙 -->
          <path d="M30 30c1.5 1.5 2.5 1.5 4 0l-2 4z" fill="#C9A84C" stroke="#8B6914" stroke-width="0.8" class="owl-beak"/>
          <!-- 金法徽 -->
          <circle cx="32" cy="44" r="3" fill="#C9A84C" stroke="#8B6914" stroke-width="0.8"/>
          <!-- 腿 -->
          <path d="M27 54l-2 6M37 54l2 6" stroke="#C9A84C" stroke-width="2" stroke-linecap="round"/>
        </svg>
        <!-- 听录音效环 -->
        <span v-if="listening" class="owl-ring r1"></span>
        <span v-if="listening" class="owl-ring r2"></span>
      </div>
      <!-- 名字标签 -->
      <span class="owl-name-tag">法小鹰</span>
    </button>

    <!-- 展开：面板 -->
    <transition name="va-pop">
      <div v-if="expanded" class="owl-panel">
        <!-- 顶部：宠物形象 + 状态 -->
        <div class="owl-panel-head">
          <div class="owl-mini" :class="{ awake: listening }">
            <svg width="44" height="44" viewBox="0 0 64 64" fill="none">
              <path d="M14 30c0-9 8-16 18-16s18 7 18 16c0 10-5 18-10 22H24c-5-4-10-12-10-22z" fill="#1E293B" stroke="#334155" stroke-width="1.5"/>
              <path d="M24 32c0-5 4-9 8-9s8 4 8 9c0 6-3 12-8 12s-8-6-8-12z" fill="#F1F5F9" opacity="0.9"/>
              <path d="M17 20l-4-7M21 17l-2-8" stroke="#1E293B" stroke-width="2" stroke-linecap="round" class="owl-ear owl-ear-l"/>
              <path d="M47 20l4-7M43 17l2-8" stroke="#1E293B" stroke-width="2" stroke-linecap="round" class="owl-ear owl-ear-r"/>
              <circle cx="23" cy="24" r="5.5" fill="#FFF8DC" stroke="#1E293B" stroke-width="1"/>
              <circle cx="41" cy="24" r="5.5" fill="#FFF8DC" stroke="#1E293B" stroke-width="1"/>
              <circle cx="23" cy="24" r="2.4" class="owl-pupil" fill="#38BDF8"/>
              <circle cx="41" cy="24" r="2.4" class="owl-pupil" fill="#38BDF8"/>
              <path d="M30 30c1.5 1.5 2.5 1.5 4 0l-2 4z" fill="#C9A84C" stroke="#8B6914" stroke-width="0.8" class="owl-beak"/>
            </svg>
          </div>
          <div class="owl-panel-title">
            <span class="owl-name">法小鹰</span>
            <span class="owl-motto" :class="{ active: listening }">
              {{ listening ? '正在聆听您的法律问题...' : '随时为您解答劳动法' }}
            </span>
          </div>
          <button class="owl-close" @click="expanded = false">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>

        <!-- 听写区 -->
        <div class="owl-body">
          <div class="owl-transcript" :class="{ empty: !transcript }">
            {{ transcript || '点击下方开始，说出您的劳动法律问题' }}
          </div>

          <div class="owl-controls">
            <button class="owl-btn" :class="{ danger: listening }" @click="toggleListen" :disabled="!supported">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <template v-if="!listening"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" /><path d="M19 10v2a7 7 0 0 1-14 0v-2" /><line x1="12" y1="19" x2="12" y2="23" /></template>
                <template v-else><rect x="6" y="4" width="4" height="12" rx="1"/><rect x="14" y="4" width="4" height="12" rx="1"/></template>
              </svg>
              {{ listening ? '停止聆听' : '开始说话' }}
            </button>
            <button class="owl-btn primary" @click="sendToChat" :disabled="!transcript">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><polyline points="19 12 12 19 5 12"/></svg>
              发问
            </button>
          </div>

          <p v-if="!supported" class="owl-unsupported">当前浏览器不支持语音，请用 Chrome / Edge</p>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, onBeforeUnmount, computed } from 'vue'
import { ElMessage } from 'element-plus'

const expanded = ref(false)
const listening = ref(false)
const transcript = ref('')
const supported = ref(false)
const dragging = ref(false)

// ── 拖拽状态 ──
const pos = ref({ x: 20, y: 20 })   // 相对右下角的偏移
let dragStart = null                // { mouseX, mouseY, origX, origY }
let moved = false

// 记住上次位置（localStorage）
const saved = localStorage.getItem('owl-pos')
if (saved) {
  try { pos.value = JSON.parse(saved) } catch {}
}

const posStyle = computed(() => ({
  left: pos.value.x + 'px',
  bottom: pos.value.y + 'px'
}))

function startDrag(e) {
  // 只有折叠态可拖拽
  if (expanded.value) return
  const clientX = e.touches ? e.touches[0].clientX : e.clientX
  const clientY = e.touches ? e.touches[0].clientY : e.clientY
  dragStart = { clientX, clientY, origX: pos.value.x, origY: pos.value.y }
  moved = false
  dragging.value = true

  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', endDrag)
  document.addEventListener('touchmove', onDrag, { passive: false })
  document.addEventListener('touchend', endDrag)
  // 阻止默认拖动图片/文本
  if (e.preventDefault) e.preventDefault()
}

function onDrag(e) {
  if (!dragStart) return
  const clientX = e.touches ? e.touches[0].clientX : e.clientX
  const clientY = e.touches ? e.touches[0].clientY : e.clientY
  const dx = clientX - dragStart.clientX
  const dy = clientY - dragStart.clientY

  // 移动超过阈值视为拖动（区分点击）
  if (!moved && Math.hypot(dx, dy) > 5) moved = true

  // 新位置 = 原始位置 + 位移
  pos.value = {
    x: dragStart.origX + dx,
    y: dragStart.origY - dy   // bottom 向上为正
  }
}

function endDrag() {
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', endDrag)
  document.removeEventListener('touchmove', onDrag)
  document.removeEventListener('touchend', endDrag)
  dragging.value = false
  dragStart = null

  // 保存位置
  try { localStorage.setItem('owl-pos', JSON.stringify(pos.value)) } catch {}
}

// 点击展开时，若发生了拖动则不展开
function onFabClick() {
  if (moved) { moved = false; return }
  expanded.value = true
}

let recognition = null
let synth = null

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
if (SpeechRecognition) {
  supported.value = true
  recognition = new SpeechRecognition()
  recognition.lang = 'zh-CN'
  recognition.continuous = false
  recognition.interimResults = true

  recognition.onresult = (e) => {
    let final = ''
    for (let i = e.resultIndex; i < e.results.length; i++) {
      if (e.results[i].isFinal) final += e.results[i][0].transcript
    }
    if (final) {
      transcript.value = final
      listening.value = false
    }
  }
  recognition.onerror = (e) => {
    listening.value = false
    if (e.error === 'not-allowed') ElMessage.warning('麦克风权限被拒绝，请在浏览器设置中允许')
    else if (e.error !== 'no-speech') ElMessage.error('语音识别出错：' + e.error)
  }
  recognition.onend = () => { listening.value = false }
}

if ('speechSynthesis' in window) synth = window.speechSynthesis

function toggleListen() {
  if (!recognition) return
  if (listening.value) {
    recognition.stop()
    listening.value = false
  } else {
    transcript.value = ''
    try { recognition.start() } catch {}
    listening.value = true
  }
}

function sendToChat() {
  if (!transcript.value) return
  const q = transcript.value
  transcript.value = ''
  expanded.value = false
  window.dispatchEvent(new CustomEvent('voice-question', { detail: { text: q } }))
  ElMessage.success('已发送：' + q)
}

function speak(text) {
  if (!synth) return
  synth.cancel()
  const u = new SpeechSynthesisUtterance(text.replace(/[#*`_>\[\]|]/g, ''))
  u.lang = 'zh-CN'
  u.rate = 1
  synth.speak(u)
}
window.speakAssistantText = speak

onBeforeUnmount(() => {
  if (recognition) recognition.abort()
})
</script>

<style scoped>
.owl-assistant {
  position: fixed;
  z-index: 999;
  perspective: 600px;
  transition: left 0.2s ease, bottom 0.2s ease;
  display: flex; flex-direction: column-reverse;  /* 面板显示在按钮上方 */
  align-items: flex-start;
}
.owl-assistant.dragging {
  transition: none;
  cursor: grabbing;
}
.owl-assistant.dragging .owl-fab { cursor: grabbing; }
.owl-assistant.dragging .owl-3d { transform: scale(1.05); box-shadow: 0 12px 36px rgba(0,0,0,0.5); }

/* ═══════ 折叠：立体猫头鹰 ═══════ */
.owl-fab {
  position: relative;
  border: none; background: none; cursor: pointer;
  padding: 0;
  display: flex; flex-direction: column; align-items: center;
  gap: 4px;
}
.owl-3d {
  width: 68px; height: 68px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  background:
    radial-gradient(circle at 32% 28%, rgba(255,255,255,0.14), transparent 45%),
    radial-gradient(circle at 50% 50%, rgba(56,189,248,0.1), rgba(15,23,42,0.85) 70%);
  border: 1px solid rgba(56,189,248,0.25);
  box-shadow:
    0 8px 28px rgba(0,0,0,0.45),
    0 0 30px rgba(56,189,248,0.08),
    inset 0 1px 0 rgba(255,255,255,0.1);
  transition: transform 0.35s cubic-bezier(0.34,1.56,0.64,1), box-shadow 0.3s;
}
.owl-3d:hover { transform: translateY(-4px) rotateX(-4deg) rotateY(3deg) scale(1.03); }
.owl-3d.awake { animation: owlBob 0.9s ease infinite; }
@keyframes owlBob {
  0%,100% { transform: translateY(0) rotateZ(0); }
  25% { transform: translateY(-3px) rotateZ(-1.5deg); }
  75% { transform: translateY(0) rotateZ(1.5deg); }
}

/* 猫头鹰动画 */
.owl-eye { transform-origin: center; animation: owlBlink 4s ease infinite; }
.owl-eye-l { animation-delay: 0s; }
.owl-eye-r { animation-delay: 0s; }
@keyframes owlBlink {
  0%, 92%, 100% { transform: scaleY(1); }
  95% { transform: scaleY(0.1); }
}
.owl-pupil { transform-origin: center; }
.owl-3d.awake .owl-pupil { animation: pupilScan 2.4s ease infinite; }
@keyframes pupilScan {
  0%,100% { transform: translateX(0); }
  25% { transform: translateX(-1px); }
  50% { transform: translateX(1.5px); }
  75% { transform: translateX(0.5px); }
}
.owl-ear { transform-origin: bottom; }
.owl-3d.awake .owl-ear { animation: owlEar 1.8s ease infinite; }
@keyframes owlEar {
  0%,100% { transform: rotate(0); }
  50% { transform: rotate(-6deg); }
}
.owl-3d.awake .owl-ear-r { animation-name: owlEarR; }
@keyframes owlEarR {
  0%,100% { transform: rotate(0); }
  50% { transform: rotate(6deg); }
}
.owl-beak { transform-origin: top; }
.owl-3d.awake .owl-beak { animation: owlTalk 0.4s ease infinite alternate; }
@keyframes owlTalk {
  from { transform: scaleY(1); }
  to { transform: scaleY(0.5); }
}

/* 听录音效环 */
.owl-ring {
  position: absolute; inset: 0;
  border-radius: 50%;
  border: 2px solid rgba(56,189,248,0.5);
  animation: owlRing 1.6s ease-out infinite;
  pointer-events: none;
}
.owl-ring.r2 { animation-delay: 0.8s; }
@keyframes owlRing {
  from { transform: scale(1); opacity: 0.8; }
  to { transform: scale(1.5); opacity: 0; }
}

/* 名字标签 */
.owl-name-tag {
  font-size: 10px; color: #94A3B8;
  letter-spacing: 1px;
  background: rgba(15,23,42,0.7);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 8px;
  padding: 2px 8px;
  backdrop-filter: blur(8px);
}

/* ═══════ 展开面板 ═══════ */
.owl-panel {
  width: 310px;
  background: rgba(15,23,42,0.93);
  backdrop-filter: blur(18px);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 18px;
  overflow: hidden;
  box-shadow: 0 24px 70px rgba(0,0,0,0.55);
  margin-bottom: 12px;
}
.owl-panel-head {
  display: flex; align-items: center; gap: 12px;
  padding: 14px 16px;
  background: linear-gradient(135deg, rgba(56,189,248,0.08), transparent);
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.owl-mini { flex-shrink: 0; }
.owl-mini.awake { animation: owlBob 0.9s ease infinite; }
.owl-panel-title { flex: 1; display: flex; flex-direction: column; }
.owl-name { font-size: 14px; font-weight: 700; color: #F1F5F9; letter-spacing: 1px; }
.owl-motto { font-size: 11px; color: #64748B; margin-top: 2px; transition: color 0.2s; }
.owl-motto.active { color: #38BDF8; }
.owl-close {
  width: 24px; height: 24px;
  display: flex; align-items: center; justify-content: center;
  background: transparent; border: none; cursor: pointer;
  color: #64748B; border-radius: 6px;
  transition: all 0.15s;
}
.owl-close:hover { background: rgba(255,255,255,0.08); color: #E2E8F0; }

.owl-body { padding: 16px; }
.owl-transcript {
  min-height: 44px;
  padding: 12px 14px;
  border-radius: 10px;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.08);
  font-size: 13px; color: #E2E8F0; line-height: 1.7;
  max-height: 90px; overflow-y: auto;
}
.owl-transcript.empty { color: #475569; font-size: 12px; }

.owl-controls { display: flex; gap: 8px; margin-top: 14px; }
.owl-btn {
  flex: 1;
  display: flex; align-items: center; justify-content: center; gap: 6px;
  padding: 10px 0;
  border-radius: 10px;
  border: 1px solid rgba(255,255,255,0.12);
  background: rgba(255,255,255,0.06);
  color: #E2E8F0; font-size: 13px; cursor: pointer;
  transition: all 0.2s;
  font-family: inherit;
}
.owl-btn:hover:not(:disabled) { background: rgba(255,255,255,0.12); }
.owl-btn.danger { background: rgba(239,68,68,0.15); border-color: rgba(239,68,68,0.3); color: #F87171; }
.owl-btn.primary {
  background: linear-gradient(135deg, #0369A1, #38BDF8);
  border-color: transparent; color: #FFF;
  font-weight: 600;
}
.owl-btn.primary:hover:not(:disabled) { box-shadow: 0 4px 16px rgba(56,189,248,0.3); }
.owl-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.owl-unsupported { margin: 10px 0 0; font-size: 11px; color: #F87171; text-align: center; }

/* 面板弹出 */
.va-pop-enter-active { transition: all 0.25s cubic-bezier(0.22,1,0.36,1); }
.va-pop-leave-active { transition: all 0.15s ease; }
.va-pop-enter-from, .va-pop-leave-to { opacity: 0; transform: translateY(12px) scale(0.96); }

@media (prefers-reduced-motion: reduce) {
  .owl-3d, .owl-3d.awake, .owl-eye, .owl-pupil, .owl-ear, .owl-beak, .owl-ring { animation: none !important; }
}
</style>
