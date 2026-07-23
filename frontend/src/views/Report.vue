<template>
  <div class="report-page">
    <div class="page-header">
      <h2>周报生成</h2>
    </div>

    <el-card style="max-width: 800px;" class="report-card">
      <el-form label-width="100px">
        <el-form-item label="选择项目">
          <el-select v-model="projectId" filterable style="width: 300px" placeholder="请选择项目">
            <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="generateReport" :loading="loading" :disabled="!projectId">
            {{ loading ? '生成中...' : '生成周报' }}
          </el-button>
          <el-button @click="exportWord" :disabled="!reportText" style="margin-left: 12px;">
            导出 Word
          </el-button>
        </el-form-item>
      </el-form>

      <div v-if="reportText" class="report-preview">
        <div class="report-content markdown-body" v-html="renderMarkdown(reportText)"></div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'
import { getWeeklyReport, exportReport } from '@/api/report'

const projects = ref<any[]>([])
const projectId = ref<number | null>(null)
const loading = ref(false)
const reportText = ref('')

onMounted(async () => {
  try {
    const res = await api.get('/projects')
    projects.value = res.data
  } catch {}
})

async function generateReport() {
  if (!projectId.value) return
  loading.value = true
  try {
    const res = await getWeeklyReport(projectId.value)
    reportText.value = res.data.report_text
  } catch (e: any) {
    ElMessage.error('生成失败: ' + e.message)
  } finally {
    loading.value = false
  }
}

async function exportWord() {
  if (!projectId.value) return
  try {
    const res = await exportReport(projectId.value, 'weekly')
    const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' }))
    const a = document.createElement('a')
    a.href = url
    a.download = `周报_${projectId.value}.docx`
    a.click()
    window.URL.revokeObjectURL(url)
  } catch {
    ElMessage.error('导出失败')
  }
}

function escapeHtml(text: string): string {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

function renderMarkdown(text: string): string {
  const safe = escapeHtml(text)
  return safe
    .replace(/### (.*)/g, '<h3>$1</h3>')
    .replace(/## (.*)/g, '<h2 style="margin-top:20px;">$1</h2>')
    .replace(/# (.*)/g, '<h1>$1</h1>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/- (.*)/g, '<li style="margin-left:16px;">$1</li>')
    .replace(/\n/g, '<br>')
}
</script>

<style scoped>
.report-page { padding: 20px; max-width: 800px; margin: 0 auto; }
.page-header { margin-bottom: 16px; }
.page-header h2 { margin: 0; }
.report-preview { margin-top: 20px; padding: 20px; background: #f9fafb; border-radius: 6px; animation: fadeUp 0.3s ease; }
.report-content { font-size: 14px; line-height: 1.8; }
.report-card { transition: box-shadow 0.2s ease; }
.report-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,.06); }
@keyframes fadeUp { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
</style>
