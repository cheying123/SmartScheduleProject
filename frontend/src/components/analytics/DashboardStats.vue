<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { CheckCircle, Clock, TrendingUp, Calendar } from 'lucide-vue-next'

const props = defineProps({
  API_URL: {
    type: String,
    required: true
  },
  token: {
    type: String,
    required: true
  }
})

const stats = ref({
  today: { total: 0, completed: 0, completion_rate: 0 },
  week: { total: 0, completed: 0, completion_rate: 0, focus_hours: 0 }
})
const isLoading = ref(false)

async function fetchStats() {
  try {
    isLoading.value = true
    const response = await axios.get(`${props.API_URL}/analytics/stats`, {
      headers: { 'Authorization': `Bearer ${props.token}` }
    })
    stats.value = response.data
  } catch (err) {
    console.error('获取统计数据失败:', err)
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  fetchStats()
})

defineExpose({ fetchStats })
</script>

<template>
  <div class="dashboard-stats">
    <h3 class="section-title">
      <TrendingUp :size="20" />
      数据统计
    </h3>
    
    <div v-if="isLoading" class="loading">加载中...</div>
    
    <div v-else class="stats-grid">
      <!-- 今日完成 -->
      <div class="stat-card">
        <div class="stat-icon today">
          <Calendar :size="24" />
        </div>
        <div class="stat-content">
          <div class="stat-label">今日完成</div>
          <div class="stat-value">
            {{ stats.today.completed }}/{{ stats.today.total }}
          </div>
          <div class="progress-bar">
            <div 
              class="progress-fill" 
              :style="{ width: stats.today.completion_rate + '%' }"
            ></div>
          </div>
          <div class="stat-rate">{{ stats.today.completion_rate }}%</div>
        </div>
      </div>
      
      <!-- 本周专注时长 -->
      <div class="stat-card">
        <div class="stat-icon week">
          <Clock :size="24" />
        </div>
        <div class="stat-content">
          <div class="stat-label">本周专注</div>
          <div class="stat-value">{{ stats.week.focus_hours }}h</div>
          <div class="stat-subtitle">总日程 {{ stats.week.completed }}/{{ stats.week.total }}</div>
        </div>
      </div>
      
      <!-- 本周完成率 -->
      <div class="stat-card">
        <div class="stat-icon rate">
          <CheckCircle :size="24" />
        </div>
        <div class="stat-content">
          <div class="stat-label">本周完成率</div>
          <div class="stat-value">{{ stats.week.completion_rate }}%</div>
          <div class="progress-bar">
            <div 
              class="progress-fill" 
              :style="{ width: stats.week.completion_rate + '%' }"
            ></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard-stats {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.section-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0 0 1.5rem 0;
  color: #32325D;
  font-size: 1.2rem;
  font-weight: 600;
}

.loading {
  text-align: center;
  padding: 2rem;
  color: #8898aa;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.25rem;
  background: linear-gradient(135deg, #f8f9fe 0%, #ffffff 100%);
  border-radius: 10px;
  border: 1px solid #e9ecef;
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(94, 114, 228, 0.15);
}

.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.stat-icon.today {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-icon.week {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-icon.rate {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-content {
  flex: 1;
}

.stat-label {
  font-size: 0.85rem;
  color: #8898aa;
  margin-bottom: 0.25rem;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #32325D;
  margin-bottom: 0.25rem;
}

.stat-subtitle {
  font-size: 0.75rem;
  color: #adb5bd;
}

.stat-rate {
  font-size: 0.75rem;
  color: #5E72E4;
  font-weight: 600;
  margin-top: 0.25rem;
}

.progress-bar {
  width: 100%;
  height: 6px;
  background-color: #e9ecef;
  border-radius: 3px;
  overflow: hidden;
  margin-top: 0.5rem;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #5E72E4 0%, #825EE4 100%);
  border-radius: 3px;
  transition: width 0.5s ease;
}
</style>
