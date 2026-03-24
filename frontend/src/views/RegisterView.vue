<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { UserPlus, Mail, Lock, Eye, EyeOff, AtSign } from 'lucide-vue-next'

const router = useRouter()
const userStore = useUserStore()

const loading = ref(false)
const error = ref('')
const showPassword = ref(false)
const showConfirmPassword = ref(false)

const registerForm = ref({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

async function handleRegister() {
  if (!registerForm.value.username || !registerForm.value.password) {
    error.value = '用户名和密码不能为空'
    return
  }
  
  if (registerForm.value.password !== registerForm.value.confirmPassword) {
    error.value = '两次输入的密码不一致'
    return
  }
  
  if (registerForm.value.password.length < 6) {
    error.value = '密码长度至少为 6 位'
    return
  }
  
  loading.value = true
  error.value = ''
  
  const result = await userStore.register(
    registerForm.value.username,
    registerForm.value.password,
    registerForm.value.email || undefined
  )
  
  loading.value = false
  
  if (result.success) {
    router.push('/')
  } else {
    error.value = result.error
  }
}

function goToLogin() {
  router.push('/login')
}
</script>

<template>
  <div class="auth-container">
    <div class="auth-card">
      <div class="auth-header">
        <UserPlus :size="48" color="#5E72E4" />
        <h1>创建账户</h1>
        <p>加入我们，开始管理你的日程</p>
      </div>
      
      <form @submit.prevent="handleRegister" class="auth-form">
        <div v-if="error" class="error-message">
          {{ error }}
        </div>
        
        <div class="form-group">
          <label for="username">
            <AtSign :size="18" />
            用户名 *
          </label>
          <input
            id="username"
            v-model="registerForm.username"
            type="text"
            placeholder="请输入用户名"
            :disabled="loading"
            required
          />
        </div>
        
        <div class="form-group">
          <label for="email">
            <Mail :size="18" />
            邮箱（可选）
          </label>
          <input
            id="email"
            v-model="registerForm.email"
            type="email"
            placeholder="请输入邮箱"
            :disabled="loading"
          />
        </div>
        
        <div class="form-group">
          <label for="password">
            <Lock :size="18" />
            密码 *
          </label>
          <div class="password-input">
            <input
              id="password"
              v-model="registerForm.password"
              :type="showPassword ? 'text' : 'password'"
              placeholder="请输入密码（至少 6 位）"
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
        
        <div class="form-group">
          <label for="confirmPassword">
            <Lock :size="18" />
            确认密码 *
          </label>
          <div class="password-input">
            <input
              id="confirmPassword"
              v-model="registerForm.confirmPassword"
              :type="showConfirmPassword ? 'text' : 'password'"
              placeholder="请再次输入密码"
              :disabled="loading"
              required
            />
            <button
              type="button"
              class="password-toggle"
              @click="showConfirmPassword = !showConfirmPassword"
              tabindex="-1"
            >
              <EyeOff v-if="showConfirmPassword" :size="20" />
              <Eye v-else :size="20" />
            </button>
          </div>
        </div>
        
        <button type="submit" class="submit-btn" :disabled="loading">
          <UserPlus :size="20" />
          {{ loading ? '注册中...' : '注册' }}
        </button>
      </form>
      
      <div class="auth-footer">
        <p>已有账户？<router-link to="/login">立即登录</router-link></p>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 样式与 LoginView.vue 相同 */
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