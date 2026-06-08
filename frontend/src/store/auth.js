import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const useAuthStore = defineStore('auth', () => {
  // Initialize from localStorage if available
  const storedUser = localStorage.getItem('user')
  const user = ref(storedUser ? JSON.parse(storedUser) : null)
  const token = ref(localStorage.getItem('access_token') || null)
  const loading = ref(false)
  const error = ref(null)

  const isAuthenticated = computed(() => !!token.value && !!user.value)

  const setUser = (newUser) => {
    user.value = newUser
    if (newUser) {
      localStorage.setItem('user', JSON.stringify(newUser))
    } else {
      localStorage.removeItem('user')
    }
  }

  const setToken = (newToken) => {
    token.value = newToken
    if (newToken) {
      localStorage.setItem('access_token', newToken)
    } else {
      localStorage.removeItem('access_token')
    }
  }

  const register = async (username, email, password, fullName) => {
    loading.value = true
    error.value = null

    try {
      const response = await api.post('/auth/register', {
        username,
        email,
        password,
        full_name: fullName,
      })

      setUser(response.data)
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Erro ao registrar'
      return false
    } finally {
      loading.value = false
    }
  }

  const login = async (username, password) => {
    loading.value = true
    error.value = null

    try {
      const response = await api.post('/auth/login', {
        username,
        password,
      })

      setToken(response.data.access_token)
      setUser(response.data.user)
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Erro ao fazer login'
      return false
    } finally {
      loading.value = false
    }
  }

  const getCurrentUser = async () => {
    if (!token.value) return false

    loading.value = true
    error.value = null

    try {
      const response = await api.get('/auth/me')
      setUser(response.data)
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Erro ao obter usuário'
      logout()
      return false
    } finally {
      loading.value = false
    }
  }

  const logout = async () => {
    try {
      await api.post('/auth/logout')
    } catch (err) {
      console.error('Erro ao fazer logout:', err)
    } finally {
      setToken(null)
      setUser(null)
      error.value = null
    }
  }

  const changePassword = async (oldPassword, newPassword) => {
    loading.value = true
    error.value = null

    try {
      await api.post('/auth/change-password', null, {
        params: {
          old_password: oldPassword,
          new_password: newPassword,
        },
      })
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Erro ao alterar senha'
      return false
    } finally {
      loading.value = false
    }
  }

  return {
    user,
    token,
    loading,
    error,
    isAuthenticated,
    setUser,
    setToken,
    register,
    login,
    getCurrentUser,
    logout,
    changePassword,
  }
})
