/** Axios 实例 — 统一 baseURL + token 注入 + 401 拦截。 */
import axios, { AxiosError, type AxiosInstance } from 'axios'
import { useAuthStore } from '@/stores/auth'

const http: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 60_000,
})

// 请求拦截器：注入 Bearer token
http.interceptors.request.use((config) => {
  const store = useAuthStore()
  if (store.token) {
    config.headers.Authorization = `Bearer ${store.token}`
  }
  return config
})

// 响应拦截器：401 → 清理 token + 跳登录
http.interceptors.response.use(
  (r) => r,
  (err: AxiosError) => {
    if (err.response?.status === 401) {
      const store = useAuthStore()
      store.logout()
      // 只有不在 /login 时才跳转
      if (!location.pathname.startsWith('/login')) {
        location.href = '/login'
      }
    }
    return Promise.reject(err)
  },
)

export default http
