<template>
  <div v-loading="store.loading">
    <div v-if="project" style="max-width: 1100px; margin: 0 auto;">
      <!-- 头部 -->
      <div class="page-header">
        <div>
          <el-button link @click="$router.push('/')" style="margin-bottom: 4px; font-size: 13px;">
            <el-icon><ArrowLeft /></el-icon> 返回列表
          </el-button>
          <h1>{{ project.name }}</h1>
          <div style="color: #86909c; font-size: 13px; margin-top: 2px;">
            客户：{{ project.customer_name }} |
            阶段：<el-tag :type="stageTagType" size="small">{{ stageLabel }}</el-tag> |
            时间：{{ project.start_date }} → {{ project.planned_end_date || '待定' }}
          </div>
        </div>
        <el-button type="primary" @click="exportExcel" :loading="exporting">
          <el-icon><Download /></el-icon> 导出 Excel
        </el-button>
      </div>

      <!-- 进度条 -->
      <el-card shadow="never" style="margin-bottom: 16px; padding: 4px 0;">
        <div style="display: flex; gap: 40px; align-items: center;">
          <div><span class="stat-label">阶段</span><div class="stat-value">{{ project.phases.length }}</div></div>
          <div><span class="stat-label">任务</span><div class="stat-value">{{ totalTasks }}</div></div>
          <div><span class="stat-label">已完成</span><div class="stat-value" style="color: #00b42a;">{{ completedTasks }}</div></div>
          <div style="flex: 1; min-width: 200px;">
            <el-progress :percentage="overallProgress" :stroke-width="16" />
          </div>
        </div>
      </el-card>

      <!-- Excel 表格 -->
      <el-table :data="flatTasks" :span-method="spanMethod" border stripe size="small"
                max-height="calc(100vh - 280px)" style="width: 100%;">
        <el-table-column label="编号" width="80" prop="display.task_number" />
        <el-table-column label="任务名称" min-width="220">
          <template #default="{ row }">
            <span v-if="row._isPhase" style="font-weight: 600;">{{ row.display.name }}</span>
            <span v-else>{{ row.display.name }}</span>
          </template>
        </el-table-column>
        <el-table-column label="负责人" width="120" prop="display.assignee" />
        <el-table-column label="计划开始" width="105" prop="display.planned_start" />
        <el-table-column label="计划结束" width="105" prop="display.planned_end" />
        <el-table-column label="进度" width="80">
          <template #default="{ row }">
            <el-progress v-if="!row._isPhase" :percentage="row.display.progress || 0" :width="60" :stroke-width="8" />
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag v-if="!row._isPhase" :type="taskStatusType(row.display.status)" size="small">
              {{ taskStatusLabel(row.display.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="90">
          <template #default="{ row }">
            <el-button v-if="!row._isPhase && row.display.status !== 'completed'"
                       link size="small" type="primary"
                       @click="quickComplete(row)">
              完成
            </el-button>
            <el-button v-if="!row._isPhase && row.display.status === 'completed'"
                       link size="small" @click="quickUncomplete(row)">
              重开
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useProjectStore } from '@/stores/project'
import { updateTask } from '@/api/tasks'
import api from '@/api'

const route = useRoute()
const store = useProjectStore()
const exporting = ref(false)

const projectId = computed(() => Number(route.params.id))
const project = computed(() => store.currentProject)

const totalTasks = computed(() => project.value?.phases.reduce((s, p) => s + p.tasks.length, 0) || 0)
const completedTasks = computed(() => project.value?.phases.reduce((s, p) => s + p.tasks.filter(t => t.status === 'completed').length, 0) || 0)
const overallProgress = computed(() => totalTasks.value ? Math.round(completedTasks.value / totalTasks.value * 100) : 0)

// 展平为带阶段行的平面数组
const flatTasks = computed(() => {
  if (!project.value) return []
  const rows: any[] = []
  for (const p of project.value.phases) {
    rows.push({
      _isPhase: true,
      display: {
        name: `阶段${p.phase_number}: ${p.name}`,
        planned_start: p.planned_start,
        planned_end: p.planned_end,
      }
    })
    for (const t of p.tasks) {
      rows.push({
        _isPhase: false,
        _taskId: t.id,
        _phaseId: p.id,
        display: {
          task_number: t.task_number,
          name: t.name,
          assignee: t.assignee,
          planned_start: t.planned_start,
          planned_end: t.planned_end,
          progress: t.progress,
          status: t.status,
        }
      })
    }
  }
  return rows
})

function spanMethod({ rowIndex, columnIndex }: { rowIndex: number; columnIndex: number }) {
  if (flatTasks.value[rowIndex]?._isPhase) {
    if (columnIndex === 0) return { rowspan: 1, colspan: 1 }
    return { rowspan: 1, colspan: 0 }
  }
  return { rowspan: 1, colspan: 1 }
}

async function quickComplete(row: any) {
  try {
    await updateTask(projectId.value, row._taskId, { status: 'completed', progress: 100 })
    ElMessage.success('已完成')
    store.fetchProject(projectId.value)
  } catch { ElMessage.error('操作失败') }
}

async function quickUncomplete(row: any) {
  try {
    await updateTask(projectId.value, row._taskId, { status: 'pending', progress: 0 })
    ElMessage.success('已重开')
    store.fetchProject(projectId.value)
  } catch { ElMessage.error('操作失败') }
}

async function exportExcel() {
  exporting.value = true
  try {
    const res = await api.get(`/projects/${projectId.value}/export/excel`, {
      responseType: 'blob'
    })
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const a = document.createElement('a')
    a.href = url
    a.download = `project_${projectId.value}.xlsx`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '导出失败')
  } finally {
    exporting.value = false
  }
}

onMounted(() => store.fetchProject(projectId.value))

function stageTagType(s: string) {
  return ({ presale: 'warning', signed: 'info', executing: 'primary', delivered: 'success', archived: '' })[s] || 'info'
}
function stageLabel(s: string) {
  return ({ presale: '售前', signed: '已签约', executing: '执行中', delivered: '已交付', archived: '已归档' })[s] || s
}
function taskStatusType(s: string) {
  return ({ pending: 'info', in_progress: 'warning', completed: 'success', blocked: 'danger' })[s] || 'info'
}
function taskStatusLabel(s: string) {
  return ({ pending: '待开始', in_progress: '进行中', completed: '已完成', blocked: '阻塞' })[s] || s
}
</script>
