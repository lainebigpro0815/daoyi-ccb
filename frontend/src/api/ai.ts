import api from './index'
import type { ChatMessage, AIAction } from '@/stores/ai'

export interface AIConfig {
  current: string
  providers: { id: string; name: string; models: string[] }[]
}

export async function fetchAIConfig(): Promise<AIConfig> {
  const res = await api.get('/ai/config')
  return res.data
}

export async function sendQuery(
  projectId: number,
  message: string,
  history: ChatMessage[],
  provider: string,
  onText: (chunk: string) => void,
  onAction: (action: AIAction) => void,
  onDone: () => void,
  onError: (err: string) => void,
): Promise<void> {
  try {
    const endpoint = projectId > 0
      ? `/api/projects/${projectId}/ai/query`
      : '/api/ai/query'

    const resp = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, history, provider }),
    })

    if (!resp.ok) {
      onError(`请求失败: ${resp.status}`)
      return
    }

    const reader = resp.body?.getReader()
    if (!reader) return

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            if (data.type === 'text') {
              onText(data.content)
            } else if (data.type === 'action') {
              onAction(data.action)
            } else if (data.type === 'done') {
              onDone()
            } else if (data.type === 'error') {
              onError(data.content)
            }
          } catch {
            // skip parse errors for incomplete chunks
          }
        }
      }
    }
  } catch (e: any) {
    onError(e.message || '连接失败')
  }
}

export async function executeAction(projectId: number, action: AIAction) {
  const res = await api.post(`/projects/${projectId}/ai/execute`, action)
  return res.data
}
