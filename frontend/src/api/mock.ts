// 離線示範用的 mock 資料與假 API。
// 由環境變數 VITE_USE_MOCK 控制（見 .env.development）。開啟時所有 auth/check
// 請求都改回傳本檔的假資料，不需啟動後端即可走完整學生端流程。

import type {
  CheckResult,
  Department,
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  RegisterResponse,
  Role,
  StatusResponse,
  UploadResponse,
} from './types'

export const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

function delay<T>(value: T, ms = 350): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms))
}

type MockUser = {
  user_id: string
  account: string
  password: string
  role: Role
  student_id?: string | null
  student_number?: string | null
  name?: string | null
  admission_year?: number | null
  administrator_id?: string | null
  department_id?: string | null
  department_name?: string | null
}

const departments = new Map<string, string>([
  ['703', '資訊科學系'],
  ['306', '資訊管理學系'],
  ['304', '統計學系'],
  ['2S3', '教務處通識教育中心'],
])

const mockUsers = new Map<string, MockUser>([
  [
    '112703043@example.com',
    {
      user_id: 'mock-student-account-id',
      account: '112703043@example.com',
      password: 'password123',
      role: 'student',
      student_id: '112703043',
      student_number: '112703043',
      name: '彭啟則',
      admission_year: 112,
    },
  ],
  [
    'admin@example.com',
    {
      user_id: 'mock-admin-account-id',
      account: 'admin@example.com',
      password: '12345678',
      role: 'admin',
      administrator_id: 'mock-admin-account-id',
      department_id: '703',
      department_name: '資訊科學系',
      name: '系辦管理員',
    },
  ],
])

let nextUserId = 3
const MOCK_ACCOUNT_KEY = 'gradcheck_mock_account'

function readMockAccount() {
  if (typeof localStorage === 'undefined') return '112703043@example.com'
  return localStorage.getItem(MOCK_ACCOUNT_KEY) || '112703043@example.com'
}

let currentAccount = readMockAccount()

export const mockCheckResult: CheckResult = {
  student: {
    id: '112703043',
    student_number: '112703043',
    chinese_name: '彭啟則',
    entry_year: 112,
    register_major: '資訊科學系',
    register_double_major: '資訊管理學系',
    minor1: '統計學系',
    minor2: null,
    graduation_credit: 128,
    total_credits: 102,
  },
  major_check: {
    dept_name: '資訊科學系',
    found: true,
    total_credits_required: 36,
    earned_credits: 27,
    in_progress_credits: 3,
    missing_credits: 6,
    status: 'incomplete',
    passed_courses: [
      { course_name: '計算機概論', course_code: 'CS101', credits: 3, score: '透過', match_confidence: 'exact' },
      { course_name: '程式設計（一）', course_code: 'CS102', credits: 3, score: '95', match_confidence: 'exact' },
      { course_name: '資料結構', course_code: 'CS201', credits: 3, score: '88', match_confidence: 'exact' },
      { course_name: '離散數學', course_code: 'CS210', credits: 3, score: '76', match_confidence: 'exact' },
      { course_name: '數位邏輯設計', course_code: 'CS220', credits: 3, score: '透過', match_confidence: 'normalized' },
      { course_name: '機率論', course_code: 'CS231', credits: 3, score: '82', group_label: '群A', match_confidence: 'exact' },
      { course_name: '線性代數', course_code: 'CS232', credits: 3, score: '90', group_label: '群A', match_confidence: 'exact' },
      { course_name: '計算機組織', course_code: 'CS240', credits: 3, score: '70', group_label: '群B', match_confidence: 'fuzzy' },
      { course_name: '物件導向程式設計', course_code: 'CS250', credits: 3, score: '85', match_confidence: 'exact' },
    ],
    in_progress_courses: [
      { course_name: '演演算法', course_code: 'CS301', credits: 3, score: null, group_label: '群B', match_confidence: 'exact' },
    ],
    missing_courses: [
      { course_name: '作業系統', course_code: 'CS310', credits: 3, course_type: '必修', match_confidence: 'none' },
      { course_name: '計算機網路', course_code: 'CS320', credits: 3, course_type: '必修', match_confidence: 'none' },
    ],
    group_violations: [
      {
        group: '群B',
        min_courses: 2,
        passed_courses: 1,
        in_progress_courses: 1,
        note: '群B（系統類）至少需透過 2 門',
        status: 'incomplete',
      },
    ],
  },
  double_major_check: {
    dept_name: '資訊管理學系',
    type: 'double_major',
    found: true,
    total_credits_required: 40,
    earned_credits: 12,
    in_progress_credits: 0,
    missing_credits: 28,
    status: 'incomplete',
    group_checks: [
      { group: '管理核心', credits_required: 12, earned_credits: 6, missing_credits: 6, status: 'incomplete' },
      { group: '資管應用', credits_required: 12, earned_credits: 6, missing_credits: 6, status: 'incomplete' },
    ],
    passed_courses: [
      { course_name: '管理學', course_code: 'MIS101', credits: 3, score: '80', group_label: '管理核心', match_confidence: 'exact' },
      { course_name: '會計學', course_code: 'MIS110', credits: 3, score: '78', group_label: '管理核心', match_confidence: 'exact' },
      { course_name: '資料庫管理', course_code: 'MIS220', credits: 3, score: '92', group_label: '資管應用', match_confidence: 'exact' },
      { course_name: '系統分析與設計', course_code: 'MIS230', credits: 3, score: '透過', group_label: '資管應用', match_confidence: 'normalized' },
    ],
    in_progress_courses: [],
    missing_courses: [
      { course_name: '生產與作業管理', course_code: 'MIS240', credits: 3, course_type: '必修', group_label: '管理核心', match_confidence: 'none' },
      { course_name: '電子商務', course_code: 'MIS320', credits: 3, course_type: '必修', group_label: '資管應用', match_confidence: 'none' },
    ],
  },
  minor_checks: [
    {
      dept_name: '統計學系',
      found: true,
      total_credits_required: 20,
      earned_credits: 6,
      in_progress_credits: 0,
      missing_credits: 14,
      status: 'incomplete',
      passed_courses: [
        { course_name: '統計學（一）', course_code: 'STAT101', credits: 3, score: '85', match_confidence: 'exact' },
        { course_name: '統計學（二）', course_code: 'STAT102', credits: 3, score: '83', match_confidence: 'exact' },
      ],
      in_progress_courses: [],
      missing_courses: [
        { course_name: '迴歸分析', course_code: 'STAT201', credits: 3, course_type: '必修', match_confidence: 'none' },
        { course_name: '抽樣方法', course_code: 'STAT210', credits: 3, course_type: '選修', match_confidence: 'none' },
      ],
    },
  ],
  ge_check: {
    status: 'incomplete',
    categories: [
      {
        category_name: '語文通識',
        remark_code: 'LA',
        credits_required: 6,
        earned_credits: 6,
        missing_credits: 0,
        status: 'complete',
        courses: [
          { course_name: '大學國文', course_code: 'GE101', credits: 3, score: '88' },
          { course_name: '大學英文', course_code: 'GE102', credits: 3, score: '90' },
        ],
      },
      {
        category_name: '藝術與美學',
        remark_code: 'AE',
        credits_required: 4,
        earned_credits: 2,
        missing_credits: 2,
        status: 'incomplete',
        courses: [{ course_name: '音樂與生活', course_code: 'GE210', credits: 2, score: '透過' }],
      },
      {
        category_name: '社會科學',
        remark_code: 'SS',
        credits_required: 6,
        earned_credits: 3,
        missing_credits: 3,
        status: 'incomplete',
        courses: [{ course_name: '經濟學原理', course_code: 'GE320', credits: 3, score: '79' }],
      },
      {
        category_name: '自然科學',
        remark_code: 'NS',
        credits_required: 4,
        earned_credits: 0,
        missing_credits: 4,
        status: 'incomplete',
        courses: [],
      },
    ],
  },
  pe_check: {
    required_semesters: 4,
    passed_semesters: 3,
    missing_semesters: 1,
    status: 'incomplete',
    passed_courses: [
      { course_name: '體育（一）羽球', course_code: 'PE101', academic_year_semester: '1121', score: '透過' },
      { course_name: '體育（二）桌球', course_code: 'PE102', academic_year_semester: '1122', score: '透過' },
      { course_name: '體育（三）籃球', course_code: 'PE201', academic_year_semester: '1131', score: '透過' },
    ],
    in_progress_courses: [],
    failed_courses: [],
  },
  summary: {
    all_complete: false,
    incomplete_items: ['主系必修', '雙主修', '輔系 統計學系', '通識', '體育必修'],
    elective_credits: {
      graduation_total: 128,
      major_required: 36,
      ge_required: 28,
      pe_required: 4,
      elective_required: 60,
      total_credits_earned: 102,
      major_earned: 27,
      ge_earned: 13,
      pe_earned: 3,
      elective_earned: 59,
      elective_gap: 1,
      note: '選修應修 = 128 - 主系36 - 通識28 - 體育4 = 60 學分',
    },
  },
}

export function mockLogin(body: LoginRequest): Promise<LoginResponse> {
  const user = mockUsers.get(body.email)
  if (!user || user.password !== body.password) {
    return Promise.reject(new Error('電子信箱或密碼錯誤'))
  }
  currentAccount = user.account
  if (typeof localStorage !== 'undefined') {
    localStorage.setItem(MOCK_ACCOUNT_KEY, user.account)
  }
  return delay({
    access_token: `mock-token-${user.role}-${user.user_id}`,
    token_type: 'bearer',
    account: user.account,
    role: user.role,
    user_id: user.user_id,
  })
}

export function mockRegister(body: RegisterRequest): Promise<RegisterResponse> {
  if (mockUsers.has(body.email)) {
    return Promise.reject(new Error('電子信箱已存在'))
  }
  if (body.password.length < 8) {
    return Promise.reject(new Error('密碼至少需 8 碼'))
  }

  const base = {
    user_id: `mock-account-${nextUserId++}`,
    account: body.email,
    password: body.password,
    role: body.role,
  }

  if (body.role === 'student') {
    const student = body.student
    if (!student?.student_id || !student.name || !student.admission_year) {
      return Promise.reject(new Error('請完整填寫學生資料'))
    }
    if (!/^\d{9}$/.test(student.student_id)) {
      return Promise.reject(new Error('學生學號需為 9 碼數字'))
    }
    if (!Number.isInteger(student.admission_year)) {
      return Promise.reject(new Error('請輸入有效的入學年度'))
    }

    mockUsers.set(body.email, {
      ...base,
      role: 'student',
      student_id: null,
      student_number: student.student_id,
      name: student.name,
      admission_year: student.admission_year,
    })
    return delay({
      user_id: base.user_id,
      account: body.email,
      role: 'student',
      student_number: student.student_id,
    })
  }

  const administrator = body.administrator
  if (!administrator?.department_id || !departments.has(administrator.department_id)) {
    return Promise.reject(new Error('請選擇有效的管理單位'))
  }

  mockUsers.set(body.email, {
    ...base,
    role: 'admin',
    administrator_id: base.user_id,
    department_id: administrator.department_id,
    department_name: departments.get(administrator.department_id) ?? null,
    name: body.email,
  })
  return delay({
    user_id: base.user_id,
    account: body.email,
    role: 'admin',
    administrator_id: base.user_id,
    department_id: administrator.department_id,
  })
}

export function mockStatus(): Promise<StatusResponse> {
  const user = mockUsers.get(currentAccount) ?? mockUsers.get('112703043@example.com')!
  return delay({
    user_id: user.user_id,
    account: user.account,
    role: user.role,
    student_id: user.student_id ?? null,
    student_number: user.student_number ?? null,
    name: user.name ?? null,
    admission_year: user.admission_year ?? null,
    administrator_id: user.administrator_id ?? null,
    department_id: user.department_id ?? null,
    department_name: user.department_name ?? null,
  })
}

export function mockLogout(): Promise<{ message: string }> {
  if (typeof localStorage !== 'undefined') {
    localStorage.removeItem(MOCK_ACCOUNT_KEY)
  }
  currentAccount = '112703043@example.com'
  return delay({ message: 'Successfully logged out' })
}

export function mockGetCheck(): Promise<CheckResult> {
  return delay(mockCheckResult)
}

export function mockListDepartments(): Promise<Department[]> {
  return delay(Array.from(departments, ([id, name]) => ({ id, name, college: '' })))
}

export function mockUpload(): Promise<UploadResponse> {
  return delay({
    student_id: '112703043',
    student_number: '112703043',
    chinese_name: '彭啟則',
    course_count: 48,
  })
}
