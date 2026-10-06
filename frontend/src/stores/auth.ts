import { defineStore } from 'pinia'
import { ref } from 'vue'
import { authApi } from '@/api/auth'
import type { User } from '@/types'

const LS_TOKEN = 'pkb_token'
const LS_USER = 'pkb_user'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(localStorage.getItem(LS_TOKEN) || '')
  const user = ref<User | null>(null)

  async function login(username: string, password: string): Promise<boolean> {
    const res = await authApi.login({ username, password })
    token.value = res.data.access_token
    localStorage.setItem(LS_TOKEN, token.value)
    try {
      const me = await authApi.me()
      user.value = me.data
      localStorage.setItem(LS_USER, JSON.stringify(user.value))
    } catch {
      // ignore — 下次刷新时再取
    }
    return true
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem(LS_TOKEN)
    localStorage.removeItem(LS_USER)
  }

  return { token, user, login, logout }
})
