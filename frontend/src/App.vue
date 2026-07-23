<template>
  <div class="app-container">
    <div class="sidebar" :style="{ width: sidebarWidth + 'px' }">
      <div class="sidebar-logo">
        <el-icon size="20"><Menu /></el-icon>
        CCB 项目管理系统
      </div>
      <el-menu router :default-active="route.path" style="border-right: none;">
        <el-menu-item index="/">
            <el-icon><List /></el-icon>
            <span>项目列表</span>
            <span v-if="overdueCount > 0" class="sidebar-badge">{{ overdueCount > 99 ? '99+' : overdueCount }}</span>
          </el-menu-item>
        <el-menu-item index="/projects/new">
          <el-icon><Plus /></el-icon>
          <span>新建项目</span>
        </el-menu-item>
        <el-menu-item index="/templates">
          <el-icon><CopyDocument /></el-icon>
          <span>项目模板</span>
        </el-menu-item>
        <!-- 周报已移入项目详情页 -->
        <el-sub-menu index="tools" style="margin-top: auto;">
          <template #title>
            <el-icon><Tools /></el-icon>
            <span>系统工具</span>
          </template>
          <el-menu-item index="/settings">
            <el-icon><Setting /></el-icon>
            <span>系统设置</span>
          </el-menu-item>
          <el-menu-item index="/settings/email">
            <el-icon><Message /></el-icon>
            <span>邮件配置</span>
          </el-menu-item>
        </el-sub-menu>
      </el-menu>
    </div>
    <!-- 侧栏拖拽手柄 -->
    <div class="sidebar-resizer" @mousedown="startResize"></div>
    <div class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="page" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </div>
    <div v-if="!showAiPanel" class="ai-reopen" @click="showAiPanel = true">
      <el-icon size="16"><ChatLineSquare /></el-icon>
    </div>
    <AIPanel v-if="showAiPanel" :project-id="projectId" @close="showAiPanel = false" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api'
import AIPanel from '@/components/AIPanel.vue'

const route = useRoute()
const sidebarWidth = ref(260)
const resizing = ref(false)
const overdueCount = ref(0)

// 轮询逾期数量
let pollTimer: ReturnType<typeof setInterval> | null = null
onMounted(() => {
  fetchOverdueCount()
  pollTimer = setInterval(fetchOverdueCount, 60000)
})
onUnmounted(() => { if (pollTimer) clearInterval(pollTimer) })

async function fetchOverdueCount() {
  try {
    const res = await api.get('/overdue/count')
    overdueCount.value = res.data.count
  } catch {}
}

onMounted(() => {
  const saved = localStorage.getItem('ccb_sidebar_width')
  if (saved) sidebarWidth.value = parseInt(saved)
})

const projectId = computed(() => Number(route.params.id))
const showAiPanel = ref(true)

function startResize(e: MouseEvent) {
  resizing.value = true
  document.addEventListener('mousemove', onResize)
  document.addEventListener('mouseup', stopResize)
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

function onResize(e: MouseEvent) {
  if (!resizing.value) return
  const newWidth = Math.max(180, Math.min(400, e.clientX))
  sidebarWidth.value = newWidth
}

function stopResize() {
  resizing.value = false
  localStorage.setItem('ccb_sidebar_width', String(sidebarWidth.value))
  document.removeEventListener('mousemove', onResize)
  document.removeEventListener('mouseup', stopResize)
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
}

</script>

<style scoped>
:deep(.el-menu) { display: flex; flex-direction: column; height: 100%; }
:deep(.el-sub-menu:last-child) { margin-top: auto; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 4px; }
:deep(.el-sub-menu__title) { color: #c9cdd4 !important; height: 44px !important; line-height: 44px !important; }
:deep(.el-sub-menu__title:hover) { background: rgba(255,255,255,0.08) !important; color: #fff !important; }
:deep(.el-sub-menu .el-menu) { background: #1d2129 !important; border: 1px solid rgba(255,255,255,0.08) !important; border-radius: 6px !important; }
:deep(.el-sub-menu .el-menu-item) { padding-left: 44px !important; color: #c9cdd4 !important; }
:deep(.el-sub-menu .el-menu-item:hover) { background: rgba(255,255,255,0.08) !important; color: #fff !important; }
:deep(.el-sub-menu .el-menu-item.is-active) { background: rgba(64,150,255,0.2) !important; color: #409eff !important; }
.ai-reopen {
  position: fixed;
  top: 12px;
  right: 12px;
  z-index: 999;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #bfc2c8;
}
.ai-reopen:hover { color: #409eff; }

.sidebar-badge {
  margin-left: auto;
  background: #f56c6c;
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  min-width: 18px;
  height: 18px;
  line-height: 18px;
  text-align: center;
  padding: 0 5px;
  border-radius: 9px;
}
</style>
