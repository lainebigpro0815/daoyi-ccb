<template>
  <div>
    <div class="page-header">
      <h1>项目列表</h1>
      <el-button type="primary" @click="$router.push('/projects/new')">
        <el-icon><Plus /></el-icon> 新建项目
      </el-button>
    </div>

    <el-table :data="store.projects" v-loading="store.loading" stripe
      @row-click="(row: any) => $router.push('/projects/' + row.id)"
      style="width: 100%; cursor: pointer;">
      <el-table-column prop="name" label="项目名称" min-width="200" />
      <el-table-column prop="customer_name" label="客户名称" width="150" />
      <el-table-column prop="stage" label="阶段" width="120">
        <template #default="{ row }">
          <el-tag :type="stageTagType(row.stage)" size="small">
            {{ stageLabel(row.stage) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="start_date" label="启动日期" width="120" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
            {{ row.status === 'active' ? '进行中' : '已暂停' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button type="primary" link size="small" @click="$router.push(`/projects/${row.id}`)">
            查看详情
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useProjectStore } from '@/stores/project'

const store = useProjectStore()

onMounted(() => {
  store.fetchProjects()
})

function stageTagType(stage: string) {
  const map: Record<string, string> = {
    presale: 'warning',
    signed: 'info',
    executing: 'primary',
    delivered: 'success',
    archived: '',
  }
  return map[stage] || 'info'
}

function stageLabel(stage: string) {
  const map: Record<string, string> = {
    presale: '售前',
    signed: '已签约',
    executing: '执行中',
    delivered: '已交付',
    archived: '已归档',
  }
  return map[stage] || stage
}
</script>
