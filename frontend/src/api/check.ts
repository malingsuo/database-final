import http from './http'
import { USE_MOCK, mockGetCheck, mockUpload } from './mock'
import type { CheckResult, UploadResponse } from './types'

export function getCheck(studentId: number) {
  if (USE_MOCK) return mockGetCheck()
  return http.get<CheckResult>(`/api/check/${studentId}`).then((r) => r.data)
}

// 後端就緒後可提供 GET /api/check/me（用 X-User-ID 解析）。
// 目前 backend 未實作，呼叫端需對 404 做後備處理。
export function getMyCheck() {
  if (USE_MOCK) return mockGetCheck()
  return http.get<CheckResult>('/api/check/me').then((r) => r.data)
}

export function uploadStudentJson(file: File) {
  if (USE_MOCK) return mockUpload()
  const form = new FormData()
  form.append('file', file)
  return http
    .post<UploadResponse>('/api/check/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    .then((r) => r.data)
}
