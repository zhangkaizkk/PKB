import http from './http'
import type { LoginRequest, TokenResponse, User } from '@/types'

export const authApi = {
  login(data: LoginRequest) {
    return http.post<TokenResponse>('/auth/login', data)
  },
  me() {
    return http.get<User>('/auth/me')
  },
}
