export interface ProjectTask {
  id: number
  project_phase_id: number
  task_number: string
  name: string
  guide: string
  deliverable: string
  assignee: string
  planned_start: string | null
  planned_end: string | null
  actual_start: string | null
  actual_end: string | null
  status: string
  progress: number
  notes: string
  sort_order: number
}

export interface ProjectPhase {
  id: number
  phase_number: number
  name: string
  planned_start: string | null
  planned_end: string | null
  status: string
  sort_order: number
  tasks: ProjectTask[]
}

export interface Project {
  id: number
  name: string
  customer_name: string
  stage: string
  start_date: string
  planned_end_date: string | null
  status: string
  created_at: string
  products: { product_id: number }[]
  phases: ProjectPhase[]
}

export interface ProjectListItem {
  id: number
  name: string
  customer_name: string
  stage: string
  start_date: string
  status: string
  created_at: string
}

export interface ProjectCreate {
  name: string
  customer_name: string
  stage: string
  start_date: string
  product_ids: number[]
}

import api from './index'

export async function createProject(data: ProjectCreate): Promise<Project> {
  const res = await api.post('/projects', data)
  return res.data
}
