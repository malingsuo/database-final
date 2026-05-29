import http from './http'
import {
  USE_MOCK,
  mockAdminDashboard,
  mockAdminStudentDetail,
  mockListAdminStudents,
  mockUpdateAdminStudent,
} from './mock'
import type {
  AdminDashboardData,
  AdminStudentDetail,
  AdminStudentProfile,
} from './types'

export function getDashboard(): Promise<AdminDashboardData> {
  if (USE_MOCK) return mockAdminDashboard()
  return http.get<AdminDashboardData>('/api/admin/dashboard').then((r) => r.data)
}

export function listStudents(): Promise<AdminStudentProfile[]> {
  if (USE_MOCK) return mockListAdminStudents()
  return http.get<AdminStudentProfile[]>('/api/admin/students').then((r) => r.data)
}

export function getStudentDetail(sid: string): Promise<AdminStudentDetail> {
  if (USE_MOCK) return mockAdminStudentDetail(sid)
  return http.get<AdminStudentDetail>(`/api/admin/students/${sid}`).then((r) => r.data)
}

export function updateStudent(
  sid: string,
  body: { status?: 'on_track' | 'at_risk'; notes?: string },
): Promise<AdminStudentProfile> {
  if (USE_MOCK) return mockUpdateAdminStudent(sid, body)
  return http.patch<AdminStudentProfile>(`/api/admin/students/${sid}`, body).then((r) => r.data)
}
