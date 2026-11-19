import { defineStore } from 'pinia'
import type { MeOut, UserMe } from '~/types/api'

export const useAuth = defineStore('auth', () => {
  const user = ref<UserMe | null>(null)
  const loaded = ref(false)

  const isExpert = computed(() => user.value?.role === 'expert' || user.value?.role === 'admin')
  const isAdmin = computed(() => user.value?.role === 'admin')

  async function fetchMe() {
    try {
      // на ssr прокидываем куки
      const fetcher = import.meta.server ? useRequestFetch() : $fetch
      const me = await fetcher<MeOut>('/api/auth/me')
      user.value = me.user
    }
    catch {
      user.value = null
    }
    finally {
      loaded.value = true
    }
  }

  async function login(email: string, password: string) {
    user.value = await api<UserMe>('/api/auth/login', {
      method: 'POST',
      body: { email, password, anon_id: getAnonId() },
      silent: true,
    })
  }

  async function register(name: string, email: string, password: string) {
    user.value = await api<UserMe>('/api/auth/register', {
      method: 'POST',
      body: { name, email, password, anon_id: getAnonId() },
      silent: true,
    })
  }

  async function logout() {
    await api('/api/auth/logout', { method: 'POST' })
    user.value = null
  }

  return { user, loaded, isExpert, isAdmin, fetchMe, login, register, logout }
})
