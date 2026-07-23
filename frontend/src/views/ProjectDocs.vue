<template>
  <div class="doc-layout">
    <div class="doc-sidebar">
      <div class="doc-sidebar-header">
        <span style="font-weight: 600; font-size: 14px;">文档</span>
        <el-upload :action="`/api/projects/${projectId}/docs/upload`" :show-file-list="false"
                   :on-success="loadTree" style="display: inline-block;">
          <el-button size="small" circle><el-icon><Plus /></el-icon></el-button>
        </el-upload>
      </div>
      <el-tree :data="treeData" :props="{ children: 'children', label: 'label' }"
               node-key="id" :highlight-current="true" @node-click="onNodeClick"
               default-expand-all class="doc-tree">
        <template #default="{ data }">
          <span class="doc-tree-node">
            <el-icon v-if="data.type === 'folder'" size="14"><Folder /></el-icon>
            <el-icon v-else-if="data.file_type === 'word'" size="14" style="color:#2b579a;"><Tickets /></el-icon>
            <el-icon v-else-if="data.file_type === 'excel'" size="14" style="color:#217346;"><Grid /></el-icon>
            <el-icon v-else-if="data.file_type === 'ppt'" size="14" style="color:#d04525;"><Monitor /></el-icon>
            <el-icon v-else size="14"><Document /></el-icon>
            {{ data.label }}
          </span>
        </template>
      </el-tree>
    </div>
    <div class="doc-content">
      <div v-if="!currentDoc" class="doc-empty">
        <el-icon size="40"><FolderOpened /></el-icon>
        <p style="margin-top: 8px;">选择左侧文档查看</p>
        <p style="font-size: 12px; color: #999;">支持 .docx / .xlsx / .pptx / .md</p>
      </div>
      <template v-else>
        <div class="doc-toolbar">
          <div>
            <span style="font-weight: 600; font-size: 15px;">{{ currentDoc.name }}</span>
            <el-tag size="small" style="margin-left: 6px;">{{ currentDoc.ext }}</el-tag>
          </div>
          <div style="display: flex; gap: 8px;">
            <el-button size="small" @click="downloadDoc">下载</el-button>
            <template v-if="currentDoc.ext === '.md'">
              <el-switch v-model="editing" active-text="编辑" inactive-text="预览" size="small" />
              <el-button v-if="editing" type="primary" size="small" @click="saveDoc">保存</el-button>
            </template>
          </div>
        </div>
        <div class="doc-viewer">
          <!-- Markdown -->
          <template v-if="currentDoc.ext === '.md'">
            <div v-if="!editing" class="markdown-body" v-html="renderedHtml"></div>
            <el-input v-else v-model="editContent" type="textarea" :rows="30" />
          </template>
          <!-- Office -->
          <div v-else-if="currentDoc.html" class="office-preview" v-html="currentDoc.html"></div>
          <div v-else style="color: #999; padding: 40px; text-align: center;">无法预览此文件，请下载查看</div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '@/api'

const route = useRoute()
const projectId = computed(() => Number(route.params.id))
const treeData = ref<any[]>([])
const currentDoc = ref<any>(null)
const editContent = ref('')
const editing = ref(false)

const renderedHtml = computed(() => {
  let text = editContent.value
  if (!text) return ''
  return text
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/^### (.*$)/gm, '<h3>$1</h3>')
    .replace(/^## (.*$)/gm, '<h2>$1</h2>')
    .replace(/^# (.*$)/gm, '<h1>$1</h1>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>')
})

async function loadTree() {
  const res = await api.get(`/projects/${projectId.value}/docs/tree`)
  treeData.value = res.data.items || []
}
async function onNodeClick(data: any) {
  if (data.type !== 'file') return
  const res = await api.get(`/projects/${projectId.value}/docs/read`, { params: { path: data.path } })
  currentDoc.value = res.data
  editContent.value = res.data.content || ''
  editing.value = false
}
async function saveDoc() {
  await api.post(`/projects/${projectId.value}/docs/save`, { path: currentDoc.value.path, content: editContent.value })
  ElMessage.success('已保存'); editing.value = false
}
function downloadDoc() {
  window.open(`/api/projects/${projectId.value}/docs/download?path=${encodeURIComponent(currentDoc.value.path)}`)
}
onMounted(loadTree)
</script>

<style scoped>
.doc-layout {
  display: flex; height: calc(100vh - 160px); margin: -20px; overflow: hidden;
}
.doc-sidebar {
  width: 260px; min-width: 260px; border-right: 1px solid #e5e6e8;
  display: flex; flex-direction: column; overflow-y: auto;
  background: #f8f9fa;
}
.doc-sidebar-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 14px; border-bottom: 1px solid #e5e6e8;
  background: #f0f1f2;
  font-size: 12px; text-transform: uppercase; letter-spacing: .5px;
  color: #666; user-select: none;
}
.doc-tree {
  padding: 4px 0;
  font-size: 13px;
}
.doc-tree :deep(.el-tree-node__content) {
  height: 30px;
  padding: 0 8px;
  border-radius: 0;
  transition: background 0.1s;
}
.doc-tree :deep(.el-tree-node__content:hover) {
  background: #e8eaed;
}
.doc-tree :deep(.el-tree-node.is-current > .el-tree-node__content) {
  background: #d3e3fd;
  color: #1a1a1a;
}
.doc-tree-node {
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 4px;
  width: 100%;
}
.doc-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  background: #fff;
}
.doc-empty {
  color: #999;
  text-align: center;
  margin-top: 100px;
}
.doc-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 20px;
  border-bottom: 1px solid #e5e6e8;
  background: #fff;
}
.doc-viewer {
  padding: 24px 32px;
  flex: 1;
  overflow-y: auto;
  max-width: 900px;
}
.markdown-body, .office-preview {
  line-height: 1.8;
  font-size: 14px;
  color: #1d2129;
}
.markdown-body h1, .office-preview h1 {
  font-size: 22px; margin: 20px 0 8px;
  padding-bottom: 8px; border-bottom: 1px solid #eee;
}
.markdown-body h2, .office-preview h2 {
  font-size: 18px; margin: 18px 0 6px;
}
.markdown-body h3, .office-preview h3 {
  font-size: 15px; margin: 14px 0 4px;
}
.markdown-body pre {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
}
.markdown-body code {
  background: #f0f1f2;
  padding: 2px 4px;
  border-radius: 3px;
  font-size: 13px;
}
.office-preview table {
  border-collapse: collapse;
  width: 100%;
  font-size: 13px;
  margin-bottom: 16px;
}
.office-preview td, .office-preview th {
  border: 1px solid #d0d0d0;
  padding: 6px 10px;
}
.office-preview th {
  background: #f5f7fa;
  font-weight: 600;
}
</style>
