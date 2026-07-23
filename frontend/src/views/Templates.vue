<template>
  <div class="templates-page">
    <div class="page-header">
      <h2>项目模板</h2>
      <el-button type="primary" @click="openCreate">新建模板</el-button>
    </div>

    <!-- 模板列表 — 每个模板一个扁平计划表格 -->
    <div v-for="tpl in templates" :key="tpl.id" class="template-card">
      <div class="template-header">
        <div>
          <span class="template-name">{{ tpl.name }}</span>
          <el-tag size="small" style="margin-left:6px;">v{{ tpl.version }}</el-tag>
          <el-tag v-if="!tpl.is_active" type="info" size="small">停用</el-tag>
          <span style="color:#999;font-size:12px;margin-left:8px;">{{ totalRows(tpl) }} 项</span>
        </div>
        <div class="template-actions">
          <el-button size="small" @click="editTemplate(tpl)">编辑</el-button>
          <el-button size="small" @click="applyToProject(tpl)">套用</el-button>
          <el-button size="small" type="danger" link @click="confirmDelete(tpl)">删除</el-button>
        </div>
      </div>

      <el-table :data="flattenTemplate(tpl)" border stripe size="small" style="width:100%;"
                :max-height="600" empty-text="暂无计划内容">
        <el-table-column label="阶段" width="120" prop="phase_name" />
        <el-table-column label="编号" width="60" prop="task_number" />
        <el-table-column label="任务名称" min-width="160" prop="name" />
        <el-table-column label="操作指引" min-width="200" prop="guide" show-overflow-tooltip />
        <el-table-column label="预期输出" min-width="160" prop="deliverable" show-overflow-tooltip />
        <el-table-column label="我方角色" width="96" prop="vendor_role" />
        <el-table-column label="客户角色" width="96" prop="customer_role" />
        <el-table-column label="工期(天)" width="76" prop="estimated_days" />
      </el-table>
    </div>

    <div v-if="templates.length === 0 && !loading" style="text-align:center;padding:60px;color:#999;">
      暂无模板，点击右上角新建
    </div>

    <!-- 新建/编辑模板 -->
    <el-dialog v-model="showEditor" :title="editingId ? '编辑模板' : '新建模板'" width="1000px" top="5vh">
      <el-form :model="form" label-width="80px">
        <el-form-item label="模板名称">
          <el-input v-model="form.name" placeholder="如：银行移动办公项目标准模板" />
        </el-form-item>
        <el-form-item label="版本">
          <el-input v-model="form.version" placeholder="1.0" style="width:120px" />
        </el-form-item>
      </el-form>

      <div style="margin:16px 0 8px;font-weight:600;">计划内容</div>
      <el-table :data="flatRows" border stripe size="small" style="width:100%;" max-height="500">
        <el-table-column label="阶段" width="120">
          <template #default="{ row, $index }">
            <el-input v-model="row.phase_name" size="small" placeholder="阶段" />
          </template>
        </el-table-column>
        <el-table-column label="编号" width="60">
          <template #default="{ row }">
            <el-input v-model="row.task_number" size="small" placeholder="编号" />
          </template>
        </el-table-column>
        <el-table-column label="任务名称" min-width="150">
          <template #default="{ row }">
            <el-input v-model="row.name" size="small" placeholder="任务名称" />
          </template>
        </el-table-column>
        <el-table-column label="操作指引" min-width="180">
          <template #default="{ row }">
            <el-input v-model="row.guide" size="small" placeholder="操作指引/注意事项" />
          </template>
        </el-table-column>
        <el-table-column label="预期输出" min-width="140">
          <template #default="{ row }">
            <el-input v-model="row.deliverable" size="small" placeholder="输出物" />
          </template>
        </el-table-column>
        <el-table-column label="我方角色" width="90">
          <template #default="{ row }">
            <el-input v-model="row.vendor_role" size="small" placeholder="我方" />
          </template>
        </el-table-column>
        <el-table-column label="客户角色" width="90">
          <template #default="{ row }">
            <el-input v-model="row.customer_role" size="small" placeholder="客户" />
          </template>
        </el-table-column>
        <el-table-column label="工期(天)" width="76">
          <template #default="{ row }">
            <el-input-number v-model="row.estimated_days" :min="0.5" :step="0.5" size="small" style="width:68px;" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="36" fixed="right">
          <template #default="{ $index }">
            <el-button link type="danger" size="small" @click="flatRows.splice($index, 1)">×</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-button size="small" style="margin-top:8px" @click="addRow">+ 添加行</el-button>

      <template #footer>
        <el-button @click="showEditor = false">取消</el-button>
        <el-button type="primary" @click="saveTemplate" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 套用 -->
    <el-dialog v-model="showApply" title="套用到项目" width="400px">
      <el-form label-width="80px">
        <el-form-item label="目标项目">
          <el-select v-model="applyProjectId" filterable style="width:100%">
            <el-option v-for="p in projectList" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="开始日期">
          <el-date-picker v-model="applyStartDate" type="date" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showApply = false">取消</el-button>
        <el-button type="primary" @click="doApply" :loading="applying">确认套用</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listTemplates, createTemplate, updateTemplate, deleteTemplate, applyTemplate, type Template, type PhaseDef } from '@/api/templates'
import api from '@/api'

interface FlatRow {
  phase_name: string
  task_number: string
  name: string
  guide: string
  deliverable: string
  vendor_role: string
  customer_role: string
  estimated_days: number
}

const loading = ref(false)
const saving = ref(false)
const templates = ref<Template[]>([])

// Editor
const showEditor = ref(false)
const editingId = ref<number | null>(null)
const form = ref({ name: '', version: '1.0' })
const flatRows = ref<FlatRow[]>([])

// Apply
const showApply = ref(false)
const applyProjectId = ref<number | null>(null)
const applyStartDate = ref('')
const applying = ref(false)
const projectList = ref<any[]>([])
const applyTemplateId = ref<number>(0)

// ── 扁平化：嵌套 → 行列表 ──
function flattenTemplate(tpl: Template): FlatRow[] {
  const rows: FlatRow[] = []
  for (const phase of tpl.phases || []) {
    for (const task of phase.tasks || []) {
      rows.push({
        phase_name: phase.name,
        task_number: task.task_number || '',
        name: task.name,
        guide: task.guide || '',
        deliverable: task.deliverable || '',
        vendor_role: task.vendor_role || '',
        customer_role: task.customer_role || '',
        estimated_days: task.estimated_days ?? 1,
      })
    }
  }
  return rows
}

function totalRows(tpl: Template): number {
  let n = 0
  for (const p of tpl.phases || []) n += p.tasks?.length || 0
  return n
}

// ── 逆扁平化：行列表 → 嵌套 ──
function rowsToPhases(rows: FlatRow[]): PhaseDef[] {
  const seen = new Map<string, number>()
  const phases: PhaseDef[] = []
  for (const row of rows) {
    const pn = row.phase_name || '默认阶段'
    let idx = seen.get(pn)
    if (idx === undefined) {
      idx = phases.length
      seen.set(pn, idx)
      phases.push({
        phase_number: idx + 1,
        name: pn,
        sort_order: idx,
        tasks: [],
      })
    }
    const tasks = phases[idx].tasks
    tasks.push({
      name: row.name,
      task_number: row.task_number,
      guide: row.guide,
      deliverable: row.deliverable,
      vendor_role: row.vendor_role,
      customer_role: row.customer_role,
      estimated_days: row.estimated_days,
      sort_order: tasks.length,
    })
  }
  return phases
}

// ── 增删行 ──
function addRow() {
  flatRows.value.push({
    phase_name: '',
    task_number: '',
    name: '',
    guide: '',
    deliverable: '',
    vendor_role: '',
    customer_role: '',
    estimated_days: 1,
  })
}

// ── 打开新建 ──
function openCreate() {
  editingId.value = null
  form.value = { name: '', version: '1.0' }
  flatRows.value = []
  showEditor.value = true
}

// ── 打开编辑 ──
function editTemplate(tpl: Template) {
  editingId.value = tpl.id
  form.value = { name: tpl.name, version: tpl.version }
  flatRows.value = flattenTemplate(tpl)
  showEditor.value = true
}

// ── 保存 ──
async function saveTemplate() {
  if (!form.value.name) { ElMessage.warning('请输入模板名称'); return }
  if (flatRows.value.length === 0) { ElMessage.warning('请添加至少一行计划内容'); return }
  saving.value = true
  try {
    const payload = {
      name: form.value.name,
      version: form.value.version,
      phases: rowsToPhases(flatRows.value),
    }
    if (editingId.value) {
      await updateTemplate(editingId.value, { name: form.value.name, version: form.value.version })
      // recreate phases/tasks — delete & re-post
      await api.put(`/templates/${editingId.value}/phases`, payload)
    } else {
      await createTemplate(payload)
    }
    ElMessage.success(editingId.value ? '模板已更新' : '模板创建成功')
    showEditor.value = false
    loadTemplates()
  } catch (e: any) {
    ElMessage.error('保存失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

// ── 删除 ──
function confirmDelete(tpl: Template) {
  ElMessageBox.confirm(`确认删除模板「${tpl.name}」？所有阶段和任务一并删除。`, '提示')
    .then(async () => {
      await deleteTemplate(tpl.id)
      ElMessage.success('已删除')
      loadTemplates()
    })
    .catch(() => {})
}

// ── 套用 ──
async function applyToProject(tpl: Template) {
  applyTemplateId.value = tpl.id
  try {
    const res = await api.get('/projects')
    projectList.value = res.data.filter((p: any) => p.status === 'active')
  } catch {}
  applyProjectId.value = null
  applyStartDate.value = ''
  showApply.value = true
}

async function doApply() {
  if (!applyProjectId.value || !applyStartDate.value) {
    ElMessage.warning('请选择项目和开始日期')
    return
  }
  applying.value = true
  try {
    await applyTemplate(applyTemplateId.value, applyProjectId.value, applyStartDate.value)
    ElMessage.success('模板已套用到项目')
    showApply.value = false
  } catch (e: any) {
    ElMessage.error('套用失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    applying.value = false
  }
}

// ── 加载 ──
async function loadTemplates() {
  loading.value = true
  try {
    const res = await listTemplates()
    templates.value = res.data
  } catch (e: any) {
    ElMessage.error('加载模板失败: ' + e.message)
  } finally {
    loading.value = false
  }
}

onMounted(loadTemplates)
</script>

<style scoped>
.templates-page { padding: 20px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; }
.template-card { border: 1px solid #e4e7ed; border-radius: 8px; margin-bottom: 20px; overflow: hidden; transition: box-shadow 0.2s ease; }
.template-card:hover { box-shadow: 0 2px 12px rgba(0,0,0,.06); }
.template-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 16px; background: #f7f8fa; border-bottom: 1px solid #e4e7ed;
}
.template-name { font-weight: 600; font-size: 15px; }
.template-actions { display: flex; gap: 4px; }
</style>
