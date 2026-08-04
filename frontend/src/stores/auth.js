import { defineStore } from 'pinia'
import { authApi } from '@/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: localStorage.getItem('access_token') || null,
  }),
  getters: {
    isLoggedIn: state => !!state.token,
  },
  actions: {
    async login(data) {
      const res = await authApi.login(data)
      this.token = res.access_token
      this.user = res.user
      localStorage.setItem('access_token', res.access_token)
      return res
    },
    async register(data) {
      const res = await authApi.register(data)
      this.token = res.access_token
      this.user = res.user
      localStorage.setItem('access_token', res.access_token)
      return res
    },
    async fetchMe() {
      if (!this.token) return
      try {
        this.user = await authApi.me()
      } catch {
        this.logout()
      }
    },
    logout() {
      this.token = null
      this.user = null
      localStorage.removeItem('access_token')
    },
  },
})
