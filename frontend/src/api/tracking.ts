import api from './index'

export async function listRisks(projectId: number) {
  const res = await api.get(`/projects/${projectId}/risks`)
  return res.data.items || []
}
export async function createRisk(projectId: number, data: any) {
  return api.post(`/projects/${projectId}/risks`, data)
}
export async function updateRisk(projectId: number, riskId: number, data: any) {
  return api.put(`/projects/${projectId}/risks/${riskId}`, data)
}
export async function deleteRisk(projectId: number, riskId: number) {
  return api.delete(`/projects/${projectId}/risks/${riskId}`)
}

export async function listIssues(projectId: number) {
  const res = await api.get(`/projects/${projectId}/issues`)
  return res.data.items || []
}
export async function createIssue(projectId: number, data: any) {
  return api.post(`/projects/${projectId}/issues`, data)
}
export async function updateIssue(projectId: number, issueId: number, data: any) {
  return api.put(`/projects/${projectId}/issues/${issueId}`, data)
}
export async function deleteIssue(projectId: number, issueId: number) {
  return api.delete(`/projects/${projectId}/issues/${issueId}`)
}
