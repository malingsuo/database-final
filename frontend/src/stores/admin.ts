import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// ==================== 型別定義 ====================
export interface Course {
  course_id: string
  course_name: string
  year: number
  semester: number
  credits: number
  grade: number
  is_passed: boolean
  category: 'core' | 'departmentCore' | 'elective' | 'general'
}

export interface Student {
  student_id: string
  name: string
  admission_year: number
  status: 'on_track' | 'at_risk'
  double_major?: boolean
  exchange_student?: boolean
  total_credits: number
  required_credits: number
  completed_courses: number
  notes?: string
  courses: Course[]
}

export interface AdminUser {
  admin_id: string
  name: string
  department: string
}

export interface DashboardStats {
  total_students: number
  on_track_students: number
  at_risk_students: number
  pass_rate: number
}

// ==================== Mock 資料 ====================
const mockStudents: Student[] = [
  {
    student_id: '112703001',
    name: '林子晴',
    admission_year: 112,
    status: 'on_track',
    double_major: true,
    exchange_student: false,
    total_credits: 120,
    required_credits: 120,
    completed_courses: 42,
    notes: '雙主修資訊科學系，學分進度穩定。',
    courses: [
      {
        course_id: 'CS101',
        course_name: '數位系統',
        year: 113,
        semester: 1,
        credits: 3,
        grade: 80,
        is_passed: true,
        category: 'departmentCore',
      },
      {
        course_id: 'CS102',
        course_name: '離散數學',
        year: 113,
        semester: 1,
        credits: 3,
        grade: 85,
        is_passed: true,
        category: 'departmentCore',
      },
      {
        course_id: 'CS103',
        course_name: '資料結構',
        year: 113,
        semester: 2,
        credits: 3,
        grade: 92,
        is_passed: true,
        category: 'departmentCore',
      },
    ],
  },
  {
    student_id: '112703002',
    name: '王浩宇',
    admission_year: 112,
    status: 'at_risk',
    double_major: false,
    exchange_student: false,
    total_credits: 45,
    required_credits: 90,
    completed_courses: 15,
    notes: '學分進度落後，建議安排導師晤談。',
    courses: [
      {
        course_id: 'CORE201',
        course_name: '線性代數',
        year: 113,
        semester: 1,
        credits: 3,
        grade: 68,
        is_passed: true,
        category: 'departmentCore',
      },
      {
        course_id: 'CORE202',
        course_name: '微積分',
        year: 113,
        semester: 1,
        credits: 3,
        grade: 52,
        is_passed: false,
        category: 'departmentCore',
      },
      {
        course_id: 'GEN101',
        course_name: '大一英文',
        year: 112,
        semester: 1,
        credits: 2,
        grade: 75,
        is_passed: true,
        category: 'general',
      },
    ],
  },
  {
    student_id: '112703003',
    name: '陳思語',
    admission_year: 112,
    status: 'on_track',
    double_major: false,
    exchange_student: true,
    total_credits: 115,
    required_credits: 120,
    completed_courses: 38,
    notes: '交換生預審透過，需追蹤學分抵免進度。',
    courses: [
      {
        course_id: 'CS301',
        course_name: '演演算法設計',
        year: 113,
        semester: 1,
        credits: 3,
        grade: 88,
        is_passed: true,
        category: 'departmentCore',
      },
      {
        course_id: 'CS302',
        course_name: '資料庫系統',
        year: 113,
        semester: 2,
        credits: 3,
        grade: 90,
        is_passed: true,
        category: 'elective',
      },
    ],
  },
  {
    student_id: '113703004',
    name: '許家豪',
    admission_year: 113,
    status: 'at_risk',
    double_major: false,
    exchange_student: false,
    total_credits: 52,
    required_credits: 90,
    completed_courses: 18,
    notes: '必修課多次未透過，需安排學業輔導。',
    courses: [
      {
        course_id: 'CORE203',
        course_name: '程式設計',
        year: 112,
        semester: 1,
        credits: 3,
        grade: 45,
        is_passed: false,
        category: 'departmentCore',
      },
      {
        course_id: 'CORE204',
        course_name: '計算機組織',
        year: 113,
        semester: 1,
        credits: 3,
        grade: 60,
        is_passed: true,
        category: 'departmentCore',
      },
    ],
  },
  {
    student_id: '112703005',
    name: '黃詩涵',
    admission_year: 112,
    status: 'on_track',
    double_major: false,
    exchange_student: false,
    total_credits: 128,
    required_credits: 120,
    completed_courses: 45,
    notes: '畢業門檻已接近完成，可準備畢業資格複核。',
    courses: [
      {
        course_id: 'CS401',
        course_name: '專題研討',
        year: 113,
        semester: 2,
        credits: 3,
        grade: 95,
        is_passed: true,
        category: 'elective',
      },
      {
        course_id: 'CS402',
        course_name: '人工智慧',
        year: 113,
        semester: 2,
        credits: 3,
        grade: 87,
        is_passed: true,
        category: 'elective',
      },
    ],
  },
]

// ==================== Pinia Store ====================
export const useAdminStore = defineStore('admin', () => {
  // ===== 狀態 =====
  const admin = ref<AdminUser | null>(null)
  const students = ref<Student[]>(mockStudents)
  const currentStudent = ref<Student | null>(null)
  const searchQuery = ref('')
  const filterYear = ref<number | null>(null)
  const filterStatus = ref<'all' | 'on_track' | 'at_risk'>('all')

  // ===== 計算屬性 =====
  const dashboardStats = computed(() => {
    const total = students.value.length
    const onTrack = students.value.filter((s) => s.status === 'on_track').length
    const atRisk = students.value.filter((s) => s.status === 'at_risk').length
    const passRate = total > 0 ? Math.round((onTrack / total) * 100) : 0

    return {
      total_students: total,
      on_track_students: onTrack,
      at_risk_students: atRisk,
      pass_rate: passRate,
    }
  })

  // 高風險學生列表
  const riskStudents = computed(() => {
    return students.value
      .filter((s) => s.status === 'at_risk')
      .sort((a, b) => {
        const riskA = 1 - a.total_credits / a.required_credits
        const riskB = 1 - b.total_credits / b.required_credits
        return riskB - riskA
      })
      .slice(0, 5)
  })

  // 未透過率最高的課程前三名
  const difficultCourses = computed(() => {
    const courseStats = new Map<string, { name: string; total: number; failed: number }>()

    students.value.forEach((student) => {
      student.courses.forEach((course) => {
        const key = course.course_id
        if (!courseStats.has(key)) {
          courseStats.set(key, { name: course.course_name, total: 0, failed: 0 })
        }
        const stats = courseStats.get(key)!
        stats.total++
        if (!course.is_passed) {
          stats.failed++
        }
      })
    })

    return Array.from(courseStats.values())
      .map((s) => ({
        ...s,
        failRate: Math.round((s.failed / s.total) * 100),
      }))
      .sort((a, b) => b.failRate - a.failRate)
      .slice(0, 3)
  })

  const filteredStudents = computed(() => {
    let filtered = [...students.value]

    if (searchQuery.value) {
      const query = searchQuery.value.toLowerCase()
      filtered = filtered.filter(
        (s) => s.name.toLowerCase().includes(query) || s.student_id.toLowerCase().includes(query)
      )
    }

    if (filterYear.value) {
      filtered = filtered.filter((s) => s.admission_year === filterYear.value)
    }

    if (filterStatus.value !== 'all') {
      filtered = filtered.filter((s) => s.status === filterStatus.value)
    }

    return filtered
  })

  // ===== 操作方法 =====
  // 管理員登入（保留舊頁相容）
  function adminLogin(account: string, password: string) {
    if (account && password) {
      admin.value = {
        admin_id: 'ADMIN001',
        name: '李老師',
        department: '資訊科學系',
      }
      return true
    }
    return false
  }

  // 管理員登出
  function adminLogout() {
    admin.value = null
    currentStudent.value = null
  }

  // 取得學生詳情
  function getStudentDetail(studentId: string) {
    const student = students.value.find((s) => s.student_id === studentId)
    if (student) {
      currentStudent.value = student
    }
    return student
  }

  // 更新學生備註
  function updateStudentNotes(studentId: string, notes: string) {
    const student = students.value.find((s) => s.student_id === studentId)
    if (student) {
      student.notes = notes
      if (currentStudent.value && currentStudent.value.student_id === studentId) {
        currentStudent.value.notes = notes
      }
    }
  }

  // 更新學生狀態
  function updateStudentStatus(studentId: string, status: 'on_track' | 'at_risk') {
    const student = students.value.find((s) => s.student_id === studentId)
    if (student) {
      student.status = status
      if (currentStudent.value && currentStudent.value.student_id === studentId) {
        currentStudent.value.status = status
      }
    }
  }

  // 匯出學生列表為 CSV 格式
  function exportStudentsAsCSV() {
    const header = ['學號', '姓名', '入學年度', '狀態', '總學分', '應修學分', '已完成課程數']
    const rows = filteredStudents.value.map((s) => [
      s.student_id,
      s.name,
      `${s.admission_year} 學年度`,
      s.status === 'on_track' ? '已達標' : '需關注',
      s.total_credits,
      s.required_credits,
      s.completed_courses,
    ])

    const csv = [header, ...rows].map((row) => row.join(',')).join('\n')

    // 建立下載連結
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', `學生列表_${new Date().getTime()}.csv`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  return {
    // 狀態
    admin,
    students,
    currentStudent,
    searchQuery,
    filterYear,
    filterStatus,
    // 計算屬性
    dashboardStats,
    riskStudents,
    difficultCourses,
    filteredStudents,
    // 方法
    adminLogin,
    adminLogout,
    getStudentDetail,
    updateStudentNotes,
    updateStudentStatus,
    exportStudentsAsCSV,
  }
})
