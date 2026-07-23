import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'project-list',
      component: () => import('@/views/ProjectList.vue'),
    },
    {
      path: '/projects/new',
      name: 'project-new',
      component: () => import('@/views/ProjectNew.vue'),
    },
    {
      path: '/projects/:id',
      name: 'project-detail',
      component: () => import('@/views/ProjectDetail.vue'),
      props: true,
    },
    {
      path: '/projects/:id/docs',
      name: 'project-docs',
      component: () => import('@/views/ProjectDocs.vue'),
    },
    {
      path: '/templates',
      name: 'templates',
      component: () => import('@/views/Templates.vue'),
    },
    {
      path: '/report',
      name: 'report',
      component: () => import('@/views/Report.vue'),
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('@/views/Settings.vue'),
    },
    {
      path: '/settings/email',
      name: 'email-settings',
      component: () => import('@/views/EmailSettings.vue'),
    },
  ],
})

export default router
