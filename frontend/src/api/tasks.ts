export interface TaskUpdate {
  status?: string
  progress?: number
  assignee?: string
  actual_start?: string
  actual_end?: string
  notes?: string
}

import api from './index'

export async function updateTask(projectId: number, taskId: number, data: TaskUpdate) {
  const res = await api.put(`/projects/${projectId}/tasks/${taskId}`, data)
  return res.data
}
