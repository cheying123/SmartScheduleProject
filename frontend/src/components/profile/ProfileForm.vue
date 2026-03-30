<script setup>
import { MapPin, User, Mail, Bell } from 'lucide-vue-next'

const props = defineProps({
  profile: {
    type: Object,
    required: true
  },
  isLocating: {
    type: Boolean,
    default: false
  },
  locationStatus: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['submit', 'cancel', 'locate', 'update:profile'])
</script>

<template>
  <div class="profile-form-container">
    <div class="form-header">
      <h2>编辑个人资料</h2>
      <p class="form-description">更新您的个人信息和偏好设置</p>
    </div>
    
    <form @submit.prevent="$emit('submit')" class="profile-form">
      <!-- 用户名和邮箱并排 -->
      <div class="form-row">
        <div class="form-section half">
          <label for="username" class="field-label">
            <User :size="16" />
            <span>用户名</span>
            <span class="required">*</span>
          </label>
          <input 
            id="username" 
            type="text" 
            :value="profile.username"
            @input="$emit('update:profile', { ...profile, username: $event.target.value })"
            placeholder="请输入用户名"
            required
            class="styled-input"
          >
          <small class="field-hint">用于登录和显示</small>
        </div>
        
        <div class="form-section half">
          <label for="email" class="field-label">
            <Mail :size="16" />
            <span>邮箱</span>
            <span class="optional">(可选)</span>
          </label>
          <input 
            id="email" 
            type="email" 
            :value="profile.email"
            @input="$emit('update:profile', { ...profile, email: $event.target.value })"
            placeholder="example@email.com"
            class="styled-input"
          >
          <small class="field-hint">用于账户恢复</small>
        </div>
      </div>
      
      <!-- 所在城市 -->
      <div class="form-section">
        <label for="location" class="field-label">
          <MapPin :size="16" />
          <span>所在城市</span>
          <span class="optional">(可选)</span>
        </label>
        
        <div class="location-group">
          <div class="input-with-button">
            <input 
              id="location" 
              type="text" 
              :value="profile.location_name"
              @input="$emit('update:profile', { ...profile, location_name: $event.target.value })"
              placeholder="例如：北京 或输入城市 ID"
              :disabled="isLocating"
              class="styled-input"
            >
            <button 
              type="button" 
              class="locate-btn" 
              @click="$emit('locate')"
              :disabled="isLocating"
              title="自动定位当前位置"
            >
              <MapPin :size="16" :class="{ 'spinning': isLocating }" />
              <span v-if="isLocating">定位中...</span>
              <span v-else>定位</span>
            </button>
          </div>
          
          <transition name="fade">
            <div v-if="profile.location_name" class="current-location-badge">
              <span class="badge-icon">📍</span>
              <span class="badge-text">当前城市：<strong>{{ profile.location_name }}</strong></span>
            </div>
          </transition>
          
          <transition name="slide">
            <div v-if="locationStatus" class="location-status" :class="{ 'status-error': locationStatus.includes('失败') }">
              <span class="status-icon">{{ locationStatus.includes('成功') ? '✅' : '⚠️' }}</span>
              <span class="status-text">{{ locationStatus }}</span>
            </div>
          </transition>
        </div>
      </div>
      
      <!-- 天气提醒开关 -->
      <div class="form-section compact">
        <div class="toggle-wrapper">
          <div class="toggle-info">
            <label for="weather-alerts" class="toggle-label">
              <Bell :size="16" />
              <span>启用天气提醒</span>
            </label>
            <p class="toggle-description">根据当地天气智能提醒您</p>
          </div>
          <label class="switch">
            <input 
              id="weather-alerts" 
              type="checkbox" 
              :checked="profile.weather_alerts_enabled"
              @change="$emit('update:profile', { ...profile, weather_alerts_enabled: $event.target.checked })"
            >
            <span class="slider"></span>
          </label>
        </div>
      </div>
      
      <!-- 表单按钮 -->
      <div class="form-actions">
        <button type="button" class="btn-cancel" @click="$emit('cancel')">
          取消
        </button>
        <button type="submit" class="btn-submit">
          <span class="btn-icon">💾</span>
          <span>保存修改</span>
        </button>
      </div>
    </form>
  </div>
</template>

<style scoped>
/* 容器 - 减小尺寸 */
.profile-form-container {
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
  width: 100%;
  max-width: 500px;
  animation: slideUp 0.3s ease-out;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 表单头部 - 简化 */
.form-header {
  text-align: center;
  margin-bottom: 1.5rem;
}

.form-header h2 {
  margin: 0 0 0.25rem 0;
  color: #2d3748;
  font-size: 1.5rem;
  font-weight: 700;
}

.form-description {
  color: #718096;
  font-size: 0.85rem;
  margin: 0;
}

/* 表单行 - 并排布局 */
.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1rem;
}

/* 表单区域 - 紧凑化 */
.form-section {
  margin-bottom: 1.25rem;
}

.form-section.half {
  margin-bottom: 0;
}

.form-section.compact {
  margin-bottom: 1rem;
}

/* 标签样式 - 缩小 */
.field-label {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  color: #4a5568;
  font-weight: 600;
  font-size: 0.85rem;
  margin-bottom: 0.5rem;
}

.field-label svg {
  color: #667eea;
}

.required {
  color: #e53e3e;
  margin-left: 0.15rem;
  font-size: 0.9rem;
}

.optional {
  color: #a0aec0;
  font-weight: 400;
  font-size: 0.75rem;
  margin-left: 0.15rem;
}

/* 输入框 - 缩小 */
.styled-input {
  width: 100%;
  padding: 0.65rem 0.85rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.9rem;
  transition: all 0.25s ease;
  background-color: white;
  color: #2d3748;
}

.styled-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  transform: translateY(-1px);
}

.styled-input:disabled {
  background-color: #f7fafc;
  cursor: not-allowed;
  opacity: 0.7;
}

.styled-input::placeholder {
  color: #a0aec0;
}

/* 提示文字 - 缩小 */
.field-hint {
  display: block;
  margin-top: 0.35rem;
  font-size: 0.75rem;
  color: #718096;
  font-style: italic;
  line-height: 1.3;
}

/* 定位组件 - 紧凑 */
.location-group {
  position: relative;
}

.input-with-button {
  display: flex;
  gap: 0.5rem;
}

.input-with-button .styled-input {
  flex: 1;
}

.locate-btn {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.65rem 1rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s ease;
  box-shadow: 0 3px 10px rgba(102, 126, 234, 0.3);
  white-space: nowrap;
}

.locate-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
}

.locate-btn:active:not(:disabled) {
  transform: translateY(0);
}

.locate-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.locate-btn svg.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 当前位置徽章 - 缩小 */
.current-location-badge {
  margin-top: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: linear-gradient(135deg, #e3f9e5 0%, #d4f4d9 100%);
  border-radius: 6px;
  border-left: 3px solid #48bb78;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.8rem;
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(-10px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.badge-icon {
  font-size: 1rem;
}

.badge-text {
  color: #276749;
  line-height: 1.3;
}

.badge-text strong {
  color: #22543d;
  font-weight: 700;
}

/* 定位状态 - 缩小 */
.location-status {
  margin-top: 0.5rem;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.8rem;
  font-weight: 500;
  animation: slideIn 0.3s ease-out;
}

.location-status:not(.status-error) {
  background-color: #f0fff4;
  color: #276749;
  border: 1px solid #9ae6b4;
}

.location-status.status-error {
  background-color: #fff5f5;
  color: #c53030;
  border: 1px solid #feb2b2;
}

.status-icon {
  font-size: 0.9rem;
}

.status-text {
  flex: 1;
}

/* 开关切换 - 紧凑 */
.toggle-wrapper {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background-color: #f7fafc;
  border-radius: 8px;
  border: 2px solid #e2e8f0;
}

.toggle-info {
  flex: 1;
}

.toggle-label {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  color: #4a5568;
  font-weight: 600;
  font-size: 0.9rem;
  margin-bottom: 0.25rem;
  cursor: pointer;
}

.toggle-label svg {
  color: #667eea;
}

.toggle-description {
  color: #718096;
  font-size: 0.75rem;
  margin: 0;
  line-height: 1.3;
}

.switch {
  position: relative;
  display: inline-block;
  width: 48px;
  height: 26px;
  flex-shrink: 0;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #cbd5e0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 26px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 20px;
  width: 20px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 50%;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

input:checked + .slider {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

input:checked + .slider:before {
  transform: translateX(22px);
}

input:focus + .slider {
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
}

/* 表单按钮 - 紧凑 */
.form-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 1.5rem;
  padding-top: 1.25rem;
  border-top: 1px solid #e2e8f0;
}

.btn-cancel, .btn-submit {
  flex: 1;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
}

.btn-cancel {
  background: linear-gradient(135deg, #edf2f7 0%, #e2e8f0 100%);
  color: #4a5568;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
}

.btn-cancel:hover {
  background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e0 100%);
  transform: translateY(-2px);
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.12);
}

.btn-submit {
  background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
  color: white;
  box-shadow: 0 3px 12px rgba(72, 187, 120, 0.4);
}

.btn-submit:hover {
  background: linear-gradient(135deg, #38a169 0%, #2f855a 100%);
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(72, 187, 120, 0.6);
}

.btn-submit:active {
  transform: translateY(0);
}

.btn-icon {
  font-size: 1.1rem;
}

/* 过渡动画 */
.fade-enter-active, .fade-leave-active {
  transition: all 0.25s ease;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

.slide-enter-active, .slide-leave-active {
  transition: all 0.25s ease;
}

.slide-enter-from, .slide-leave-to {
  opacity: 0;
  transform: translateX(-15px);
}

/* 响应式设计 */
@media (max-width: 640px) {
  .profile-form-container {
    padding: 1.5rem;
    max-width: 100%;
  }
  
  .form-header h2 {
    font-size: 1.3rem;
  }
  
  .form-row {
    grid-template-columns: 1fr;
  }
  
  .form-section.half {
    margin-bottom: 1.25rem;
  }
  
  .input-with-button {
    flex-direction: column;
  }
  
  .locate-btn {
    width: 100%;
    justify-content: center;
  }
  
  .toggle-wrapper {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .switch {
    width: 100%;
    margin-top: 0.5rem;
  }
  
  .form-actions {
    flex-direction: column-reverse;
  }
  
  .btn-cancel, .btn-submit {
    width: 100%;
  }
}
</style>