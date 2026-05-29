import http from './http'
import { USE_MOCK, mockGetCheck, mockUpload } from './mock'
import type { CheckResult, UploadResponse } from './types'

export function getCheck(studentId: number) {
  if (USE_MOCK) return mockGetCheck()
  return http.get<CheckResult>(`/api/check/${studentId}`).then((r) => r.data)
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
