import axios, { type AxiosInstance } from 'axios'

export const TOKEN_KEY = 'gradcheck_token'

// baseURL 預設空字串：dev 走 vite proxy（/api → nginx），prod 在 nginx 後同源直連。
const http: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE ?? '',
})

http.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 統一錯誤訊息：後端錯誤格式為 { detail: "..." }
export class ApiError extends Error {
  status?: number
  constructor(message: string, status?: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

let onUnauthorized: (() => void) | null = null
export function setUnauthorizedHandler(fn: () => void) {
  onUnauthorized = fn
}

http.interceptors.response.use(
  (response) => response,
  (error) => {
    const status: number | undefined = error.response?.status
    if (status === 401) {
      localStorage.removeItem(TOKEN_KEY)
      onUnauthorized?.()
    }
    const detail = error.response?.data?.detail
    const message =
      (typeof detail === 'string' && detail) ||
      error.message ||
      '發生未知錯誤，請稍後再試。'
    return Promise.reject(new ApiError(message, status))
  },
)

export default http
