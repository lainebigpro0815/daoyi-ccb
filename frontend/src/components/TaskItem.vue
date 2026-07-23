<template>
  <div class="task-item" :class="{ 'task-completed': task.status === 'completed' }">
    <div style="display: flex; align-items: flex-start; gap: 12px;">
      <!-- 状态切换 -->
      <el-checkbox
        :model-value="task.status === 'completed'"
        @change="toggleComplete"
        :disabled="task.status === 'blocked'"
        class="task-checkbox"
      />

      <!-- 任务信息 -->
      <div style="flex: 1; min-width: 0;">
        <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
          <span style="color: #666; font-size: 12px; font-family: monospace;">{{ task.task_number }}</span>
          <span class="task-name">{{ task.name }}</span>
          <el-tag :type="taskStatusType" size="small">{{ taskStatusLabel }}</el-tag>
        </div>

        <!-- 操作指引下拉 -->
        <div v-if="task.guide" style="margin-top: 4px;">
          <el-popover trigger="click" :width="400">
            <template #reference>
              <el-button link size="small" type="primary" style="font-size: 12px;">
                查看指引
              </el-button>
            </template>
            <div style="white-space: pre-wrap; font-size: 13px; line-height: 1.6;">
              {{ task.guide }}
            </div>
          </el-popover>
        </div>

        <!-- 日期和负责人 -->
        <div style="display: flex; gap: 16px; margin-top: 4px; font-size: 12px; color: #999;">
          <span>计划: {{ task.planned_start }} → {{ task.planned_end }}</span>
          <span>负责人: <el-input v-model="task.assignee" size="small" style="width: 120px;"
                    @blur="updateField('assignee', task.assignee)" /></span>
          <span>进度: <el-progress :percentage="task.progress" :width="80" :stroke-width="12"
                    style="display: inline-block;" /></span>
        </div>

        <!-- 交付物 -->
        <div v-if="task.deliverable" style="margin-top: 4px; font-size: 12px; color: #409eff;">
          输出物：{{ task.deliverable }}
        </div>
      </div>

      <!-- 进度编辑 -->
      <el-button link size="small" @click="showProgressEditor = true" style="flex-shrink: 0;">
        {{ task.progress }}%
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import type { ProjectTask } from '@/api/projects'
import { updateTask } from '@/api/tasks'

const props = defineProps<{
  task: ProjectTask
  projectId: number
}>()

const emit = defineEmits<{ refresh: [] }>()
const showProgressEditor = ref(false)

const taskStatusType = computed(() => {
  const map: Record<string, string> = { pending: 'info', in_progress: 'warning', completed: 'success', blocked: 'danger' }
  return map[props.task.status] || 'info'
})

const taskStatusLabel = computed(() => {
  const map: Record<string, string> = { pending: '待开始', in_progress: '进行中', completed: '已完成', blocked: '阻塞' }
  return map[props.task.status] || props.task.status
})

async function toggleComplete(checked: boolean) {
  await doUpdate({
    status: checked ? 'completed' : 'pending',
    progress: checked ? 100 : 0,
    actual_end: checked ? new Date().toISOString().split('T')[0] : null,
  })
}

async function updateField(field: string, value: any) {
  await doUpdate({ [field]: value })
}

async function doUpdate(data: any) {
  try {
    await updateTask(props.projectId, props.task.id, data)
    emit('refresh')
  } catch {
    ElMessage.error('更新失败')
  }
}
</script>

<style scoped>
.task-item {
  padding: 10px 12px;
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  background: #fafafa;
  transition: all 0.2s ease;
}
.task-item:hover {
  background: #f0f5ff;
  border-color: #409eff;
  transform: translateX(2px);
}
.task-completed {
  opacity: 0.7;
  transition: opacity 0.3s ease;
}
.task-completed .task-name {
  text-decoration: line-through;
  color: #999;
  transition: color 0.3s ease;
}
.task-name {
  font-size: 14px;
  font-weight: 500;
}
.task-checkbox {
  transition: transform 0.15s ease;
}
.task-checkbox:hover {
  transform: scale(1.1);
}
</style>
