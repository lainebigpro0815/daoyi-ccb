import { defineStore } from 'pinia'

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface AIAction {
  action_type: string
  entity?: string
  entity_id?: number
  data?: Record<string, any>
}

const STORAGE_KEY = 'ccb_ai_messages'

function loadMessages(): ChatMessage[] {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch { return [] }
}

function saveMessages(msgs: ChatMessage[]) {
  try { sessionStorage.setItem(STORAGE_KEY, JSON.stringify(msgs)) } catch {}
}

interface AIState {
  messages: ChatMessage[]
  loading: boolean
  panelOpen: boolean
  pendingAction: AIAction | null
}

export const useAIStore = defineStore('ai', {
  state: (): AIState => ({
    messages: loadMessages(),
    loading: false,
    panelOpen: true,
    pendingAction: null,
  }),
  actions: {
    togglePanel() {
      this.panelOpen = !this.panelOpen
    },
    addMessage(msg: ChatMessage) {
      this.messages.push(msg)
      saveMessages(this.messages)
    },
    appendToLastMessage(text: string) {
      const last = this.messages[this.messages.length - 1]
      if (last && last.role === 'assistant') {
        last.content += text
        saveMessages(this.messages)
      }
    },
    clearMessages() {
      this.messages = []
      saveMessages([])
    },
  },
})
