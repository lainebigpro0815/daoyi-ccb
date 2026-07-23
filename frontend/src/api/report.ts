import api from './index'

export function getWeeklyReport(projectId: number) {
  return api.get(`/projects/${projectId}/report/weekly`)
}

export function exportReport(projectId: number, type: string = 'weekly') {
  return api.get(`/projects/${projectId}/report/export?type=${type}`, {
    responseType: 'blob',
  })
}
