import api from './index'

export interface AISettings {
  provider: string
  api_key: string
  api_base: string
  model: string
}

export async function getAISettings(): Promise<AISettings> {
  const res = await api.get('/settings/ai')
  return res.data
}

export async function saveAISettings(data: Partial<AISettings>): Promise<void> {
  await api.post('/settings/ai', data)
}

export async function testAIConnection(data: Partial<AISettings>): Promise<{ status: string; message: string }> {
  const res = await api.post('/settings/ai/test', data)
  return res.data
}
