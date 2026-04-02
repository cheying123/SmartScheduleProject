
<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useUserStore } from '@/stores/user'
import { Clock, TrendingUp, Calendar, Target , ArrowLeft} from 'lucide-vue-next'

const API_URL = 'http://127.0.0.1:5000/api'
const userStore = useUserStore()
const router = useRouter() // 确保有这行

const statistics = ref(null)
const recommendations = ref([])
const isLoading = ref(true)
const activeTab = ref('overview')

const weekdayMap = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']


// 新增：返回主页函数
function goBack() {
  router.push('/')
}


async function loadStatistics() {
  try {

    console.log('🔍 ========== 开始加载统计数据 ==========')
    console.log('🔍 userStore.token:', userStore.token)
    console.log('🔍 Token 类型:', typeof userStore.token)
    console.log('🔍 Token 长度:', userStore.token?.length)
    console.log('🔍 Token 前 20 个字符:', userStore.token?.substring(0, 20))

    if (!userStore.token) {
      console.error('❌ 未找到 token，请先登录')
      router.push('/login')
      return
    }
    
    // 检查 token 格式
    const authHeader = `Bearer ${userStore.token}`
    console.log('🔍 Authorization Header:', authHeader.substring(0, 30) + '...')

    const response = await axios.get(`${API_URL}/analytics/statistics`, {
      headers: {
        'Authorization': authHeader,
        'Content-Type': 'application/json'
      }
    })
    console.log('✅ 统计数据加载成功:', response.data)
    statistics.value = response.data
  } catch (error) {
    console.error('❌ 加载统计数据失败:')
    console.error('❌ 错误对象:', error)
    console.error('❌ 错误响应:', error.response)
    console.error('❌ 错误状态码:', error.response?.status)
    console.error('❌ 错误数据:', error.response?.data)
    console.error('❌ 请求头:', error.config?.headers)

    if (error.response?.status === 422) {
      console.error('❌ Token 无效或格式错误')
      console.error('❌ 后端返回的错误信息:', error.response.data)
    }
  } finally {
    isLoading.value = false
  }
}

async function loadRecommendations() {
  try {

    console.log('🔍 ========== 开始加载推荐数据 ==========')
    console.log('🔍 userStore.token:', userStore.token)
    
    if (!userStore.token) {
      console.error('❌ 未找到 token，请先登录')
      return
    }


    const response = await axios.get(`${API_URL}/analytics/recommendations`, {
      headers: {
        'Authorization': `Bearer ${userStore.token}`,
        'Content-Type': 'application/json'
      }
    })

    console.log('✅ 推荐加载成功:', response.data)
    recommendations.value = response.data.recommendations
  } catch (error) {
    console.error('❌ 加载推荐失败:')
    console.error('❌ 错误响应:', error.response)
    console.error('❌ 错误状态码:', error.response?.status)
    console.error('❌ 错误数据:', error.response?.data)
    
    if (error.response?.status === 422) {
      console.error('❌ Token 无效或格式错误')
      console.error('❌ 后端返回的错误信息:', error.response.data)
    }
  }
}

const productiveHoursText = computed(() => {
  if (!statistics.value?.productivity?.productive_hours?.length) return '暂无数据'
  const hours = statistics.value.productivity.productive_hours
  return hours.map(h => `${h}点`).join('、')
})

const busyDaysText = computed(() => {
  if (!statistics.value?.weekly_pattern?.busy_days?.length) return '暂无数据'
  const days = statistics.value.weekly_pattern.busy_days
  return days.map(d => weekdayMap[d]).join('、')
})

onMounted(() => {
  loadStatistics()
  loadRecommendations()
})
</script>

<template>
  <div class="statistics-container">
     <!-- 新增：返回按钮 -->
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
        @click="activeTab = 'overview'"
      >
        总览
      </button>
      <button 
        :class="['tab-btn', { active: activeTab === 'recommendations' }]"
        @click="activeTab = 'recommendations'"
      >
        智能推荐
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
          <Target :size="24" color="#11CDEF" />
          <h3>平均任务时长</h3>
        </div>
        <p class="stat-value">
          {{ statistics?.duration_preference?.average_duration_minutes || 0 }} 分钟
        </p>
        <p class="stat-desc">建议适时休息，保持专注力</p>
      </div>
      
      <div class="stat-card">
        <div class="stat-header">
          <TrendingUp :size="24" color="#2DCE89" />
          <h3>任务完成率</h3>
        </div>
        <p class="stat-value">
          {{ ((statistics?.productivity?.completion_rate || 0) * 100).toFixed(1) }}%
        </p>
        <p class="stat-desc">继续保持良好的执行力！</p>
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
  </div>
</template>

<style scoped>
.statistics-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

/* 新增：页面头部样式 */
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
  margin-bottom: 2rem;
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
</style>