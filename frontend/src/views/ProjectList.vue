<template>
  <div>
    <!-- 逾期提醒 -->
    <div v-if="overdueTasks.length > 0" class="overdue-bar" @click="showOverdue = !showOverdue">
      <el-icon size="14" color="#e6a23c"><WarningFilled /></el-icon>
      <span style="font-weight:500;">{{ overdueTasks.length }} 个逾期任务</span>
      <el-icon size="12" style="margin-left:auto;transition:transform .2s;" :style="{ transform: showOverdue ? 'rotate(180deg)' : '' }"><ArrowDown /></el-icon>
    </div>

    <transition name="slide-up">
      <div v-if="showOverdue" class="overdue-detail">
        <div v-for="(ot, i) in overdueTasks.slice(0, 20)" :key="i" class="overdue-item">
          <el-tag size="small" type="danger" style="min-width: 56px;">逾期 {{ ot.overdue_days }} 天</el-tag>
          <el-button link size="small" type="primary" @click="$router.push(`/projects/${ot.project_id}`)">{{ ot.project_name }}</el-button>
          <span style="color:#666;">{{ ot.task_name }}</span>
          <span v-if="ot.assignee" style="color:#999;">({{ ot.assignee }})</span>
        </div>
        <div v-if="overdueTasks.length > 20" style="color:#999;font-size:12px;padding:4px 12px 8px;">还有 {{ overdueTasks.length - 20 }} 个</div>
      </div>
    </transition>

    <div class="page-header">
      <h1>项目列表</h1>
      <el-button type="primary" @click="$router.push('/projects/new')">
        <el-icon><Plus /></el-icon> 新建项目
      </el-button>
    </div>

    <!-- 搜索栏 -->
    <el-card shadow="never" style="margin-bottom: 16px; padding: 12px 16px;">
      <div style="display: flex; gap: 12px; align-items: center; flex-wrap: wrap;">
        <el-input v-model="searchQuery" placeholder="搜索项目名称..." prefix-icon="Search"
                  clearable style="width: 240px;" size="default" />
        <el-select v-model="stageFilter" placeholder="阶段" clearable size="default" style="width: 120px;">
          <el-option label="售前" value="presale" />
          <el-option label="已签约" value="signed" />
          <el-option label="执行中" value="executing" />
          <el-option label="已交付" value="delivered" />
          <el-option label="已归档" value="archived" />
        </el-select>
        <el-select v-model="statusFilter" placeholder="状态" clearable size="default" style="width: 120px;">
          <el-option label="进行中" value="active" />
          <el-option label="已暂停" value="paused" />
        </el-select>
        <span v-if="filteredProjects.length !== store.projects.length" style="color: #999; font-size: 13px;">
          匹配 {{ filteredProjects.length }} 项
        </span>
      </div>
    </el-card>

    <!-- 空状态 -->
    <div v-if="store.projects.length === 0 && !store.loading" class="empty-state">
      <el-icon size="48" color="#c9cdd4"><FolderOpened /></el-icon>
      <h3 style="color: #4e5969; margin: 12px 0 4px;">暂无项目</h3>
      <p style="color: #86909c; font-size: 13px;">创建第一个项目来开始管理</p>
      <el-button type="primary" style="margin-top: 16px;" @click="$router.push('/projects/new')">
        <el-icon><Plus /></el-icon> 新建项目
      </el-button>
    </div>

    <!-- 搜索无结果 -->
    <div v-else-if="filteredProjects.length === 0 && !store.loading" class="empty-state">
      <el-icon size="48" color="#c9cdd4"><Search /></el-icon>
      <h3 style="color: #4e5969; margin: 12px 0 4px;">未找到匹配项目</h3>
      <p style="color: #86909c; font-size: 13px;">试试调整搜索条件</p>
    </div>

    <!-- 表格 -->
    <transition name="fade" mode="out-in">
      <el-table v-if="filteredProjects.length > 0 || store.loading"
        :data="filteredProjects" v-loading="store.loading" stripe
        @row-click="(row: any) => $router.push('/projects/' + row.id)"
        style="width: 100%; cursor: pointer;"
        :row-class-name="tableRowClass"
        :header-cell-style="headerCellStyle"
        :cell-style="cellStyle">
        <el-table-column prop="name" label="项目名称" width="0">
          <template #default="{ row }">
            <div class="project-name-cell">{{ row.name }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="customer_name" label="客户名称" width="0" />
        <el-table-column label="阶段" width="0">
          <template #default="{ row }">
            <el-tag :type="stageTagType(row.stage)" size="small" effect="plain">
              {{ stageLabel(row.stage) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="start_date" label="启动日期" width="0" />
        <el-table-column label="状态" width="0">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small" effect="plain">
              {{ row.status === 'active' ? '进行中' : '已暂停' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="0">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click.stop="$router.push(`/projects/${row.id}`)">
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useProjectStore } from '@/stores/project'
import api from '@/api'

const store = useProjectStore()
const overdueTasks = ref<any[]>([])
const showOverdue = ref(false)
const searchQuery = ref('')
const stageFilter = ref('')
const statusFilter = ref('')

const filteredProjects = computed(() => {
  let list = store.projects
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter((p: any) => p.name.toLowerCase().includes(q))
  }
  if (stageFilter.value) {
    list = list.filter((p: any) => p.stage === stageFilter.value)
  }
  if (statusFilter.value) {
    list = list.filter((p: any) => p.status === statusFilter.value)
  }
  return list
})

onMounted(async () => {
  store.fetchProjects()
  await fetchOverdueTasks()
})

function headerCellStyle() {
  return { padding: '6px 8px' }
}
function cellStyle() {
  return { padding: '6px 8px' }
}

function tableRowClass() {
  return 'project-table-row'
}

async function fetchOverdueTasks() {
  try {
    const res = await api.get('/overdue')
    overdueTasks.value = res.data || []
  } catch {}
}

function stageTagType(stage: string) {
  const map: Record<string, string> = {
    presale: 'warning', signed: 'info', executing: 'primary',
    delivered: 'success', archived: '',
  }
  return map[stage] || 'info'
}

function stageLabel(stage: string) {
  const map: Record<string, string> = {
    presale: '售前', signed: '已签约', executing: '执行中',
    delivered: '已交付', archived: '已归档',
  }
  return map[stage] || stage
}
</script>

<style scoped>
.project-name-cell {
  font-weight: 500;
  color: #1d2129;
}

:deep(.project-table-row) {
  transition: background 0.15s;
}

:deep(.project-table-row:hover td) {
  background: #f0f5ff !important;
}

.overdue-bar {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 14px; margin-bottom: 16px;
  background: #fffbe6; border: 1px solid #ffe58f;
  border-radius: 6px; cursor: pointer; font-size: 13px; color: #ad8b00;
  transition: background 0.15s;
}
.overdue-bar:hover { background: #fff7cc; }
.overdue-detail {
  margin: -12px 0 16px; padding: 8px 0;
  background: #fffbe6; border: 1px solid #ffe58f;
  border-top: none; border-radius: 0 0 6px 6px;
}
.overdue-item {
  display: flex; align-items: center; gap: 6px;
  padding: 4px 14px; font-size: 13px;
}
.overdue-item:hover { background: rgba(0,0,0,.02); }

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #e5e6e8;
}
</style>
