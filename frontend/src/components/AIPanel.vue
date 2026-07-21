<template>
  <div class="ai-panel" :class="{ collapsed: !store.panelOpen }">
    <!-- 切换按钮 -->
    <div class="ai-toggle" @click="store.togglePanel()">
      <el-icon size="20"><ChatLineSquare /></el-icon>
      <span v-if="!store.panelOpen" style="writing-mode: vertical-rl; margin-top: 8px;">AI 助手</span>
    </div>

    <!-- 面板内容 -->
    <div v-show="store.panelOpen" class="ai-content">
      <div class="ai-header">
        <span style="font-weight: 600; font-size: 14px;">AI 助手</span>
        <div style="display: flex; gap: 4px; align-items: center;">
          <!-- Provider 选择 -->
          <el-select v-model="currentProvider" size="small" style="width: 100px;"
                     @change="onProviderChange" v-if="providers.length > 1">
            <el-option v-for="p in providers" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
          <el-button link size="small" @click="store.clearMessages()">
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
      </div>

      <!-- 消息列表 -->
      <div class="ai-messages" ref="msgContainer">
        <div v-if="store.messages.length === 0" class="ai-welcome">
          <p style="font-size: 14px; font-weight: 500;">可以问我：</p>
          <ul style="font-size: 12px; color: #666; line-height: 1.8;">
            <li v-if="hasProject">这个项目现在到什么阶段了？</li>
            <li v-if="hasProject">第一阶段要注意什么？</li>
            <li v-if="hasProject">有没有逾期任务？</li>
            <li>帮我列一下所有项目</li>
            <li>项目管理的通用建议</li>
          </ul>
          <p v-if="!hasProject" style="font-size: 12px; color: #999; margin-top: 8px;">
            进入项目详情页可获取项目级上下文
          </p>
        </div>

        <div v-for="(msg, i) in store.messages" :key="i"
             class="ai-message" :class="msg.role">
          <div class="msg-label">{{ msg.role === 'user' ? '你' : 'AI' }}</div>
          <div :class="msg.role === 'user' ? 'msg-content' : 'msg-content markdown-body'"
               v-html="renderMarkdown(msg.content)"></div>
        </div>

        <div v-if="store.loading" class="ai-message assistant">
          <div class="msg-label">AI</div>
          <div class="msg-content">
            <span class="typing-dot">.</span>
            <span class="typing-dot">.</span>
            <span class="typing-dot">.</span>
          </div>
        </div>
      </div>

      <!-- 操作确认弹窗 -->
      <el-dialog v-model="showConfirm" title="确认执行操作" width="400px">
        <div style="font-size: 14px; line-height: 1.6;">
          <p style="margin-bottom: 8px;">
            <el-tag size="small">{{ store.pendingAction?.action_type }}</el-tag>
            <el-tag size="small" type="info" style="margin-left: 4px;">{{ store.pendingAction?.entity }}</el-tag>
          </p>
          <pre style="background: #f5f7fa; padding: 8px; border-radius: 4px; font-size: 12px;">{{ JSON.stringify(store.pendingAction?.data || store.pendingAction, null, 2) }}</pre>
        </div>
        <template #footer>
          <el-button @click="rejectAction">取消</el-button>
          <el-button type="primary" @click="confirmAction">确认执行</el-button>
        </template>
      </el-dialog>

      <!-- 输入框 -->
      <div class="ai-input">
        <el-input
          v-model="inputMessage"
          type="textarea"
          :rows="2"
          :placeholder="hasProject ? '输入问题...' : '输入问题（通用模式）'"
          :disabled="store.loading"
          @keydown.enter.ctrl="sendMessage"
        />
        <el-button type="primary" :loading="store.loading"
                   @click="sendMessage" style="margin-top: 4px; width: 100%;">
          发送
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useAIStore } from '@/stores/ai'
import { sendQuery, executeAction, fetchAIConfig } from '@/api/ai'

const props = defineProps<{ projectId: number | null }>()
const store = useAIStore()
const inputMessage = ref('')
const msgContainer = ref<HTMLElement | null>(null)
const showConfirm = ref(false)
const providers = ref<{id:string,name:string}[]>([])
const currentProvider = ref('')

const hasProject = computed(() => !!props.projectId && props.projectId > 0)

// Auto-scroll on new messages
watch(() => store.messages.length, () => {
  nextTick(() => {
    if (msgContainer.value) {
      msgContainer.value.scrollTop = msgContainer.value.scrollHeight
    }
  })
})

onMounted(async () => {
  try {
    const config = await fetchAIConfig()
    providers.value = config.providers
    currentProvider.value = config.current
  } catch {
    // config not critical
  }
})

function onProviderChange(val: string) {
  currentProvider.value = val
}

async function sendMessage() {
  const msg = inputMessage.value.trim()
  if (!msg || store.loading) return

  inputMessage.value = ''
  store.addMessage({ role: 'user', content: msg })
  store.loading = true
  store.addMessage({ role: 'assistant', content: '' })

  // Build history excluding the last empty assistant message
  const history = store.messages
    .filter(m => m.role === 'user' || m.role === 'assistant')
    .slice(0, -1)
    .map(m => ({ role: m.role as 'user' | 'assistant', content: m.content }))

  const targetId = hasProject ? props.projectId! : 0

  await sendQuery(
    targetId,
    msg,
    history,
    currentProvider.value,
    (chunk) => store.appendToLastMessage(chunk),
    (action) => {
      store.pendingAction = action
      showConfirm.value = true
    },
    () => { store.loading = false },
    (err) => {
      store.loading = false
      store.appendToLastMessage(`\n\n[错误: ${err}]`)
    },
  )
}

async function confirmAction() {
  if (!store.pendingAction || !hasProject) {
    store.appendToLastMessage('\n\n⚠️ 请先进入项目详情后再执行操作')
    showConfirm.value = false
    store.pendingAction = null
    return
  }
  showConfirm.value = false
  try {
    const result = await executeAction(props.projectId!, store.pendingAction)
    store.appendToLastMessage(`\n\n✅ 操作已执行: ${result.action || result.status} (${result.entity} #${result.id || ''})`)
    // Refresh project data to reflect changes
    const { useProjectStore } = await import('@/stores/project')
    const pstore = useProjectStore()
    pstore.fetchProject(props.projectId!)
  } catch (e: any) {
    store.appendToLastMessage(`\n\n❌ 操作执行失败: ${e.message}`)
  }
  store.pendingAction = null
}

function rejectAction() {
  showConfirm.value = false
  store.appendToLastMessage('\n\n⚠️ 操作已取消')
  store.pendingAction = null
}

function escapeHtml(text: string): string {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

function renderMarkdown(text: string): string {
  const safe = escapeHtml(text)
  return safe
    .replace(/```(\w*)\n?([\s\S]*?)```/g, '<pre style="background:#f5f5f5;padding:8px;border-radius:4px;font-size:12px;overflow-x:auto;">$2</pre>')
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
}
</script>

<style scoped>
.ai-panel {
  display: flex;
  border-left: 1px solid #e4e7ed;
  background: #fff;
  transition: width 0.2s;
}

.ai-panel.collapsed {
  width: 48px !important;
  min-width: 48px !important;
}

.ai-toggle {
  width: 48px;
  min-width: 48px;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 0;
  cursor: pointer;
  background: #fafafa;
  border-left: 1px solid #e4e7ed;
}

.ai-toggle:hover {
  background: #f0f5ff;
  color: #409eff;
}

.ai-content {
  width: 360px;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.ai-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid #e4e7ed;
}

.ai-messages {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.ai-welcome {
  padding: 16px 8px;
  color: #999;
}

.ai-message {
  margin-bottom: 12px;
  padding: 8px 10px;
  border-radius: 6px;
  font-size: 13px;
  line-height: 1.6;
}

.ai-message.user {
  background: #ecf5ff;
  margin-left: 20px;
}

.ai-message.assistant {
  background: #f5f7fa;
  margin-right: 20px;
}

.msg-label {
  font-size: 11px;
  color: #999;
  margin-bottom: 4px;
  font-weight: 500;
}

.msg-content {
  word-break: break-all;
}

.typing-dot {
  animation: blink 1.4s infinite;
  font-size: 24px;
  line-height: 0;
}
.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes blink { 0% { opacity: 0.2; } 50% { opacity: 1; } 100% { opacity: 0.2; } }

.ai-input {
  padding: 12px;
  border-top: 1px solid #e4e7ed;
}
</style>
