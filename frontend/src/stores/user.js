import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import Cookies from 'js-cookie'
import axios from 'axios'

export const useUserStore = defineStore('user', () => {
  // 状态
  const user = ref(null)
  const token = ref(Cookies.get('token') || null)
  
  // 计算属性
  const isLoggedIn = computed(() => !!token.value)
  
  // API 基础 URL
  const API_URL = 'http://127.0.0.1:5000/api'
  
  // 配置 axios 默认 header
  function setupAxios() {
    if (token.value) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
    } else {
      delete axios.defaults.headers.common['Authorization']
    }
  }
  
  // 初始化时检查 token
  async function checkAuth() {
    if (token.value) {
      try {
        setupAxios()
        const response = await axios.get(`${API_URL}/auth/me`)
        user.value = response.data
        return true
      } catch (error) {
        console.error('Token 验证失败:', error)
        logout()
        return false
      }
    }
    return false
  }
  
  // 登录
  async function login(username, password) {
    try {
      const response = await axios.post(`${API_URL}/auth/login`, {
        username,
        password
      })
      
      const { user: userData, token: authToken } = response.data
      
      user.value = userData
      token.value = authToken
      
      // 保存 token 到 cookie（7 天有效期）
      Cookies.set('token', authToken, { expires: 7 })
      
      setupAxios()
      
      return { success: true }
    } catch (error) {
      const errorMsg = error.response?.data?.error || '登录失败'
      return { success: false, error: errorMsg }
    }
  }
  
  // 注册
  async function register(username, password, email) {
    try {
      const response = await axios.post(`${API_URL}/auth/register`, {
        username,
        password,
        email
      })
      
      const { user: userData, token: authToken } = response.data
      
      user.value = userData
      token.value = authToken
      
      Cookies.set('token', authToken, { expires: 7 })
      
      setupAxios()
      
      return { success: true }
    } catch (error) {
      const errorMsg = error.response?.data?.error || '注册失败'
      return { success: false, error: errorMsg }
    }
  }
  
  // 登出
  function logout() {
    user.value = null
    token.value = null
    Cookies.remove('token')
    delete axios.defaults.headers.common['Authorization']
  }
  
  // 初始化
  setupAxios()
  
  return {
    user,
    token,
    isLoggedIn,
    login,
    register,
    logout,
    checkAuth
  }
})