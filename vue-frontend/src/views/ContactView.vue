<template>
  <div class="contact-page">
    <div class="page-head">
      <div>
        <h2 class="page-title">联系我们</h2>
        <p class="page-subtitle">对本系统有任何疑问、建议或合作意向，欢迎通过以下方式与我们取得联系</p>
      </div>
    </div>

    <!-- 项目简介 -->
    <section class="panel about-panel animate-fade-in-up">
      <div class="panel-head"><span class="panel-index">壹</span><h3>关于本系统</h3></div>
      <p class="about-text">
        <b>劳动法律智能问答系统</b> —— 面向劳动法领域的智能问答与普法平台。
        系统融合 BM25 关键词检索、向量语义检索与知识图谱关系检索，结合大语言模型生成回答，
        支持时效感知、新旧条文修订对比、检索过程可视化、智能案情诊断与互动式普法，
        为劳动者提供便捷、可靠的法律知识服务。
      </p>
      <div class="tech-chips">
        <span class="tech-chip">Vue 3</span>
        <span class="tech-chip">Spring Boot</span>
        <span class="tech-chip">FastAPI</span>
        <span class="tech-chip">Neo4j 知识图谱</span>
        <span class="tech-chip">MySQL</span>
        <span class="tech-chip">BM25 + FAISS 混合检索</span>
        <span class="tech-chip">DeepSeek 大模型</span>
      </div>
    </section>

    <!-- 联系方式 -->
    <section class="panel animate-fade-in-up">
      <div class="panel-head"><span class="panel-index">贰</span><h3>联系方式</h3></div>
      <div class="contact-grid">
        <a v-for="c in contacts" :key="c.label" class="contact-card" :href="c.link || undefined" :target="c.link ? '_blank' : undefined">
          <div class="contact-icon" :style="{ background: c.bg, color: c.color }">{{ c.icon }}</div>
          <div class="contact-info">
            <div class="contact-label">{{ c.label }}</div>
            <div class="contact-value">{{ c.value }}</div>
          </div>
        </a>
      </div>
    </section>

    <!-- 意见反馈 -->
    <section class="panel animate-fade-in-up">
      <div class="panel-head"><span class="panel-index">叁</span><h3>意见与反馈</h3></div>
      <ul class="feedback-list">
        <li>对回答质量不满意？可在「问答记录与评估」页对每条回答进行 ⭐ 评分与评价，帮助我们改进。</li>
        <li>发现法条引用错误或时效状态标注有误？请附上问题截图与具体说明发送至上方邮箱。</li>
        <li>有想了解但系统中没有的劳动法律主题？欢迎提出，我们将扩充语料库与知识图谱。</li>
      </ul>
    </section>

    <!-- 免责声明 -->
    <div class="disclaimer">
      ⚖️ 本系统仅用于学术研究与法律知识科普，生成内容基于现行法律法规与公开案例，
      不构成正式法律意见；涉及具体纠纷，请咨询执业律师或当地劳动监察部门。
    </div>
  </div>
</template>

<script setup>
// ── 联系方式（按需修改此处即可） ──
const contacts = [
  { label: '电子邮箱', value: 'your-email@example.com', icon: '✉️', link: 'mailto:your-email@example.com', bg: '#eef4ff', color: '#2f54eb' },
  { label: '联系电话', value: '138-XXXX-XXXX', icon: '📞', bg: '#f0fdf4', color: '#16a34a' },
  { label: '微信', value: '微信同号，添加请备注「劳动法问答」', icon: '💬', bg: '#f5f3ff', color: '#7c3aed' },
  { label: '学校 / 单位', value: 'XX 大学 · 计算机学院', icon: '🏫', bg: '#fff7ed', color: '#ea580c' },
  { label: '地址', value: 'XX省XX市XX区XX路XX号', icon: '📍', bg: '#fef2f2', color: '#dc2626' },
  { label: '在线反馈', value: '登录后在「问答记录与评估」页对回答评分', icon: '⭐', bg: '#fffbeb', color: '#ca8a04' },
]
</script>

<style scoped>
.contact-page { max-width: 920px; margin: 0 auto; }

.about-text { color: var(--text-secondary, #475569); line-height: 1.9; font-size: 14px; }
.about-text b { color: var(--text-primary, #1e293b); }

.tech-chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 16px; }
.tech-chip {
  padding: 5px 14px; border-radius: 999px; font-size: 12.5px;
  background: #eef4ff; color: #2f54eb; border: 1px solid #dbe6ff;
}

.contact-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(270px, 1fr)); gap: 14px; margin-top: 6px; }
.contact-card {
  display: flex; align-items: center; gap: 14px; padding: 16px 18px;
  background: #f8fafc; border: 1px solid #eef1f5; border-radius: 14px;
  text-decoration: none; transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
}
.contact-card:hover { transform: translateY(-3px); box-shadow: 0 8px 20px rgba(30, 64, 175, .10); border-color: #d4defc; }
.contact-icon {
  width: 44px; height: 44px; border-radius: 12px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; font-size: 21px;
}
.contact-label { font-size: 12.5px; color: #64748b; }
.contact-value { font-size: 14px; color: #1e293b; font-weight: 600; margin-top: 2px; word-break: break-all; }

.edit-hint { margin-top: 14px; font-size: 12.5px; color: #94a3b8; }
.edit-hint code { background: #f1f5f9; padding: 1px 6px; border-radius: 5px; }

.feedback-list { padding-left: 20px; margin: 4px 0 0; }
.feedback-list li { color: var(--text-secondary, #475569); font-size: 14px; line-height: 2; }

.disclaimer {
  margin-top: 18px; padding: 14px 18px; border-radius: 12px; font-size: 13px;
  background: #fffbeb; border: 1px solid #fde68a; color: #92400e; line-height: 1.8;
}
</style>
