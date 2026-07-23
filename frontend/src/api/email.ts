import api from './index'

export function getConfig() {
  return api.get('/email/config')
}

export function saveConfig(data: {
  smtp_host: string
  smtp_port: number
  smtp_user: string
  smtp_pass: string
  sender_name: string
}) {
  return api.post('/email/config', data)
}

export function testConfig(data: {
  smtp_host: string
  smtp_port: number
  smtp_user: string
  smtp_pass: string
  sender_name: string
}) {
  return api.post('/email/test', data)
}

export function sendEmail(to: string[], subject: string, body: string) {
  return api.post('/email/send', { to, subject, body })
}

export function notifyOverdue(projectId: number) {
  return api.post(`/email/projects/${projectId}/notify/overdue`)
}
