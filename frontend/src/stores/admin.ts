import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// ==================== 类型定义 ====================
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
  status: 'on_track' | 'at_risk' // 是否达标
  double_major?: boolean // 是否双主修
  exchange_student?: boolean // 是否交换生
  total_credits: number
  required_credits: number
  completed_courses: number
  notes?: string // 管理员备注
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

// ==================== Mock 数据 ====================
const mockStudents: Student[] = [
  {
    student_id: 'S001',
    name: '林子晴',
    admission_year: 2021,
    status: 'on_track',
    double_major: true,
    exchange_student: false,
    total_credits: 120,
    required_credits: 120,
    completed_courses: 42,
    notes: '双主修资工系，进度超前',
    courses: [
      {
        course_id: 'CS101',
        course_name: '数位系统',
        year: 2024,
        semester: 1,
        credits: 3,
        grade: 80,
        is_passed: true,
        category: 'departmentCore',
      },
      {
        course_id: 'CS102',
        course_name: '离散数学',
        year: 2024,
        semester: 1,
        credits: 3,
        grade: 85,
        is_passed: true,
        category: 'departmentCore',
      },
      {
        course_id: 'CS103',
        course_name: '数据结构',
        year: 2024,
        semester: 2,
        credits: 3,
        grade: 92,
        is_passed: true,
        category: 'departmentCore',
      },
    ],
  },
  {
    student_id: 'S002',
    name: '王浩宇',
    admission_year: 2022,
    status: 'at_risk',
    double_major: false,
    exchange_student: false,
    total_credits: 45,
    required_credits: 90,
    completed_courses: 15,
    notes: '二年级学分落后，建议加强指导',
    courses: [
      {
        course_id: 'CORE201',
        course_name: '线性代数',
        year: 2024,
        semester: 1,
        credits: 3,
        grade: 68,
        is_passed: true,
        category: 'departmentCore',
      },
      {
        course_id: 'CORE202',
        course_name: '微积分',
        year: 2024,
        semester: 1,
        credits: 3,
        grade: 52,
        is_passed: false,
        category: 'departmentCore',
      },
      {
        course_id: 'GEN101',
        course_name: '大一英文',
        year: 2023,
        semester: 1,
        credits: 2,
        grade: 75,
        is_passed: true,
        category: 'general',
      },
    ],
  },
  {
    student_id: 'S003',
    name: '陈思语',
    admission_year: 2021,
    status: 'on_track',
    double_major: false,
    exchange_student: true,
    total_credits: 115,
    required_credits: 120,
    completed_courses: 38,
    notes: '预审通过，赴日本交换一年',
    courses: [
      {
        course_id: 'CS301',
        course_name: '算法设计',
        year: 2024,
        semester: 1,
        credits: 3,
        grade: 88,
        is_passed: true,
        category: 'departmentCore',
      },
      {
        course_id: 'CS302',
        course_name: '数据库系统',
        year: 2024,
        semester: 2,
        credits: 3,
        grade: 90,
        is_passed: true,
        category: 'elective',
      },
    ],
  },
  {
    student_id: 'S004',
    name: '许家豪',
    admission_year: 2022,
    status: 'at_risk',
    double_major: false,
    exchange_student: false,
    total_credits: 52,
    required_credits: 90,
    completed_courses: 18,
    notes: '必修多次挂科，需要学业辅导',
    courses: [
      {
        course_id: 'CORE203',
        course_name: '程式设计',
        year: 2023,
        semester: 1,
        credits: 3,
        grade: 45,
        is_passed: false,
        category: 'departmentCore',
      },
      {
        course_id: 'CORE204',
        course_name: '计算机组织',
        year: 2024,
        semester: 1,
        credits: 3,
        grade: 60,
        is_passed: true,
        category: 'departmentCore',
      },
    ],
  },
  {
    student_id: 'S005',
    name: '黄诗涵',
    admission_year: 2021,
    status: 'on_track',
    double_major: false,
    exchange_student: false,
    total_credits: 128,
    required_credits: 120,
    completed_courses: 45,
    notes: '大四学生，准备办理离校',
    courses: [
      {
        course_id: 'CS401',
        course_name: '专题研讨',
        year: 2024,
        semester: 2,
        credits: 3,
        grade: 95,
        is_passed: true,
        category: 'elective',
      },
      {
        course_id: 'CS402',
        course_name: '人工智能',
        year: 2024,
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
  // ===== 状态 =====
  const admin = ref<AdminUser | null>(null)
  const students = ref<Student[]>(mockStudents)
  const currentStudent = ref<Student | null>(null)
  const searchQuery = ref('')
  const filterYear = ref<number | null>(null)
  const filterStatus = ref<'all' | 'on_track' | 'at_risk'>('all')

  // ===== 计算属性 =====
  // 获取仪表板统计数据
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

  // 高风险学生列表（学分落后超过50%）
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

  // 魔王课程（未通过率最高的课程前三名）
  const difficultCourses = computed(() => {
    const courseStats = new Map<string, { name: string; total: number; failed: number }>()

    // 统计所有课程的通过情况
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

    // 计算未通过率并排序
    return Array.from(courseStats.values())
      .map((s) => ({
        ...s,
        failRate: Math.round((s.failed / s.total) * 100),
      }))
      .sort((a, b) => b.failRate - a.failRate)
      .slice(0, 3)
  })

  // 过滤后的学生列表
  const filteredStudents = computed(() => {
    let filtered = [...students.value]

    // 按搜索词过滤
    if (searchQuery.value) {
      const query = searchQuery.value.toLowerCase()
      filtered = filtered.filter(
        (s) => s.name.toLowerCase().includes(query) || s.student_id.toLowerCase().includes(query)
      )
    }

    // 按年级过滤
    if (filterYear.value) {
      filtered = filtered.filter((s) => s.admission_year === filterYear.value)
    }

    // 按状态过滤
    if (filterStatus.value !== 'all') {
      filtered = filtered.filter((s) => s.status === filterStatus.value)
    }

    return filtered
  })

  // ===== 操作方法 =====
  // 管理员登入（模拟）
  function adminLogin(account: string, password: string) {
    // 模拟登入逻辑
    if (account && password) {
      admin.value = {
        admin_id: 'ADMIN001',
        name: '李老师',
        department: '资讯工程系',
      }
      return true
    }
    return false
  }

  // 管理员登出
  function adminLogout() {
    admin.value = null
    currentStudent.value = null
  }

  // 获取学生详情
  function getStudentDetail(studentId: string) {
    const student = students.value.find((s) => s.student_id === studentId)
    if (student) {
      currentStudent.value = student
    }
    return student
  }

  // 更新学生备注
  function updateStudentNotes(studentId: string, notes: string) {
    const student = students.value.find((s) => s.student_id === studentId)
    if (student) {
      student.notes = notes
      if (currentStudent.value && currentStudent.value.student_id === studentId) {
        currentStudent.value.notes = notes
      }
    }
  }

  // 更新学生状态
  function updateStudentStatus(studentId: string, status: 'on_track' | 'at_risk') {
    const student = students.value.find((s) => s.student_id === studentId)
    if (student) {
      student.status = status
      if (currentStudent.value && currentStudent.value.student_id === studentId) {
        currentStudent.value.status = status
      }
    }
  }

  // 导出学生列表为 CSV 格式
  function exportStudentsAsCSV() {
    const header = ['学号', '姓名', '入学年度', '状态', '总学分', '必需学分', '已完成课程数']
    const rows = filteredStudents.value.map((s) => [
      s.student_id,
      s.name,
      s.admission_year,
      s.status === 'on_track' ? '已达标' : '未达标',
      s.total_credits,
      s.required_credits,
      s.completed_courses,
    ])

    const csv = [header, ...rows].map((row) => row.join(',')).join('\n')

    // 创建下载链接
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', `学生列表_${new Date().getTime()}.csv`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  return {
    // 状态
    admin,
    students,
    currentStudent,
    searchQuery,
    filterYear,
    filterStatus,
    // 计算属性
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
