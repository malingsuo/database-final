import http from './http'
import { USE_MOCK } from './mock'
import type { Department } from './types'

export function listDepartments() {
  if (USE_MOCK) {
    return import('./mock').then((m) => m.mockListDepartments())
  }
  return http.get<Department[]>('/api/public/departments').then((r) => r.data)
}
