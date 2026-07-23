<template>
  <div class="ai-panel">
    <div class="ai-header">
      <span style="font-weight:600;font-size:14px;">AI 助手</span>
      <div style="display:flex;gap:4px;align-items:center;">
        <el-select v-model="currentProvider" size="small" style="width:100px;"
                   @change="onProviderChange" v-if="providers.length > 1">
          <el-option v-for="p in providers" :key="p.id" :label="p.name" :value="p.id" />
        </el-select>
        <el-button link size="small" @click="clearCurrentChat"><el-icon><Delete /></el-icon></el-button>
        <el-button link size="small" @click="$emit('close')"><el-icon><Close /></el-icon></el-button>
      </div>
    </div>

    <div class="ai-tabs">
      <div class="tab-item" :class="{ active: activeTab === 'chat' }" @click="switchTab('chat')">💬 对话</div>
      <div class="tab-item" :class="{ active: activeTab === 'meeting' }" @click="switchTab('meeting')">📝 会议纪要</div>
    </div>

    <div class="ai-messages" ref="msgContainer">
      <div v-if="currentMessages.length === 0" style="padding:12px 4px;font-size:13px;color:#999;text-align:center;">
        <span v-if="activeTab === 'chat'">输入问题开始对话</span>
        <span v-else>粘贴会议纪要，AI 自动处理任务</span>
      </div>
      <div v-for="(msg, i) in currentMessages" :key="i" class="ai-message" :class="msg.role">
        <div class="msg-label">{{ msg.role === 'user' ? '你' : 'AI' }}</div>
        <div :class="msg.role === 'user' ? 'msg-content' : 'msg-content markdown-body'"
             v-html="renderMarkdown(msg.content)"></div>
      </div>
      <div v-if="store.loading" class="ai-message assistant">
        <div class="msg-label">AI</div>
        <div class="msg-content"><span class="typing-dot">.</span><span class="typing-dot">.</span><span class="typing-dot">.</span></div>
      </div>
    </div>

    <el-dialog v-model="showConfirm" title="确认执行操作" width="400px" append-to-body>
      <div style="font-size:14px;line-height:1.6;">
        <p style="margin-bottom:8px;">
          <el-tag size="small">{{ store.pendingAction?.action_type }}</el-tag>
          <el-tag size="small" type="info" style="margin-left:4px;">{{ store.pendingAction?.entity }}</el-tag>
        </p>
        <pre style="background:#f5f7fa;padding:8px;border-radius:4px;font-size:12px;">{{ JSON.stringify(store.pendingAction?.data || store.pendingAction, null, 2) }}</pre>
      </div>
      <template #footer>
        <el-button @click="rejectAction">取消</el-button>
        <el-button type="primary" @click="confirmAction">确认执行</el-button>
      </template>
    </el-dialog>

    <div class="ai-input">
      <el-input v-if="activeTab === 'chat'" v-model="inputMessage" type="textarea" :rows="2"
                :placeholder="hasProject ? '输入问题...' : '输入问题（通用模式）'" :disabled="store.loading"
                @keydown.enter.ctrl="sendMessage" />
      <el-input v-else v-model="inputMessage" type="textarea" :rows="6"
                placeholder="粘贴会议纪要内容..." :disabled="store.loading" />
      <el-button type="primary" :loading="store.loading" @click="sendMessage" style="margin-top:4px;width:100%;">
        {{ activeTab === 'meeting' ? 'AI 解析纪要并执行' : '发送' }}
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useAIStore } from '@/stores/ai'
import { sendQuery, executeAction, fetchAIConfig } from '@/api/ai'
import type { ChatMessage } from '@/stores/ai'

const props = defineProps<{ projectId: number | null }>()
const emit = defineEmits<{ close: [] }>()
const store = useAIStore()

const inputMessage = ref('')
const msgContainer = ref<HTMLElement | null>(null)
const showConfirm = ref(false)
const providers = ref<{id:string;name:string}[]>([])
const currentProvider = ref('')
const activeTab = ref<'chat' | 'meeting'>('chat')
const chatHistory = ref<ChatMessage[]>([])
const meetingHistory = ref<ChatMessage[]>([])

const currentMessages = computed(() => activeTab.value === 'chat' ? chatHistory.value : meetingHistory.value)
const hasProject = computed(() => !!props.projectId && props.projectId > 0)

watch(currentMessages, () => {
  nextTick(() => { if (msgContainer.value) msgContainer.value.scrollTop = msgContainer.value.scrollHeight })
})

onMounted(async () => {
  try {
    const savedChat = sessionStorage.getItem('ccb_ai_chat')
    if (savedChat) chatHistory.value = JSON.parse(savedChat)
    const savedMeeting = sessionStorage.getItem('ccb_ai_meeting')
    if (savedMeeting) meetingHistory.value = JSON.parse(savedMeeting)
  } catch {}
  try {
    const config = await fetchAIConfig()
    providers.value = config.providers
    currentProvider.value = config.current
  } catch {}
})

function saveHistory() {
  sessionStorage.setItem('ccb_ai_chat', JSON.stringify(chatHistory.value))
  sessionStorage.setItem('ccb_ai_meeting', JSON.stringify(meetingHistory.value))
}

function switchTab(tab: 'chat' | 'meeting') { activeTab.value = tab }
function clearCurrentChat() {
  if (activeTab.value === 'chat') chatHistory.value = []
  else meetingHistory.value = []
  saveHistory()
}
function onProviderChange(val: string) { currentProvider.value = val }

function addMessage(msg: ChatMessage) {
  if (activeTab.value === 'chat') chatHistory.value.push(msg)
  else meetingHistory.value.push(msg)
  saveHistory()
}

function appendToLastMessage(text: string) {
  const hist = activeTab.value === 'chat' ? chatHistory.value : meetingHistory.value
  const last = hist[hist.length - 1]
  if (last && last.role === 'assistant') { last.content += text; saveHistory() }
}

async function sendMessage() {
  let msg = inputMessage.value.trim()
  if (!msg || store.loading) return
  if (activeTab.value === 'meeting') {
    msg = `以下是会议纪要，请根据内容增删改任务。如果有新任务就创建，有完成的任务就更新状态为completed，有取消的任务就删除。\n\n会议纪要：\n${msg}`
  }
  inputMessage.value = ''
  addMessage({ role: 'user', content: msg })
  store.loading = true
  addMessage({ role: 'assistant', content: '' })

  const history = (activeTab.value === 'chat' ? chatHistory.value : meetingHistory.value)
    .filter(m => m.role === 'user' || m.role === 'assistant').slice(0, -1)
    .map(m => ({ role: m.role as 'user' | 'assistant', content: m.content }))

  const targetId = hasProject ? props.projectId! : 0
  await sendQuery(targetId, msg, history, currentProvider.value,
    (chunk) => appendToLastMessage(chunk),
    (action) => { store.pendingAction = action; showConfirm.value = true },
    () => { store.loading = false },
    (err) => { store.loading = false; appendToLastMessage(`\n\n[错误: ${err}]`) })
}

async function confirmAction() {
  if (!store.pendingAction || !hasProject) {
    appendToLastMessage('\n\n⚠️ 请先进入项目详情后再执行操作')
    showConfirm.value = false; store.pendingAction = null; return
  }
  showConfirm.value = false
  try {
    const result = await executeAction(props.projectId!, store.pendingAction)
    appendToLastMessage(`\n\n✅ 操作已执行: ${result.action || result.status} (${result.entity} #${result.id || ''})`)
    window.dispatchEvent(new CustomEvent('ccb:ai-action', { detail: { entity: store.pendingAction.entity } }))
  } catch (e: any) { appendToLastMessage(`\n\n❌ 操作执行失败: ${e.message}`) }
  store.pendingAction = null
}

function rejectAction() {
  showConfirm.value = false
  appendToLastMessage('\n\n⚠️ 操作已取消')
  store.pendingAction = null
}

function escapeHtml(text: string): string {
  const div = document.createElement('div'); div.textContent = text; return div.innerHTML
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
  width: 360px;
  min-width: 360px;
  background: #fff;
  border-left: 1px solid #dcdfe6;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.ai-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  border-bottom: 1px solid #e4e7ed;
}

.ai-tabs { display: flex; border-bottom: 1px solid #e4e7ed; background: #fafafa; }
.tab-item { flex:1; text-align:center; padding:6px 0; font-size:12px; cursor:pointer; color:#999; border-bottom:2px solid transparent; transition:all .15s; }
.tab-item:hover { color:#409eff; background:#f0f5ff; }
.tab-item.active { color:#409eff; border-bottom-color:#409eff; font-weight:500; }

.ai-messages { flex:1; overflow-y:auto; padding:12px; }
.ai-message { margin-bottom:12px; padding:8px 10px; border-radius:6px; font-size:13px; line-height:1.6; animation:msgSlide .2s ease; }
.ai-message.user { background:#ecf5ff; margin-left:20px; }
.ai-message.assistant { background:#f5f7fa; margin-right:20px; }
.msg-label { font-size:11px; color:#999; margin-bottom:4px; font-weight:500; }
.msg-content { word-break:break-all; }
.typing-dot { animation:blink 1.4s infinite; font-size:24px; line-height:0; }
.typing-dot:nth-child(2) { animation-delay:.2s; }
.typing-dot:nth-child(3) { animation-delay:.4s; }
@keyframes blink { 0%{opacity:.2} 50%{opacity:1} 100%{opacity:.2} }
@keyframes msgSlide { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }

.ai-input { padding:12px; border-top:1px solid #e4e7ed; }
</style>
