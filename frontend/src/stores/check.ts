import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as checkApi from '@/api/check'
import { ApiError } from '@/api/http'
import { useAuthStore } from './auth'
import type { CheckResult } from '@/api/types'

export const useCheckStore = defineStore('check', () => {
  const studentId = ref<string | null>(null)
  const result = ref<CheckResult | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const hasData = ref<boolean | null>(null)

  // 學號取自登入身分（/api/auth/status 的 student_number），不再使用 localStorage。
  function currentStudentId(): string | null {
    const auth = useAuthStore()
    return auth.user?.student_number ?? null
  }

  async function loadById(id: string) {
    const data = await checkApi.getCheck(id)
    result.value = data
    studentId.value = data.student.id
    hasData.value = true
    return data
  }

  // 進入學生頁時自動載入本人的檢核資料：學號直接取自登入身分。
  async function resolveMyCheck() {
    loading.value = true
    error.value = null
    try {
      const sid = currentStudentId()
      if (sid != null) {
        try {
          await loadById(sid)
          return
        } catch (e) {
          // 後端回 404 代表本人尚未上傳資料，視為無資料而非錯誤
          if (!(e instanceof ApiError && e.status === 404)) throw e
        }
      }

      result.value = null
      hasData.value = false
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
