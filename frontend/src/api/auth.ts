import http from './http'
import { USE_MOCK, mockLogin, mockRegister, mockStatus, mockLogout } from './mock'
import type {
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  RegisterResponse,
  StatusResponse,
} from './types'

interface ApiTokenResponse {
  access_token: string
  token_type: string
  role: 'student' | 'admin'
}

interface ApiAccountInfo {
  id: string
  email: string
  role: 'student' | 'admin'
  student_number?: string | null
  name?: string | null
  admission_year?: number | null
  administrator_id?: string | null
  department_id?: string | null
  department_name?: string | null
}

export function login(body: LoginRequest): Promise<LoginResponse> {
  if (USE_MOCK) return mockLogin(body)
  return http
    .post<ApiTokenResponse>('/api/auth/login', {
      email: body.email,
      password: body.password,
    })
    .then((r) => ({
      access_token: r.data.access_token,
      token_type: r.data.token_type,
      account: body.email,
      role: r.data.role,
      user_id: '',
    }))
}

export function register(body: RegisterRequest): Promise<RegisterResponse> {
  if (USE_MOCK) return mockRegister(body)
  const endpoint =
    body.role === 'admin' ? '/api/auth/register/admin' : '/api/auth/register/student'
  const payload =
    body.role === 'admin'
      ? {
          email: body.email,
          password: body.password,
          department_id: body.administrator?.department_id,
        }
      : {
          email: body.email,
          password: body.password,
          student_id: body.student?.student_id,
          name: body.student?.name || undefined,
          admission_year: body.student?.admission_year,
        }

  return http
    .post<ApiAccountInfo>(endpoint, payload)
    .then((r) => ({
      user_id: r.data.id,
      account: r.data.email,
      role: r.data.role,
    }))
}

export function logout() {
  if (USE_MOCK) return mockLogout()
  return http.post('/api/auth/logout').then((r) => r.data)
}

export function status(): Promise<StatusResponse> {
  if (USE_MOCK) return mockStatus()
  return http.get<ApiAccountInfo>('/api/auth/status').then((r) => ({
    user_id: r.data.id,
    account: r.data.email,
    role: r.data.role,
    student_number: r.data.student_number ?? null,
    name: r.data.name ?? null,
    admission_year: r.data.admission_year ?? null,
    administrator_id: r.data.administrator_id ?? null,
    department_id: r.data.department_id ?? null,
    department_name: r.data.department_name ?? null,
  } satisfies StatusResponse))
}
