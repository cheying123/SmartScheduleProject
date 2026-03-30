<script setup>
import { ref, onMounted, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { PlusCircle, LogOut, Clock, Globe, Bell } from 'lucide-vue-next'
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
  addSchedule,
  deleteSchedule,
  openEditModal,
  closeEditModal,
  saveEdit,
  resetScheduleForm
} = useSchedule(userStore)

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
} = useNaturalLanguage(API_URL)

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
      :recommendations-count="recommendations.length"
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

      <!-- 通知页面 -->
      <div v-if="activeTab === 'notifications'" class="tab-content">
        <NotificationList
          :recommendations="recommendations"
          @refresh="loadRecommendations"
        />
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

/* ===== 过渡动画 ===== */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>