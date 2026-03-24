
<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { LogIn, Mail, Lock, Eye, EyeOff } from 'lucide-vue-next'

const router = useRouter()
const userStore = useUserStore()

const loading = ref(false)
const error = ref('')
const showPassword = ref(false)

const loginForm = ref({
  username: '',
  password: ''
})

async function handleLogin() {
  if (!loginForm.value.username || !loginForm.value.password) {
    error.value = '请输入用户名和密码'
    return
  }
  
  loading.value = true
  error.value = ''
  
  const result = await userStore.login(loginForm.value.username, loginForm.value.password)
  
  loading.value = false
  
  if (result.success) {
    router.push('/')
  } else {
    error.value = result.error
  }
}

function goToRegister() {
  router.push('/register')
}
</script>

<template>
  <div class="auth-container">
    <div class="auth-card">
      <div class="auth-header">
        <LogIn :size="48" color="#5E72E4" />
        <h1>欢迎回来</h1>
        <p>登录你的智能日程账户</p>
      </div>
      
      <form @submit.prevent="handleLogin" class="auth-form">
        <div v-if="error" class="error-message">
          {{ error }}
        </div>
        
        <div class="form-group">
          <label for="username">
            <Mail :size="18" />
            用户名
          </label>
          <input
            id="username"
            v-model="loginForm.username"
            type="text"
            placeholder="请输入用户名"
            :disabled="loading"
            required
          />
        </div>
        
        <div class="form-group">
          <label for="password">
            <Lock :size="18" />
            密码
          </label>
          <div class="password-input">
            <input
              id="password"
              v-model="loginForm.password"
              :type="showPassword ? 'text' : 'password'"
              placeholder="请输入密码"
              :disabled="loading"
              required
            />
            <button
              type="button"
              class="password-toggle"
              @click="showPassword = !showPassword"
              tabindex="-1"
            >
              <EyeOff v-if="showPassword" :size="20" />
              <Eye v-else :size="20" />
            </button>
          </div>
        </div>
        
        <button type="submit" class="submit-btn" :disabled="loading">
          <LogIn :size="20" />
          {{ loading ? '登录中...' : '登录' }}
        </button>
      </form>
      
      <div class="auth-footer">
        <p>还没有账户？<router-link to="/register">立即注册</router-link></p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 2rem;
}

.auth-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  padding: 3rem;
  width: 100%;
  max-width: 420px;
  animation: slideUp 0.5s ease-out;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.auth-header {
  text-align: center;
  margin-bottom: 2rem;
}

.auth-header h1 {
  color: #32325D;
  margin: 1rem 0 0.5rem;
  font-size: 1.8rem;
}

.auth-header p {
  color: #8898aa;
  margin: 0;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
  color: #525F7F;
}

.form-group input {
  padding: 0.875rem 1rem;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  font-size: 1rem;
  transition: all 0.3s;
}

.form-group input:focus {
  outline: none;
  border-color: #5E72E4;
  box-shadow: 0 0 0 3px rgba(94, 114, 228, 0.1);
}

.form-group input:disabled {
  background-color: #f4f5f7;
  cursor: not-allowed;
}

.password-input {
  position: relative;
  display: flex;
  align-items: center;
}

.password-input input {
  width: 100%;
  padding-right: 3rem;
}

.password-toggle {
  position: absolute;
  right: 1rem;
  background: none;
  border: none;
  cursor: pointer;
  color: #8898aa;
  display: flex;
  align-items: center;
  padding: 0;
}

.password-toggle:hover {
  color: #5E72E4;
}

.submit-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  background-color: #5E72E4;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 1rem;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.submit-btn:hover:not(:disabled) {
  background-color: #4c5fd5;
  transform: translateY(-2px);
  box-shadow: 0 7px 14px rgba(94, 114, 228, 0.3);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-message {
  background-color: #fdd;
  color: #c00;
  padding: 0.875rem;
  border-radius: 8px;
  font-size: 0.9rem;
  text-align: center;
}

.auth-footer {
  margin-top: 2rem;
  text-align: center;
  color: #8898aa;
}

.auth-footer a {
  color: #5E72E4;
  text-decoration: none;
  font-weight: 600;
}

.auth-footer a:hover {
  text-decoration: underline;
}
</style>