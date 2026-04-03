<script setup>
import { ref, onMounted, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useUserStore } from '@/stores/user'
import { Clock, TrendingUp, Calendar, Target, ArrowLeft, MessageCircle, Send, Sparkles, RefreshCw, BarChart } from 'lucide-vue-next'

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
    const response = await axios.get(`${API_URL}/analytics/recommendations`, {
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    })
    recommendations.value = response.data.recommendations
  } catch (error) {
    console.error('加载推荐失败:', error)
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

function clearChatHistory() {
  if (confirm('确定要清空对话历史吗？')) {
    chatMessages.value = []
    sessionId.value = null
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

onMounted(async () => {
  await loadStatistics()
  await loadRecommendations()
})

async function handleTabChange(tab) {
  activeTab.value = tab
  if (tab === 'ai-chat' && chatMessages.value.length === 0) {
    await loadSmartAnalysis()
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
      <div class="stat-card">
        <div class="stat-header">
          <Clock :size="24" color="#5E72E4" />
          <h3>高效时段</h3>
        </div>
        <p class="stat-value">{{ productiveHoursText }}</p>
        <p class="stat-desc">基于过去 30 天的日程数据分析</p>
      </div>
      
      <div class="stat-card">
        <div class="stat-header">
          <Calendar :size="24" color="#FB6340" />
          <h3>繁忙日期</h3>
        </div>
        <p class="stat-value">{{ busyDaysText }}</p>
        <p class="stat-desc">这些天的日程安排较为密集</p>
      </div>
      
      <div class="stat-card">
        <div class="stat-header">
          <TrendingUp :size="24" color="#2DCE89" />
          <h3>任务完成率</h3>
        </div>
        <p class="stat-value">{{ (statistics?.productivity?.completion_rate * 100 || 0).toFixed(1) }}%</p>
        <p class="stat-desc">过去 30 天的平均完成率</p>
      </div>
      
      <div class="stat-card">
        <div class="stat-header">
          <Target :size="24" color="#F5365C" />
          <h3>总任务数</h3>
        </div>
        <p class="stat-value">{{ statistics?.productivity?.total_tasks || 0 }}</p>
        <p class="stat-desc">过去 30 天创建的日程总数</p>
      </div>
    </div>
    
    <div v-if="activeTab === 'recommendations'" class="recommendations-content">
      <div v-for="(rec, index) in recommendations" :key="index" class="recommendation-card">
        <div class="rec-header">
          <span class="rec-type">{{ rec.type }}</span>
          <span class="rec-confidence">置信度：{{ (rec.confidence * 100).toFixed(0) }}%</span>
        </div>
        <h4>{{ rec.title }}</h4>
        <p>{{ rec.message }}</p>
      </div>
      
      <div v-if="recommendations.length === 0" class="empty-state">
        <p>暂无推荐，继续使用以获取更多智能建议吧！</p>
      </div>
    </div>
    
    <div v-if="activeTab === 'ai-chat'" class="ai-chat-container">
      <div class="chat-header">
        <div class="chat-title">
          <Sparkles :size="20" color="#5E72E4" />
          <h3>AI 日程分析助手</h3>
        </div>
        <button class="clear-btn" @click="clearChatHistory" title="清空对话历史">
          <RefreshCw :size="18" />
          <span>清空对话</span>
        </button>
      </div>
      
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
</template>

<style scoped>
.statistics-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background-color: white;
  color: #5E72E4;
  border: 2px solid #5E72E4;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.3s;
}

.back-btn:hover {
  background-color: #5E72E4;
  color: white;
  transform: translateX(-5px);
}

h1 {
  color: #32325D;
  margin: 0;
}

.tabs {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  border-bottom: 2px solid #e9ecef;
}

.tab-btn {
  padding: 0.75rem 1.5rem;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1rem;
  color: #525F7F;
  border-bottom: 2px solid transparent;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.tab-btn.active {
  color: #5E72E4;
  border-bottom-color: #5E72E4;
}

.overview-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.stat-card {
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(50, 50, 93, 0.11);
  transition: transform 0.3s;
}

.stat-card:hover {
  transform: translateY(-5px);
}

.stat-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.stat-header h3 {
  margin: 0;
  color: #32325D;
  font-size: 1rem;
}

.stat-value {
  font-size: 1.75rem;
  font-weight: bold;
  color: #5E72E4;
  margin: 0.5rem 0;
}

.stat-desc {
  color: #8898aa;
  font-size: 0.875rem;
  margin: 0;
}

.recommendations-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.recommendation-card {
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(50, 50, 93, 0.11);
  border-left: 4px solid #5E72E4;
}

.rec-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.rec-type {
  background: #e3f2fd;
  color: #1976d2;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.875rem;
  text-transform: capitalize;
}

.rec-confidence {
  color: #8898aa;
  font-size: 0.875rem;
}

.recommendation-card h4 {
  color: #32325D;
  margin: 0.5rem 0;
}

.recommendation-card p {
  color: #525F7F;
  line-height: 1.6;
  margin: 0;
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: #8898aa;
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