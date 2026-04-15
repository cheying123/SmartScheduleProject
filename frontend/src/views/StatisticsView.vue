<script setup>
import { ref, onMounted, computed, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useUserStore } from '@/stores/user'
import { Clock, TrendingUp, Calendar, Target, ArrowLeft, MessageCircle, Send, Sparkles, RefreshCw, BarChart, PlusCircle, MessageSquare, Trash2, Award, Zap, Activity, PieChart, Layers, Globe } from 'lucide-vue-next'


const API_URL = 'http://127.0.0.1:5000/api'
const userStore = useUserStore()
const router = useRouter()

const statistics = ref(null)
const recommendations = ref([])
const isLoading = ref(true)
const activeTab = ref('overview')

const weekdayMap = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

// AI 聊天相关
const chatMessages = ref([])
const newMessage = ref('')
const isChatLoading = ref(false)
const sessionId = ref(null)
const chatContainerRef = ref(null)
const isAnalyzing = ref(false)

// 对话管理相关
const conversationSessions = ref([])
const showConversationList = ref(false)

function goBack() {
  router.push('/')
}

async function loadStatistics() {
  try {
    const response = await axios.get(`${API_URL}/analytics/statistics`, {
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    })
    statistics.value = response.data
  } catch (error) {
    console.error('加载统计数据失败:', error)
  } finally {
    isLoading.value = false
  }
}

async function loadRecommendations() {
  try {
    // 使用 AI 接口获取深度推荐
    const response = await axios.get(`${API_URL}/ai/recommendations`, {
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    })
    recommendations.value = response.data.recommendations || []
  } catch (error) {
    console.error('加载 AI 推荐失败:', error)
    // 如果 AI 接口失败，可以回退到旧的统计推荐，或者显示错误提示
    recommendations.value = []
  }
}

async function loadSmartAnalysis() {
  isAnalyzing.value = true
  
  try {
    const response = await axios.get(`${API_URL}/ai/smart-analysis?days=7`, {
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    })
    
    const { report, recommendations: recs, stats } = response.data
    
    // 初始化欢迎消息
    let welcomeMessage = `👋 您好！我已经仔细分析了您的所有日程数据。\n\n`
    
    if (stats.total_tasks > 0) {
      welcomeMessage += `【数据概览】\n`
      welcomeMessage += `• 共记录了 ${stats.total_tasks} 个日程\n`
      
      if (stats.productive_hours.length > 0) {
        welcomeMessage += `• 您的高效时段：${stats.productive_hours.map(h => h + '点').join('、')}\n`
      }
      
      if (stats.busy_days.length > 0) {
        const busyDaysStr = stats.busy_days.map(d => weekdayMap[d]).join('、')
        welcomeMessage += `• 繁忙日期：${busyDaysStr}\n`
      }
      
      welcomeMessage += `\n【智能分析】\n${report}\n`
      
      if (recs && recs.length > 0) {
        welcomeMessage += `\n【优化建议】\n`
        recs.forEach((rec, i) => {
          welcomeMessage += `${i + 1}. ${rec.message}\n`
        })
      }
    } else {
      welcomeMessage += `您还没有创建任何日程呢～\n\n`
      welcomeMessage += `💡 小贴士：您可以点击首页的"表单创建"或"智能输入"按钮来添加日程，我会根据您的日程数据提供个性化建议哦！`
    }
    
    chatMessages.value = [{
      role: 'assistant',
      message: welcomeMessage,
      created_at: new Date().toISOString()
    }]
    
  } catch (error) {
    console.error('加载智能分析失败:', error)
    chatMessages.value = [{
      role: 'assistant',
      message: '抱歉，加载分析数据时出现错误，请稍后再试。',
      created_at: new Date().toISOString()
    }]
  } finally {
    isAnalyzing.value = false
  }
}

async function sendMessage() {
  if (!newMessage.value.trim()) return
  
  const userMsg = newMessage.value.trim()
  chatMessages.value.push({
    role: 'user',
    message: userMsg,
    created_at: new Date().toISOString()
  })
  
  newMessage.value = ''
  isChatLoading.value = true
  
  try {
    const response = await axios.post(
      `${API_URL}/ai/chat`,
      {
        message: userMsg,
        session_id: sessionId.value
      },
      {
        headers: {
          'Authorization': `Bearer ${userStore.token}`
        }
      }
    )
    
    sessionId.value = response.data.session_id
    
    chatMessages.value.push({
      role: 'assistant',
      message: response.data.response,
      created_at: new Date().toISOString()
    })
    
    await nextTick()
    scrollToBottom()
  } catch (error) {
    console.error('发送消息失败:', error)
    chatMessages.value.push({
      role: 'assistant',
      message: '抱歉，出现了错误，请稍后再试。',
      created_at: new Date().toISOString()
    })
  } finally {
    isChatLoading.value = false
  }
}

function scrollToBottom() {
  if (chatContainerRef.value) {
    chatContainerRef.value.scrollTop = chatContainerRef.value.scrollHeight
  }
}

function formatTime(timeStr) {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

function formatDate(timeStr) {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  return date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
}

function clearChatHistory() {
  if (confirm('确定要清空当前对话吗？')) {
    chatMessages.value = []
    sessionId.value = null
  }
}

async function createNewConversation() {
  chatMessages.value = []
  sessionId.value = null
  await loadSmartAnalysis()
  showConversationList.value = false
}

async function loadConversationSessions() {
  try {
    const response = await axios.get(
      `${API_URL}/ai/conversations`,
      {
        headers: {
          'Authorization': `Bearer ${userStore.token}`
        }
      }
    )
    conversationSessions.value = response.data.sessions
  } catch (error) {
    console.error('加载会话列表失败:', error)
  }
}

async function selectConversation(sessionIdToLoad) {
  try {
    const response = await axios.get(
      `${API_URL}/ai/conversations/${sessionIdToLoad}`,
      {
        headers: {
          'Authorization': `Bearer ${userStore.token}`
        }
      }
    )
    
    sessionId.value = sessionIdToLoad
    chatMessages.value = response.data.messages.map(msg => ({
      role: msg.role,
      message: msg.message,
      created_at: msg.created_at
    }))
    
    showConversationList.value = false
  } catch (error) {
    console.error('加载对话失败:', error)
    alert('加载对话失败，请稍后再试')
  }
}

async function deleteConversation(sessionIdToDelete) {
  if (!confirm('确定要删除这个对话吗？')) return
  
  try {
    await axios.delete(
      `${API_URL}/ai/conversations/${sessionIdToDelete}`,
      {
        headers: {
          'Authorization': `Bearer ${userStore.token}`
        }
      }
    )
    
    if (sessionId.value === sessionIdToDelete) {
      chatMessages.value = []
      sessionId.value = null
    }
    
    await loadConversationSessions()
  } catch (error) {
    console.error('删除对话失败:', error)
    alert('删除对话失败，请稍后再试')
  }
}

const productiveHoursText = computed(() => {
  if (!statistics.value?.productivity?.productive_hours?.length) return '暂无数据'
  const hours = statistics.value.productivity.productive_hours
  return hours.map(h => `${h}点`).join(',')
})

const busyDaysText = computed(() => {
  if (!statistics.value?.weekly_pattern?.busy_days?.length) return '暂无数据'
  const days = statistics.value.weekly_pattern.busy_days
  return days.map(d => weekdayMap[d]).join(',')
})





// 新增计算属性 - 任务时长分析
const avgDurationText = computed(() => {
  if (!statistics.value?.duration_preference) return '暂无数据'
  const minutes = statistics.value.duration_preference.average_duration_minutes
  if (minutes < 60) {
    return `${Math.round(minutes)} 分钟`
  }
  const hours = Math.floor(minutes / 60)
  const mins = Math.round(minutes % 60)
  return mins > 0 ? `${hours} 小时 ${mins} 分钟` : `${hours} 小时`
})

// 优先级分布文本 (修复版)
const priorityDistributionText = computed(() => {
  if (!statistics.value?.priority_distribution) return []
  
  const rawData = statistics.value.priority_distribution
  // 兼容后端可能返回的不同结构
  const distribution = rawData.distribution || rawData.Pdistribution || {}
  
  if (Object.keys(distribution).length === 0) return []
  
  const total = Object.values(distribution).reduce((sum, count) => sum + Number(count), 0)
  if (total === 0) return []
  
  const priorityLabels = {
    1: '普通',
    2: '一般', 
    3: '重要',
    4: '紧急',
    5: '非常重要'
  }
  
  const priorityColors = {
    1: '#94a3b8', // Slate
    2: '#3b82f6', // Blue
    3: '#f59e0b', // Amber
    4: '#ef4444', // Red
    5: '#7c3aed'  // Violet
  }

  const priorityIcons = {
    1: '📝', // 普通
    2: '🔹', // 一般
    3: '⭐', // 重要
    4: '🔥', // 紧急
    5: '💎'  // 非常重要
  }

  return Object.entries(distribution).map(([priority, count]) => ({
    label: priorityLabels[priority] || `P${priority}`,
    count: Number(count),
    percentage: ((Number(count) / total) * 100).toFixed(1),
    color: priorityColors[priority] || '#cbd5e1',
    icon: priorityIcons[priority] || '📌'
  })).sort((a, b) => b.count - a.count)
})


// 获取优先级颜色
function getPriorityColor(priority) {
  const colors = {
    1: '#9e9e9e',
    2: '#42a5f5',
    3: '#ffa726',
    4: '#ef5350',
    5: '#c62828'
  }
  return colors[priority] || '#9e9e9e'
}

// 计算每日平均任务数
const dailyAverageTasks = computed(() => {
  if (!statistics.value?.weekly_pattern) return 0
  return statistics.value.weekly_pattern.average_tasks_per_day || 0
})

// 周模式详细数据
const weeklyPatternData = computed(() => {
  if (!statistics.value?.weekly_pattern?.day_distribution) return []
  
  const distribution = statistics.value.weekly_pattern.day_distribution
  return weekdayMap.map((day, index) => ({
    day,
    count: distribution[index] || 0,
    isBusy: statistics.value.weekly_pattern.busy_days.includes(index)
  }))
})

// 高效时段分布数据（用于图表）
const productivityChartData = computed(() => {
  if (!statistics.value?.productivity?.distribution) return []
  
  const distribution = statistics.value.productivity.distribution
  const maxCount = Math.max(...Object.values(distribution), 1)
  
  return Array.from({ length: 24 }, (_, hour) => ({
    hour,
    count: distribution[hour] || 0,
    percentage: ((distribution[hour] || 0) / maxCount * 100)
  }))
})

// 新增：计算标签饼图的角度
function getStartAngle(index) {
  if (!statistics.value?.tag_distribution) return 0
  const tags = statistics.value.tag_distribution
  let sum = 0
  for (let i = 0; i < index; i++) {
    sum += tags[i].percentage
  }
  return sum * 3.6 // 转换为角度
}

function getEndAngle(index) {
  if (!statistics.value?.tag_distribution) return 0
  const tag = statistics.value.tag_distribution[index]
  return getStartAngle(index) + (tag.percentage * 3.6)
}

// 新增：生成分享链接
async function generateShareLink() {
  try {
    const response = await axios.post(`${API_URL}/analytics/share-link`, {}, {
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    })
    
    const shareUrl = response.data.url
    
    // 复制到剪贴板
    if (navigator.clipboard) {
      await navigator.clipboard.writeText(shareUrl)
      alert(`✅ 约时链接已复制！\n${shareUrl}\n\n发送给朋友，他们可以看到你未来3天的空闲时间。`)
    } else {
      prompt('请手动复制链接：', shareUrl)
    }
  } catch (error) {
    console.error('生成链接失败:', error)
    alert('❌ 生成链接失败，请稍后重试。')
  }
}

// 新增：导出 ICS 文件
async function exportICS() {
  try {
    const response = await axios.get(`${API_URL}/analytics/export/ics`, {
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      },
      responseType: 'blob' // 重要：指定响应类型为 blob
    })
    
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    const dateStr = new Date().toISOString().split('T')[0]
    link.setAttribute('download', `smart_schedule_${dateStr}.ics`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    
    alert('✅ 日历文件已导出，您可以将其导入手机或电脑日历。')
  } catch (error) {
    console.error('导出失败:', error)
    alert('❌ 导出失败，请稍后重试。')
  }
}

// 监听用户信息变化，更新标题
watch(() => userStore.user, (newUser) => {
  if (newUser?.username) {
    document.title = `${newUser.username} - 统计分析`
  }
}, { immediate: true })

// 获取推荐类型图标
function getRecommendationTypeIcon(type) {
  const icons = {
    '时间偏好': '⏰',
    '日程平衡': '⚖️',
    '效率提升': '🚀',
    '习惯养成': '🎯',
    'AI 洞察': '🤖'
  }
  return icons[type] || '💡'
}

onMounted(async () => {
  // 设置页面标题
  if (userStore.user?.username) {
    document.title = `${userStore.user.username} - 统计分析`
  }
  
  await loadStatistics()
  await loadRecommendations()
})

async function handleTabChange(tab) {
  activeTab.value = tab
  
  if (tab === 'ai-chat' && chatMessages.value.length === 0) {
    await loadSmartAnalysis()
  }
  
  // 当切换到推荐页且数据为空时，触发 AI 推荐加载
  if (tab === 'recommendations' && recommendations.value.length === 0) {
    isLoading.value = true
    await loadRecommendations()
    isLoading.value = false
  }
  
  await nextTick()
  if (chatContainerRef.value) {
    chatContainerRef.value.scrollTop = chatContainerRef.value.scrollHeight
  }
}

</script>

<template>
  <div class="statistics-container">
    <div class="page-header">
      <button class="back-btn" @click="goBack" title="返回主页">
        <ArrowLeft :size="20" />
        <span>返回</span>
      </button>
      <h1>📊 我的效率分析</h1>
    </div>
    
    <div class="tabs">
      <button 
        :class="['tab-btn', { active: activeTab === 'overview' }]"
        @click="handleTabChange('overview')"
      >
        总览
      </button>
      <button 
        :class="['tab-btn', { active: activeTab === 'recommendations' }]"
        @click="handleTabChange('recommendations')"
      >
        智能推荐
      </button>
      <button 
        :class="['tab-btn', { active: activeTab === 'ai-chat' }]"
        @click="handleTabChange('ai-chat')"
      >
        <MessageCircle :size="16" />
        AI 分析助手
      </button>
    </div>
    
    <div v-if="activeTab === 'overview'" class="overview-content">
      <!-- 核心指标卡片 -->
      <div class="stats-header-actions">
        <div class="header-title-group">
          <h2>📊 数据概览</h2>
        </div>
        <div class="action-buttons">
          <button class="btn-share" @click="generateShareLink">
            <Globe :size="18" />
            <span>生成约时链接</span>
          </button>
          <button class="btn-export" @click="exportICS">
            <Calendar :size="18" />
            <span>导出日历 (.ics)</span>
          </button>
        </div>
      </div>

      <div class="stats-grid">
        <div class="stat-card primary">
          <div class="stat-icon">
            <Target :size="28" />
          </div>
          <div class="stat-info">
            <h3>总任务数</h3>
            <p class="stat-value">{{ statistics?.productivity?.total_tasks || 0 }}</p>
            <p class="stat-desc">过去 30 天创建的日程</p>
          </div>
        </div>
        
        <div class="stat-card warning">
          <div class="stat-icon">
            <Clock :size="28" />
          </div>
          <div class="stat-info">
            <h3>日均任务</h3>
            <p class="stat-value">{{ dailyAverageTasks.toFixed(1) }}</p>
            <p class="stat-desc">平均每天的任务数</p>
          </div>
        </div>
        
        <div class="stat-card info">
          <div class="stat-icon">
            <Activity :size="28" />
          </div>
          <div class="stat-info">
            <h3>平均时长</h3>
            <p class="stat-value">{{ avgDurationText }}</p>
            <p class="stat-desc">单个任务持续时间</p>
          </div>
        </div>
      </div>

      <!-- 标签分布分析 -->
      <div class="analysis-section" v-if="statistics?.tag_distribution && statistics.tag_distribution.length > 0">
        <div class="section-header">
          <Layers :size="20" />
          <h3>时间分配概览</h3>
        </div>
        <div class="tag-distribution-container">
          <div class="tag-pie-chart">
            <div v-for="(item, index) in statistics.tag_distribution" 
                 :key="item.tag"
                 class="pie-segment"
                 :style="{ 
                   '--segment-color': item.color,
                   '--start-angle': getStartAngle(index),
                   '--end-angle': getEndAngle(index)
                 }"
                 :title="`${item.label}: ${item.percentage}%`"
            ></div>
            <div class="pie-center">
              <span>{{ statistics.tag_distribution.reduce((sum, i) => sum + i.count, 0) }}</span>
              <small>总日程</small>
            </div>
          </div>
          
          <div class="tag-legend-list">
            <div v-for="item in statistics.tag_distribution" :key="item.tag" class="tag-legend-item">
              <div class="tag-info">
                <span class="tag-icon">{{ item.icon }}</span>
                <span class="tag-label">{{ item.label }}</span>
              </div>
              <div class="tag-stats">
                <span class="tag-count">{{ item.count }} 个</span>
                <span class="tag-percentage" :style="{ color: item.color }">{{ item.percentage }}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 高效时段分析 -->
      <div class="analysis-section">
        <div class="section-header">
          <Zap :size="20" />
          <h3>高效时段分析</h3>
        </div>
        <div class="chart-container">
          <div class="productivity-chart">
            <div v-for="item in productivityChartData" :key="item.hour" 
                 class="chart-bar-wrapper">
              <div class="tooltip" v-if="item.count > 0">{{ item.count }} 个任务</div>
              <div class="chart-bar" 
                   :style="{ height: Math.max((item.percentage / 100) * 180, 4) + 'px' }"
                   :class="{ 'peak-hour': statistics?.productivity?.productive_hours?.includes(item.hour) }"
                   :title="`${item.hour}点: ${item.count}个任务`">
              </div>
              <span class="chart-label">{{ item.hour }}</span>
            </div>
          </div>
          <div class="chart-legend">
            <div class="legend-item">
              <span class="legend-color peak"></span>
              <span>高效时段（Top 3）</span>
            </div>
            <div class="legend-item">
              <span class="legend-color normal"></span>
              <span>其他时段</span>
            </div>
          </div>
        </div>
        <div class="insight-box">
          <Award :size="18" />
          <p>您的高效时段是：<strong>{{ productiveHoursText }}</strong>，建议将重要任务安排在这些时间段。</p>
        </div>
      </div>

      <!-- 周模式分析 -->
      <div class="analysis-section">
        <div class="section-header">
          <Calendar :size="20" />
          <h3>周模式分析</h3>
        </div>
        <div class="weekly-pattern-grid">
          <div v-for="item in weeklyPatternData" :key="item.day" 
               class="weekday-card"
               :class="{ 'busy-day': item.isBusy }">
            <div class="weekday-name">{{ item.day }}</div>
            <div class="weekday-count">{{ item.count }}</div>
            <div class="weekday-bar" :style="{ width: (item.count / Math.max(...weeklyPatternData.map(d => d.count)) * 100) + '%' }"></div>
          </div>
        </div>
        <div class="insight-box">
          <Layers :size="18" />
          <p>您最繁忙的日子是：<strong>{{ busyDaysText }}</strong>，这些天的日程较为密集。</p>
        </div>
      </div>

      <!-- 优先级分布统计 -->
      <div class="analysis-section">
        <div class="section-header">
          <Target :size="20" />
          <h3>优先级分布</h3>
        </div>
        
        <div v-if="priorityDistributionText.length > 0" class="priority-stats-container">
          <div v-for="item in priorityDistributionText" :key="item.label" class="priority-stat-card">
            <div class="priority-info">
              <span class="priority-icon">{{ item.icon }}</span>
              <div class="priority-text">
                <span class="priority-name">{{ item.label }}</span>
                <span class="priority-count">{{ item.count }} 个任务</span>
              </div>
              <span class="priority-percent" :style="{ color: item.color }">{{ item.percentage }}%</span>
            </div>
            
            <div class="priority-bar-wrapper">
              <div class="progress-track">
                <div class="progress-fill" 
                     :style="{ width: item.percentage + '%', backgroundColor: item.color, boxShadow: `0 0 10px ${item.color}40` }">
                </div>
              </div>
            </div>
          </div>
          
          <div class="insight-box modern-insight">
            <Award :size="18" />
            <p>
              您的日程中 <strong>{{ priorityDistributionText[0]?.label }}</strong> 类任务最多。
              <span v-if="priorityDistributionText.some(p => p.label === '紧急' || p.label === '非常重要')">
                建议适当减少高优任务，保持工作与生活的平衡。
              </span>
            </p>
          </div>
        </div>

        <div v-else class="empty-hint">
          <p>暂无优先级数据，创建日程时设置优先级以获取分析。</p>
        </div>
      </div>
    </div>
    
    <div v-if="activeTab === 'recommendations'" class="recommendations-content">
      <div class="recommendations-header">
        <Sparkles :size="32" />
        <h3>AI 深度智能推荐</h3>
        <p>基于您的日程习惯、优先级分布及时间模式生成的个性化优化方案</p>
      </div>
      
      <div v-if="isLoading" class="loading-recommendations">
        <div class="spinner"></div>
        <p>AI 正在分析您的日程数据...</p>
      </div>

      <div v-else class="recommendations-list">
        <div v-for="(rec, index) in recommendations" :key="index" class="recommendation-card">
          <div class="rec-header">
            <span class="rec-type">
              {{ getRecommendationTypeIcon(rec.type) }} {{ rec.type || 'AI 洞察' }}
            </span>
            <span class="rec-confidence" v-if="rec.confidence">
              <Award :size="14" />
              匹配度 {{ (rec.confidence * 100).toFixed(0) }}%
            </span>
          </div>
          
          <h4>{{ rec.title }}</h4>
          <p class="rec-message">{{ rec.message }}</p>
          
          <div v-if="rec.action_suggestions && rec.action_suggestions.length > 0" class="action-suggestions">
            <h5>💡 行动建议：</h5>
            <ul>
              <li v-for="(suggestion, i) in rec.action_suggestions" :key="i">{{ suggestion }}</li>
            </ul>
          </div>
        </div>
        
        <div v-if="recommendations.length === 0 && !isLoading" class="empty-state">
          <BarChart :size="64" />
          <h4>暂无深度推荐</h4>
          <p>请尝试创建更多不同优先级的日程，以便 AI 更好地理解您的工作模式。</p>
          <button class="create-first-btn" @click="router.push('/')">
            <PlusCircle :size="18" />
            去创建日程
          </button>
        </div>
      </div>
    </div>
    
  
    <div v-if="activeTab === 'ai-chat'" class="ai-chat-container">
      <div class="chat-header">
        <div class="chat-title">
          <Sparkles :size="20" color="#5E72E4" />
          <h3>AI 日程分析助手</h3>
        </div>
        <div class="chat-actions">
          <button class="action-btn" @click="createNewConversation" title="新建对话">
            <PlusCircle :size="18" />
            <span v-if="!showConversationList">新建对话</span>
          </button>
          <button class="action-btn" @click="loadConversationSessions(); showConversationList = !showConversationList" title="历史对话">
            <MessageSquare :size="18" />
            <span v-if="!showConversationList">历史对话</span>
          </button>
          <button class="action-btn" @click="clearChatHistory" title="清空对话">
            <RefreshCw :size="18" />
            <span v-if="!showConversationList">清空</span>
          </button>
        </div>
      </div>
      
      <div class="chat-body-wrapper" :class="{ 'show-sidebar': showConversationList }">
        <!-- 历史对话列表侧边栏 -->
        <div class="conversation-sidebar" v-if="showConversationList">
          <div class="sidebar-header">
            <h4>历史对话</h4>
            <button class="close-sidebar-btn" @click="showConversationList = false">×</button>
          </div>
          <div class="conversation-list">
            <div 
              v-for="session in conversationSessions" 
              :key="session.session_id"
              class="conversation-item"
              :class="{ active: session.session_id === sessionId }"
              @click="selectConversation(session.session_id)"
            >
              <div class="conversation-info">
                <div class="conversation-title">
                  <MessageSquare :size="16" />
                  <span>对话 {{ formatDate(session.last_message_time) }}</span>
                </div>
                <div class="conversation-time">
                  {{ formatTime(session.last_message_time) }}
                </div>
              </div>
              <button class="delete-conversation-btn" @click.stop="deleteConversation(session.session_id)" title="删除此对话">
                <Trash2 :size="14" />
              </button>
            </div>
            
            <div v-if="conversationSessions.length === 0" class="empty-conversations">
              <MessageSquare :size="32" color="#8898aa" />
              <p>暂无历史对话</p>
            </div>
          </div>
        </div>
        
        <!-- 聊天主界面 -->
        <div class="chat-main">
          <div class="chat-messages" ref="chatContainerRef">
            <div v-for="(msg, index) in chatMessages" :key="index" :class="['message', msg.role]">
              <div class="message-avatar">
                <Sparkles v-if="msg.role === 'assistant'" :size="24" color="#5E72E4" />
                <div v-else class="user-avatar">我</div>
              </div>
              <div class="message-content">
                <p>{{ msg.message }}</p>
                <span class="message-time">{{ formatTime(msg.created_at) }}</span>
              </div>
            </div>
            
            <div v-if="isChatLoading" class="message assistant">
              <div class="message-avatar">
                <Sparkles :size="24" color="#5E72E4" />
              </div>
              <div class="message-content">
                <div class="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
            
            <div v-if="chatMessages.length === 0 && !isChatLoading" class="empty-chat">
              <Sparkles :size="48" color="#5E72E4" />
              <p>正在分析您的日程数据...</p>
            </div>
          </div>
          
          <div class="chat-input-area">
            <input 
              v-model="newMessage"
              @keyup.enter="sendMessage"
              type="text"
              placeholder="例如：我应该如何优化下周的工作安排？"
              class="chat-input"
            />
            <button @click="sendMessage" class="send-btn" :disabled="!newMessage.trim() || isChatLoading">
              <Send :size="20" />
            </button>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>


<style scoped>
.statistics-container {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
  min-height: calc(100vh - 80px);
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.page-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;
}

.back-btn {
  background: white;
  border: none;
  border-radius: 20px;
  padding: 0.5rem 1rem;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s;
  color: #5E72E4;
  font-weight: 600;
  font-size: 0.9rem;
}

.back-btn:hover {
  transform: translateX(-3px);
  box-shadow: 0 4px 12px rgba(94, 114, 228, 0.2);
  background: #f8f9fe;
}

.page-title {
  margin: 0;
  color: #32325D;
  font-size: 1.8rem;
}

.tabs {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  background: white;
  padding: 0.5rem;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.tab-btn {
  flex: 1;
  padding: 0.75rem 1.5rem;
  border: none;
  background: transparent;
  border-radius: 8px;
  font-weight: 600;
  color: #8898aa;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.tab-btn.active {
  background: #5E72E4;
  color: white;
  box-shadow: 0 4px 12px rgba(94, 114, 228, 0.3);
}

.tab-btn:hover:not(.active) {
  background: #f8f9fe;
  color: #5E72E4;
}

/* ===== 导出按钮样式 ===== */
.stats-header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding: 1rem;
  background: #f8f9fe;
  border-radius: 12px;
}

.action-buttons {
  display: flex;
  gap: 1rem;
}

.btn-share, .btn-export {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.btn-share {
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
}

.btn-export {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.btn-share:hover, .btn-export:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
}

/* 核心指标卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(50, 50, 93, 0.11), 0 1px 3px rgba(0, 0, 0, 0.08);
  display: flex;
  align-items: center;
  gap: 1rem;
  transition: transform 0.3s;
}

.stat-card:hover {
  transform: translateY(-5px);
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.stat-card.primary .stat-icon { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
.stat-card.warning .stat-icon { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
.stat-card.success .stat-icon { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
.stat-card.info .stat-icon { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }

.stat-info h3 {
  margin: 0 0 0.5rem 0;
  color: #8898aa;
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-value {
  margin: 0;
  font-size: 1.8rem;
  font-weight: 700;
  color: #32325D;
}

.stat-desc {
  margin: 0.25rem 0 0 0;
  color: #8898aa;
  font-size: 0.85rem;
}

/* 分析区块 */
.analysis-section {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 4px 6px rgba(50, 50, 93, 0.11), 0 1px 3px rgba(0, 0, 0, 0.08);
}

.section-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
  color: #32325D;
  font-size: 1.2rem;
  font-weight: 600;
}

.chart-container {
  margin-bottom: 1.5rem;
}

.productivity-chart {
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  height: 200px;
  padding: 1rem 0;
  border-bottom: 2px solid #e9ecef;
}

.chart-bar-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  flex: 1;
  position: relative;
}

.tooltip {
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  background: #32325D;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: all 0.2s;
  margin-bottom: 5px;
  z-index: 10;
}

.tooltip::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border-width: 4px;
  border-style: solid;
  border-color: #32325D transparent transparent transparent;
}

.chart-bar-wrapper:hover .tooltip {
  opacity: 1;
  transform: translateX(-50%) translateY(-5px);
}

.chart-bar {
  width: 16px;
  background: #e9ecef;
  border-radius: 8px;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  min-height: 4px;
  position: relative;
  overflow: hidden;
}

.chart-bar::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(to bottom, rgba(255,255,255,0.2), transparent);
  border-radius: 8px;
}

.chart-bar:hover {
  transform: scaleY(1.05);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.chart-bar.peak-hour {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.chart-label {
  font-size: 0.75rem;
  color: #8898aa;
}

.chart-legend {
  display: flex;
  justify-content: center;
  gap: 2rem;
  margin-top: 1rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  color: #525F7F;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

.legend-color.peak { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
.legend-color.normal { background: #e9ecef; }

.insight-box {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1rem;
  background: #f8f9fe;
  border-radius: 8px;
  border-left: 4px solid #5E72E4;
}

.insight-box p {
  margin: 0;
  color: #32325D;
  line-height: 1.6;
}

/* ===== 优先级分布优化样式 ===== */
.priority-stats-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.priority-stat-card {
  background: white;
  padding: 1.25rem;
  border-radius: 12px;
  border: 1px solid #f1f5f9;
  transition: all 0.3s ease;
}

.priority-stat-card:hover {
  border-color: #e2e8f0;
  box-shadow: 0 8px 24px rgba(149, 157, 165, 0.1);
  transform: translateY(-2px);
}

.priority-info {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 0.75rem;
}

.priority-icon {
  font-size: 1.5rem;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f8fafc;
  border-radius: 8px;
}

.priority-text {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.priority-name {
  font-weight: 600;
  color: #32325D;
  font-size: 1rem;
}

.priority-count {
  font-size: 0.85rem;
  color: #8898aa;
}

.priority-percent {
  font-weight: 700;
  font-size: 1.25rem;
}

.progress-track {
  height: 8px;
  background: #f1f5f9;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
}

.modern-insight {
  background: linear-gradient(135deg, #f8f9fe 0%, #eef2ff 100%);
  border-left: 4px solid #667eea;
}

/* 周模式网格 */
.weekly-pattern-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.weekday-card {
  background: #f8f9fe;
  padding: 1rem;
  border-radius: 8px;
  text-align: center;
  transition: all 0.3s;
}

.weekday-card.busy-day {
  background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
  transform: scale(1.05);
}

.weekday-name {
  font-weight: 600;
  color: #32325D;
  margin-bottom: 0.5rem;
}

.weekday-count {
  font-size: 1.5rem;
  font-weight: 700;
  color: #5E72E4;
  margin-bottom: 0.5rem;
}

.weekday-bar {
  height: 4px;
  background: #5E72E4;
  border-radius: 2px;
  margin: 0 auto;
}

/* AI 聊天区域 */
.ai-chat-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(50, 50, 93, 0.11), 0 1px 3px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  height: 600px;
}

.chat-header {
  padding: 1.5rem 2rem;
  border-bottom: 2px solid #e9ecef;
  background: linear-gradient(135deg, #f8f9fe 0%, #eef2f9 100%);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-header h3 {
  margin: 0;
  color: #32325D;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.manage-btn {
  background: white;
  border: 2px solid #e9ecef;
  color: #5E72E4;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s;
}

.manage-btn:hover {
  background: #5E72E4;
  color: white;
  border-color: #5E72E4;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.message {
  display: flex;
  gap: 1rem;
  max-width: 85%;
  animation: fadeIn 0.3s ease-out;
}

.message.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 1.2rem;
}

.message.assistant .message-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.message.user .message-avatar {
  background: #e9ecef;
  color: #5E72E4;
}

.message-bubble {
  padding: 1rem 1.25rem;
  border-radius: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.message.assistant .message-bubble {
  background: #f8f9fe;
  color: #32325D;
  border-top-left-radius: 4px;
}

.message.user .message-bubble {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-top-right-radius: 4px;
}

.message-time {
  display: block;
  font-size: 0.75rem;
  color: #8898aa;
  margin-top: 0.5rem;
}

.message.user .message-time {
  color: rgba(255, 255, 255, 0.8);
}

.chat-input-area {
  display: flex;
  gap: 1rem;
  padding: 1.5rem 2rem;
  border-top: 2px solid #e9ecef;
  background: white;
  border-radius: 0 0 12px 12px;
}

.chat-input {
  flex: 1;
  padding: 0.75rem 1rem;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  font-size: 1rem;
  outline: none;
  transition: border-color 0.3s;
}

.chat-input:focus {
  border-color: #5E72E4;
}

.send-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform 0.2s;
}

.send-btn:hover:not(:disabled) {
  transform: scale(1.1);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.typing-indicator {
  display: flex;
  gap: 0.5rem;
  padding: 0.5rem 0;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: #8898aa;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.typing-indicator span:nth-child(1) {
  animation-delay: -0.32s;
}

.typing-indicator span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.empty-chat {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  padding: 4rem 2rem;
  color: #8898aa;
  text-align: center;
}

.empty-chat p {
  margin: 0;
  font-size: 1.1rem;
}

/* ===== 标签分布样式 ===== */
.tag-distribution-container {
  display: flex;
  gap: 3rem;
  align-items: center;
  padding: 2rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(50, 50, 93, 0.11), 0 1px 3px rgba(0, 0, 0, 0.08);
}

.tag-pie-chart {
  position: relative;
  width: 220px;
  height: 220px;
  border-radius: 50%;
  background: conic-gradient(
    from 0deg,
    var(--segment-color) var(--start-angle) var(--end-angle)
  );
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease;
}

.tag-pie-chart:hover {
  transform: scale(1.05);
}

.pie-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 120px;
  height: 120px;
  background: white;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.05);
}

.pie-center span {
  font-size: 2rem;
  font-weight: 700;
  color: #32325D;
}

.pie-center small {
  font-size: 0.85rem;
  color: #8898aa;
}

.tag-legend-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.tag-legend-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: #f8f9fe;
  border-radius: 8px;
  transition: all 0.2s;
}

.tag-legend-item:hover {
  background: #eef2ff;
  transform: translateX(4px);
}

.tag-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.tag-icon {
  font-size: 1.5rem;
}

.tag-label {
  font-weight: 600;
  color: #32325D;
}

.tag-stats {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.tag-count {
  font-size: 0.9rem;
  color: #525F7F;
}

.tag-percentage {
  font-weight: 700;
  font-size: 1.1rem;
  min-width: 60px;
  text-align: right;
}

@media (max-width: 768px) {
  .tag-distribution-container {
    flex-direction: column;
    gap: 2rem;
  }
  
  .tag-pie-chart {
    width: 180px;
    height: 180px;
  }
  
  .pie-center {
    width: 100px;
    height: 100px;
  }
  
  .pie-center span {
    font-size: 1.5rem;
  }
}
</style>
