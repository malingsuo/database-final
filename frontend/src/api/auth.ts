import http from './http'
import { USE_MOCK, mockLogin, mockRegister, mockStatus, mockLogout } from './mock'
import type {
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  RegisterResponse,
  StatusResponse,
} from './types'

export function login(body: LoginRequest) {
  if (USE_MOCK) return mockLogin(body)
  return http.post<LoginResponse>('/api/auth/login', body).then((r) => r.data)
}

export function register(body: RegisterRequest) {
  if (USE_MOCK) return mockRegister(body)
  return http.post<RegisterResponse>('/api/auth/register', body).then((r) => r.data)
}

export function logout() {
  if (USE_MOCK) return mockLogout()
  return http.post('/api/auth/logout').then((r) => r.data)
}

export function status() {
  if (USE_MOCK) return mockStatus()
  return http.get<StatusResponse>('/api/auth/status').then((r) => r.data)
}
