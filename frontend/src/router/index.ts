import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/auth/LoginView.vue'),
    meta: { public: true },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('@/views/auth/RegisterView.vue'),
    meta: { public: true },
  },
  // ==================== 管理員路由 ====================
  {
    path: '/admin/login',
    name: 'admin-login',
    component: () => import('@/views/admin/AdminLogin.vue'),
    meta: { public: true },
  },
  {
    path: '/admin',
    redirect: { name: 'admin-dashboard' },
  },
  {
    path: '/admin/dashboard',
    name: 'admin-dashboard',
    component: () => import('@/views/admin/AdminDashboard.vue'),
    meta: { requiresAdminAuth: true },
  },
  {
    path: '/admin/student-list',
    name: 'student-list',
    component: () => import('@/views/admin/StudentList.vue'),
    meta: { requiresAdminAuth: true },
  },
  {
    path: '/admin/student/:id',
    name: 'student-detail',
    component: () => import('@/views/admin/StudentDetail.vue'),
    meta: { requiresAdminAuth: true },
  },
  // ==================== 學生路由 ====================
  {
    path: '/',
    component: () => import('@/layouts/StudentLayout.vue'),
    redirect: { name: 'overview' },
    children: [
      {
        path: 'overview',
        name: 'overview',
        component: () => import('@/views/student/OverviewView.vue'),
      },
      {
        path: 'inventory',
        name: 'inventory',
        component: () => import('@/views/student/InventoryView.vue'),
      },
      {
        path: 'upload',
        name: 'upload',
        component: () => import('@/views/student/UploadView.vue'),
      },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: { name: 'overview' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  if (auth.isAuthenticated && !auth.user) {
    await auth.fetchStatus().catch(() => undefined)
  }

  // ===== 管理員身份驗證 =====
  if (to.meta.requiresAdminAuth) {
    if (!auth.isAuthenticated) {
      return { name: 'admin-login', query: { redirect: to.fullPath } }
    }
    if (!auth.isAdmin) {
      return { name: 'overview' }
    }
  }

  // ===== 學生身份驗證 =====
  if (!to.meta.public && !to.meta.requiresAdminAuth && !auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  // ===== 已認證學生訪問公共路由的重定向 =====
  if (to.meta.public && to.name === 'login' && auth.isAuthenticated) {
    return auth.isAdmin ? { name: 'admin-dashboard' } : { name: 'overview' }
  }

  // ===== 已認證管理員訪問管理員登入的重定向 =====
  if (to.name === 'admin-login' && auth.isAdmin) {
    return { name: 'admin-dashboard' }
  }

  return true
})

export default router
