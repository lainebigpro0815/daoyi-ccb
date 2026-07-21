import { defineStore } from 'pinia'
import api from '@/api'
import type { Project, ProjectListItem } from '@/api/projects'

interface ProjectState {
  projects: ProjectListItem[]
  currentProject: Project | null
  loading: boolean
}

export const useProjectStore = defineStore('project', {
  state: (): ProjectState => ({
    projects: [],
    currentProject: null,
    loading: false,
  }),
  actions: {
    async fetchProjects() {
      this.loading = true
      try {
        const res = await api.get('/projects')
        this.projects = res.data.items
      } finally {
        this.loading = false
      }
    },
    async fetchProject(id: number) {
      this.loading = true
      try {
        const res = await api.get(`/projects/${id}`)
        this.currentProject = res.data
      } finally {
        this.loading = false
      }
    },
  },
})
