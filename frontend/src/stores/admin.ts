import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as adminApi from '@/api/admin'
import type {
  AdminDashboardData,
  AdminStudentDetail,
  AdminStudentProfile,
} from '@/api/types'

export const useAdminStore = defineStore('admin', () => {
  // ===== 狀態 =====
  const students = ref<AdminStudentProfile[]>([])
  const dashboard = ref<AdminDashboardData | null>(null)
  const currentDetail = ref<AdminStudentDetail | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const searchQuery = ref('')
  const filterYear = ref<number | null>(null)
  const filterStatus = ref<'all' | 'on_track' | 'at_risk'>('all')

  // ===== 計算屬性 =====
  const dashboardStats = computed(() => ({
    total_students: dashboard.value?.total_students ?? students.value.length,
    on_track_students: dashboard.value?.on_track_students ?? 0,
    at_risk_students: dashboard.value?.at_risk_students ?? 0,
    pass_rate: dashboard.value?.pass_rate ?? 0,
  }))

  const riskStudents = computed(() => dashboard.value?.risk_students ?? [])
  const difficultCourses = computed(() => dashboard.value?.difficult_courses ?? [])

  const filteredStudents = computed(() => {
    let list = [...students.value]
    if (searchQuery.value) {
      const q = searchQuery.value.toLowerCase()
      list = list.filter(
        (s) => (s.name ?? '').toLowerCase().includes(q) || s.student_id.toLowerCase().includes(q),
      )
    }
    if (filterYear.value) {
      list = list.filter((s) => s.admission_year === filterYear.value)
    }
    if (filterStatus.value !== 'all') {
      list = list.filter((s) => s.status === filterStatus.value)
    }
    return list
  })

  const currentStudent = computed(() => currentDetail.value?.profile ?? null)
  const currentCheck = computed(() => currentDetail.value?.check ?? null)

  // ===== 操作方法 =====
  async function fetchDashboard() {
    loading.value = true
    error.value = null
    try {
      dashboard.value = await adminApi.getDashboard()
    } catch (e) {
      error.value = e instanceof Error ? e.message : '載入儀表板失敗'
    } finally {
      loading.value = false
    }
  }

  async function fetchStudents() {
    loading.value = true
    error.value = null
    try {
      students.value = await adminApi.listStudents()
    } catch (e) {
      error.value = e instanceof Error ? e.message : '載入學生列表失敗'
    } finally {
      loading.value = false
    }
  }

  async function fetchStudentDetail(studentId: string) {
    loading.value = true
    error.value = null
    try {
      currentDetail.value = await adminApi.getStudentDetail(studentId)
    } catch (e) {
      error.value = e instanceof Error ? e.message : '載入學生詳情失敗'
      currentDetail.value = null
    } finally {
      loading.value = false
    }
  }

  function applyUpdate(updated: AdminStudentProfile) {
    const idx = students.value.findIndex((s) => s.student_id === updated.student_id)
    if (idx >= 0) students.value[idx] = updated
    if (currentDetail.value?.profile.student_id === updated.student_id) {
      currentDetail.value.profile = updated
    }
  }

  async function updateStudentNotes(studentId: string, notes: string) {
    const updated = await adminApi.updateStudent(studentId, { notes })
    applyUpdate(updated)
  }

  async function updateStudentStatus(studentId: string, status: 'on_track' | 'at_risk') {
    const updated = await adminApi.updateStudent(studentId, { status })
    applyUpdate(updated)
  }

  // 匯出目前篩選後的學生列表為 CSV
  function exportStudentsAsCSV() {
    const header = ['學號', '姓名', '入學年度', '狀態', '已取得學分', '應修學分', '已修課程', '未通過課程']
    const rows = filteredStudents.value.map((s) => [
      s.student_id,
      s.name ?? '',
      `${s.admission_year} 學年度`,
      s.status === 'on_track' ? '已達標' : '需關注',
      s.total_credits,
      s.required_credits,
      s.completed_courses,
      s.failed_courses,
    ])

    const csv = [header, ...rows]
      .map((row) => row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(','))
      .join('\r\n')
    // 前置 UTF-8 BOM（﻿），Excel 才不會把中文判讀成亂碼
    const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', `學生列表_${new Date().getTime()}.csv`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  function reset() {
    students.value = []
    dashboard.value = null
    currentDetail.value = null
    error.value = null
    searchQuery.value = ''
    filterYear.value = null
    filterStatus.value = 'all'
  }

  return {
    // 狀態
    students,
    dashboard,
    currentDetail,
    currentStudent,
    currentCheck,
    loading,
    error,
    searchQuery,
    filterYear,
    filterStatus,
    // 計算屬性
    dashboardStats,
    riskStudents,
    difficultCourses,
    filteredStudents,
    // 方法
    fetchDashboard,
    fetchStudents,
    fetchStudentDetail,
    updateStudentNotes,
    updateStudentStatus,
    exportStudentsAsCSV,
    reset,
  }
})
