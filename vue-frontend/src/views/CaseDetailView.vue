<template>
  <div class="case-detail" v-if="c">
    <button class="back-link" @click="$router.push('/app/cases')">
      <span>←</span> 返回案例库
    </button>

    <div class="case-head">
      <div class="case-no">{{ c.caseNumber }}</div>
      <div class="case-meta">
        <span class="court-name">{{ c.court }}</span>
        <span class="cat-tag">{{ c.category || '劳动争议' }}</span>
        <span class="judge-date">{{ c.judgeDate || '未知日期' }}</span>
      </div>
    </div>

    <div class="keyword-row" v-if="keywordList.length">
      <span class="kw-label">关键词</span>
      <span class="kw-chip" v-for="(kw,i) in keywordList" :key="i">{{ kw }}</span>
    </div>

    <section class="panel" v-if="c.caseContent">
      <div class="panel-head"><span class="panel-index">壹</span><h3>案例内容</h3></div>
      <div class="panel-body">{{ c.caseContent }}</div>
    </section>

    <section class="panel" v-if="c.reasoning">
      <div class="panel-head"><span class="panel-index">贰</span><h3>法院认为</h3></div>
      <div class="panel-body reason">{{ c.reasoning }}</div>
    </section>

    <section class="panel" v-if="c.judgment">
      <div class="panel-head"><span class="panel-index">叁</span><h3>判决结果</h3></div>
      <div class="panel-body result">{{ c.judgment }}</div>
    </section>

    <section class="panel" v-if="c.legalBasis">
      <div class="panel-head"><span class="panel-index">肆</span><h3>引用法条</h3></div>
      <div class="law-list">
        <div v-for="(law,i) in lawList" :key="i" class="law-item">
          <span class="law-dot"></span>{{ law }}
        </div>
      </div>
    </section>
  </div>
  <div v-else class="loading" v-loading="true">加载中...</div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import api from '../api'
const route = useRoute(), c = ref(null)
const keywordList = computed(() => { if(!c.value?.keywords)return[];const kw=c.value.keywords;return typeof kw==='string'?kw.split(';').filter(Boolean):Array.isArray(kw)?kw:[] })
const lawList = computed(() => { if(!c.value?.legalBasis)return[];return c.value.legalBasis.split(';').filter(Boolean) })
watch(()=>route.params.id,async(id)=>{c.value=null;const res=await api.get(`/cases/${id}`);if(res.code===200)c.value=res.data},{immediate:true})
</script>

<style scoped>
.case-detail { max-width: 900px; margin: 0 auto; padding-bottom: 40px; }

.back-link {
  display: inline-flex; align-items: center; gap: 6px;
  border: none; background: none; color: #0369A1;
  font-size: 13px; cursor: pointer; padding: 0;
  margin-bottom: 20px; font-family: inherit;
  transition: color 0.15s;
}
.back-link:hover { color: #0284C7; }

.case-head {
  margin-bottom: 16px;
  padding-bottom: 20px;
  border-bottom: 1px solid #E2E8F0;
}
.case-no { font-size: 24px; font-weight: 700; color: var(--text-primary); letter-spacing: 0.5px; }
.case-meta { display: flex; align-items: center; gap: 12px; margin-top: 10px; }
.court-name { font-size: 13px; color: #64748B; }
.cat-tag {
  font-size: 11px; font-weight: 500;
  padding: 3px 10px; border-radius: 20px;
  background: #0369A1; color: #FFF;
}
.judge-date { font-size: 12px; color: #94A3B8; font-family: 'Space Grotesk', sans-serif; }

.keyword-row {
  display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
  margin-bottom: 24px;
}
.kw-label { font-size: 11px; color: #94A3B8; letter-spacing: 2px; font-weight: 600; }
.kw-chip {
  font-size: 12px; color: #475569;
  padding: 3px 12px; border-radius: 20px;
  background: #F8FAFC; border: 1px solid #EEF2F7;
}

.panel {
  background: #FFF;
  border: 1px solid #E2E8F0;
  border-radius: 14px;
  padding: 24px 28px;
  margin-bottom: 20px;
}
.panel-head {
  display: flex; align-items: center; gap: 10px;
  margin-bottom: 16px; padding-bottom: 12px;
  border-bottom: 1px solid #F1F5F9;
}
.panel-index {
  font-size: 11px; font-weight: 700; color: #0369A1;
  padding: 2px 8px; border: 1px solid #BAE6FD; border-radius: 6px;
  background: #F0F9FF; font-family: 'Noto Serif SC', serif;
}
.panel-head h3 { margin: 0; font-size: 15px; font-weight: 700; color: #1E293B; }
.panel-body {
  line-height: 2; font-size: 15px; color: #334155;
  text-indent: 2em; white-space: pre-wrap;
}
.panel-body.reason { color: #1E40AF; }
.panel-body.result { color: #065F46; }

.law-list { display: flex; flex-direction: column; gap: 8px; }
.law-item {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 14px;
  background: #F8FAFC; border-radius: 10px;
  font-size: 14px; color: #1E40AF;
  border-left: 3px solid #0369A1;
  transition: all 0.2s;
}
.law-item:hover { background: #EFF6FF; }
.law-dot { width: 6px; height: 6px; background: #0369A1; border-radius: 50%; flex-shrink: 0; }

.loading { text-align: center; padding: 100px; color: var(--text-muted); }
</style>
