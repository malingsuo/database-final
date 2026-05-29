// 與後端契約對齊的型別定義。
// 認證 API 依 docs/API_SPEC.md 使用 email/password；檢核部分以 backend/src/services/checker.py 實際輸出為準。

export type Role = 'student' | 'admin'

export type CheckStatus = 'complete' | 'incomplete' | 'dept_not_found' | 'no_data'

// ---------------- Auth ----------------

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  role: Role
  student?: {
    student_id: string
    name: string
    admission_year: number
  }
  administrator?: {
    department_id: string
  }
}

export interface LoginResponse {
  access_token: string
  token_type: string
  account: string
  role: Role
  user_id: string
}

export interface RegisterResponse {
  user_id: string
  account: string
  role: Role
  student_number?: string | null
  administrator_id?: string | null
  department_id?: string | null
}

export interface StatusResponse {
  user_id: string
  account: string
  role: Role
  student_id?: string | null
  student_number?: string | null
  name?: string | null
  admission_year?: number | null
  administrator_id?: string | null
  department_id?: string | null
  department_name?: string | null
}

// ---------------- Check / 課程 ----------------

export type MatchConfidence = 'exact' | 'normalized' | 'fuzzy' | 'none'

export interface CourseEntry {
  course_name: string
  course_code: string
  credits: number
  score?: string | null
  group_label?: string | null
  course_type?: string | null
  note?: string | null
  match_confidence?: MatchConfidence
}

export interface GroupViolation {
  group: string
  min_courses: number
  passed_courses: number
  in_progress_courses: number
  note: string
  status: string
}

export interface DeptCheck {
  dept_name: string
  found: boolean
  no_data?: boolean
  type?: string
  total_credits_required: number | null
  earned_credits: number
  in_progress_credits: number
  missing_credits: number | null
  passed_courses: CourseEntry[]
  in_progress_courses: CourseEntry[]
  missing_courses: CourseEntry[]
  group_violations?: GroupViolation[]
  group_checks?: DoubleMajorGroupCheck[]
  status: CheckStatus
  note?: string | null
}

export interface DoubleMajorGroupCheck {
  group: string
  credits_required: number
  earned_credits: number
  missing_credits: number
  status: 'complete' | 'incomplete'
}

export interface GeCategory {
  category_name: string
  remark_code: string
  credits_required: number
  earned_credits: number
  missing_credits: number
  courses: CourseEntry[]
  status: 'complete' | 'incomplete'
}

export interface GeCheck {
  categories: GeCategory[]
  status: 'complete' | 'incomplete'
}

export interface PeCourse {
  course_name: string
  course_code: string
  academic_year_semester: string
  score?: string | null
}

export interface PeCheck {
  required_semesters: number
  passed_semesters: number
  missing_semesters: number
  passed_courses: PeCourse[]
  in_progress_courses: PeCourse[]
  failed_courses: PeCourse[]
  status: 'complete' | 'incomplete'
}

export interface ElectiveCredits {
  graduation_total: number
  major_required: number
  ge_required: number
  pe_required: number
  elective_required: number
  total_credits_earned: number
  major_earned: number
  ge_earned: number
  pe_earned: number
  elective_earned: number
  elective_gap: number
  note: string
}

export interface CheckSummary {
  all_complete: boolean
  incomplete_items: string[]
  elective_credits: ElectiveCredits
}

export interface StudentInfo {
  id: string
  student_number: string
  chinese_name: string | null
  entry_year: number
  register_major: string | null
  register_double_major: string | null
  minor1: string | null
  minor2: string | null
  graduation_credit: number | null
  total_credits: number | null
}

export interface Department {
  id: string
  college: string
  name: string
}

export interface CheckResult {
  student: StudentInfo
  major_check: DeptCheck
  double_major_check: DeptCheck | null
  minor_checks: DeptCheck[]
  ge_check: GeCheck
  pe_check: PeCheck
  summary: CheckSummary
}

export interface UploadResponse {
  student_id: string
  student_number: string
  chinese_name: string | null
  course_count: number
}
