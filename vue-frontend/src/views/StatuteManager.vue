<template>
  <div class="statute-manager">
    <div class="page-head">
      <div>
        <h2 class="page-title">法规文档管理</h2>
        <p class="page-subtitle">法律法规维护与录入</p>
      </div>
      <el-button type="primary" @click="openAdd" round>
        <el-icon><Plus /></el-icon> 录入新法规
      </el-button>
    </div>

    <!-- Edit dialog -->
    <el-dialog v-model="dialogVisible" :title="editing ? '编辑法规' : '录入法规'" width="560px" class="form-dialog">
      <el-form :model="form" label-width="90px">
        <el-form-item label="法规名称" required>
          <el-input v-model="form.name" placeholder="如：中华人民共和国劳动法" />
        </el-form-item>
        <el-form-item label="文号">
          <el-input v-model="form.documentNumber" placeholder="如：主席令第XX号" />
        </el-form-item>
        <el-form-item label="发布机关">
          <el-input v-model="form.issuingAuthority" placeholder="如：全国人民代表大会常务委员会" />
        </el-form-item>
        <el-form-item label="适用地区">
          <el-input v-model="form.applicableRegion" placeholder="如：全国 / 北京市" />
        </el-form-item>
        <el-form-item label="适用主体">
          <el-input v-model="form.applicableSubject" placeholder="如：企业、个体工商户、民办非企业单位" />
        </el-form-item>
        <el-form-item label="类别">
          <el-select v-model="form.category" style="width:100%">
            <el-option label="法律" value="法律" />
            <el-option label="行政法规" value="行政法规" />
            <el-option label="司法解释" value="司法解释" />
            <el-option label="部门规章" value="部门规章" />
          </el-select>
        </el-form-item>
        <el-form-item label="条文数">
          <el-input-number v-model="form.articleCount" :min="0" />
        </el-form-item>
        <el-form-item label="发布日期">
          <el-input v-model="form.publishDate" placeholder="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="生效日期">
          <el-input v-model="form.effectiveDate" placeholder="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="效力状态">
          <el-select v-model="form.status" style="width:100%">
            <el-option label="🟢 现行有效" value="现行有效" />
            <el-option label="🟡 已被修订" value="已被修订" />
            <el-option label="🔴 已废止" value="已废止" />
            <el-option label="🔵 尚未生效" value="尚未生效" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false" round>取消</el-button>
        <el-button type="primary" @click="save" round>保存</el-button>
      </template>
    </el-dialog>

    <!-- Table -->
    <section class="panel">
      <div class="panel-head"><span class="panel-index">壹</span><h3>法规清单</h3><span class="panel-count">{{ statutes.length }} 部</span></div>
      <el-table :data="statutes" stripe v-loading="loading"
                :header-cell-style="{ background: '#F8FAFC', color: '#334155', fontWeight: 600, fontSize: '13px' }">
        <el-table-column label="名称" min-width="200">
          <template #default="{row}">
            <span class="statute-name">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="documentNumber" label="文号" width="140">
          <template #default="{row}">
            <span class="muted-text">{{ row.documentNumber || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="issuingAuthority" label="发布机关" width="160" show-overflow-tooltip />
        <el-table-column prop="applicableRegion" label="适用地区" width="100" />
        <el-table-column label="状态" width="110">
          <template #default="{row}">
            <el-tag :type="statusColor(row.status)" size="small" effect="dark" round>
              {{ row.status || '现行有效' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="类别" width="100">
          <template #default="{row}">
            <el-tag :type="row.category==='法律'?'primary':'warning'" size="small" effect="light" round>
              {{ row.category }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="articleCount" label="条文数" width="80" align="center" />
        <el-table-column label="生效日期" width="120">
          <template #default="{row}">
            <span class="muted-text">{{ row.effectiveDate || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{row}">
            <el-button size="small" @click="openEdit(row)" round>编辑</el-button>
            <el-button size="small" type="danger" @click="remove(row)" round>删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import api from '../api'

const statutes = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const editing = ref(null)
const form = ref({ name: '', documentNumber: '', issuingAuthority: '', applicableRegion: '全国', applicableSubject: '', category: '法律', articleCount: 0, publishDate: '', effectiveDate: '', status: '现行有效' })

function statusColor(s) {
  return s === '现行有效' ? 'success' : s === '已被修订' ? 'warning' : s === '已废止' ? 'danger' : 'info'
}

async function load() {
  loading.value = true
  try {
    const r = await api.get('/statutes')
    if (r.code === 200) statutes.value = r.data
  } catch (error) {
    console.warn('加载法条失败', error)
  }
  loading.value = false
}

function openAdd() {
  editing.value = null
  form.value = { name: '', documentNumber: '', issuingAuthority: '', applicableRegion: '全国', applicableSubject: '', category: '法律', articleCount: 0, publishDate: '', effectiveDate: '', status: '现行有效' }
  dialogVisible.value = true
}
function openEdit(row) {
  editing.value = row.id
  form.value = { ...row }
  dialogVisible.value = true
}

async function save() {
  try {
    if (editing.value) {
      await api.put(`/statutes/${editing.value}`, form.value)
      ElMessage.success('更新成功')
    } else {
      await api.post('/statutes', form.value)
      ElMessage.success('添加成功')
    }
    dialogVisible.value = false
    load()
  } catch { ElMessage.error('操作失败') }
}

async function remove(row) {
  await ElMessageBox.confirm(`确定删除「${row.name}」？`, '确认', { type: 'warning' })
  await api.delete(`/statutes/${row.id}`)
  ElMessage.success('已删除')
  load()
}

onMounted(load)
</script>

<style scoped>
.statute-manager { max-width: 1200px; margin: 0 auto; padding-bottom: 40px; }
.page-head { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 24px; }
.page-title { margin: 0; font-size: 24px; font-weight: 700; color: var(--text-primary); }
.page-subtitle { margin: 4px 0 0; font-size: 13px; color: var(--text-muted); }

.panel { background: #FFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 20px 24px; }
.panel-head { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid #F1F5F9; }
.panel-index { font-size: 11px; font-weight: 700; color: #0369A1; padding: 2px 8px; border: 1px solid #BAE6FD; border-radius: 6px; background: #F0F9FF; font-family: 'Noto Serif SC', serif; }
.panel-head h3 { margin: 0; font-size: 15px; font-weight: 700; color: #1E293B; flex: 1; }
.panel-count { font-size: 11px; color: #94A3B8; font-family: 'Space Grotesk', sans-serif; }

.statute-name { font-weight: 500; color: var(--text-primary); }
.muted-text { color: var(--text-muted); font-size: 13px; }
.form-dialog :deep(.el-dialog) { border-radius: 16px; }
</style>
