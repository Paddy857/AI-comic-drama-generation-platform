import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', name: 'Login', component: () => import('@/views/LoginView.vue'), meta: { public: true } },
  {
    path: '/', component: () => import('@/views/Layout.vue'),
    children: [
      { path: '', name: 'Home', component: () => import('@/views/HomeView.vue') },
      { path: 'projects', name: 'Projects', component: () => import('@/views/ProjectsView.vue') },
      { path: 'workspace/:id', name: 'Workspace', component: () => import('@/views/WorkspaceView.vue') },
      { path: 'ai-generate', name: 'AiGenerate', component: () => import('@/views/AiGenerateView.vue') },
      { path: 'templates', name: 'Templates', component: () => import('@/views/TemplatesView.vue') },
      { path: 'templates/:id/workspace', name: 'TemplateWorkspace', component: () => import('@/views/TemplateWorkspaceView.vue') },
      { path: 'characters', name: 'Characters', component: () => import('@/views/CharactersView.vue') },
      { path: 'scenes', name: 'Scenes', component: () => import('@/views/ScenesView.vue') },
      { path: 'assets', name: 'Assets', component: () => import('@/views/AssetsView.vue') },
      { path: 'settings', name: 'Settings', component: () => import('@/views/SettingsView.vue') },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  // 开发模式：认证已关闭，所有页面直接放行（登录页仍保留，供后续恢复鉴权）
  next()
})

export default router
