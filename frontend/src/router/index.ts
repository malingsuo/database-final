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
  // ==================== 管理员路由 ====================
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
  // ==================== 学生路由 ====================
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

  // ===== 管理员身份验证 =====
  if (to.meta.requiresAdminAuth) {
    if (!auth.isAuthenticated) {
      return { name: 'admin-login', query: { redirect: to.fullPath } }
    }
    if (!auth.isAdmin) {
      return { name: 'overview' }
    }
  }

  // ===== 学生身份验证 =====
  if (!to.meta.public && !to.meta.requiresAdminAuth && !auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  // ===== 已认证学生访问公共路由的重定向 =====
  if (to.meta.public && to.name === 'login' && auth.isAuthenticated) {
    return auth.isAdmin ? { name: 'admin-dashboard' } : { name: 'overview' }
  }

  // ===== 已认证管理员访问管理员登入的重定向 =====
  if (to.name === 'admin-login' && auth.isAdmin) {
    return { name: 'admin-dashboard' }
  }

  return true
})

export default router
