import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as checkApi from '@/api/check'
import { ApiError } from '@/api/http'
import { useAuthStore } from './auth'
import type { CheckResult } from '@/api/types'

const STUDENT_ID_PREFIX = 'gradcheck_student_id:'

function storedStudentIdKey(account: string) {
  return `${STUDENT_ID_PREFIX}${account}`
}

export const useCheckStore = defineStore('check', () => {
  const studentId = ref<number | null>(null)
  const result = ref<CheckResult | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  // null = 尚未解析；true = 有資料；false = 確認無資料（引導上傳）
  const hasData = ref<boolean | null>(null)

  function rememberStudentId(id: number) {
    const auth = useAuthStore()
    studentId.value = id
    if (auth.user?.account) {
      localStorage.setItem(storedStudentIdKey(auth.user.account), String(id))
    }
  }

  function candidateStudentId(): number | null {
    const auth = useAuthStore()
    if (auth.user?.student_id != null) return auth.user.student_id
    if (auth.user?.account) {
      const raw = localStorage.getItem(storedStudentIdKey(auth.user.account))
      if (raw) {
        const n = Number(raw)
        if (Number.isFinite(n)) return n
      }
    }
    return null
  }

  async function loadById(id: number) {
    const data = await checkApi.getCheck(id)
    result.value = data
    studentId.value = data.student.id
    hasData.value = true
    return data
  }

  // 解析目前登入學生的檢核資料：student_id → localStorage 後備 → /me。
  async function resolveMyCheck() {
    loading.value = true
    error.value = null
    try {
      const candidate = candidateStudentId()
      if (candidate != null) {
        try {
          await loadById(candidate)
          return
        } catch (e) {
          // 資料可能已被刪除，往下嘗試其他途徑
          if (!(e instanceof ApiError && e.status === 404)) throw e
        }
      }

      // 後端若提供 /api/check/me 則用它解析；未實作會 404 → 視為無資料
      try {
        const data = await checkApi.getMyCheck()
        result.value = data
        rememberStudentId(data.student.id)
        hasData.value = true
        return
      } catch (e) {
        if (e instanceof ApiError && (e.status === 404 || e.status === 405)) {
          result.value = null
          hasData.value = false
          return
        }
        throw e
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : '載入檢核資料失敗'
      hasData.value = null
    } finally {
      loading.value = false
    }
  }

  async function upload(file: File) {
    loading.value = true
    error.value = null
    try {
      const res = await checkApi.uploadStudentJson(file)
      rememberStudentId(res.student_id)
      await loadById(res.student_id)
      return res
    } catch (e) {
      error.value = e instanceof Error ? e.message : '上傳失敗'
      throw e
    } finally {
      loading.value = false
    }
  }

  function reset() {
    studentId.value = null
    result.value = null
    error.value = null
    hasData.value = null
  }

  return {
    studentId,
    result,
    loading,
    error,
    hasData,
    resolveMyCheck,
    loadById,
    upload,
    reset,
  }
})
