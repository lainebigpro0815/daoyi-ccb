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
        </el-menu-item>
        <el-menu-item index="/projects/new">
          <el-icon><Plus /></el-icon>
          <span>新建项目</span>
        </el-menu-item>
        <el-menu-item index="/settings" style="margin-top: auto;">
          <el-icon><Setting /></el-icon>
          <span>系统设置</span>
        </el-menu-item>
      </el-menu>
    </div>
    <!-- 侧栏拖拽手柄 -->
    <div class="sidebar-resizer" @mousedown="startResize"></div>
    <div class="main-content">
      <router-view />
    </div>
    <AIPanel :project-id="projectId" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import AIPanel from '@/components/AIPanel.vue'

const route = useRoute()
const sidebarWidth = ref(260)
const resizing = ref(false)

onMounted(() => {
  const saved = localStorage.getItem('ccb_sidebar_width')
  if (saved) sidebarWidth.value = parseInt(saved)
})

const projectId = computed(() => Number(route.params.id))

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
