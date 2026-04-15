<script setup>
import { ref, watch } from 'vue'
import { MapPin, User, Mail, Bell, Search, X } from 'lucide-vue-next'
import axios from 'axios'
import { useUserStore } from '@/stores/user'

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

const userStore = useUserStore()
const API_URL = 'http://127.0.0.1:5000/api'

// 城市搜索相关状态
const showCityDropdown = ref(false)
const citySearchKeyword = ref('')
const citySearchResults = ref([])
const isSearching = ref(false)
let searchTimeout = null

// 监听输入框变化，防抖搜索
watch(citySearchKeyword, (newVal) => {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
  
  if (!newVal || newVal.trim().length < 1) {
    citySearchResults.value = []
    showCityDropdown.value = false
    return
  }
  
  searchTimeout = setTimeout(() => {
    searchCities(newVal.trim())
  }, 300) // 300ms 防抖
})

/**
 * 搜索城市
 */
async function searchCities(keyword) {
  if (!keyword) return
  
  isSearching.value = true
  
  try {
    const response = await axios.get(`${API_URL}/location/search`, {
      params: { keyword },
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    })
    
    citySearchResults.value = response.data.cities || []
    showCityDropdown.value = citySearchResults.value.length > 0
  } catch (error) {
    console.error('城市搜索失败:', error)
    citySearchResults.value = []
  } finally {
    isSearching.value = false
  }
}

/**
 * 选择城市
 */
function selectCity(city) {
  emit('update:profile', {
    ...props.profile,
    location: city.id,
    location_name: city.display_name
  })
  
  citySearchKeyword.value = city.display_name
  showCityDropdown.value = false
  citySearchResults.value = []
}

/**
 * 清除城市选择
 */
function clearCitySelection() {
  emit('update:profile', {
    ...props.profile,
    location: '',
    location_name: ''
  })
  citySearchKeyword.value = ''
  citySearchResults.value = []
  showCityDropdown.value = false
}

/**
 * 点击外部关闭下拉框
 */
function handleClickOutside(event) {
  const dropdown = document.querySelector('.city-dropdown')
  const input = document.querySelector('.city-search-input')
  
  if (dropdown && input && !dropdown.contains(event.target) && !input.contains(event.target)) {
    showCityDropdown.value = false
  }
}

// 添加全局点击事件监听
if (typeof window !== 'undefined') {
  window.addEventListener('click', handleClickOutside)
}
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
      
      <!-- 所在城市（优化版：支持搜索选择） -->
      <div class="form-section">
        <label for="location" class="field-label">
          <MapPin :size="16" />
          <span>所在城市</span>
          <span class="optional">(可选)</span>
        </label>
        
        <div class="location-group">
          <!-- 城市搜索输入框 -->
          <div class="city-search-wrapper">
            <div class="input-with-icons">
              <Search :size="16" class="search-icon" />
              <input 
                id="location" 
                type="text" 
                v-model="citySearchKeyword"
                @focus="showCityDropdown = citySearchResults.length > 0"
                placeholder="搜索城市（如：北京、上海、广州...）"
                :disabled="isLocating"
                class="styled-input city-search-input"
                autocomplete="off"
              >
              <button 
                v-if="citySearchKeyword"
                type="button"
                class="clear-btn"
                @click="clearCitySelection"
                title="清除选择"
              >
                <X :size="14" />
              </button>
            </div>
            
            <!-- 城市下拉列表 -->
            <transition name="dropdown">
              <div v-if="showCityDropdown && citySearchResults.length > 0" class="city-dropdown">
                <div 
                  v-for="city in citySearchResults" 
                  :key="city.id"
                  class="city-item"
                  @click="selectCity(city)"
                >
                  <div class="city-info">
                    <span class="city-name">{{ city.display_name }}</span>
                    <span v-if="city.adm1" class="city-adm">{{ city.adm1 }}</span>
                  </div>
                  <span class="city-id">{{ city.id }}</span>
                </div>
                
                <div v-if="isSearching" class="city-loading">
                  <span class="loading-spinner"></span>
                  <span>搜索中...</span>
                </div>
                
                <div v-if="!isSearching && citySearchResults.length === 0 && citySearchKeyword" class="city-no-result">
                  未找到匹配的城市
                </div>
              </div>
            </transition>
          </div>
          
          <!-- 定位按钮 -->
          <button 
            type="button" 
            class="locate-btn" 
            @click="$emit('locate')"
            :disabled="isLocating"
            title="自动定位当前位置"
          >
            <MapPin :size="16" :class="{ 'spinning': isLocating }" />
            <span v-if="isLocating">定位中...</span>
            <span v-else>GPS定位</span>
          </button>
          
          <!-- 当前城市显示 -->
          <transition name="fade">
            <div v-if="profile.location_name" class="current-location-badge">
              <span class="badge-icon">📍</span>
              <span class="badge-text">当前城市：<strong>{{ profile.location_name }}</strong></span>
              <span class="badge-id">ID: {{ profile.location }}</span>
            </div>
          </transition>
          
          <!-- 定位状态提示 -->
          <transition name="slide">
            <div v-if="locationStatus" class="location-status" :class="{ 'status-error': locationStatus.includes('失败') }">
              <span class="status-icon">{{ locationStatus.includes('成功') ? '✅' : '⚠️' }}</span>
              <span class="status-text">{{ locationStatus }}</span>
            </div>
          </transition>
        </div>
        
        <small class="field-hint">
          💡 提示：可以手动输入城市名称搜索，或使用GPS自动定位
        </small>
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
/* ===== 城市搜索样式 ===== */
.city-search-wrapper {
  position: relative;
  flex: 1;
}

.input-with-icons {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 12px;
  color: #94a3b8;
  pointer-events: none;
  z-index: 1;
}

.city-search-input {
  padding-left: 40px !important;
  padding-right: 35px !important;
}

.clear-btn {
  position: absolute;
  right: 8px;
  background: transparent;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.clear-btn:hover {
  background: #f1f5f9;
  color: #64748b;
}

/* 城市下拉列表 */
.city-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 4px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  max-height: 300px;
  overflow-y: auto;
  z-index: 1000;
}

.city-item {
  padding: 12px 16px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: all 0.2s;
  border-bottom: 1px solid #f1f5f9;
}

.city-item:last-child {
  border-bottom: none;
}

.city-item:hover {
  background: #f8fafc;
}

.city-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.city-name {
  font-size: 0.9rem;
  font-weight: 600;
  color: #1e293b;
}

.city-adm {
  font-size: 0.75rem;
  color: #64748b;
}

.city-id {
  font-size: 0.7rem;
  color: #94a3b8;
  font-family: monospace;
  background: #f1f5f9;
  padding: 2px 6px;
  border-radius: 4px;
}

.city-loading,
.city-no-result {
  padding: 16px;
  text-align: center;
  color: #64748b;
  font-size: 0.85rem;
}

.loading-spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid #e2e8f0;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-right: 8px;
  vertical-align: middle;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 下拉动画 */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.2s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* 当前城市徽章优化 */
.current-location-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border: 1px solid #bae6fd;
  border-radius: 8px;
  margin-top: 8px;
}

.badge-icon {
  font-size: 1.1rem;
}

.badge-text {
  flex: 1;
  font-size: 0.85rem;
  color: #0369a1;
}

.badge-text strong {
  color: #0284c7;
}

.badge-id {
  font-size: 0.7rem;
  color: #64748b;
  font-family: monospace;
  background: white;
  padding: 2px 6px;
  border-radius: 4px;
}

/* 定位按钮优化 */
.locate-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.25);
}

.locate-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.35);
}

.locate-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.spinning {
  animation: spin 1s linear infinite;
}

/* ===== 基础表单样式（恢复）===== */
.profile-form-container {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  padding: 2rem;
  max-width: 700px;
  margin: 0 auto;
}

.form-header {
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #f1f5f9;
}

.form-header h2 {
  margin: 0 0 0.5rem 0;
  color: #1e293b;
  font-size: 1.5rem;
  font-weight: 700;
}

.form-description {
  margin: 0;
  color: #64748b;
  font-size: 0.9rem;
}

.profile-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-section.half {
  /* 由grid布局控制 */
}

.form-section.compact {
  gap: 0;
}

.field-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  font-weight: 600;
  color: #334155;
}

.required {
  color: #ef4444;
  font-size: 0.8rem;
}

.optional {
  color: #94a3b8;
  font-size: 0.8rem;
  font-weight: 400;
}

.styled-input {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.95rem;
  color: #1e293b;
  transition: all 0.2s;
  background: #f8fafc;
}

.styled-input:focus {
  outline: none;
  border-color: #667eea;
  background: white;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.styled-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background: #f1f5f9;
}

.field-hint {
  font-size: 0.8rem;
  color: #94a3b8;
  margin-top: 0.25rem;
}

.location-group {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.input-with-button {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.location-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: #fef3c7;
  border: 1px solid #fbbf24;
  border-radius: 8px;
  font-size: 0.85rem;
  color: #92400e;
}

.location-status.status-error {
  background: #fee2e2;
  border-color: #f87171;
  color: #991b1b;
}

.status-icon {
  font-size: 1rem;
}

.status-text {
  flex: 1;
}

.toggle-wrapper {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.toggle-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.toggle-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.95rem;
  font-weight: 600;
  color: #334155;
  cursor: pointer;
}

.toggle-description {
  margin: 0;
  font-size: 0.8rem;
  color: #64748b;
}

.switch {
  position: relative;
  display: inline-block;
  width: 50px;
  height: 26px;
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
  background-color: #cbd5e1;
  transition: 0.3s;
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
  transition: 0.3s;
  border-radius: 50%;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

input:checked + .slider {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

input:checked + .slider:before {
  transform: translateX(24px);
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 1rem;
  padding-top: 1.5rem;
  border-top: 2px solid #f1f5f9;
}

.btn-cancel {
  padding: 0.75rem 1.5rem;
  background: white;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.95rem;
  font-weight: 600;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
  color: #475569;
}

.btn-submit {
  padding: 0.75rem 2rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 8px;
  font-size: 0.95rem;
  font-weight: 600;
  color: white;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.btn-submit:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
}

.btn-icon {
  font-size: 1.1rem;
}

/* 淡入淡出动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 滑动动画 */
.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
}

.slide-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* 响应式调整 */
@media (max-width: 768px) {
  .profile-form-container {
    padding: 1.5rem;
  }

  .form-row {
    grid-template-columns: 1fr;
    gap: 1rem;
  }

  .form-actions {
    flex-direction: column-reverse;
  }

  .btn-cancel,
  .btn-submit {
    width: 100%;
    justify-content: center;
  }
}

/* 响应式调整 */
@media (max-width: 640px) {
  .location-group {
    flex-direction: column;
  }
  
  .locate-btn {
    width: 100%;
    justify-content: center;
  }
  
  .city-dropdown {
    max-height: 250px;
  }
}
</style>
