import api from './index'

export interface TaskDef {
  name: string
  task_number?: string
  guide?: string
  deliverable?: string
  vendor_role?: string
  customer_role?: string
  estimated_days?: number
  sort_order?: number
}

export interface PhaseDef {
  phase_number: number
  name: string
  description?: string
  sort_order?: number
  tasks: TaskDef[]
}

export interface Template {
  id: number
  name: string
  product_id: number
  version: string
  is_active: boolean
  phases: (PhaseDef & { id: number; tasks: (TaskDef & { id: number })[] })[]
}

export function listTemplates() {
  return api.get('/templates')
}

export function getTemplate(id: number) {
  return api.get(`/templates/${id}`)
}

export function createTemplate(data: { name: string; version?: string; phases: PhaseDef[] }) {
  return api.post('/templates', data)
}

export function updateTemplate(id: number, data: { name?: string; version?: string; is_active?: boolean }) {
  return api.put(`/templates/${id}`, data)
}

export function deleteTemplate(id: number) {
  return api.delete(`/templates/${id}`)
}

export function applyTemplate(templateId: number, projectId: number, startDate: string) {
  return api.post(`/templates/${templateId}/apply`, { project_id: projectId, start_date: startDate })
}
