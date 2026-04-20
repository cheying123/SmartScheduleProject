<script setup>
import { ref, onMounted, computed, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { PlusCircle, LogOut, Clock, Globe, Bell, AlertCircle, Calendar, Check, Sun, BarChart, Sparkles, Search, Filter, MessageSquare, Download, Upload } from 'lucide-vue-next'

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
import ConflictDialog from '@/components/schedule/ConflictDialog.vue'
import DashboardStats from '@/components/analytics/DashboardStats.vue'
// 新增组件导入
import DailyBriefing from '@/components/dashboard/DailyBriefing.vue'
import AutoScheduleModal from '@/components/schedule/AutoScheduleModal.vue'
import FloatingActionButton from '@/components/common/FloatingActionButton.vue'
import NotificationsCenter from '@/components/notifications/NotificationsCenter.vue'
import SettingsPanel from '@/components/settings/SettingsPanel.vue'
import LogoutConfirmDialog from '@/components/common/LogoutConfirmDialog.vue'
import ScheduleExport from '@/components/schedule/ScheduleExport.vue'
import ScheduleImport from '@/components/schedule/ScheduleImport.vue'

const router = useRouter()
const userStore = useUserStore()
const API_URL = 'http://127.0.0.1:5000/api'

// 新增：每日摘要状态
const dailyBriefing = ref(null)
const isBriefingLoading = ref(false)

// 统计面板引用
const statsPanel = ref(null)

// FAB 快速添加按钮状态
const showFabMenu = ref(false)

// 新增：自动排程状态
const isAutoScheduleModalVisible = ref(false)
const autoScheduleTasksInput = ref('') // 格式示例：复习数学 60, 跑步 30
const isAutoScheduling = ref(false)

// 新增：导出/导入日程状态
const isExportModalVisible = ref(false)
const isImportModalVisible = ref(false)

async function handleAutoSchedule(tasks) {
  if (!tasks || tasks.length === 0) return
  
  try {
    isAutoScheduling.value = true
    
    const response = await axios.post(`${API_URL}/analytics/auto-schedule`, 
      { tasks, days: 3 },
      { headers: { 'Authorization': `Bearer ${userStore.token}` } }
    )
    
    if (response.data.success) {
      showNotification({
        type: 'success',
        message: response.data.message + (response.data.unscheduled.length > 0 ? `\n未安排: ${response.data.unscheduled.join(', ')}` : '')
      })
      fetchSchedules() // 刷新日程列表
      if (statsPanel.value) statsPanel.value.fetchStats() // 刷新统计数据
      isAutoScheduleModalVisible.value = false
    }
  } catch (err) {
    showNotification({ type: 'error', message: '智能排程失败，请稍后再试' })
  } finally {
    isAutoScheduling.value = false
  }
}

// ===== FAB 快速添加按钮相关方法 =====

/**
 * 切换 FAB 菜单显示状态
 */
function toggleFabMenu() {
  showFabMenu.value = !showFabMenu.value
}

/**
 * 打开语音输入模式
 */
function openNaturalLanguageMode() {
  showFabMenu.value = false
  activeTab.value = 'schedule'
  setTimeout(() => {
    const nlpInput = document.querySelector('.nlp-input-container')
    if (nlpInput) {
      nlpInput.scrollIntoView({ behavior: 'smooth', block: 'center' })
      const input = nlpInput.querySelector('input, textarea')
      if (input) input.focus()
    }
  }, 100)
}

/**
 * 打开手动创建表单
 */
function openManualForm() {
  showFabMenu.value = false
  activeTab.value = 'schedule'
  isFormVisible.value = true
}

/**
 * 打开智能排程模态框
 */
function openAutoScheduleModal() {
  showFabMenu.value = false
  activeTab.value = 'schedule'
  isAutoScheduleModalVisible.value = true
}

async function fetchDailyBriefing() {
  try {
    isBriefingLoading.value = true
    const response = await axios.get(`${API_URL}/analytics/daily-briefing`, {
      headers: { 'Authorization': `Bearer ${userStore.token}` }
    })
    dailyBriefing.value = response.data
  } catch (err) {
    console.error('获取每日摘要失败:', err)
  } finally {
    isBriefingLoading.value = false
  }
}

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
  markScheduleComplete,
  openEditModal,
  closeEditModal,
  saveEdit,
  resetScheduleForm
} = useSchedule(userStore, API_URL)

// 包装 addSchedule，成功后关闭模态框并显示通知
async function addSchedule() {
  console.log('📝 开始创建日程...')
  
  try {
    const result = await originalAddSchedule()
    console.log('✅ 创建结果:', result)
    
    // 【新增】检查是否有冲突
    if (result.conflict) {
      console.log('⚠️ 显示冲突对话框')
      conflictDialog.value = result.conflict
      return
    }
    
    // 先立即关闭模态框
    isFormVisible.value = false
    
    // 重置表单
    setTimeout(() => {
      resetScheduleForm()
    }, 100)
    
    // 显示通知
    if (result.success) {
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
  parseNaturalLanguage, // 新增：只解析不创建
  handleNaturalLanguageSubmit,
  startVoiceInput,
  stopRecording,
  handleCancelClick
} = useNaturalLanguage(API_URL, fetchSchedules)

// ✅ 新增：定义本地播报函数，解决模板中找不到 speak 的问题
function handleSpeak(text) {
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel() // 停止之前的播报
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = 'zh-CN'
    window.speechSynthesis.speak(utterance)
  } else {
    alert('您的浏览器不支持语音播报')
  }
}

/**
 * 处理"预填表单"按钮点击
 * 解析自然语言后切换到表单模式并填充数据
 */
async function handleParseAndFill() {
  console.log('📝 开始解析自然语言并预填表单...')
  
  // 获取时区偏移量
  const timezoneInfo = getTimezoneInfo()
  const timezoneOffset = timezoneInfo.offset
  
  // 调用解析接口
  const result = await parseNaturalLanguage(timezoneOffset)
  
  if (result && result.success) {
    console.log('✅ 解析成功，准备填充表单:', result.data)
    
    // 将解析结果填充到 newSchedule 对象中
    const parsedData = result.data
    
    // 构建表单数据
    newSchedule.value = {
      title: parsedData.title || '',
      content: parsedData.content || '',
      start_time: parsedData.start_time || '',
      end_time: parsedData.end_time || '',
      priority: parsedData.priority || 1,
      is_recurring: parsedData.is_recurring || false,
      recurring_pattern: parsedData.recurring_pattern || null,
      tags: parsedData.tags || []
    }
    
    console.log('📋 表单数据已填充:', newSchedule.value)
    
    // 关闭自然语言输入框
    isNaturalLanguageMode.value = false
    naturalLanguageInput.value = ''
    
    // 打开传统表单模式
    createMode.value = CREATE_MODES.FORM
    isFormVisible.value = true
    
    // 显示成功提示
    showNotification('success', `✨ AI 解析成功！请审查表单内容`)
    
    // 可选：语音播报
    handleSpeak(`已为您解析出${parsedData.title}，请确认信息是否正确`)
  } else {
    console.error('❌ 解析失败')
    showNotification('error', '❌ 解析失败，请重试或手动输入')
  }
}

// 强制创建日程（忽略冲突）
async function forceCreateSchedule() {
  if (!conflictDialog.value?.parsed_data) {
    return
  }
  
  try {
    const response = await axios.post(`${API_URL}/schedules/force-create`, {
      title: conflictDialog.value.parsed_data.title,
      start_time: conflictDialog.value.parsed_data.start_time,
      end_time: conflictDialog.value.parsed_data.end_time,
      content: naturalLanguageInput.value,
      priority: conflictDialog.value.parsed_data.priority || 1,
      is_recurring: conflictDialog.value.parsed_data.is_recurring || false,
      recurring_pattern: conflictDialog.value.parsed_data.recurring_pattern,
      tags: conflictDialog.value.parsed_data.tags
    }, {
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    })
    
    // 关闭冲突对话框
    conflictDialog.value = null
    
    // 刷新日程列表
    await fetchSchedules()
    
    // 显示成功通知
    showNotification('success', '✅ 日程已创建（已忽略冲突）！')
    
  } catch (error) {
    console.error('强制创建失败:', error)
    const errorMsg = error.response?.data?.error || '创建失败，请重试'
    showNotification('error', `❌ ${errorMsg}`)
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
} = useNotifications(userStore, API_URL)

// 页面状态
const activeTab = ref(NAVIGATION.tabs.SCHEDULE)
const isSidebarCollapsed = ref(false)
const currentTimezone = ref('')
const isLogoutModalVisible = ref(false)
const createMode = ref(CREATE_MODES.FORM)
const isFormVisible = ref(false)
const searchQuery = ref('')
const notification = ref({
  show: false,
  type: 'success',
  message: '',
  duration: 3000
})

const notificationFilter = ref('all')

// 通知统计与分组
const urgentCount = computed(() => {
  if (!recommendations.value) return 0
  return recommendations.value.filter(r => r.priority === 'urgent').length
})

const scheduleReminderCount = computed(() => {
  if (!recommendations.value) return 0
  return recommendations.value.filter(r => r.type === 'schedule_reminder').length
})

const filteredRecommendations = computed(() => {
  if (!recommendations.value) return []
  if (notificationFilter.value === 'all') return recommendations.value
  return recommendations.value.filter(r => r.type === notificationFilter.value)
})

const groupedNotifications = computed(() => {
  const groups = {}
  filteredRecommendations.value.forEach(rec => {
    if (!groups[rec.type]) {
      groups[rec.type] = []
    }
    groups[rec.type].push(rec)
  })
  return groups
})

// 获取通知图标
function getNotificationIcon(type) {
  const icons = {
    'schedule_reminder': Clock,
    'weather': Sun,
    'time_preference': Check,
    'balance': Sparkles,
    'info': Globe
  }
  return icons[type] || Bell
}

// 获取通知颜色
function getNotificationColor(type) {
  const colors = {
    'schedule_reminder': '#f97316',
    'weather': '#0ea5e9',
    'time_preference': '#10b981',
    'balance': '#8b5cf6',
    'info': '#667eea'
  }
  return colors[type] || '#667eea'
}

// 计算属性
const filteredSchedules = computed(() => {
  if (!searchQuery.value.trim()) {
    return schedules.value
  }
  
  const query = searchQuery.value.toLowerCase().trim()
  
  // 模糊搜索函数：检查 query 中的字符是否按顺序出现在 text 中
  const fuzzyMatch = (text, query) => {
    if (!text) return false
    text = text.toLowerCase()
    
    let queryIndex = 0
    for (let i = 0; i < text.length && queryIndex < query.length; i++) {
      if (text[i] === query[queryIndex]) {
        queryIndex++
      }
    }
    return queryIndex === query.length
  }
  
  return schedules.value.filter(schedule => 
    fuzzyMatch(schedule.title, query) ||
    (schedule.content && fuzzyMatch(schedule.content, query))
  )
})

// 将日程分为未过期和已过期两组
const upcomingSchedules = computed(() => {
  const now = new Date()
  // 添加30分钟缓冲时间，避免刚开始的日程立即进入历史记录
  const bufferTime = 30 * 60 * 1000 // 30分钟的毫秒数
  
  return filteredSchedules.value.filter(schedule => {
    const scheduleDate = new Date(schedule.start_time)
    const scheduleEndDate = schedule.end_time 
      ? new Date(schedule.end_time) 
      : new Date(scheduleDate.getTime() + 60 * 60 * 1000) // 默认1小时
    
    // 如果日程还未结束，或者在缓冲时间内，都算作"即将开始"
    return scheduleEndDate > new Date(now.getTime() - bufferTime)
  })
})

const pastSchedules = computed(() => {
  const now = new Date()
  // 与upcomingSchedules保持一致的缓冲逻辑
  const bufferTime = 30 * 60 * 1000 // 30分钟的毫秒数
  
  return filteredSchedules.value.filter(schedule => {
    const scheduleDate = new Date(schedule.start_time)
    const scheduleEndDate = schedule.end_time 
      ? new Date(schedule.end_time) 
      : new Date(scheduleDate.getTime() + 60 * 60 * 1000) // 默认1小时
    
    // 只有真正结束超过缓冲时间的日程才进入历史记录
    return scheduleEndDate <= new Date(now.getTime() - bufferTime)
  })
})

// 按日期分组 - 未过期日程
const groupedUpcomingSchedules = computed(() => {
  const groups = {}
  upcomingSchedules.value.forEach(schedule => {
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

// 按日期分组 - 已过期日程
const groupedPastSchedules = computed(() => {
  const groups = {}
  pastSchedules.value.forEach(schedule => {
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

const groupedSchedules = computed(() => {
  const groups = {}
  filteredSchedules.value.forEach(schedule => {
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

function goToStatistics() {
  router.push('/statistics')
}

// 导出日程
function openExportModal() {
  isExportModalVisible.value = true
}

// 导入日程
function openImportModal() {
  isImportModalVisible.value = true
}

// 监听用户信息变化，更新标题
watch(() => userStore.user, (newUser) => {
  if (newUser?.username) {
    document.title = `${newUser.username} - 我的日程`
  }
}, { immediate: true })

// 生命周期
onMounted(async () => {
  currentTimezone.value = getTimezoneInfo()

  // 获取每日智能摘要
  await fetchDailyBriefing()
  
  if (!userStore.user && userStore.token) {
    try {
      const response = await axios.get(`${API_URL}/auth/me`, {
        headers: { 'Authorization': `Bearer ${userStore.token}` }
      })
      userStore.user = response.data
      
      // 用户信息加载完成后更新标题
      document.title = `${userStore.user.username} - 我的日程`
    } catch (error) {
      console.error('恢复用户信息失败:', error)
      if (error.response?.status === 401) {
        userStore.logout()
        window.location.href = '/login'
      }
    }
  } else if (userStore.user?.username) {
    // 如果用户信息已存在，也更新标题
    document.title = `${userStore.user.username} - 我的日程`
  }
  
  fetchSchedules()
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

          <!-- 搜索框 -->
          <div v-if="activeTab === 'schedule'" class="search-container">
            <input 
              v-model="searchQuery" 
              type="text" 
              placeholder="搜索日程..." 
              class="search-input"
            />
            <span v-if="searchQuery" class="clear-search" @click="searchQuery = ''">×</span>
          </div>


          <button 
            v-if="activeTab === 'schedule'"
            class="add-btn-top" 
            @click="openCreateForm"
          >
            <PlusCircle :size="20" />
            <span>新建日程</span>
          </button>
          
          <button 
            v-if="activeTab === 'schedule'"
            class="auto-schedule-btn" 
            @click="isAutoScheduleModalVisible = true"
          >
            <Sparkles :size="20" />
            <span>智能排程</span>
          </button>
          
          <button 
            v-if="activeTab === 'schedule'"
            class="export-btn" 
            @click="openExportModal"
          >
            <Download :size="20" />
            <span>导出日程</span>
          </button>
          
          <button 
            v-if="activeTab === 'schedule'"
            class="import-btn" 
            @click="openImportModal"
          >
            <Upload :size="20" />
            <span>导入日程</span>
          </button>
        </div>
      </header>

      <!-- 日程页面 -->
      <div v-if="activeTab === 'schedule'" class="tab-content">
        <!-- ✅ 优化：每日智能摘要卡片 (Modern UI) -->
        <DailyBriefing
          :dailyBriefing="dailyBriefing"
          :isBriefingLoading="isBriefingLoading"
          :API_URL="API_URL"
          :token="userStore.token"
          @refresh-briefing="fetchDailyBriefing"
        />
        
        <!-- 统计面板 -->
        <DashboardStats 
          ref="statsPanel"
          :API_URL="API_URL"
          :token="userStore.token"
        />
        
        <ScheduleList
          :schedules="filteredSchedules"
          :upcomingSchedules="upcomingSchedules"
          :pastSchedules="pastSchedules"
          :groupedUpcomingSchedules="groupedUpcomingSchedules"
          :groupedPastSchedules="groupedPastSchedules"
          :groupedSchedules="groupedSchedules"
          :isLoading="isLoading"
          :error="error"
          :searchQuery="searchQuery"
          @edit="openEditModal"
          @delete="deleteSchedule"
          @complete="markScheduleComplete"
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
        <NotificationsCenter
          :recommendations="recommendations"
          :API_URL="API_URL"
          :token="userStore.token"
          @navigate-to-schedule="navigateToSchedule"
          @load-recommendations="loadRecommendations"
        />
      </div>

      <!-- 设置页面 -->
      <div v-if="activeTab === 'settings'" class="tab-content">
        <SettingsPanel
          :user="userStore.user"
          :currentTimezone="currentTimezone"
        />
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
          @parse-and-fill="handleParseAndFill"
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
    <LogoutConfirmDialog
      :is-visible="isLogoutModalVisible"
      @confirm="handleLogout"
      @cancel="isLogoutModalVisible = false"
    />

    <!-- 弹窗：导出日程 -->
    <ScheduleExport
      :visible="isExportModalVisible"
      :API_URL="API_URL"
      :token="userStore.token"
      @close="isExportModalVisible = false"
    />

    <!-- 弹窗：导入日程 -->
    <ScheduleImport
      :visible="isImportModalVisible"
      :API_URL="API_URL"
      :token="userStore.token"
      @close="isImportModalVisible = false"
      @import-success="fetchSchedules"
    />

     <!-- 冲突解决对话框 -->
    <transition name="fade">
      <div v-if="conflictDialogVisible" class="form-overlay" @click.self="conflictDialogVisible = false">
        <ConflictDialog
          :conflict-info="conflictInfo"
          @resolve="handleResolveConflict"
          @cancel="conflictDialogVisible = false"
        />
      </div>
    </transition>

    <!-- 弹窗：智能排程助手 -->
    <AutoScheduleModal
      :is-visible="isAutoScheduleModalVisible"
      :is-processing="isAutoScheduling"
      :API_URL="API_URL"
      :token="userStore.token"
      @close="isAutoScheduleModalVisible = false"
      @submit="handleAutoSchedule"
    />
    
    <!-- FAB 快速添加按钮 -->
    <FloatingActionButton
      :show-menu="showFabMenu"
      @toggle-menu="toggleFabMenu"
      @voice-input="openNaturalLanguageMode"
      @manual-input="openManualForm"
      @auto-schedule="openAutoScheduleModal"
    />
  </div>
</template>



<style scoped>
/* ✅ 优化：现代简报卡片样式 */
.briefing-card-modern {
  display: flex;
  gap: 20px;
  background: white;
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 24px;
  border: 1px solid #eef2f7;
  box-shadow: 0 10px 30px -10px rgba(102, 126, 234, 0.15);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.briefing-card-modern::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: linear-gradient(to bottom, #667eea, #764ba2);
}

.briefing-card-modern:hover {
  transform: translateY(-4px);
  box-shadow: 0 20px 40px -10px rgba(102, 126, 234, 0.25);
}

.briefing-icon-wrapper {
  flex-shrink: 0;
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, #f6f9fc 0%, #eef2f9 100%);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: inset 0 2px 4px rgba(255, 255, 255, 0.8);
}

.briefing-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.briefing-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.briefing-header-row h3 {
  margin: 0;
  font-size: 1.25rem;
  color: #2d3748;
  font-weight: 700;
  letter-spacing: -0.025em;
}

.speak-btn-mini {
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 1.2rem;
  opacity: 0.6;
  transition: opacity 0.2s;
  padding: 4px;
}

.speak-btn-mini:hover {
  opacity: 1;
}

.briefing-text {
  margin: 0 0 16px 0;
  color: #4a5568;
  font-size: 1rem;
  line-height: 1.6;
}

.briefing-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  padding-top: 12px;
  border-top: 1px dashed #e2e8f0;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.875rem;
  color: #718096;
  font-weight: 500;
}

.weather-item {
  color: #ed8936;
}

.refresh-briefing {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 6px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 5px rgba(118, 75, 162, 0.2);
}

.refresh-briefing:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 4px 8px rgba(118, 75, 162, 0.3);
}

.refresh-briefing:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  filter: grayscale(0.5);
}

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

.search-container {
  position: relative;
  display: flex;
  align-items: center;
}

.search-input {
  padding: 0.6rem 2.5rem 0.6rem 1rem;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  font-size: 0.9rem;
  width: 250px;
  transition: all 0.2s;
  background-color: #f8f9fe;
}

.search-input:focus {
  outline: none;
  border-color: #5E72E4;
  background-color: white;
  box-shadow: 0 0 0 3px rgba(94, 114, 228, 0.1);
}

.search-input::placeholder {
  color: #adb5bd;
}

.clear-search {
  position: absolute;
  right: 10px;
  cursor: pointer;
  color: #adb5bd;
  font-size: 1.2rem;
  line-height: 1;
  padding: 2px 6px;
  border-radius: 50%;
  transition: all 0.2s;
}

.clear-search:hover {
  background-color: #e9ecef;
  color: #32325D;
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

/* ✨ 智能排程按钮 - 科技感优化 */
.auto-schedule-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 0.6rem 1.2rem;
  border-radius: 25px;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 15px rgba(118, 75, 162, 0.3);
  position: relative;
  overflow: hidden;
}

/* 按钮光效动画 */
.auto-schedule-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: 0.5s;
}

.auto-schedule-btn:hover {
  transform: translateY(-3px) scale(1.02);
  box-shadow: 0 8px 25px rgba(118, 75, 162, 0.5);
}

.auto-schedule-btn:hover::before {
  left: 100%;
}

.auto-schedule-btn svg {
  transition: transform 0.3s ease;
}

.auto-schedule-btn:hover svg {
  transform: rotate(15deg) scale(1.1);
}

/* 导出按钮 */
.export-btn {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border: none;
  padding: 0.6rem 1.2rem;
  border-radius: 25px;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
  position: relative;
  overflow: hidden;
}

.export-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: 0.5s;
}

.export-btn:hover {
  transform: translateY(-3px) scale(1.02);
  box-shadow: 0 8px 25px rgba(16, 185, 129, 0.5);
}

.export-btn:hover::before {
  left: 100%;
}

.export-btn svg {
  transition: transform 0.3s ease;
}

.export-btn:hover svg {
  transform: scale(1.1);
}

/* 导入按钮 */
.import-btn {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  border: none;
  padding: 0.6rem 1.2rem;
  border-radius: 25px;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
  position: relative;
  overflow: hidden;
}

.import-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: 0.5s;
}

.import-btn:hover {
  transform: translateY(-3px) scale(1.02);
  box-shadow: 0 8px 25px rgba(59, 130, 246, 0.5);
}

.import-btn:hover::before {
  left: 100%;
}

.import-btn svg {
  transition: transform 0.3s ease;
}

.import-btn:hover svg {
  transform: scale(1.1);
}

.tab-content {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
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


.replay-btn {
  background: none;
  border: 1px solid #5E72E4;
  color: #5E72E4;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 0.8rem;
  cursor: pointer;
  margin-left: auto;
  transition: all 0.2s;
}
.replay-btn:hover {
  background-color: #5E72E4;
  color: white;
}

/* ===== 铃铛动画优化 ===== */
.bell-icon {
  animation: ring 2s ease-in-out infinite;
}

@keyframes ring {
  0%, 100% { 
    transform: rotate(0); 
  }
  10%, 30% { 
    transform: rotate(-10deg); 
  }
  20%, 40% { 
    transform: rotate(10deg); 
  }
  50% { 
    transform: rotate(0); 
  }
}

/* ===== 优先级徽章脉冲动画 ===== */
.reminder-urgent .notification-icon {
  animation: urgent-pulse 2s ease-in-out infinite;
}

@keyframes urgent-pulse {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(244, 67, 54, 0.4);
  }
  50% {
    box-shadow: 0 0 0 10px rgba(244, 67, 54, 0);
  }
}

/* ===== 分组标题悬停效果 ===== */
.group-header {
  transition: all 0.2s;
}

.group-header:hover {
  background-color: rgba(94, 114, 228, 0.05);
  padding-left: 0.5rem;
  border-radius: 6px;
}

/* ===== 进度条渐变动画 ===== */
.progress-bar {
  position: relative;
  overflow: hidden;
}

.progress-bar::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  right: 0;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255,255,255,0.3),
    transparent
  );
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

/* ===== 智能排程弹窗样式 ===== */
.auto-schedule-modal {
  max-width: 500px;
  border-radius: 16px;
}

.modal-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 1rem;
  color: #2d3748;
}

.modal-desc {
  font-size: 0.9rem;
  color: #718096;
  margin-bottom: 1rem;
  line-height: 1.5;
}

.auto-schedule-textarea {
  width: 100%;
  min-height: 150px;
  padding: 12px;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  resize: vertical;
  font-family: inherit;
  font-size: 0.95rem;
  transition: all 0.2s;
  background: #f8fafc;
}

.auto-schedule-textarea:focus {
  outline: none;
  border-color: #667eea;
  background: white;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.schedule-preview-hint {
  margin-top: 0.75rem;
  font-size: 0.85rem;
  color: #667eea;
  background: #f6f9fc;
  padding: 8px 12px;
  border-radius: 6px;
  border-left: 3px solid #667eea;
}

.btn-auto-schedule {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-auto-schedule:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(118, 75, 162, 0.3);
}

.btn-auto-schedule:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* ===== FAB 快速添加按钮 ===== */
.fab-container {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  z-index: 1000;
}

.fab-main-btn {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  font-size: 1.5rem;
}

.fab-main-btn:hover {
  transform: scale(1.1) rotate(90deg);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
}

.fab-menu {
  position: absolute;
  bottom: 70px;
  right: 0;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  animation: slideUp 0.3s ease;
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

.fab-menu-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1.25rem;
  background: white;
  border: none;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
  font-size: 0.9rem;
  color: #32325D;
  font-weight: 500;
}

.fab-menu-item:hover {
  transform: translateX(-5px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  background: #f8f9fe;
}

.fab-menu-item .menu-icon {
  font-size: 1.2rem;
}
</style>
