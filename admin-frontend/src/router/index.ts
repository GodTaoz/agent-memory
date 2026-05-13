import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('../views/LoginView.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/',
      redirect: '/dashboard',
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: () => import('../views/DashboardView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/api-keys',
      name: 'ApiKeys',
      component: () => import('../views/ApiKeysView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/memories',
      name: 'Memories',
      component: () => import('../views/MemoriesView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/agents',
      name: 'Agents',
      component: () => import('../views/AgentsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/logs',
      name: 'Logs',
      component: () => import('../views/LogsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/settings',
      name: 'Settings',
      component: () => import('../views/SettingsView.vue'),
      meta: { requiresAuth: true },
    },
  ],
})

// Navigation guard
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  if (to.meta.requiresAuth !== false && !authStore.isAuthenticated) {
    next('/login')
  } else {
    next()
  }
})

export default router
