<script setup>
import { ref, onMounted, computed, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useUserStore } from '@/stores/user'
import { Clock, TrendingUp, Calendar, Target, ArrowLeft, MessageCircle, Send, Sparkles, RefreshCw, BarChart, PlusCircle, MessageSquare, Trash2, Award, Zap, Activity, PieChart, Layers } from 'lucide-vue-next'


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

  return Object.entries(distribution).map(([priority, count]) => ({
    label: priorityLabels[priority] || `P${priority}`,
    count: Number(count),
    percentage: ((Number(count) / total) * 100).toFixed(1),
    color: priorityColors[priority] || '#cbd5e1'
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
    percentage: ((distribution[hour] || 0) / maxCount * 100).toFixed(0)
  }))
})

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
        
        <div class="stat-card success">
          <div class="stat-icon">
            <TrendingUp :size="28" />
          </div>
          <div class="stat-info">
            <h3>完成率</h3>
            <p class="stat-value">{{ (statistics?.productivity?.completion_rate * 100 || 0).toFixed(1) }}%</p>
            <p class="stat-desc">任务完成比例</p>
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
              <div class="chart-bar" 
                   :style="{ height: item.percentage + '%' }"
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
          <div v-for="item in priorityDistributionText" :key="item.label" class="priority-stat-row">
            <div class="priority-label-col">
              <span class="priority-dot" :style="{ backgroundColor: item.color }"></span>
              <span class="priority-name">{{ item.label }}</span>
            </div>
            
            <div class="priority-bar-area">
              <div class="progress-track">
                <div class="progress-fill" 
                     :style="{ width: item.percentage + '%', backgroundColor: item.color }">
                </div>
              </div>
            </div>
            
            <div class="priority-value-col">
              <span class="count-text">{{ item.count }} 个</span>
              <span class="percent-text">{{ item.percentage }}%</span>
            </div>
          </div>
          
          <div class="insight-box" style="margin-top: 1.5rem;">
            <Award :size="18" />
            <p>
              您的日程中 <strong>{{ priorityDistributionText[0]?.label }}</strong> 类任务最多。
              <span v-if="priorityDistributionText.some(p => p.label === '紧急' || p.label === '非常重要')">
                注意平衡高优先级任务，避免长期处于高压状态。
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
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 1rem;
  background: white;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  color: #4a5568;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.back-btn:hover {
  background: #f7fafc;
  border-color: #cbd5e0;
  transform: translateY(-2px);
}

.page-header h1 {
  margin: 0;
  font-size: 2rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.tabs {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  background: white;
  padding: 0.5rem;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.tab-btn {
  flex: 1;
  padding: 0.8rem 1.5rem;
  border: none;
  background: transparent;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  color: #718096;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.tab-btn:hover {
  background: #f7fafc;
  color: #667eea;
}

.tab-btn.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

/* ===== 总览页面样式 ===== */
.overview-content {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.stat-card {
  background: white;
  border-radius: 16px;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  border-left: 4px solid transparent;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.12);
}

.stat-card.primary {
  border-left-color: #667eea;
}

.stat-card.success {
  border-left-color: #48bb78;
}

.stat-card.warning {
  border-left-color: #ed8936;
}

.stat-card.info {
  border-left-color: #4299e1;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-card.primary .stat-icon {
  background: linear-gradient(135deg, #667eea20 0%, #764ba220 100%);
  color: #667eea;
}

.stat-card.success .stat-icon {
  background: linear-gradient(135deg, #48bb7820 0%, #38a16920 100%);
  color: #48bb78;
}

.stat-card.warning .stat-icon {
  background: linear-gradient(135deg, #ed893620 0%, #dd6b2020 100%);
  color: #ed8936;
}

.stat-card.info .stat-icon {
  background: linear-gradient(135deg, #4299e120 0%, #3182ce20 100%);
  color: #4299e1;
}

.stat-info h3 {
  margin: 0 0 0.25rem 0;
  font-size: 0.9rem;
  color: #718096;
  font-weight: 500;
}

.stat-value {
  margin: 0;
  font-size: 1.8rem;
  font-weight: 700;
  color: #2d3748;
  line-height: 1;
}

.stat-desc {
  margin: 0.25rem 0 0 0;
  font-size: 0.8rem;
  color: #a0aec0;
}

/* 分析区域 */
.analysis-section {
  background: white;
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.section-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e2e8f0;
}

.section-header h3 {
  margin: 0;
  font-size: 1.3rem;
  color: #2d3748;
  font-weight: 700;
}

.section-header svg {
  color: #667eea;
}

/* 高效时段图表 */
.chart-container {
  margin-bottom: 1rem;
}

.productivity-chart {
  display: flex;
  align-items: flex-end;
  gap: 4px;
  height: 200px;
  padding: 1rem 0;
  border-bottom: 2px solid #e2e8f0;
}

.chart-bar-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
  justify-content: flex-end;
}

.chart-bar {
  width: 100%;
  max-width: 30px;
  background: linear-gradient(to top, #667eea, #764ba2);
  border-radius: 4px 4px 0 0;
  transition: all 0.3s ease;
  opacity: 0.6;
  min-height: 4px;
}

.chart-bar:hover {
  opacity: 1;
  transform: scaleY(1.05);
}

.chart-bar.peak-hour {
  opacity: 1;
  background: linear-gradient(to top, #f093fb 0%, #f5576c 100%);
  box-shadow: 0 0 10px rgba(245, 87, 108, 0.4);
}

.chart-label {
  font-size: 0.7rem;
  color: #718096;
  margin-top: 0.5rem;
  font-weight: 600;
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
  color: #4a5568;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 4px;
}

.legend-color.peak {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.legend-color.normal {
  background: linear-gradient(135deg, #667eea, #764ba2);
  opacity: 0.6;
}

/* 周模式网格 */
.weekly-pattern-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 1rem;
  margin-bottom: 1rem;
}

.weekday-card {
  background: #f7fafc;
  border-radius: 12px;
  padding: 1rem;
  text-align: center;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.weekday-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.weekday-card.busy-day {
  background: linear-gradient(135deg, #fff5f5 0%, #fed7d7 100%);
  border: 2px solid #fc8181;
}

.weekday-name {
  font-weight: 700;
  color: #2d3748;
  margin-bottom: 0.5rem;
  font-size: 0.95rem;
}

.weekday-count {
  font-size: 1.5rem;
  font-weight: 700;
  color: #667eea;
  margin-bottom: 0.5rem;
}

.weekday-card.busy-day .weekday-count {
  color: #e53e3e;
}

.weekday-bar {
  height: 4px;
  background: linear-gradient(90deg, #667eea, #764ba2);
  border-radius: 2px;
  margin-top: 0.5rem;
}

.weekday-card.busy-day .weekday-bar {
  background: linear-gradient(90deg, #fc8181, #f56565);
}

/* 优先级分布统计样式 */
.priority-stats-container {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.priority-stat-row {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.priority-label-col {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-width: 100px;
}

.priority-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.priority-name {
  font-weight: 600;
  color: #475569;
  font-size: 0.95rem;
}

.priority-bar-area {
  flex: 1;
  padding: 0 0.5rem;
}

.progress-track {
  height: 10px;
  background-color: #f1f5f9;
  border-radius: 5px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 5px;
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.priority-value-col {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  min-width: 80px;
}

.count-text {
  font-weight: 700;
  color: #1e293b;
  font-size: 1rem;
}

.percent-text {
  font-size: 0.8rem;
  color: #94a3b8;
}

.empty-hint {
  text-align: center;
  padding: 2rem;
  color: #94a3b8;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px dashed #cbd5e1;
}

/* ===== 推荐页面样式 ===== */
.recommendations-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.recommendations-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 16px;
  padding: 2.5rem;
  text-align: center;
  box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
}

.recommendations-header svg {
  color: white;
  margin-bottom: 0.5rem;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
}

.recommendations-header h3 {
  margin: 0.5rem 0;
  font-size: 1.8rem;
  font-weight: 700;
}

.recommendations-header p {
  margin: 0;
  color: rgba(255, 255, 255, 0.9);
  font-size: 1rem;
}

.loading-recommendations {
  text-align: center;
  padding: 4rem;
  color: #667eea;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e2e8f0;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.recommendations-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 1.5rem;
}

.recommendation-card {
  background: white;
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  border: 1px solid #f1f5f9;
  display: flex;
  flex-direction: column;
}

.recommendation-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
  border-color: #cbd5e1;
}

.rec-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.rec-type {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.8rem;
  background: #f1f5f9;
  color: #475569;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
}

.rec-confidence {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.8rem;
  color: #10b981;
  font-weight: 600;
  background: #ecfdf5;
  padding: 0.25rem 0.6rem;
  border-radius: 12px;
}

.recommendation-card h4 {
  margin: 0 0 0.75rem 0;
  color: #1e293b;
  font-size: 1.15rem;
  line-height: 1.4;
}

.rec-message {
  margin: 0 0 1rem 0;
  color: #64748b;
  line-height: 1.6;
  font-size: 0.95rem;
  flex-grow: 1;
}

.action-suggestions {
  padding: 1rem;
  background: #f8fafc;
  border-radius: 10px;
  margin-top: auto;
  border-left: 3px solid #667eea;
}

.action-suggestions h5 {
  margin: 0 0 0.5rem 0;
  color: #334155;
  font-size: 0.9rem;
  font-weight: 600;
}

.action-suggestions ul {
  margin: 0;
  padding-left: 1.2rem;
  color: #475569;
  font-size: 0.9rem;
}

.action-suggestions li {
  margin: 0.3rem 0;
  line-height: 1.5;
}

.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 4rem 2rem;
  background: white;
  border-radius: 16px;
  border: 2px dashed #e2e8f0;
}

.empty-state svg {
  color: #cbd5e1;
  margin-bottom: 1rem;
}

.empty-state h4 {
  margin: 0.5rem 0;
  color: #334155;
  font-size: 1.3rem;
}

.empty-state p {
  margin: 0.5rem 0 1.5rem 0;
  color: #94a3b8;
}

.create-first-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.create-first-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.ai-chat-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(50, 50, 93, 0.11);
  height: 650px;
  display: flex;
  flex-direction: column;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 2rem;
  border-bottom: 2px solid #e9ecef;
  background: linear-gradient(135deg, #f8f9fe 0%, #ffffff 100%);
  border-radius: 12px 12px 0 0;
}

.chat-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.chat-title h3 {
  margin: 0;
  color: #32325D;
  font-size: 1.1rem;
}

.chat-actions {
  display: flex;
  gap: 0.75rem;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background-color: white;
  border: 2px solid #dee2e6;
  border-radius: 6px;
  color: #525F7F;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.3s;
}

.action-btn:hover {
  background-color: #f8f9fe;
  border-color: #5E72E4;
  color: #5E72E4;
}

.chat-body-wrapper {
  display: flex;
  flex: 1;
  overflow: hidden;
  position: relative;
}

.conversation-sidebar {
  width: 300px;
  background: #fafbfc;
  border-right: 2px solid #e9ecef;
  display: flex;
  flex-direction: column;
  transition: transform 0.3s ease;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 2px solid #e9ecef;
}

.sidebar-header h4 {
  margin: 0;
  color: #32325D;
  font-size: 1rem;
}

.close-sidebar-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #8898aa;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}

.close-sidebar-btn:hover {
  color: #f5365c;
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem;
}

.conversation-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  margin-bottom: 0.5rem;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid transparent;
}

.conversation-item:hover {
  background: #f8f9fe;
  border-color: #dee2e6;
}

.conversation-item.active {
  background: #e3f2fd;
  border-color: #5E72E4;
}

.conversation-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.conversation-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #32325D;
  font-weight: 500;
  font-size: 0.9rem;
}

.conversation-time {
  color: #8898aa;
  font-size: 0.75rem;
}

.delete-conversation-btn {
  background: none;
  border: none;
  color: #8898aa;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  transition: all 0.2s;
}

.delete-conversation-btn:hover {
  background: #fee;
  color: #f5365c;
}

.empty-conversations {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  padding: 3rem 1rem;
  color: #8898aa;
  text-align: center;
}

.empty-conversations p {
  margin: 0;
  font-size: 0.9rem;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.clear-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background-color: white;
  border: 2px solid #dee2e6;
  border-radius: 6px;
  color: #525F7F;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s;
}

.clear-btn:hover {
  background-color: #f8f9fe;
  border-color: #5E72E4;
  color: #5E72E4;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  background-color: #fafbfc;
}

.message {
  display: flex;
  gap: 1rem;
  animation: fadeIn 0.3s ease;
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  flex-shrink: 0;
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 1rem;
}

.message-content {
  max-width: 70%;
  background: white;
  padding: 1rem 1.5rem;
  border-radius: 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.message.user .message-content {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.message-content p {
  margin: 0;
  line-height: 1.6;
  white-space: pre-wrap;
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
</style>