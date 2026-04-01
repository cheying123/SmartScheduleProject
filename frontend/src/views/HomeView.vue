

<script setup>
import { ref, onMounted, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { PlusCircle, LogOut, Clock, Globe, Bell, AlertCircle, Calendar, Check, Sun } from 'lucide-vue-next'
import axios from 'axios'
import { useUserStore } from '../stores/user'

// Composables
import { useSchedule } from '@/composables/useSchedule'
import { useNaturalLanguage } from '@/composables/useNaturalLanguage'
import { useProfile } from '@/composables/useProfile'
import { useNotifications } from '@/composables/useNotifications'

// 工具函数和常量
import { getTimezoneInfo } from '@/utils/timeUtils'
import { NAVIGATION, CREATE_MODES } from '@/constants'

// 组件导入
import Sidebar from '@/components/layout/Sidebar.vue'
import ScheduleList from '@/components/schedule/ScheduleList.vue'
import ScheduleForm from '@/components/schedule/ScheduleForm.vue'
import NaturalLanguageInput from '@/components/schedule/NaturalLanguageInput.vue'
import ProfileCard from '@/components/profile/ProfileCard.vue'
import ProfileForm from '@/components/profile/ProfileForm.vue'
import NotificationList from '@/components/common/NotificationList.vue'

const router = useRouter()
const userStore = useUserStore()
const API_URL = 'http://127.0.0.1:5000/api'

// 使用 Composables
const {
  schedules,
  isLoading,
  error,
  editingSchedule,
  newSchedule,
  editForm,
  fetchSchedules,
  addSchedule: originalAddSchedule,
  deleteSchedule,
  openEditModal,
  closeEditModal,
  saveEdit,
  resetScheduleForm
} = useSchedule(userStore, API_URL)

// 包装 addSchedule，成功后关闭模态框并显示通知
async function addSchedule() {
  console.log('📝 开始创建日程...')
  
  try {
    const success = await originalAddSchedule()
    console.log('✅ 创建结果:', success)
    
    // 先立即关闭模态框
    isFormVisible.value = false
    
    // 重置表单
    setTimeout(() => {
      resetScheduleForm()
    }, 100)
    
    // 显示通知
    if (success) {
      showNotification('success', '✅ 日程创建成功！')
    } else {
      showNotification('error', '❌ 创建失败，请重试')
    }
    
  } catch (err) {
    console.error('创建失败:', err)
    
    // 即使出错也关闭模态框
    isFormVisible.value = false
    
    // 显示错误信息
    const errorMsg = err.response?.data?.error || err.message || '未知错误'
    showNotification('error', `❌ 创建失败：${errorMsg}`)
  }
}

// 显示通知的辅助函数
function showNotification(type, message, duration = 3000) {
  notification.value = {
    show: true,
    type,
    message,
    duration
  }
  
  // 自动关闭
  setTimeout(() => {
    notification.value.show = false
  }, duration)
}

const {
  isNaturalLanguageMode,
  naturalLanguageInput,
  isProcessingNL,
  isAIProcessing,
  conflictDialog,
  isRecording,
  recordingDuration,
  handleNaturalLanguageSubmit,
  startVoiceInput,
  stopRecording,
  handleCancelClick
} = useNaturalLanguage(API_URL, fetchSchedules)

// 强制创建日程（忽略冲突）
async function forceCreateSchedule() {
  if (!conflictDialog.value?.parsed_data) {
    return
  }
  
  try {
    // 关闭冲突对话框
    conflictDialog.value = null
    
    // TODO: 调用后端 API 强制创建（需要后端支持）
    // 或者提示用户修改时间
    
    alert('功能开发中：您可以先手动调整时间，或者联系开发者添加"强制创建"功能')
    
  } catch (error) {
    console.error('强制创建失败:', error)
    alert('创建失败，请重试')
  }
}

const {
  isProfileEditModalVisible,
  profileForm,
  isLocating,
  locationStatus,
  openProfileEdit,
  saveProfile,
  locateUser,
  refreshWeatherFromProfile
} = useProfile(userStore, API_URL)

const {
  recommendations,
  loadRecommendations,
  clearNotifications
} = useNotifications(API_URL)

// 页面状态
const activeTab = ref(NAVIGATION.tabs.SCHEDULE)
const isSidebarCollapsed = ref(false)
const currentTimezone = ref('')
const isLogoutModalVisible = ref(false)
const createMode = ref(CREATE_MODES.FORM)
const isFormVisible = ref(false)
const notification = ref({
  show: false,
  type: 'success',
  message: '',
  duration: 3000
})

// 计算属性
const groupedSchedules = computed(() => {
  const groups = {}
  schedules.value.forEach(schedule => {
    const date = new Date(schedule.start_time).toLocaleDateString('zh-CN', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    })
    if (!groups[date]) groups[date] = []
    groups[date].push(schedule)
  })
  return groups
})

// 方法
function getTabTitle() {
  return NAVIGATION.titles[activeTab.value] || '我的日程'
}

function openCreateForm() {
  isFormVisible.value = true
  createMode.value = CREATE_MODES.FORM
  resetScheduleForm()
}

function openNaturalLanguageForm() {
  isNaturalLanguageMode.value = true
  createMode.value = CREATE_MODES.NATURAL
  isFormVisible.value = true
  naturalLanguageInput.value = ''
}

// 格式化相对时间
function formatRelativeTime(isoString) {
  if (!isoString) return ''
  const date = new Date(isoString)
  const now = new Date()
  const diffMs = date - now
  const diffMins = Math.floor(diffMs / 60000)
  
  if (diffMins < 1) return '刚刚'
  if (diffMins < 60) return `${diffMins}分钟后`
  if (diffMins < 1440) return `${Math.floor(diffMins / 60)}小时后`
  return `${Math.floor(diffMins / 1440)}天后`
}

// 获取提醒图标
function getReminderIcon(priority) {
  switch(priority) {
    case 'urgent':
      return AlertCircle
    case 'high':
      return Bell
    default:
      return Calendar
  }
}

// 获取提醒样式
function getReminderStyle(priority) {
  const styles = {
    urgent: 'reminder-urgent',
    high: 'reminder-high',
    medium: 'reminder-medium',
    low: 'reminder-low'
  }
  return styles[priority] || 'reminder-low'
}

// 计算进度条宽度
function getProgressWidth(countdown) {
  if (!countdown) return '0%'
  
  const remainingSeconds = countdown.remaining_seconds
  const totalSeconds = 24 * 60 * 60 // 24 小时作为最大值
  
  if (remainingSeconds <= 0) return '100%'
  if (remainingSeconds > totalSeconds) return '10%'
  
  const percentage = ((totalSeconds - remainingSeconds) / totalSeconds) * 100
  return `${Math.min(100, Math.max(10, percentage))}%`
}

// 跳转到指定日程
function navigateToSchedule(scheduleId) {
  // 切换到日程标签页
  activeTab.value = 'schedule'
  
  // 滚动到该日程位置
  setTimeout(() => {
    const element = document.getElementById(`schedule-${scheduleId}`)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' })
      element.style.animation = 'highlight 2s ease'
    }
  }, 300)
}

// 获取通知标题
function getNotificationTitle(type) {
  const titles = {
    'weather': '🌦️ 天气提醒',
    'time_preference': '⏰ 时间偏好',
    'balance': '⚖️ 日程平衡',
    'schedule_reminder': '📅 日程提醒',
    'info': 'ℹ️ 提示信息'
  }
  return titles[type] || '消息通知'
}

function handleLogout() {
  userStore.logout()
  isLogoutModalVisible.value = false
  window.location.href = '/login'
}

function switchToNotifications() {
  activeTab.value = NAVIGATION.tabs.NOTIFICATIONS
  clearNotifications()
}

// 生命周期
onMounted(async () => {
  currentTimezone.value = getTimezoneInfo()
  
  if (!userStore.user && userStore.token) {
    try {
      const response = await axios.get(`${API_URL}/auth/me`, {
        headers: { 'Authorization': `Bearer ${userStore.token}` }
      })
      userStore.user = response.data
    } catch (error) {
      console.error('恢复用户信息失败:', error)
      if (error.response?.status === 401) {
        userStore.logout()
        window.location.href = '/login'
      }
    }
  }
  
  fetchSchedules(API_URL)
  loadRecommendations()
})

onUnmounted(() => {
  stopRecording()
})
</script>

<template>
  <div class="home-container">
    <!-- 侧边栏组件 -->
    <Sidebar
      :is-collapsed="isSidebarCollapsed"
      :active-tab="activeTab"
      :user="userStore.user"
      :recommendations-count="recommendations ? recommendations.length : 0"
      @toggle-collapse="isSidebarCollapsed = !isSidebarCollapsed"
      @tab-change="activeTab = $event"
      @logout="handleLogout"
    />

    <!-- 主内容区 -->
    <main class="main-content">
      <!-- 顶部栏 -->
      <header class="top-bar">
        <h1>{{ getTabTitle() }}</h1>
        <div class="top-bar-actions">
          <span class="current-time">{{ currentTimezone }}</span>
          <button 
            v-if="activeTab === 'schedule'"
            class="add-btn-top" 
            @click="openCreateForm"
          >
            <PlusCircle :size="20" />
            <span>新建日程</span>
          </button>
        </div>
      </header>

      <!-- 日程页面 -->
      <div v-if="activeTab === 'schedule'" class="tab-content">
        <ScheduleList
          :schedules="schedules"
          :isLoading="isLoading"
          :error="error"
          :groupedSchedules="groupedSchedules"
          @edit="openEditModal"
          @delete="deleteSchedule"
        />
      </div>

      <!-- 个人资料页面 -->
      <div v-if="activeTab === 'profile'" class="tab-content">
        <ProfileCard
          :user="userStore.user"
          :schedules="schedules"
          @edit="openProfileEdit"
          @refresh-weather="refreshWeatherFromProfile"
        />
      </div>

      <!-- 通知页面（带倒计时提醒） -->
      <div v-if="activeTab === 'notifications'" class="tab-content">
        <div class="notifications-panel">
          <button class="refresh-btn" @click="loadRecommendations">
            <Check :size="18" />
            <span>刷新推荐</span>
          </button>
          
          <div v-if="!recommendations || recommendations.length === 0" class="empty-notifications">
            <Bell :size="64" />
            <h3>暂无新消息</h3>
            <p>点击"刷新推荐"获取智能建议</p>
          </div>
          
          <div v-else class="notifications-list">
            <!-- 倒计时提醒和普通通知混合显示 -->
            <div 
              v-for="(rec, index) in recommendations" 
              :key="index" 
              class="notification-item"
              :class="[
                rec.type === 'schedule_reminder' ? 'type-schedule-reminder' : ('type-' + rec.type),
                getReminderStyle(rec.priority)
              ]"
            >
              <div class="notification-icon">
                <component 
                  v-if="rec.type === 'schedule_reminder'"
                  :is="getReminderIcon(rec.priority)" 
                  :size="24"
                />
                <Sun v-else-if="rec.type === 'weather'" :size="24" />
                <Check v-else-if="rec.type === 'time_preference'" :size="24" />
                <Globe v-else :size="24" />
              </div>
              <div class="notification-content">
                <h4>
                  {{ rec.type === 'schedule_reminder' ? '⏰ 日程提醒' : getNotificationTitle(rec.type) }}
                </h4>
                <p>{{ rec.message }}</p>
                
                <!-- 倒计时详情（仅日程提醒显示） -->
                <div v-if="rec.type === 'schedule_reminder' && rec.countdown" class="countdown-details">
                  <div class="countdown-time-display">
                    <Clock :size="14" />
                    <span class="time-text">{{ rec.countdown.remaining_text }}</span>
                    <span class="relative-time">{{ formatRelativeTime(rec.start_time) }}</span>
                  </div>
                  
                  <!-- 进度条（可视化剩余时间） -->
                  <div class="countdown-progress">
                    <div 
                      class="progress-bar"
                      :style="{ width: getProgressWidth(rec.countdown) }"
                    ></div>
                  </div>
                  
                  <!-- 快速操作按钮 -->
                  <div class="quick-actions">
                    <button 
                      class="view-schedule-btn"
                      @click="navigateToSchedule(rec.schedule_id)"
                    >
                      查看日程
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 设置页面 -->
      <div v-if="activeTab === 'settings'" class="tab-content">
        <div class="settings-panel">
          <h3>偏好设置</h3>
          
          <div class="setting-item">
            <div class="setting-label">
              <Clock :size="20" />
              <span>时区显示</span>
            </div>
            <div class="setting-value">
              {{ currentTimezone }}
            </div>
          </div>
          
          <div class="setting-item">
            <div class="setting-label">
              <Globe :size="20" />
              <span>默认城市</span>
            </div>
            <div class="setting-value">
              {{ userStore.user?.location_name || '北京 (101010100)' }}
            </div>
          </div>
          
          <div class="setting-item">
            <div class="setting-label">
              <Bell :size="20" />
              <span>天气提醒</span>
            </div>
            <label class="switch">
              <input type="checkbox" :checked="userStore.user?.weather_alerts_enabled !== false" disabled>
              <span class="slider"></span>
            </label>
          </div>
          
          <div class="setting-section">
            <h4>关于</h4>
            <p class="about-text">
              基于多模态交互的个性化智能日程管理助手<br>
              版本：v1.0.0<br>
              技术栈：Vue 3 + Flask + MySQL
            </p>
          </div>
        </div>
      </div>
    </main>

    <!-- 弹窗：日程创建表单 -->
    <transition name="fade">
      <div v-if="isFormVisible && createMode === 'form'" class="form-overlay" @click.self="isFormVisible = false">
        <ScheduleForm
          :schedule="newSchedule"
          mode="create"
          @submit="addSchedule"
          @cancel="isFormVisible = false"
          @switch-mode="openNaturalLanguageForm"
          @update:schedule="newSchedule = $event"
        />
      </div>
    </transition>

    <!-- 弹窗：自然语言输入 -->
    <transition name="fade">
      <div v-if="isNaturalLanguageMode && createMode === 'natural'" class="form-overlay" @click.self="isNaturalLanguageMode = false">
        <NaturalLanguageInput
          :input-value="naturalLanguageInput"
          :is-processing="isProcessingNL"
          :is-recording="isRecording"
          :recording-duration="recordingDuration"
          :is-ai-processing="isAIProcessing"
          @submit="handleNaturalLanguageSubmit"
          @cancel="handleCancelClick"
          @switch-mode="openCreateForm"
          @voice-input="startVoiceInput"
          @update:input-value="naturalLanguageInput = $event"
        />
      </div>
    </transition>

    <!-- 弹窗：编辑日程 -->
    <transition name="fade">
      <div v-if="editingSchedule" class="form-overlay" @click.self="closeEditModal">
        <ScheduleForm
          :schedule="editForm"
          mode="edit"
          @submit="saveEdit"
          @cancel="closeEditModal"
          @update:schedule="editForm = $event"
        />
      </div>
    </transition>

    <!-- 弹窗：编辑个人资料 -->
    <transition name="fade">
      <div v-if="isProfileEditModalVisible" class="form-overlay" @click.self="isProfileEditModalVisible = false">
        <ProfileForm
          :profile="profileForm"
          :is-locating="isLocating"
          :location-status="locationStatus"
          @submit="saveProfile"
          @cancel="isProfileEditModalVisible = false"
          @locate="locateUser"
          @update:profile="profileForm = $event"
        />
      </div>
    </transition>

    <!-- 弹窗：退出确认 -->
    <transition name="fade">
      <div v-if="isLogoutModalVisible" class="form-overlay" @click.self="isLogoutModalVisible = false">
        <div class="form-container logout-confirm">
          <h2>确认退出</h2>
          <p>确定要退出登录吗？</p>
          <div class="form-actions">
            <button type="button" class="btn-cancel" @click="isLogoutModalVisible = false">取消</button>
            <button type="button" class="btn-submit btn-logout" @click="handleLogout">
              <LogOut :size="16" style="vertical-align: middle; margin-right: 4px;" />
              退出登录
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- 通知提示 -->
    <transition name="slide-fade">
      <div v-if="notification.show" class="notification-toast" :class="notification.type">
        <div class="notification-content">
          <span class="notification-icon">
            {{ notification.type === 'success' ? '✓' : '✕' }}
          </span>
          <span class="notification-message">{{ notification.message }}</span>
        </div>
        <div class="notification-progress"></div>
      </div>
    </transition>

    <!-- 冲突确认对话框 -->
    <transition name="fade">
      <div v-if="conflictDialog" class="form-overlay" @click.self="conflictDialog = null">
        <div class="form-container conflict-dialog">
          <h2>⚠️ 日程冲突提醒</h2>
          
          <div class="conflict-info">
            <div class="new-schedule">
              <h4>您想创建的日程：</h4>
              <p class="schedule-title">{{ conflictDialog.parsed_data?.title }}</p>
              <p class="schedule-time">
                📅 {{ conflictDialog.parsed_data?.start_time }}
                <span v-if="conflictDialog.parsed_data?.end_time">
                  - {{ conflictDialog.parsed_data?.end_time }}
                </span>
              </p>
            </div>
            
            <div class="existing-conflicts">
              <h4>与以下日程冲突：</h4>
              <div 
                v-for="(conflict, index) in conflictDialog.conflicts" 
                :key="index"
                class="conflict-item"
              >
                <div class="conflict-header">
                  <span class="conflict-icon">⛔</span>
                  <strong>{{ conflict.title }}</strong>
                </div>
                <div class="conflict-time">
                  🕐 {{ conflict.start_time }} - {{ conflict.end_time || '未设置结束时间' }}
                </div>
              </div>
            </div>
          </div>
          
          <div class="form-actions">
            <button type="button" class="btn-cancel" @click="conflictDialog = null">取消</button>
            <button type="button" class="btn-submit btn-force-create" @click="forceCreateSchedule">
              仍然创建
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
/* ===== 主布局样式 ===== */
.home-container {
  display: flex;
  max-width: 100%;
  margin: 0;
  padding: 0;
  height: 100vh;
  overflow: hidden;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: #F8F9FE;
}

.top-bar {
  background-color: white;
  padding: 1.5rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.top-bar h1 {
  margin: 0;
  color: #32325D;
  font-size: 1.5rem;
}

.top-bar-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.current-time {
  color: #8898aa;
  font-size: 0.9rem;
}

.add-btn-top {
  background-color: #5E72E4;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.75rem 1.5rem;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s;
}

.add-btn-top:hover {
  background-color: #4c5fd5;
  transform: translateY(-2px);
}

.tab-content {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
}

/* ===== 通知面板样式 ===== */
.notifications-panel {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(50, 50, 93, 0.11), 0 1px 3px rgba(0, 0, 0, 0.08);
}

.refresh-btn {
  background-color: #5E72E4;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.75rem 1.5rem;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  transition: all 0.2s;
}

.refresh-btn:hover {
  background-color: #4c5fd5;
  transform: translateY(-2px);
}

.empty-notifications {
  text-align: center;
  padding: 4rem 2rem;
  color: #adb5bd;
}

.empty-notifications h3 {
  margin: 1rem 0 0.5rem 0;
  color: #32325D;
}

.empty-notifications p {
  color: #8898aa;
}

.notifications-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.notification-item {
  display: flex;
  gap: 1rem;
  padding: 1.25rem;
  border-radius: 8px;
  border-left-width: 6px;
  border-left-style: solid;
  background-color: #f8f9fa;
  transition: all 0.3s ease;
}

.notification-item:hover {
  transform: translateX(5px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.notification-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background-color: rgba(94, 114, 228, 0.1);
  color: #5E72E4;
}

.notification-content {
  flex-grow: 1;
}

.notification-content h4 {
  margin: 0 0 0.5rem 0;
  color: #32325D;
  font-size: 1.1rem;
}

.notification-content p {
  margin: 0;
  color: #525F7F;
  line-height: 1.6;
}

/* 日程提醒特殊样式 */
.notification-item.type-schedule-reminder {
  animation: none;
}

/* 不同优先级的样式 */
.reminder-urgent {
  background-color: #ffebee;
  border-left-color: #f44336;
  animation: pulse-border 2s infinite;
}

.reminder-high {
  background-color: #fff3e0;
  border-left-color: #ff9800;
}

.reminder-medium {
  background-color: #fff9c4;
  border-left-color: #ffc107;
}

.reminder-low {
  background-color: #e3f2fd;
  border-left-color: #2196F3;
}

@keyframes pulse-border {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(244, 67, 54, 0.4);
  }
  50% {
    box-shadow: 0 0 0 10px rgba(244, 67, 54, 0);
  }
}

/* 倒计时详情区域 */
.countdown-details {
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
}

.countdown-time-display {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: #525F7F;
  margin-bottom: 0.5rem;
}

.countdown-time-display svg {
  color: #5E72E4;
}

.time-text {
  font-weight: 600;
  color: #32325D;
}

.relative-time {
  font-size: 0.85em;
  color: #8898aa;
  margin-left: auto;
}

/* 进度条 */
.countdown-progress {
  width: 100%;
  height: 6px;
  background-color: rgba(0, 0, 0, 0.05);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 0.75rem;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #5E72E4 0%, #825EE4 100%);
  border-radius: 3px;
  transition: width 1s ease;
}

.reminder-urgent .progress-bar {
  background: linear-gradient(90deg, #f44336 0%, #ff6659 100%);
}

.reminder-high .progress-bar {
  background: linear-gradient(90deg, #ff9800 0%, #ffb74d 100%);
}

.reminder-medium .progress-bar {
  background: linear-gradient(90deg, #ffc107 0%, #ffd54f 100%);
}

/* 快速操作按钮 */
.quick-actions {
  display: flex;
  gap: 0.5rem;
}

.view-schedule-btn {
  padding: 0.4rem 0.8rem;
  font-size: 0.85rem;
  background-color: rgba(94, 114, 228, 0.1);
  color: #5E72E4;
  border: 1px solid rgba(94, 114, 228, 0.3);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.view-schedule-btn:hover {
  background-color: #5E72E4;
  color: white;
}

/* ===== 设置面板样式 ===== */
.settings-panel {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(50, 50, 93, 0.11), 0 1px 3px rgba(0, 0, 0, 0.08);
}

.settings-panel h3 {
  margin: 0 0 1.5rem 0;
  color: #32325D;
  font-size: 1.2rem;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 0;
  border-bottom: 1px solid #e9ecef;
}

.setting-label {
  color: #32325D;
  font-weight: 500;
}

.setting-value {
  color: #8898aa;
  font-size: 0.9rem;
}

.setting-section {
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 2px solid #e9ecef;
}

.setting-section h4 {
  margin: 0 0 1rem 0;
  color: #32325D;
  font-size: 1rem;
}

.about-text {
  color: #8898aa;
  font-size: 0.9rem;
  line-height: 1.8;
}

/* ===== 通用弹窗样式 ===== */
.form-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.form-container {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(50, 50, 93, 0.11), 0 1px 3px rgba(0, 0, 0, 0.08);
  width: 100%;
  max-width: 500px;
}

.form-container h2 {
  text-align: center;
  margin-top: 0;
  color: #32325D;
}

.form-container p {
  color: #525F7F;
  margin: 1rem 0;
  text-align: center;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 1.5rem;
}

.btn-cancel, .btn-submit {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel {
  background-color: #f4f5f7;
  color: #525F7F;
}

.btn-cancel:hover {
  background-color: #e9ecef;
}

.btn-submit {
  background-color: #5E72E4;
  color: white;
}

.btn-submit:hover {
  background-color: #4a5fd6;
  transform: translateY(-1px);
}

.btn-logout {
  background-color: #f5365c;
}

.btn-logout:hover {
  background-color: #ec1a42;
}

.logout-confirm {
  text-align: center;
}

/* ===== 冲突对话框样式 ===== */
.conflict-dialog {
  max-width: 600px;
}

.conflict-info {
  margin: 1.5rem 0;
}

.new-schedule {
  background-color: #e3f2fd;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1.5rem;
}

.new-schedule h4 {
  margin: 0 0 0.5rem 0;
  color: #1976d2;
  font-size: 0.95rem;
}

.schedule-title {
  margin: 0.25rem 0;
  font-weight: 600;
  color: #32325D;
  font-size: 1.1rem;
}

.schedule-time {
  margin: 0.25rem 0;
  color: #525F7F;
  font-size: 0.9rem;
}

.existing-conflicts h4 {
  margin: 0 0 0.75rem 0;
  color: #dc3545;
  font-size: 0.95rem;
}

.conflict-item {
  background-color: #ffebee;
  padding: 0.75rem;
  border-radius: 6px;
  margin-bottom: 0.75rem;
  border-left: 3px solid #dc3545;
}

.conflict-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
}

.conflict-icon {
  font-size: 1.2rem;
}

.conflict-header strong {
  color: #c62828;
}

.conflict-time {
  font-size: 0.85rem;
  color: #8898aa;
  margin-left: 1.75rem;
}

.btn-force-create {
  background-color: #ff9800;
}

.btn-force-create:hover {
  background-color: #f57c00;
}

/* ===== 过渡动画 ===== */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

/* ===== 通知提示样式 ===== */
.notification-toast {
  position: fixed;
  top: 2rem;
  right: 2rem;
  min-width: 300px;
  max-width: 500px;
  padding: 1rem 1.5rem;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 9999;
  overflow: hidden;
  animation: slide-in 0.3s ease-out;
}

@keyframes slide-in {
  from {
    transform: translateX(400px);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.notification-toast.success {
  background-color: #d4edda;
  border-left: 4px solid #28a745;
  color: #155724;
}

.notification-toast.error {
  background-color: #f8d7da;
  border-left: 4px solid #dc3545;
  color: #721c24;
}

.notification-content {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.notification-icon {
  font-size: 1.25rem;
  font-weight: bold;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background-color: rgba(255, 255, 255, 0.3);
}

.notification-message {
  flex: 1;
  font-size: 0.95rem;
  line-height: 1.5;
}

.notification-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 3px;
  background-color: rgba(255, 255, 255, 0.5);
  animation: progress linear;
}

.notification-toast.success .notification-progress {
  animation-duration: 3s;
}

.notification-toast.error .notification-progress {
  animation-duration: 5s;
}

@keyframes progress {
  from {
    width: 100%;
  }
  to {
    width: 0%;
  }
}

/* ===== 滑出动画 ===== */
.slide-fade-enter-active {
  transition: all 0.3s ease-out;
}

.slide-fade-leave-active {
  transition: all 0.3s ease-out;
}

.slide-fade-enter-from {
  transform: translateX(400px);
  opacity: 0;
}

.slide-fade-leave-to {
  transform: translateX(400px);
  opacity: 0;
}

/* ===== 高亮动画 ===== */
@keyframes highlight {
  0%, 100% {
    background-color: white;
  }
  50% {
    background-color: #fff3cd;
  }
}
</style>