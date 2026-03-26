<script setup>
import { ref, onMounted, computed } from 'vue'
import { Calendar, PlusCircle, Sun, Edit2, Trash2, Check, LogOut, Globe, MapPin, Loader } from 'lucide-vue-next'
import axios from 'axios'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()

// --- 状态管理 ---
const API_URL = 'http://127.0.0.1:5000/api'
const schedules = ref([])
const newSchedule = ref({
  title: '',
  content: '',
  start_time: getCurrentDateTime(),
  priority: 1,
  is_recurring: false,
  recurring_pattern: ''
})
const isLoading = ref(true)
const error = ref(null)
const isFormVisible = ref(false)
const editingSchedule = ref(null)
const editForm = ref({
  title: '',
  content: '',
  start_time: ''
})
const currentTimezone = ref('')
const isLogoutModalVisible = ref(false)

const isNaturalLanguageMode = ref(false)
const naturalLanguageInput = ref('')
const isProcessingNL = ref(false)

// 新增：录音状态
const isRecording = ref(false)
const recordingDuration = ref(0)
const recordingTimer = ref(null)

const isAIProcessing = ref(false)
const recommendations = ref([])
const showRecommendations = ref(false)
const conflictDialog = ref(null)
const showConflictResolution = ref(false)
const createMode = ref('form') // 'form' 或 'natural'

// 新增：导航状态
const activeTab = ref('schedule') // 'schedule', 'profile', 'settings'
const isSidebarCollapsed = ref(false)




// 新增：个人信息编辑
const isProfileEditModalVisible = ref(false)
const profileForm = ref({
  username: '',
  email: '',
  location: '',
  location_name: '',
  weather_alerts_enabled: true
})

const isLocating = ref(false)
const locationStatus = ref('')









// --- 计算属性 ---
const groupedSchedules = computed(() => {
  const groups = {}
  schedules.value.forEach(schedule => {
    const date = new Date(schedule.start_time).toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' })
    if (!groups[date]) {
      groups[date] = []
    }
    groups[date].push(schedule)
  })
  return groups
})

// --- API 调用 ---
async function fetchSchedules() {
  try {
    isLoading.value = true
    const response = await axios.get(`${API_URL}/schedules`)
    schedules.value = response.data.sort((a, b) => new Date(a.start_time) - new Date(b.start_time))
    error.value = null
  } catch (err) {
    if (err.response?.status === 401) {
      userStore.logout()
      router.push('/login')
      return
    }
    error.value = '无法加载日程。请确保后端服务已启动。'
    console.error(err)
  } finally {
    isLoading.value = false
  }
}

async function addSchedule() {
  if (!newSchedule.value.title || !newSchedule.value.start_time) {
    alert('标题和开始时间不能为空！')
    return
  }
  try {
    const payload = {
      ...newSchedule.value,
      start_time: new Date(newSchedule.value.start_time).toISOString(),
      priority: parseInt(newSchedule.value.priority),
      is_recurring: newSchedule.value.is_recurring || false,
      recurring_pattern: newSchedule.value.is_recurring ? (newSchedule.value.recurring_pattern || 'weekly') : null
    }
    
    console.log('创建日程 payload:', payload)
    await axios.post(`${API_URL}/schedules`, payload)
    newSchedule.value = { 
      title: '', 
      content: '', 
      start_time: getCurrentDateTime(),
      priority: 1,
      is_recurring: false,
      recurring_pattern: ''
    }
    isFormVisible.value = false
    fetchSchedules()
  } catch (err) {
    alert('添加失败，请检查控制台信息。')
    console.error(err)
  }
}

async function deleteSchedule(id) {
  if (!confirm('确定要删除这个日程吗？')) {
    return
  }
  try {
    await axios.delete(`${API_URL}/schedules/${id}`)
    fetchSchedules()
  } catch (err) {
    alert('删除失败，请重试。')
    console.error(err)
  }
}

function openEditModal(schedule) {
  editingSchedule.value = schedule
  
  // 将 ISO 字符串转换为本地时间显示
  const scheduleDate = new Date(schedule.start_time)
  const year = scheduleDate.getFullYear()
  const month = String(scheduleDate.getMonth() + 1).padStart(2, '0')
  const day = String(scheduleDate.getDate()).padStart(2, '0')
  const hours = String(scheduleDate.getHours()).padStart(2, '0')
  const minutes = String(scheduleDate.getMinutes()).padStart(2, '0')
  
  editForm.value = {
    title: schedule.title,
    content: schedule.content || '',
    start_time: `${year}-${month}-${day}T${hours}:${minutes}`,
    priority: schedule.priority || 1,
    is_recurring: schedule.is_recurring || false,
    recurring_pattern: schedule.recurring_pattern || ''
  }
}

function closeEditModal() {
  editingSchedule.value = null
  editForm.value = { title: '', content: '', start_time: '' }
}

async function saveEdit() {
  if (!editForm.value.title || !editForm.value.start_time) {
    alert('标题和开始时间不能为空！')
    return
  }
  
  try {
    const payload = {
      ...editForm.value,
      start_time: new Date(editForm.value.start_time).toISOString(),
      priority: parseInt(editForm.value.priority),
      is_recurring: !!editForm.value.is_recurring,
      recurring_pattern: editForm.value.is_recurring ? (editForm.value.recurring_pattern || 'weekly') : null
    }
    
    console.log('更新日程 payload:', payload)
    await axios.put(`${API_URL}/schedules/${editingSchedule.value.id}`, payload)
    closeEditModal()
    fetchSchedules()
  } catch (err) {
    console.error('更新失败:', err)
    const errorMsg = err.response?.data?.error || err.message || '更新失败，请重试'
    alert(`更新失败：${errorMsg}`)
  }
}

function formatDateForInput(isoString) {
  if (!isoString) return ''
  const date = new Date(isoString)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day}T${hours}:${minutes}`
}

function getCurrentDateTime() {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  const hours = String(now.getHours()).padStart(2, '0')
  const minutes = String(now.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day}T${hours}:${minutes}`
}

function formatDate(isoString, format = 'time') {
  if (!isoString) return ''
  const date = new Date(isoString)
  if (format === 'time') {
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false })
  }
  return date.toLocaleString('zh-CN')
}

function getTimezoneInfo() {
  const now = new Date()
  const timezoneOffset = -now.getTimezoneOffset()
  const offsetHours = Math.floor(Math.abs(timezoneOffset) / 60)
  const offsetMinutes = Math.abs(timezoneOffset) % 60
  
  let timezoneName = ''
  let regionName = ''
  
  if (timezoneOffset === 480) {
    timezoneName = '东八区 (UTC+8)'
    regionName = '北京时间'
  } else if (timezoneOffset === 540) {
    timezoneName = '东九区 (UTC+9)'
    regionName = '东京时间'
  } else if (timezoneOffset === 330) {
    timezoneName = '东五区半 (UTC+5:30)'
    regionName = '印度标准时间'
  } else if (timezoneOffset === 0) {
    timezoneName = '中时区 (UTC+0)'
    regionName = '格林尼治时间'
  } else if (timezoneOffset === -300) {
    timezoneName = '西五区 (UTC-5)'
    regionName = '纽约时间'
  } else if (timezoneOffset === -480) {
    timezoneName = '西八区 (UTC-8)'
    regionName = '洛杉矶时间'
  } else {
    const sign = timezoneOffset >= 0 ? '+' : '-'
    timezoneName = `UTC${sign}${offsetHours}:${String(offsetMinutes).padStart(2, '0')}`
    regionName = '本地时间'
  }
  
  return `${regionName} - ${timezoneName}`
}


// 新增：获取标签标题
function getTabTitle() {
  const titles = {
    'schedule': '我的日程',
    'profile': '个人信息',
    'notifications': '消息通知',
    'settings': '系统设置'
  }
  return titles[activeTab.value] || '我的日程'
}

// 新增：获取通知标题
function getNotificationTitle(type) {
  const titles = {
    'weather': '🌤️ 天气提示',
    'time_preference': '⏰ 时间偏好',
    'balance': '😌 平衡建议',
    'info': 'ℹ️ 提示信息'
  }
  return titles[type] || '智能推荐'
}

// 新增：打开个人资料编辑
function openProfileEdit() {
  profileForm.value = {
    username: userStore.user?.username || '',
    email: userStore.user?.email || '',
    location: userStore.user?.location || '',
    location_name: userStore.user?.location_name || '',
    weather_alerts_enabled: userStore.user?.weather_alerts_enabled !== false
  }
  isProfileEditModalVisible.value = true
}
  


// 新增：保存个人资料
async function saveProfile() {
  try {
    const response = await axios.put(`${API_URL}/users/profile`, profileForm.value, {
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    })
    userStore.user = response.data
    isProfileEditModalVisible.value = false
    alert('个人资料已更新')
  } catch (error) {
    console.error('更新失败:', error)
    alert('更新失败，请重试')
  }
}

async function locateUser() {
  if (!navigator.geolocation) {
    alert('您的浏览器不支持地理定位功能')
    return
  }
  
  isLocating.value = true
  locationStatus.value = '正在获取您的位置...'
  
  navigator.geolocation.getCurrentPosition(
    async (position) => {
      try {
        const { latitude, longitude } = position.coords
        
        locationStatus.value = '正在查询位置信息...'
        
        const response = await axios.post(`${API_URL}/location/geocode`, {
          latitude,
          longitude
        }, {
          headers: {
            'Authorization': `Bearer ${userStore.token}`
          }
        })
        
        const { city_location_id, city_name } = response.data
        
        profileForm.value.location = city_location_id
        profileForm.value.location_name = city_name
        locationStatus.value = `定位成功！${city_name}`
        
        setTimeout(() => {
          locationStatus.value = ''
        }, 3000)
        
      } catch (error) {
        console.error('定位失败:', error)
        locationStatus.value = '定位失败：' + (error.response?.data?.error || '网络错误')
        setTimeout(() => {
          locationStatus.value = ''
        }, 5000)
      } finally {
        isLocating.value = false
      }
    },
    (error) => {
      isLocating.value = false
      locationStatus.value = '定位失败：' + error.message
      setTimeout(() => {
        locationStatus.value = ''
      }, 5000)
    },
    {
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 300000
    }
  )
}

async function refreshWeather() {
  if (!profileForm.value.location) {
    alert('请先设置城市位置')
    return
  }
  
  try {
    const response = await axios.post(`${API_URL}/weather/update-all`, {}, {
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    })
    
    alert(response.data.message)
    await fetchSchedules()
  } catch (error) {
    console.error('刷新天气失败:', error)
    alert('刷新天气失败，请重试')
  }
}

async function refreshWeatherFromProfile() {
  if (!userStore.user?.location) {
    alert('请先在个人资料中设置城市位置')
    openProfileEdit()
    return
  }
  
  try {
    const response = await axios.post(`${API_URL}/weather/update-all`, {}, {
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    })
    
    alert(response.data.message)
    await fetchSchedules()
  } catch (error) {
    console.error('刷新天气失败:', error)
    alert('刷新天气失败，请重试')
  }
}


function handleLogout() {
  userStore.logout()
  isLogoutModalVisible.value = false
  window.location.href = '/login'
}

async function handleNaturalLanguageSubmit() {
  if (!naturalLanguageInput.value.trim()) {
    alert('请输入指令内容')
    return
  }
  
  isProcessingNL.value = true
  
  try {
    // 获取用户时区信息
    const timezoneOffset = -new Date().getTimezoneOffset() // 分钟
    const timezoneHours = Math.floor(Math.abs(timezoneOffset) / 60)
    const timezoneMinutes = Math.abs(timezoneOffset) % 60
    const sign = timezoneOffset >= 0 ? '+' : '-'
    const timezoneStr = `UTC${sign}${timezoneHours}:${String(timezoneMinutes).padStart(2, '0')}`
    
    const response = await axios.post(`${API_URL}/schedules/natural-language`, {
      text: naturalLanguageInput.value,
      timezone: timezoneStr,
      timezone_offset: timezoneOffset // 以分钟为单位的偏移量
    })
    
    naturalLanguageInput.value = ''
    isNaturalLanguageMode.value = false
    fetchSchedules()
    
    // 显示 AI 处理结果
    if (response.data.ai_parsed) {
      alert(`✨ AI 智能解析成功！日程已创建：${response.data.schedule.title}`)
    } else {
      alert(`日程已创建：${response.data.schedule.title}`)
    }
  } catch (error) {
    if (error.response?.status === 409) {
      conflictDialog.value = error.response.data
    } else {
      alert('解析失败，请重试')
      console.error(error)
    }
  } finally {
    isProcessingNL.value = false
  }
}


async function loadRecommendations() {
  try {
    const response = await axios.get(`${API_URL}/recommendations`)
    recommendations.value = response.data.recommendations
    showRecommendations.value = true
  } catch (error) {
    console.error('加载推荐失败:', error)
  }
}

function acceptConflictSolution(conflictData) {
  showConflictResolution.value = false
  conflictDialog.value = null
  fetchSchedules()
}


async function startVoiceInput() {
  
  if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
    alert('您的浏览器不支持语音识别，请使用 Chrome、Edge 或其他基于 Chromium 的浏览器')
    return
  }
  
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
  const recognition = new SpeechRecognition()
  
  recognition.lang = 'zh-CN'
  recognition.continuous = false
  recognition.interimResults = false
  recognition.maxAlternatives = 1
  
  recognition.onstart = () => {
    console.log('语音识别已启动')
    isRecording.value = true
    recordingDuration.value = 0
    
    if (recordingTimer.value) {
      clearInterval(recordingTimer.value)
    }
    
    recordingTimer.value = setInterval(() => {
      recordingDuration.value++
    }, 1000)
  }
  
  recognition.onend = () => {
    console.log('语音识别已结束')
    isRecording.value = false
    
    if (recordingTimer.value) {
      clearInterval(recordingTimer.value)
      recordingTimer.value = null
    }
  }
  
  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript
    naturalLanguageInput.value = transcript
    console.log('识别结果:', transcript)
  }
  
  recognition.onerror = (event) => {
    console.error('语音识别错误:', event.error)
    
    let errorMessage = ''
    switch(event.error) {
      case 'no-speech':
        errorMessage = '未检测到语音，请对着麦克风说话'
        break
      case 'audio-capture':
        errorMessage = '无法访问麦克风，请检查权限设置'
        break
      case 'not-allowed':
        errorMessage = '麦克风权限被拒绝，请在浏览器设置中允许麦克风权限'
        break
      case 'network':
        errorMessage = '网络错误，请检查网络连接后重试'
        break
      case 'aborted':
        errorMessage = '语音识别已取消'
        break
      default:
        errorMessage = '语音识别失败：' + event.error
    }
    
    alert(errorMessage)
    
    isRecording.value = false
    if (recordingTimer.value) {
      clearInterval(recordingTimer.value)
      recordingTimer.value = null
    }
  }
  
  try {
    recognition.start()
  } catch (error) {
    console.error('启动语音识别失败:', error)
    alert('无法启动语音识别，请确保麦克风权限已允许')
    isRecording.value = false
    if (recordingTimer.value) {
      clearInterval(recordingTimer.value)
      recordingTimer.value = null
    }
  }
}

function formatRecordingTime(seconds) {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
}

function cancelConflictResolution() {
  conflictDialog.value = null
}

function stopRecording() {
  isRecording.value = false
  if (recordingTimer.value) {
    clearInterval(recordingTimer.value)
    recordingTimer.value = null
  }
  recordingDuration.value = 0
}


function toggleNaturalLanguageMode() {
  isNaturalLanguageMode.value = !isNaturalLanguageMode.value
  if (isNaturalLanguageMode.value) {
    isFormVisible.value = false
  }
}

function toggleCreateMode() {
  createMode.value = createMode.value === 'form' ? 'natural' : 'form'
}

function openCreateForm() {
  isFormVisible.value = true
  createMode.value = 'form'
  // 重置为默认值
  newSchedule.value = { 
    title: '', 
    content: '', 
    start_time: getCurrentDateTime(),
    priority: 1,
    is_recurring: false,
    recurring_pattern: ''
  }
}

function openNaturalLanguageForm() {
  isNaturalLanguageMode.value = true
  createMode.value = 'natural'
  isFormVisible.value = true
  naturalLanguageInput.value = ''
}

function handleCancelClick() {
  // 如果正在录音，先停止录音
  if (isRecording.value) {
    stopRecording()
  }
  // 关闭自然语言模式
  isNaturalLanguageMode.value = false
  createMode.value = 'form'
  // 清空输入内容
  naturalLanguageInput.value = ''
}




onMounted(async () => {
  currentTimezone.value = getTimezoneInfo()
  
  // 如果 userStore 中没有用户信息，尝试从后端获取
  if (!userStore.user && userStore.token) {
    try {
      const response = await axios.get(`${API_URL}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${userStore.token}`
        }
      })
      userStore.user = response.data
      console.log('用户信息已恢复:', userStore.user.username)
    } catch (error) {
      console.error('恢复用户信息失败:', error)
      if (error.response?.status === 401) {
        userStore.logout()
        window.location.href = '/login'
      }
    }
  }
  
  fetchSchedules()
})

// 添加 onUnmounted 来清理定时器
import { onUnmounted } from 'vue'

onUnmounted(() => {
  if (recordingTimer.value) {
    clearInterval(recordingTimer.value)
    recordingTimer.value = null
  }
})
</script>

<template>
  <div class="home-container">
    <!-- 左侧导航栏 -->
    <aside class="sidebar" :class="{ 'collapsed': isSidebarCollapsed }">
      <div class="sidebar-header">
        <h2 v-if="!isSidebarCollapsed">日程助手</h2>
        <button class="collapse-btn" @click="isSidebarCollapsed = !isSidebarCollapsed">
          {{ isSidebarCollapsed ? '→' : '←' }}
        </button>
      </div>
      
      <nav class="sidebar-nav">
        <a 
          href="#" 
          class="nav-item" 
          :class="{ 'active': activeTab === 'schedule' }"
          @click.prevent="activeTab = 'schedule'"
        >
          <Calendar :size="20" />
          <span v-if="!isSidebarCollapsed">你的日程</span>
        </a>
        
        <a 
          href="#" 
          class="nav-item" 
          :class="{ 'active': activeTab === 'profile' }"
          @click.prevent="activeTab = 'profile'"
        >
          <User :size="20" />
          <span v-if="!isSidebarCollapsed">个人信息</span>
        </a>
        
        <a 
          href="#" 
          class="nav-item" 
          :class="{ 'active': activeTab === 'notifications' }"
          @click.prevent="activeTab = 'notifications'"
        >
          <Bell :size="20" />
          <span v-if="!isSidebarCollapsed">消息通知</span>
          <span v-if="!isSidebarCollapsed && recommendations.length > 0" class="badge">
            {{ recommendations.length }}
          </span>
        </a>
        
        <a 
          href="#" 
          class="nav-item" 
          :class="{ 'active': activeTab === 'settings' }"
          @click.prevent="activeTab = 'settings'"
        >
          <Settings :size="20" />
          <span v-if="!isSidebarCollapsed">系统设置</span>
        </a>
      </nav>
      
      <div class="sidebar-footer">
        <div class="user-info-mini" v-if="!isSidebarCollapsed">
          <div class="avatar">{{ userStore.user?.username?.charAt(0).toUpperCase() }}</div>
          <div class="user-name">{{ userStore.user?.username }}</div>
        </div>
        <button class="logout-btn-mini" @click="isLogoutModalVisible = true" title="退出登录">
          <LogOut :size="18" />
        </button>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="main-content">
      <!-- 顶部栏 -->
      <header class="top-bar">
        <h1>{{ getTabTitle() }}</h1>
        <div class="top-bar-actions">
          <span class="current-time">{{ currentTimezone }}</span>
          <button 
            class="add-btn-top" 
            v-if="activeTab === 'schedule'"
            @click="openCreateForm"
          >
            <PlusCircle :size="20" />
            <span>新建日程</span>
          </button>
        </div>
      </header>

      <!-- 日程管理页面 -->
      <div v-if="activeTab === 'schedule'" class="tab-content">
        <!-- ... existing schedule content ... -->
        <div class="content-body">
          <div v-if="isLoading" class="loading-spinner"></div>
          <div v-if="error" class="error-msg">{{ error }}</div>
          
          <div v-if="!isLoading && !error && schedules.length === 0" class="empty-state">
            <Sun :size="64" />
            <h2>今日无事，心随云飞</h2>
            <p>点击上方"新建日程"按钮，开始你的第一个日程吧！</p>
          </div>

          <transition-group name="list" tag="div" v-else>
            <div v-for="(schedulesOnDate, date) in groupedSchedules" :key="date" class="date-group">
              <h3 class="date-header">{{ date }}</h3>
              <ul class="schedule-list">
                <li v-for="schedule in schedulesOnDate" :key="schedule.id" class="schedule-item">
                  <div class="item-time">{{ formatDate(schedule.start_time, 'time') }}</div>
                  <div class="item-content">
                    <h4>{{ schedule.title }}</h4>
                    <p v-if="schedule.content">{{ schedule.content }}</p>
                    <div v-if="schedule.weather_info" class="item-weather">
                      {{ schedule.weather_info }}
                    </div>
                    <div v-if="schedule.priority >= 4" class="item-priority priority-high">
                      🔴 高优先级
                    </div>
                    <div v-if="schedule.is_recurring" class="item-recurring">
                      🔄 {{ schedule.recurring_pattern === 'weekly' ? '每周重复' : schedule.recurring_pattern === 'daily' ? '每天重复' : '每月重复' }}
                    </div>
                  </div>
                  <div class="item-actions">
                    <button class="action-btn" @click="openEditModal(schedule)" title="编辑">
                      <Edit2 :size="20"/>
                    </button>
                    <button class="action-btn action-btn-delete" @click="deleteSchedule(schedule.id)" title="删除">
                      <Trash2 :size="20"/>
                    </button>
                  </div>
                </li>
              </ul>
            </div>
          </transition-group>
        </div>
      </div>

      <!-- 个人信息页面 -->
      <div v-if="activeTab === 'profile'" class="tab-content">
        <div class="profile-card">
          <div class="profile-header">
            <div class="profile-avatar">
              {{ userStore.user?.username?.charAt(0).toUpperCase() }}
            </div>
            <div class="profile-info">
              <h2>{{ userStore.user?.username }}</h2>
              <p class="profile-email">{{ userStore.user?.email || '未设置邮箱' }}</p>
              <p class="profile-location" v-if="userStore.user?.location_name">
                📍 {{ userStore.user.location_name }}
              </p>
              <p class="profile-location" v-else-if="userStore.user?.location">
                📍 城市 ID: {{ userStore.user.location }}
              </p>
              <p class="profile-join-date">
                注册时间：{{ userStore.user?.created_at ? new Date(userStore.user.created_at).toLocaleDateString('zh-CN') : '未知' }}
              </p>
            </div>
            <div class="profile-actions">
              <button class="edit-profile-btn" @click="openProfileEdit">
                <Edit2 :size="18" />
                <span>编辑资料</span>
              </button>
              <button class="refresh-weather-btn" @click="refreshWeatherFromProfile" title="根据当前位置更新所有日程天气">
                <Sun :size="18" />
                <span>更新天气</span>
              </button>
            </div>
          </div>
          
          <div class="profile-stats">
            <div class="stat-item">
              <div class="stat-value">{{ schedules.length }}</div>
              <div class="stat-label">日程总数</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ schedules.filter(s => s.priority >= 4).length }}</div>
              <div class="stat-label">高优先级</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ schedules.filter(s => s.is_recurring).length }}</div>
              <div class="stat-label">重复日程</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 消息通知页面 -->
      <div v-if="activeTab === 'notifications'" class="tab-content">
        <div class="notifications-panel">
          <button class="refresh-btn" @click="loadRecommendations">
            <Check :size="18" />
            <span>刷新推荐</span>
          </button>
          
          <div v-if="recommendations.length === 0" class="empty-notifications">
            <Bell :size="64" />
            <h3>暂无新消息</h3>
            <p>点击"刷新推荐"获取智能建议</p>
          </div>
          
          <div v-else class="notifications-list">
            <div v-for="(rec, index) in recommendations" :key="index" class="notification-item" :class="'type-' + rec.type">
              <div class="notification-icon">
                <Sun v-if="rec.type === 'weather'" :size="24" />
                <Check v-else-if="rec.type === 'time_preference'" :size="24" />
                <Globe v-else :size="24" />
              </div>
              <div class="notification-content">
                <h4>{{ getNotificationTitle(rec.type) }}</h4>
                <p>{{ rec.message }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 系统设置页面 -->
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
              北京 (101010100)
            </div>
          </div>
          
          <div class="setting-item">
            <div class="setting-label">
              <Bell :size="20" />
              <span>天气提醒</span>
            </div>
            <label class="switch">
              <input type="checkbox" checked>
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

    <!-- 各种弹窗保持不变... -->
    <!-- 智能推荐面板（已移除，整合到通知页面） -->
    <!-- 传统表单创建界面 -->
    <transition name="fade">
      <div v-if="isFormVisible && createMode === 'form'" class="form-overlay" @click.self="isFormVisible = false">
        <!-- ... existing form content ... -->
        <div class="form-container">
          <div class="form-header">
            <h2><PlusCircle :size="24" /> 传统日常创建</h2>
            <button class="mode-switch-btn" @click="openNaturalLanguageForm" title="切换到智能输入模式">
              <Globe :size="18" />
              <span>试试智能输入</span>
            </button>
          </div>
          <form @submit.prevent="addSchedule">
            <div class="form-group">
              <label for="title">标题</label>
              <input id="title" type="text" v-model="newSchedule.title" placeholder="例如：团队周会" required>
            </div>
            <div class="form-group">
              <label for="content">内容</label>
              <textarea id="content" v-model="newSchedule.content" placeholder="例如：讨论项目进展 (可选)"></textarea>
            </div>
            <div class="form-group">
              <label for="start_time">开始时间</label>
              <input id="start_time" type="datetime-local" v-model="newSchedule.start_time" required>
            </div>
            <div class="form-group">
              <label for="priority">优先级</label>
              <select id="priority" v-model="newSchedule.priority" class="form-select">
                <option value="1">⭐ 普通</option>
                <option value="2">⭐⭐ 一般</option>
                <option value="3">⭐⭐⭐ 重要</option>
                <option value="4">⭐⭐⭐⭐ 紧急</option>
                <option value="5">⭐⭐⭐⭐⭐ 非常重要</option>
              </select>
            </div>
            <div class="form-group">
              <label class="checkbox-label">
                <input type="checkbox" v-model="newSchedule.is_recurring" class="checkbox-input">
                <span>重复日程</span>
              </label>
            </div>
            <div v-if="newSchedule.is_recurring" class="form-group">
              <label for="recurring_pattern">重复模式</label>
              <select id="recurring_pattern" v-model="newSchedule.recurring_pattern" class="form-select">
                <option value="daily">每天重复</option>
                <option value="weekly">每周重复</option>
                <option value="monthly">每月重复</option>
              </select>
            </div>
            <div class="form-actions">
              <button type="button" class="btn-cancel" @click="isFormVisible = false">取消</button>
              <button type="submit" class="btn-submit">确认添加</button>
            </div>
          </form>
        </div>
      </div>
    </transition>

    <!-- 自然语言/智能输入界面 -->
    <!-- ... existing natural language form ... -->
    <transition name="fade">
      <div v-if="isNaturalLanguageMode && createMode === 'natural'" class="form-overlay" @click.self="isNaturalLanguageMode = false">
        <div class="form-container nl-mode">
          <div class="form-header">
            <h2><Globe :size="24" /> 🎤 智能语音/文本输入</h2>
            <button class="mode-switch-btn" @click="openCreateForm" title="切换到传统表单模式">
              <PlusCircle :size="18" />
              <span>使用表单</span>
            </button>
          </div>
          <p class="nl-hint">💡 试试这样说：</p>
          <ul class="nl-examples">
            <li>"安排下周三下午两点的团队会议"</li>
            <li>"提醒我每周一早上检查邮箱"</li>
            <li>"明天上午 9 点与客户见面"</li>
          </ul>
          
          <div class="nl-input-group">
            <textarea 
              v-model="naturalLanguageInput"
              placeholder="请输入您的指令，或直接点击麦克风说话..."
              rows="4"
              :disabled="isProcessingNL || isRecording"
            ></textarea>
            
            <!-- AI 处理状态指示器 -->
            <div v-if="isAIProcessing" class="ai-processing-indicator">
              <span class="ai-icon">🤖</span>
              <span>AI 正在智能解析中...</span>
            </div>
            
            <div class="nl-actions">
              <button 
                type="button" 
                class="voice-btn" 
                @click="startVoiceInput"
                title="语音输入"
                :disabled="isProcessingNL || isRecording"
                :class="{ 'recording': isRecording }"
              >
                <span class="btn-icon">🎤</span>
                <span class="btn-text">{{ isRecording ? '正在录音...' : '语音输入' }}</span>
                <span v-if="isRecording" class="wave-animation">
                  <span class="wave-bar"></span>
                  <span class="wave-bar"></span>
                  <span class="wave-bar"></span>
                </span>
              </button>
              
              <div v-if="isRecording" class="recording-indicator">
                <span class="recording-dot"></span>
                <span class="recording-label">录音中</span>
                <span class="recording-time">{{ formatRecordingTime(recordingDuration) }}</span>
              </div>
              
              <div class="nl-actions-right">
                <button 
                  type="button" 
                  class="btn-submit" 
                  @click="handleNaturalLanguageSubmit"
                  :disabled="isProcessingNL || !naturalLanguageInput.trim() || isRecording"
                >
                  {{ isProcessingNL ? '处理中...' : '✨ 创建日程' }}
                </button>
                <button 
                  type="button" 
                  class="btn-cancel" 
                  @click="handleCancelClick"
                >
                  取消
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <!-- 编辑日程的表单 -->
    <transition name="fade">
      <div v-if="editingSchedule" class="form-overlay" @click.self="closeEditModal">
        <div class="form-container">
          <h2>编辑日程</h2>
          <form @submit.prevent="saveEdit">
            <div class="form-group">
              <label for="edit-title">标题</label>
              <input id="edit-title" type="text" v-model="editForm.title" placeholder="日程标题" required>
            </div>
            <div class="form-group">
              <label for="edit-content">内容</label>
              <textarea id="edit-content" v-model="editForm.content" placeholder="日程内容 (可选)"></textarea>
            </div>
            <div class="form-group">
              <label for="edit-start_time">开始时间 ({{ currentTimezone }})</label>
              <input id="edit-start_time" type="datetime-local" v-model="editForm.start_time" required>
            </div>
            <div class="form-group">
              <label for="edit-priority">优先级</label>
              <select id="edit-priority" v-model="editForm.priority" class="form-select">
                <option value="1">⭐ 普通</option>
                <option value="2">⭐⭐ 一般</option>
                <option value="3">⭐⭐⭐ 重要</option>
                <option value="4">⭐⭐⭐⭐ 紧急</option>
                <option value="5">⭐⭐⭐⭐⭐ 非常重要</option>
              </select>
            </div>
            <div class="form-group">
              <label class="checkbox-label">
                <input type="checkbox" v-model="editForm.is_recurring" class="checkbox-input">
                <span>重复日程</span>
              </label>
            </div>
            <div v-if="editForm.is_recurring" class="form-group">
              <label for="edit-recurring_pattern">重复模式</label>
              <select id="edit-recurring_pattern" v-model="editForm.recurring_pattern" class="form-select">
                <option value="daily">每天重复</option>
                <option value="weekly">每周重复</option>
                <option value="monthly">每月重复</option>
              </select>
            </div>
            <div class="form-actions">
              <button type="button" class="btn-cancel" @click="closeEditModal">取消</button>
              <button type="submit" class="btn-submit">
                <Check :size="16" style="vertical-align: middle; margin-right: 4px;" />
                保存修改
              </button>
            </div>
          </form>
        </div>
      </div>
    </transition>

    <!-- 个人资料编辑弹窗 -->
    <transition name="fade">
      <div v-if="isProfileEditModalVisible" class="form-overlay" @click.self="isProfileEditModalVisible = false">
        <div class="form-container">
          <h2>编辑个人资料</h2>
          <form @submit.prevent="saveProfile">
            <div class="form-group">
              <label for="profile-username">用户名</label>
              <input id="profile-username" type="text" v-model="profileForm.username" required>
            </div>
            <div class="form-group">
              <label for="profile-email">邮箱</label>
              <input id="profile-email" type="email" v-model="profileForm.email">
            </div>
            <div class="form-group">
              <label for="profile-location">所在城市</label>
              <div class="location-input-group">
                <input 
                  id="profile-location" 
                  type="text" 
                  v-model="profileForm.location_name" 
                  placeholder="例如：101010100（北京）"
                  :disabled="isLocating"
                >
                <button 
                  type="button" 
                  class="locate-btn" 
                  @click="locateUser"
                  :disabled="isLocating"
                  title="自动定位当前位置"
                >
                  <MapPin :size="18" :class="{ 'spinning': isLocating }" />
                  <span v-if="isLocating">定位中...</span>
                  <span v-else>📍 定位</span>
                </button>
              </div>
              <div v-if="profileForm.location_name" class="current-city-name">
                当前城市：<strong>{{ profileForm.location_name }}</strong>
              </div>
              <div v-if="locationStatus" class="location-status" :class="{ 'status-error': locationStatus.includes('失败') }">
                {{ locationStatus }}
              </div>
              <small class="form-hint">点击"定位"按钮自动获取当前位置，或手动输入城市 ID</small>
            </div>


            <div class="form-group">
              <label class="checkbox-label">
                <input type="checkbox" v-model="profileForm.weather_alerts_enabled" class="checkbox-input">
                <span>启用天气提醒</span>
              </label>
            </div>
            <div class="form-actions">
              <button type="button" class="btn-cancel" @click="isProfileEditModalVisible = false">取消</button>
              <button type="submit" class="btn-submit">保存修改</button>
            </div>
          </form>
        </div>
      </div>
    </transition>

    <!-- 退出登录确认弹窗 -->
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

/* 新增布局样式 */
.home-container {
  display: flex;
  max-width: 100%;
  margin: 0;
  padding: 0;
  height: 100vh;
  overflow: hidden;
}

/* 侧边栏样式 */
.sidebar {
  width: 250px;
  background: linear-gradient(180deg, #5E72E4 0%, #4c5fd5 100%);
  color: white;
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  flex-shrink: 0;
}

.sidebar.collapsed {
  width: 70px;
}

.sidebar-header {
  padding: 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-header h2 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 600;
}

.collapse-btn {
  background: none;
  border: none;
  color: white;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0.25rem;
  transition: transform 0.2s;
}

.collapse-btn:hover {
  transform: scale(1.1);
}

.sidebar-nav {
  flex: 1;
  padding: 1rem 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1.5rem;
  color: rgba(255, 255, 255, 0.8);
  text-decoration: none;
  transition: all 0.2s;
  cursor: pointer;
  position: relative;
}

.nav-item:hover {
  background-color: rgba(255, 255, 255, 0.1);
  color: white;
}

.nav-item.active {
  background-color: rgba(255, 255, 255, 0.2);
  color: white;
  font-weight: 600;
}

.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background-color: white;
}

.badge {
  background-color: #f5365c;
  color: white;
  font-size: 0.75rem;
  padding: 0.125rem 0.5rem;
  border-radius: 10px;
  margin-left: auto;
}

.sidebar-footer {
  padding: 1rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.user-info-mini {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 1.2rem;
}

.user-name {
  font-size: 0.9rem;
  font-weight: 500;
}

.logout-btn-mini {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.8);
  cursor: pointer;
  padding: 0.5rem;
  display: flex;
  align-items: center;
  border-radius: 4px;
  transition: all 0.2s;
}

.logout-btn-mini:hover {
  background-color: rgba(255, 255, 255, 0.1);
  color: white;
}

/* 主内容区样式 */
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

/* 标签页内容 */
.tab-content {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
}

.content-body {
  /* 保持原有样式 */
}

/* 个人信息卡片 */
.profile-card {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(50, 50, 93, 0.11), 0 1px 3px rgba(0, 0, 0, 0.08);
}

.profile-header {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 2rem;
  padding-bottom: 2rem;
  border-bottom: 2px solid #e9ecef;
}

.profile-avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, #5E72E4 0%, #4c5fd5 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  font-weight: 600;
  flex-shrink: 0;
}

.profile-info {
  flex: 1;
}

.profile-info h2 {
  margin: 0 0 0.5rem 0;
  color: #32325D;
  font-size: 1.5rem;
}

.profile-email, .profile-join-date {
  margin: 0.25rem 0;
  color: #8898aa;
  font-size: 0.9rem;
}

.edit-profile-btn {
  background-color: #f4f5f7;
  border: none;
  border-radius: 8px;
  padding: 0.75rem 1.5rem;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #5E72E4;
  transition: all 0.2s;
}

.edit-profile-btn:hover {
  background-color: #5E72E4;
  color: white;
}

.profile-actions {
  display: flex;
  gap: 0.75rem;
  flex-direction: column;
}

.profile-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
}

.refresh-weather-btn {
  background-color: #2dce89;
  border: none;
  border-radius: 8px;
  padding: 0.75rem 1.5rem;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: white;
  transition: all 0.2s;
}

.refresh-weather-btn:hover {
  background-color: #26b87a;
  transform: translateY(-2px);
}

.profile-location {
  margin: 0.25rem 0;
  color: #8898aa;
  font-size: 0.9rem;
}

.location-id {
  font-size: 0.8rem;
  color: #adb5bd;
  font-weight: normal;
}

.stat-item {
  text-align: center;
  padding: 1.5rem;
  background-color: #f8f9fe;
  border-radius: 8px;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: #5E72E4;
  margin-bottom: 0.5rem;
}

.stat-label {
  color: #8898aa;
  font-size: 0.9rem;
}

/* 通知面板 */
.notifications-panel {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(50, 50, 93, 0.11), 0 1px 3px rgba(0, 0, 0, 0.08);
}

.refresh-btn {
  background-color: #2dce89;
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
  background-color: #26b87a;
}

.empty-notifications {
  text-align: center;
  padding: 4rem 2rem;
  color: #adb5bd;
}

.empty-notifications h3 {
  color: #32325D;
  margin: 1rem 0 0.5rem 0;
}

.notifications-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.notification-item {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1rem;
  border-radius: 8px;
  background-color: #f8f9fe;
  border-left: 4px solid #5E72E4;
}

.notification-item.type-weather {
  background-color: #e3f9e5;
  border-left-color: #2dce89;
}

.notification-item.type-balance {
  background-color: #fff3cd;
  border-left-color: #ffc107;
}

.notification-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background-color: rgba(94, 114, 228, 0.1);
  color: #5E72E4;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.type-weather .notification-icon {
  background-color: rgba(45, 206, 137, 0.1);
  color: #2dce89;
}

.type-balance .notification-icon {
  background-color: rgba(255, 193, 7, 0.1);
  color: #ffc107;
}

.notification-content h4 {
  margin: 0 0 0.5rem 0;
  color: #32325D;
  font-size: 1rem;
}

.notification-content p {
  margin: 0;
  color: #525F7F;
  font-size: 0.9rem;
  line-height: 1.5;
}

/* 设置面板 */
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
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: #32325D;
  font-weight: 500;
}

.setting-value {
  color: #8898aa;
  font-size: 0.9rem;
}

/* 开关样式 */
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
  background-color: #ccc;
  transition: .4s;
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
  transition: .4s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: #5E72E4;
}

input:checked + .slider:before {
  transform: translateX(24px);
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


/* .home-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
} */

.main-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.main-header h1 {
  margin: 0;
  color: #32325D;
  font-size: 2rem;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.create-buttons {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.username {
  color: #525F7F;
  font-weight: 500;
}

.logout-btn-small {
  background: none;
  border: none;
  cursor: pointer;
  color: #8898aa;
  padding: 0.5rem;
  display: flex;
  align-items: center;
  border-radius: 4px;
  transition: all 0.2s;
}

.logout-btn-small:hover {
  background-color: #f4f5f7;
  color: #f5365c;
}

.add-btn {
  background-color: #5E72E4;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s ease;
  box-shadow: 0 4px 6px rgba(50, 50, 93, 0.11), 0 1px 3px rgba(0, 0, 0, 0.08);
}

.add-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 7px 14px rgba(50, 50, 93, 0.1), 0 3px 6px rgba(0, 0, 0, 0.08);
}

.add-btn.active {
  background-color: #4c5fd5;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
  transform: translateY(0);
}

.nl-btn {
  background-color: #2dce89;
}

.nl-btn:hover {
  background-color: #26b87a;
}

.nl-btn.active {
  background-color: #26b87a;
}

.recommendation-btn {
  background-color: #fff;
  color: #5E72E4;
  border: 2px solid #5E72E4;
  border-radius: 8px;
  padding: 0.75rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.recommendation-btn:hover {
  background-color: #5E72E4;
  color: white;
  transform: translateY(-2px);
}

/* 表单头部样式 */
.form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e9ecef;
}

.form-header h2 {
  margin: 0;
  color: #32325D;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.mode-switch-btn {
  background-color: #f8f9fe;
  border: 2px solid #5E72E4;
  color: #5E72E4;
  border-radius: 6px;
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s;
}

.mode-switch-btn:hover {
  background-color: #5E72E4;
  color: white;
}

/* 智能推荐面板样式 */
.recommendation-panel {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1001;
}

.recommendation-content {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
}

.recommendation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e9ecef;
}

.recommendation-header h2 {
  margin: 0;
  color: #32325D;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.close-btn {
  background: none;
  border: none;
  font-size: 2rem;
  cursor: pointer;
  color: #8898aa;
  padding: 0;
  line-height: 1;
}

.close-btn:hover {
  color: #f5365c;
}

.recommendation-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.recommendation-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border-radius: 8px;
  background-color: #f8f9fe;
  border-left: 4px solid #5E72E4;
}

.recommendation-item.type-weather {
  background-color: #e3f9e5;
  border-left-color: #2dce89;
}

.recommendation-item.type-balance {
  background-color: #fff3cd;
  border-left-color: #ffc107;
}

.rec-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background-color: rgba(94, 114, 228, 0.1);
  color: #5E72E4;
}

.type-weather .rec-icon {
  background-color: rgba(45, 206, 137, 0.1);
  color: #2dce89;
}

.type-balance .rec-icon {
  background-color: rgba(255, 193, 7, 0.1);
  color: #ffc107;
}

.rec-message p {
  margin: 0;
  color: #525F7F;
  font-size: 0.95rem;
}

/* 自然语言模式样式 */
.nl-mode {
  max-width: 600px;
}

.nl-hint {
  color: #8898aa;
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
  text-align: center;
  background-color: #f8f9fe;
  padding: 0.75rem;
  border-radius: 6px;
  font-weight: 500;
}

.nl-examples {
  background-color: #fff;
  border: 1px dashed #5E72E4;
  padding: 1rem;
  border-radius: 6px;
  margin-bottom: 1.5rem;
  list-style-position: inside;
}

.nl-examples li {
  color: #525F7F;
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
  line-height: 1.5;
}

.nl-examples li:last-child {
  margin-bottom: 0;
}

.form-select {
  width: 100%;
  padding: 0.75rem;
  border: 2px solid #e9ecef;
  border-radius: 6px;
  font-size: 1rem;
  background-color: white;
  cursor: pointer;
  transition: border-color 0.2s;
}

.form-select:focus {
  outline: none;
  border-color: #5E72E4;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  user-select: none;
  font-weight: 500;
  color: #32325D;
}

.checkbox-input {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: #5E72E4;
}

.nl-input-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.nl-input-group textarea {
  width: 100%;
  padding: 16px;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  font-size: 1rem;
  resize: vertical;
  font-family: inherit;
  transition: all 0.3s;
  background: linear-gradient(135deg, #fafafa 0%, #ffffff 100%);
  line-height: 1.6;
}

.nl-input-group textarea:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  background: #fff;
}

.nl-input-group textarea:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

.nl-actions {
  display: flex;
  gap: 12px;
  margin-top: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.nl-actions-right {
  display: flex;
  gap: 12px;
  margin-left: auto;
  align-items: center;
}

.ai-processing-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-radius: 8px;
  color: #0284c7;
  font-size: 14px;
  font-weight: 500;
  margin-top: 8px;
  animation: pulse-ai 1.5s infinite;
}

.ai-icon {
  font-size: 18px;
  animation: spin-ai 3s linear infinite;
}

@keyframes spin-ai {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

@keyframes pulse-ai {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.02);
  }
}

.recording-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
  border-radius: 20px;
  font-size: 14px;
  color: #dc2626;
  font-weight: 500;
  animation: pulse-bg 1.5s infinite;
}

.recording-dot {
  width: 10px;
  height: 10px;
  background-color: #dc2626;
  border-radius: 50%;
  animation: pulse-dot 1s infinite;
}

@keyframes pulse-dot {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.3;
  }
}

@keyframes pulse-bg {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

.voice-btn.recording {
  background: linear-gradient(135deg, #fca5a5 0%, #ef4444 100%);
  animation: pulse-button 1.5s infinite;
}

@keyframes pulse-button {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}


.voice-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 12px;
  padding: 12px 20px;
  font-size: 1rem;
  font-weight: 600;
  color: white;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
  position: relative;
  overflow: hidden;
}

.voice-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transition: left 0.5s;
}

.voice-btn:hover:not(:disabled)::before {
  left: 100%;
}

.voice-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
}

.voice-btn.recording {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  box-shadow: 0 4px 20px rgba(245, 87, 108, 0.5);
  animation: recording-pulse 2s infinite;
}

@keyframes recording-pulse {
  0%, 100% {
    box-shadow: 0 4px 20px rgba(245, 87, 108, 0.5);
  }
  50% {
    box-shadow: 0 4px 30px rgba(245, 87, 108, 0.8);
  }
}

.voice-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

/* 录音指示器优化 */
.recording-indicator {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
  border-radius: 25px;
  font-size: 15px;
  color: #d63031;
  font-weight: 600;
  box-shadow: 0 4px 15px rgba(253, 182, 159, 0.4);
  animation: indicator-glow 1.5s infinite;
  min-width: 120px;
}

@keyframes indicator-glow {
  0%, 100% {
    box-shadow: 0 4px 15px rgba(253, 182, 159, 0.4);
    transform: scale(1);
  }
  50% {
    box-shadow: 0 4px 20px rgba(253, 182, 159, 0.6);
    transform: scale(1.02);
  }
}

.recording-dot {
  width: 12px;
  height: 12px;
  background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
  border-radius: 50%;
  animation: dot-pulse 1s infinite;
  position: relative;
}

.recording-dot::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 100%;
  height: 100%;
  background-color: #ff416c;
  border-radius: 50%;
  z-index: -1;
  animation: ripple 1s infinite;
}

@keyframes dot-pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.4;
    transform: scale(0.9);
  }
}

@keyframes ripple {
  0% {
    width: 100%;
    height: 100%;
    opacity: 1;
  }
  100% {
    width: 200%;
    height: 200%;
    opacity: 0;
  }
}

.recording-time {
  font-family: 'Courier New', monospace;
  font-weight: 700;
  letter-spacing: 1px;
  min-width: 50px;
  text-align: center;
}

/* 按钮组整体优化 */
.nl-actions .btn-submit {
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
  box-shadow: 0 4px 15px rgba(56, 239, 125, 0.4);
}

.nl-actions .btn-submit:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(56, 239, 125, 0.6);
}

.nl-actions .btn-cancel {
  background: linear-gradient(135deg, #e0e0e0 0%, #f5f5f5 100%);
  color: #555;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.nl-actions .btn-cancel:hover {
  background: linear-gradient(135deg, #d0d0d0 0%, #e8e8e8 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* 冲突对话框样式 */
.conflict-dialog {
  max-width: 600px;
}

.conflict-info {
  background-color: #f8f9fe;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
}

.conflict-title {
  font-weight: 600;
  color: #32325D;
  margin-bottom: 0.5rem;
}

.new-schedule-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  color: #525F7F;
}

.conflicts-list {
  margin: 1.5rem 0;
}

.conflicts-list h3 {
  color: #f5365c;
  font-size: 1rem;
  margin-bottom: 0.75rem;
}

.conflict-item {
  background-color: #fff5f5;
  border: 1px solid #feb2b2;
  padding: 0.75rem;
  border-radius: 6px;
  margin-bottom: 0.5rem;
}

.conflict-item-title {
  font-weight: 600;
  color: #c53030;
  margin-bottom: 0.25rem;
}

.conflict-item-time {
  font-size: 0.85rem;
  color: #742a2a;
}

.conflict-suggestion {
  background-color: #e6fffa;
  border: 1px solid #81e6d9;
  padding: 1rem;
  border-radius: 6px;
  margin-top: 1rem;
}

.conflict-suggestion h4 {
  color: #2c7a7b;
  font-size: 0.95rem;
  margin-bottom: 0.5rem;
}

.conflict-suggestion ul {
  margin: 0;
  padding-left: 1.5rem;
  color: #285e61;
  font-size: 0.9rem;
}

/* 日程项新增样式 */
.item-priority {
  margin-top: 0.5rem;
  font-size: 0.8rem;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  display: inline-block;
}

.priority-high {
  background-color: #ffebee;
  color: #c62828;
}

.item-recurring {
  margin-top: 0.5rem;
  font-size: 0.8rem;
  background-color: #e8f5e9;
  color: #2e7d32;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  display: inline-block;
}
/* ----------------------------- */
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

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: #32325D;
  font-weight: 500;
}

.form-group input[type="text"],
.form-group textarea,
.form-group input[type="datetime-local"],
.form-group select {
  width: 100%;
  padding: 0.75rem;
  border: 2px solid #e9ecef;
  border-radius: 6px;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
  outline: none;
  border-color: #5E72E4;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  user-select: none;
}

.checkbox-input {
  width: auto;
  cursor: pointer;
}

.form-hint {
  display: block;
  margin-top: 0.5rem;
  font-size: 0.8rem;
  color: #8898aa;
  font-style: italic;
}

.current-city-name {
  margin-top: 0.5rem;
  padding: 0.5rem;
  background-color: #f8f9fe;
  border-radius: 4px;
  font-size: 0.85rem;
  color: #5E72E4;
}

.current-city-name strong {
  font-weight: 600;
  color: #32325D;
}

.location-input-group input {
  flex: 1;
}

.locate-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background-color: #5E72E4;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.2s;
  white-space: nowrap;
}

.locate-btn:hover:not(:disabled) {
  background-color: #4a5fd6;
  transform: translateY(-1px);
}

.locate-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.locate-btn svg.spinning {
  animation: spin 1s linear infinite;
}

.location-status {
  margin-top: 0.5rem;
  font-size: 0.85rem;
  color: #2dce89;
  font-weight: 500;
}

.location-status.status-error {
  color: #f5365c;
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
}

.btn-cancel {
  background-color: #f4f5f7;
  color: #525F7F;
}

.btn-submit {
  flex: 1;
  padding: 12px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.btn-submit:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.btn-submit:active:not(:disabled) {
  transform: translateY(0) scale(0.98);
  box-shadow: 0 2px 10px rgba(102, 126, 234, 0.2);
}

.btn-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

@keyframes button-press {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(0.95);
  }
  100% {
    transform: scale(1);
  }
}

.btn-logout {
  background-color: #f5365c;
}

.btn-logout:hover {
  background-color: #ec1a42;
}

.date-group {
  margin-bottom: 2rem;
}

.date-header {
  color: #32325D;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #e9ecef;
  margin-bottom: 1rem;
}

.schedule-list {
  padding: 0;
  margin: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.schedule-item {
  display: flex;
  align-items: center;
  background-color: white;
  padding: 1rem;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(50, 50, 93, 0.11), 0 1px 3px rgba(0, 0, 0, 0.08);
  transition: transform 0.2s, box-shadow 0.2s;
}

.schedule-item:hover {
  transform: translateY(-3px);
  box-shadow: 0 7px 14px rgba(50, 50, 93, 0.1), 0 3px 6px rgba(0, 0, 0, 0.08);
}

.item-time {
  font-size: 1.2rem;
  font-weight: 700;
  color: #5E72E4;
  margin-right: 1.5rem;
  width: 70px;
}

.item-content {
  flex-grow: 1;
}

.item-content h4 {
  margin: 0 0 0.25rem 0;
  color: #32325D;
}

.item-content p {
  margin: 0;
  font-size: 0.9rem;
  color: #8898aa;
}

.item-weather {
  margin-top: 0.5rem;
  font-size: 0.8rem;
  background-color: #e3efff;
  color: #5185d0;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  display: inline-block;
}

.item-actions {
  display: flex;
  gap: 0.5rem;
}

.action-btn {
  background: none;
  border: none;
  padding: 0.5rem;
  cursor: pointer;
  color: #adb5bd;
  transition: color 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-btn:hover {
  color: #5E72E4;
}

.action-btn-delete:hover {
  color: #f5365c;
}

.loading-spinner {
  border: 4px solid #f4f5f7;
  border-top: 4px solid #5E72E4;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 4rem auto;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.empty-state {
  text-align: center;
  margin-top: 4rem;
  color: #adb5bd;
}

.empty-state h2 {
  color: #32325D;
  border: none;
}

.error-msg {
  text-align: center;
  background-color: #fdd;
  color: #c00;
  padding: 1rem;
  border-radius: 8px;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

.list-enter-active, .list-leave-active {
  transition: all 0.5s ease;
}

.list-enter-from, .list-leave-to {
  opacity: 0;
  transform: translateX(30px);
}

.logout-confirm {
  text-align: center;
}

.logout-confirm p {
  color: #525F7F;
  margin: 1rem 0;
}

.btn-icon {
  font-size: 1.2rem;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
}

.btn-text {
  font-weight: 600;
}

/* 声波动画 */
.wave-animation {
  display: flex;
  align-items: center;
  gap: 3px;
  margin-left: 8px;
  height: 20px;
}

.wave-bar {
  width: 3px;
  height: 100%;
  background-color: rgba(255, 255, 255, 0.9);
  border-radius: 2px;
  animation: wave 1s ease-in-out infinite;
}

.wave-bar:nth-child(1) {
  animation-delay: 0s;
}

.wave-bar:nth-child(2) {
  animation-delay: 0.1s;
}

.wave-bar:nth-child(3) {
  animation-delay: 0.2s;
}

@keyframes wave {
  0%, 100% {
    height: 4px;
    opacity: 0.5;
  }
  50% {
    height: 16px;
    opacity: 1;
  }
}

.recording-label {
  margin-right: 4px;
  font-weight: 500;
}


</style>