<template>
  <el-card class="phase-card" shadow="never">
    <template #header>
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
          <span style="font-weight: 600; font-size: 15px;">
            阶段{{ phase.phase_number }}：{{ phase.name }}
          </span>
          <el-tag :type="statusType" size="small" style="margin-left: 8px;">
            {{ statusLabel }}
          </el-tag>
        </div>
        <span style="color: #999; font-size: 13px;">
          {{ phase.planned_start }} → {{ phase.planned_end }}
        </span>
      </div>
    </template>

    <!-- 任务列表 -->
    <div v-for="task in phase.tasks" :key="task.id" style="margin-bottom: 8px;">
      <TaskItem :task="task" :project-id="projectId" @refresh="$emit('refresh')" />
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ProjectPhase } from '@/api/projects'
import TaskItem from './TaskItem.vue'

const props = defineProps<{
  phase: ProjectPhase
  projectId: number
}>()

const emit = defineEmits<{ refresh: [] }>()

const statusType = computed(() => {
  const map: Record<string, string> = {
    pending: 'info', in_progress: 'primary', completed: 'success', delayed: 'danger',
  }
  return map[props.phase.status] || 'info'
})

const statusLabel = computed(() => {
  const map: Record<string, string> = {
    pending: '待开始', in_progress: '进行中', completed: '已完成', delayed: '已延期',
  }
  return map[props.phase.status] || props.phase.status
})
</script>

<style scoped>
.phase-card {
  margin-bottom: 16px;
  border: 1px solid #e4e7ed;
  transition: box-shadow 0.2s ease, border-color 0.2s ease;
}
.phase-card:hover {
  box-shadow: 0 2px 12px rgba(0,0,0,.06);
  border-color: #c0c4cc;
}
</style>
