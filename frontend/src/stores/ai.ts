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

interface AIState {
  messages: ChatMessage[]
  loading: boolean
  panelOpen: boolean
  pendingAction: AIAction | null
}

export const useAIStore = defineStore('ai', {
  state: (): AIState => ({
    messages: [],
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
    },
    appendToLastMessage(text: string) {
      const last = this.messages[this.messages.length - 1]
      if (last && last.role === 'assistant') {
        last.content += text
      }
    },
    clearMessages() {
      this.messages = []
    },
  },
})
