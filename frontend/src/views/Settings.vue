<template>
  <div style="max-width: 600px; margin: 0 auto;">
    <div class="page-header">
      <h1>系统设置</h1>
    </div>

    <el-card shadow="never" class="settings-card">
      <template #header>
        <span style="font-weight: 600;">AI 模型配置</span>
      </template>

      <el-form :model="form" label-width="120px" v-loading="loading">
        <el-form-item label="AI 提供商">
          <el-select v-model="form.provider" style="width: 100%">
            <el-option label="Mock (开发模式)" value="mock" />
            <el-option label="OpenAI 兼容 (DeepSeek/通义千问/GLM等)" value="openai" />
            <el-option label="Claude (Anthropic)" value="anthropic" />
          </el-select>
        </el-form-item>

        <el-form-item label="API Key">
          <el-input v-model="form.api_key" type="password" show-password
                    placeholder="输入 API Key" />
        </el-form-item>

        <el-form-item label="API 地址" v-if="form.provider === 'openai'">
          <el-input v-model="form.api_base"
                    placeholder="https://api.deepseek.com" />
          <div style="font-size: 12px; color: #999; margin-top: 4px;">
            DeepSeek: https://api.deepseek.com |
            通义千问: https://dashscope.aliyuncs.com/compatible-mode/v1 |
            智谱: https://open.bigmodel.cn/api/paas/v4
          </div>
        </el-form-item>

        <el-form-item label="模型名" v-if="form.provider !== 'mock'">
          <el-input v-model="form.model" :placeholder="modelPlaceholder" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
          <el-button @click="handleTest" :loading="testing">测试连接</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never" class="settings-card" style="margin-top: 20px;">
      <template #header>
        <span style="font-weight: 600;">环境变量参考</span>
      </template>
      <div style="font-size: 13px; line-height: 1.8; color: #666;">
        <p>也可通过环境变量配置：</p>
        <pre style="background: #f5f7fa; padding: 12px; border-radius: 4px; font-size: 12px;">
# DeepSeek
AI_PROVIDER=openai
OPENAI_API_KEY=sk-xxx
OPENAI_API_BASE=https://api.deepseek.com
OPENAI_MODEL=deepseek-chat

# Claude
ANTHROPIC_API_KEY=sk-ant-xxx
        </pre>
        <p style="font-size: 12px;">环境变量优先级高于 UI 设置（UI 设置会覆盖同名字段）</p>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getAISettings, saveAISettings, testAIConnection } from '@/api/settings'

const form = ref({ provider: 'mock', api_key: '', api_base: '', model: '' })
const loading = ref(true)
const saving = ref(false)
const testing = ref(false)

const modelPlaceholder = computed(() => {
  const map: Record<string, string> = {
    openai: 'deepseek-chat / qwen-plus / glm-4-plus',
    anthropic: 'claude-sonnet-4-20250514',
    mock: '',
  }
  return map[form.value.provider] || ''
})

onMounted(async () => {
  try {
    const data = await getAISettings()
    form.value = {
      provider: data.provider || 'mock',
      api_key: data.api_key || '',
      api_base: data.api_base || 'https://api.deepseek.com',
      model: data.model || '',
    }
  } catch {
    // use defaults
  } finally {
    loading.value = false
  }
})

async function handleSave() {
  saving.value = true
  try {
    await saveAISettings(form.value)
    ElMessage.success('配置已保存')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function handleTest() {
  testing.value = true
  try {
    const res = await testAIConnection(form.value)
    if (res.status === 'ok') {
      ElMessage.success(res.message)
    } else {
      ElMessage.error(res.message)
    }
  } catch (e: any) {
    ElMessage.error('测试失败')
  } finally {
    testing.value = false
  }
}
</script>

<style scoped>
.settings-card {
  transition: box-shadow 0.2s ease;
}
.settings-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,.06);
}
</style>
