import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as authApi from '@/api/auth'
import { TOKEN_KEY } from '@/api/http'
import type { LoginRequest, RegisterRequest, Role, StatusResponse } from '@/api/types'

export interface CurrentUser {
  user_id: number
  account: string
  role: Role
  student_id?: number | null
  student_number?: string | null
  name?: string | null
  admission_year?: number | null
  administrator_id?: number | null
  department_id?: number | null
  department_name?: string | null
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
  const user = ref<CurrentUser | null>(null)

  const isAuthenticated = computed(() => !!token.value)
  const isStudent = computed(() => user.value?.role === 'student')
  const isAdmin = computed(() => user.value?.role === 'admin')

  function setToken(value: string | null) {
    token.value = value
    if (value) {
      localStorage.setItem(TOKEN_KEY, value)
    } else {
      localStorage.removeItem(TOKEN_KEY)
    }
  }

  async function login(body: LoginRequest) {
    const res = await authApi.login(body)
    setToken(res.access_token)
    user.value = { user_id: res.user_id, account: body.account, role: res.role }
    // 登入後嘗試補齊完整身分（含 student_id）
    await fetchStatus().catch(() => undefined)
    return res
  }

  async function register(body: RegisterRequest) {
    return authApi.register(body)
  }

  async function fetchStatus(): Promise<StatusResponse | null> {
    if (!token.value) return null
    const res = await authApi.status()
    user.value = {
      user_id: res.user_id,
      account: res.account,
      role: res.role,
      student_id: res.student_id ?? null,
      student_number: res.student_number ?? null,
      name: res.name ?? null,
      admission_year: res.admission_year ?? null,
      administrator_id: res.administrator_id ?? null,
      department_id: res.department_id ?? null,
      department_name: res.department_name ?? null,
    }
    return res
  }

  async function logout() {
    try {
      await authApi.logout()
    } catch {
      // 即使後端登出失敗，前端仍清除本地狀態
    }
    setToken(null)
    user.value = null
  }

  return {
    token,
    user,
    isAuthenticated,
    isStudent,
    isAdmin,
    login,
    register,
    fetchStatus,
    logout,
  }
})
