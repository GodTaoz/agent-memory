import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('admin-token'))
  const isAuthenticated = computed(() => !!token.value)

  async function login(password: string): Promise<boolean> {
    try {
      const response = await axios.post('/admin/api/auth/login', { password })
      token.value = response.data.token
      localStorage.setItem('admin-token', response.data.token)
      
      // Set default authorization header
      axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.token}`
      
      return true
    } catch (error) {
      return false
    }
  }

  async function logout() {
    try {
      await axios.post('/admin/api/auth/logout')
    } catch (error) {
      // Ignore errors on logout
    } finally {
      token.value = null
      localStorage.removeItem('admin-token')
      delete axios.defaults.headers.common['Authorization']
    }
  }

  async function changePassword(oldPassword: string, newPassword: string): Promise<boolean> {
    try {
      await axios.post('/admin/api/auth/change-password', {
        old_password: oldPassword,
        new_password: newPassword,
      })
      return true
    } catch (error) {
      return false
    }
  }

  // Initialize authorization header if token exists
  if (token.value) {
    axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
  }

  return {
    token,
    isAuthenticated,
    login,
    logout,
    changePassword,
  }
})
