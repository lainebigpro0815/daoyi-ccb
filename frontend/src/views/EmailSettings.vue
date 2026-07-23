<template>
  <div class="email-settings">
    <h2>邮件配置</h2>
    <el-card style="max-width: 500px;" class="email-card">
      <el-form label-width="100px">
        <el-form-item label="SMTP 主机">
          <el-input v-model="form.smtp_host" placeholder="smtp.qq.com" />
        </el-form-item>
        <el-form-item label="端口">
          <el-input-number v-model="form.smtp_port" :min="1" :max="65535" />
        </el-form-item>
        <el-form-item label="邮箱账号">
          <el-input v-model="form.smtp_user" placeholder="your@qq.com" />
        </el-form-item>
        <el-form-item label="授权码">
          <el-input v-model="form.smtp_pass" type="password" placeholder="SMTP 授权码/密码" show-password />
        </el-form-item>
        <el-form-item label="发件名称">
          <el-input v-model="form.sender_name" placeholder="CCB项目管理系统" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="saveConfig">保存配置</el-button>
          <el-button @click="testConfig" style="margin-left: 8px;">发送测试</el-button>
        </el-form-item>
      </el-form>
      <div v-if="testResult" :class="testResult.success ? 'test-ok' : 'test-fail'">
        {{ testResult.success ? '✅ 测试成功' : '❌ 失败: ' + testResult.message }}
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getConfig, saveConfig, testConfig } from '@/api/email'

const form = ref({
  smtp_host: '',
  smtp_port: 465,
  smtp_user: '',
  smtp_pass: '',
  sender_name: 'CCB项目管理系统',
})
const testResult = ref<{ success: boolean; message: string } | null>(null)

onMounted(async () => {
  try {
    const res = await getConfig()
    Object.assign(form.value, res.data)
  } catch {}
})

async function saveConfig() {
  try {
    await saveConfig(form.value)
    ElMessage.success('配置已保存')
  } catch (e: any) {
    ElMessage.error('保存失败: ' + e.message)
  }
}

async function testConfig() {
  testResult.value = null
  try {
    const res = await testConfig(form.value)
    testResult.value = res.data
  } catch (e: any) {
    testResult.value = { success: false, message: e.message }
  }
}
</script>

<style scoped>
.email-settings { padding: 20px; }
.email-settings h2 { margin: 0 0 16px 0; }
.test-ok { margin-top: 12px; padding: 8px; background: #f0f9eb; border-radius: 4px; animation: fadeIn 0.3s ease; }
.test-fail { margin-top: 12px; padding: 8px; background: #fef0f0; border-radius: 4px; animation: fadeIn 0.3s ease; }
.email-card { transition: box-shadow 0.2s ease; }
.email-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,.06); }
@keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
</style>
