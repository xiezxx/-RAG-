<template>
  <div class="user-manager">
    <div class="page-head">
      <div>
        <h2 class="page-title">用户管理</h2>
        <p class="page-subtitle">系统用户与操作日志</p>
      </div>
    </div>

    <!-- 台账式统计 -->
    <div class="metric-ledger">
      <div class="metric-cell" v-for="s in statItems" :key="s.label">
        <div class="metric-num">{{ s.value }}</div>
        <div class="metric-label">{{ s.label }}</div>
      </div>
    </div>

    <!-- 用户列表 -->
    <section class="panel">
      <div class="panel-head">
        <span class="panel-index">壹</span><h3>用户列表</h3><span class="panel-count">{{ users.length }} 人</span>
        <el-button type="primary" size="small" round @click="openCreate">新增用户</el-button>
      </div>
      <el-table :data="users" stripe v-loading="loading"
                :header-cell-style="{ background: '#F8FAFC', color: '#334155', fontWeight: 600, fontSize: '13px' }">
        <el-table-column label="ID" prop="id" width="60" />
        <el-table-column label="用户名" prop="username" width="130" />
        <el-table-column label="姓名" prop="name" width="100" />
        <el-table-column label="联系方式" prop="phone" width="130" />
        <el-table-column label="角色" width="100">
          <template #default="{row}">
            <el-tag :type="roleTagType(row.role)" size="small" effect="dark" round>
              {{ roleLabel(row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{row}">
            <el-tag :type="row.status==='启用'?'success':'danger'" size="small" effect="plain" round>
              {{ row.status || '启用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="注册时间" width="170">
          <template #default="{row}">
            <span class="muted-text">{{ row.createdAt }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="370" fixed="right">
          <template #default="{row}">
            <el-button size="small" round @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="warning" round @click="toggleRole(row)">
              {{ nextRoleLabel(row.role) }}
            </el-button>
            <el-button size="small" @click="toggleStatus(row)" round :type="row.status==='启用'?'warning':'success'">
              {{ row.status==='启用'?'停用':'启用' }}
            </el-button>
            <el-button size="small" type="danger" @click="remove(row)" round>删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <!-- 操作日志 -->
    <section class="panel">
      <div class="panel-head"><span class="panel-index">贰</span><h3>操作日志</h3></div>
      <el-table :data="logs" stripe size="small" max-height="300"
                :header-cell-style="{ background: '#F8FAFC', color: '#334155', fontWeight: 600, fontSize: '13px' }">
        <el-table-column prop="username" label="用户" width="100" />
        <el-table-column prop="action" label="操作" width="100" />
        <el-table-column prop="target" label="详情" min-width="200">
          <template #default="{row}">
            <span class="log-target">{{ row.target }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="ip" label="IP" width="130" />
        <el-table-column label="时间" width="170">
          <template #default="{row}">
            <span class="muted-text time-text">{{ row.createdAt }}</span>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <!-- 登录记录 -->
    <section class="panel">
      <div class="panel-head"><span class="panel-index">叁</span><h3>登录记录</h3></div>
      <el-table :data="loginLogs" stripe size="small" max-height="300"
                :header-cell-style="{ background: '#F8FAFC', color: '#334155', fontWeight: 600, fontSize: '13px' }">
        <el-table-column prop="username" label="用户" width="120" />
        <el-table-column label="结果" width="90">
          <template #default="{row}">
            <el-tag :type="row.success ? 'success' : 'danger'" size="small" effect="plain" round>
              {{ row.success ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="说明" min-width="160">
          <template #default="{row}">
            <span class="muted-text">{{ row.message }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="ip" label="IP" width="130" />
        <el-table-column label="时间" width="170">
          <template #default="{row}">
            <span class="muted-text time-text">{{ row.createdAt }}</span>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <!-- 新增用户 -->
    <el-dialog v-model="createVisible" title="新增用户" width="460px">
      <el-form label-width="80px" @submit.prevent>
        <el-form-item label="用户名" required>
          <el-input v-model="createForm.username" placeholder="登录账号" />
        </el-form-item>
        <el-form-item label="密码" required>
          <el-input v-model="createForm.password" type="password" placeholder="不少于6位" show-password />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="createForm.name" placeholder="选填，默认同用户名" />
        </el-form-item>
        <el-form-item label="联系方式">
          <el-input v-model="createForm.phone" placeholder="选填" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="createForm.role" style="width: 100%">
            <el-option label="普通用户" value="USER" />
            <el-option label="研究人员" value="RESEARCHER" />
            <el-option label="管理员" value="ADMIN" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="createForm.status" style="width: 100%">
            <el-option label="启用" value="启用" />
            <el-option label="停用" value="停用" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button round @click="createVisible = false">取消</el-button>
        <el-button type="primary" round :loading="creating" @click="submitCreate">确认新增</el-button>
      </template>
    </el-dialog>

    <!-- 编辑用户信息 -->
    <el-dialog v-model="editVisible" title="编辑用户信息" width="420px">
      <el-form label-width="80px" @submit.prevent>
        <el-form-item label="用户名">
          <el-input :model-value="editForm.username" disabled />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="editForm.name" placeholder="用户姓名" />
        </el-form-item>
        <el-form-item label="联系方式">
          <el-input v-model="editForm.phone" placeholder="手机号/邮箱" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button round @click="editVisible = false">取消</el-button>
        <el-button type="primary" round :loading="saving" @click="submitEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import api from '../api'

const users = ref([])
const logs = ref([])
const loginLogs = ref([])
const loading = ref(false)
const statItems = ref([
  { label: '注册用户', value: 0 },
  { label: '问答记录', value: 0 },
  { label: '案例', value: 0 },
  { label: '法规', value: 0 }
])

// 三级角色：普通用户 → 研究人员 → 管理员
const ROLE_META = {
  ADMIN: { label: '管理员', type: 'danger' },
  RESEARCHER: { label: '研究人员', type: 'warning' },
  USER: { label: '普通用户', type: 'info' }
}
const ROLE_CYCLE = { USER: 'RESEARCHER', RESEARCHER: 'ADMIN', ADMIN: 'USER' }
const ROLE_NEXT_LABEL = { USER: '升为研究人员', RESEARCHER: '升为管理员', ADMIN: '降为普通用户' }

function roleLabel(role) { return (ROLE_META[role] || ROLE_META.USER).label }
function roleTagType(role) { return (ROLE_META[role] || ROLE_META.USER).type }
function nextRoleLabel(role) { return ROLE_NEXT_LABEL[role] || '升为研究人员' }

// 新增用户
const createVisible = ref(false)
const creating = ref(false)
const createForm = reactive({ username: '', password: '', name: '', phone: '', role: 'USER', status: '启用' })

// 编辑用户信息（姓名/联系方式）
const editVisible = ref(false)
const saving = ref(false)
const editForm = reactive({ id: null, username: '', name: '', phone: '', role: 'USER', status: '启用' })

function openEdit(row) {
  editForm.id = row.id
  editForm.username = row.username
  editForm.name = row.name || ''
  editForm.phone = row.phone || ''
  editForm.role = row.role || 'USER'
  editForm.status = row.status || '启用'
  editVisible.value = true
}

async function submitEdit() {
  saving.value = true
  try {
    // role/status 原样回传，避免后端默认值覆盖
    const res = await api.put(`/admin/users/${editForm.id}`, {
      role: editForm.role,
      status: editForm.status,
      name: editForm.name.trim(),
      phone: editForm.phone.trim()
    })
    if (res.code === 200) {
      ElMessage.success('已保存')
      editVisible.value = false
      load()
    } else {
      ElMessage.error(res.message || '保存失败')
    }
  } catch (e) {
    ElMessage.error('保存失败：' + (e?.message || '网络错误'))
  }
  saving.value = false
}

async function load() {
  loading.value = true
  try {
    const [ur, sr, lr, llr] = await Promise.all([
      api.get('/admin/users'),
      api.get('/admin/stats'),
      api.get('/admin/logs', { params: { limit: 30 } }),
      api.get('/admin/login-logs', { params: { limit: 30 } })
    ])
    if (ur.code === 200) users.value = ur.data
    if (sr.code === 200) {
      statItems.value[0].value = sr.data.users || 0
      statItems.value[1].value = sr.data.chats || 0
      statItems.value[2].value = sr.data.cases || 0
      statItems.value[3].value = sr.data.statutes || 0
    }
    if (lr.code === 200) logs.value = lr.data
    if (llr.code === 200) loginLogs.value = llr.data
  } catch (error) {
    console.warn('加载用户管理数据失败', error)
  }
  loading.value = false
}

function openCreate() {
  createForm.username = ''
  createForm.password = ''
  createForm.name = ''
  createForm.phone = ''
  createForm.role = 'USER'
  createForm.status = '启用'
  createVisible.value = true
}

async function submitCreate() {
  if (!createForm.username.trim() || !createForm.password) {
    ElMessage.warning('请填写用户名和密码')
    return
  }
  creating.value = true
  try {
    const res = await api.post('/admin/users', {
      username: createForm.username.trim(),
      password: createForm.password,
      name: createForm.name.trim(),
      phone: createForm.phone.trim(),
      role: createForm.role,
      status: createForm.status
    })
    if (res.code === 200) {
      ElMessage.success('新增成功')
      createVisible.value = false
      load()
    } else {
      ElMessage.error(res.message || '新增失败')
    }
  } catch (e) {
    ElMessage.error('新增失败：' + (e?.message || '网络错误'))
  }
  creating.value = false
}

async function toggleRole(row) {
  const newRole = ROLE_CYCLE[row.role] || 'USER'
  await api.put(`/admin/users/${row.id}`, { role: newRole, status: row.status || '启用' })
  ElMessage.success('角色已更新')
  load()
}

async function toggleStatus(row) {
  const newStatus = (row.status === '启用') ? '停用' : '启用'
  await api.put(`/admin/users/${row.id}`, { role: row.role, status: newStatus })
  ElMessage.success('状态已更新')
  load()
}

async function remove(row) {
  await ElMessageBox.confirm(`确定删除「${row.username}」？`, '确认', { type: 'warning' })
  await api.delete(`/admin/users/${row.id}`)
  ElMessage.success('已删除')
  load()
}

onMounted(load)
</script>

<style scoped>
.user-manager { max-width: 1200px; margin: 0 auto; padding-bottom: 40px; }
.page-head { margin-bottom: 24px; }
.page-title { margin: 0; font-size: 24px; font-weight: 700; color: var(--text-primary); }
.page-subtitle { margin: 4px 0 0; font-size: 13px; color: var(--text-muted); }

.metric-ledger {
  display: grid; grid-template-columns: repeat(4, 1fr);
  border-top: 1px solid #E2E8F0; border-bottom: 1px solid #E2E8F0;
  margin-bottom: 28px;
}
.metric-cell { padding: 24px 20px; border-left: 1px solid #E2E8F0; }
.metric-cell:first-child { border-left: none; }
.metric-num { font-size: 36px; font-weight: 700; color: #0369A1; font-family: 'Space Grotesk', sans-serif; }
.metric-label { font-size: 13px; color: var(--text-muted); margin-top: 6px; }

.panel { background: #FFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 20px 24px; margin-bottom: 20px; }
.panel-head { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid #F1F5F9; }
.panel-index { font-size: 11px; font-weight: 700; color: #0369A1; padding: 2px 8px; border: 1px solid #BAE6FD; border-radius: 6px; background: #F0F9FF; font-family: 'Noto Serif SC', serif; }
.panel-head h3 { margin: 0; font-size: 15px; font-weight: 700; color: #1E293B; flex: 1; }
.panel-count { font-size: 11px; color: #94A3B8; font-family: 'Space Grotesk', sans-serif; }

.muted-text { color: var(--text-muted); font-size: 13px; }
.time-text { font-size: 12px; }
.log-target { font-size: 13px; color: var(--text-secondary); }

@media (max-width: 768px) {
  .metric-ledger { grid-template-columns: repeat(2, 1fr); }
}
</style>
