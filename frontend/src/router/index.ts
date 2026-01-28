/**
 * Vue Router 配置
 */
import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/pages/Login.vue'),
    meta: { title: '登录', requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/pages/Register.vue'),
    meta: { title: '注册', requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('@/pages/Layout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Translate',
        component: () => import('@/pages/Translate.vue'),
        meta: { title: '翻译' }
      },
      {
        path: 'history',
        name: 'History',
        component: () => import('@/pages/History.vue'),
        meta: { title: '翻译历史' }
      },
      {
        path: 'prompts',
        name: 'Prompts',
        component: () => import('@/pages/PromptManage.vue'),
        meta: { title: '提示词管理' }
      },
      {
        path: 'comparisons',
        name: 'Comparisons',
        component: () => import('@/pages/ComparisonManage.vue'),
        meta: { title: '术语对照表' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - DocTranslator` : 'DocTranslator'

  // 检查是否需要登录
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth !== false && !token) {
    next('/login')
  } else if ((to.path === '/login' || to.path === '/register') && token) {
    next('/')
  } else {
    next()
  }
})

export default router
