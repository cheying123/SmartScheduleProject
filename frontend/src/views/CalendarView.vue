<!-- NEW_FILE_CODE -->
<!-- frontend/src/views/CalendarView.vue -->
<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useUserStore } from '@/stores/user'
import { ChevronLeft, ChevronRight, Plus, Calendar as CalendarIcon } from 'lucide-vue-next'

const router = useRouter()
const userStore = useUserStore()
const API_URL = 'http://127.0.0.1:5000/api'

const currentDate = ref(new Date())
const schedules = ref([])
const selectedDate = ref(null)
const isLoading = ref(false)

onMounted(async () => {
  await fetchSchedules()
})

async function fetchSchedules() {
  try {
    isLoading.value = true
    const response = await axios.get(`${API_URL}/schedules`, {
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    })
    schedules.value = response.data
  } catch (error) {
    console.error('获取日程失败:', error)
  } finally {
    isLoading.value = false
  }
}

// 获取当前月份的天数网格
const calendarDays = computed(() => {
  const year = currentDate.value.getFullYear()
  const month = currentDate.value.getMonth()
  
  const firstDayOfMonth = new Date(year, month, 1)
  const lastDayOfMonth = new Date(year, month + 1, 0)
  
  const daysInMonth = lastDayOfMonth.getDate()
  const startingDayOfWeek = firstDayOfMonth.getDay() // 0 is Sunday
  
  const days = []
  
  // 填充上个月的空白
  for (let i = 0; i < startingDayOfWeek; i++) {
    days.push({ date: null, isPadding: true })
  }
  
  // 填充本月日期
  for (let day = 1; day <= daysInMonth; day++) {
    const date = new Date(year, month, day)
    days.push({ 
      date, 
      isPadding: false,
      isToday: isToday(date),
      isSelected: isSelected(date)
    })
  }
  
  return days
})

function isToday(date) {
  const today = new Date()
  return date.getDate() === today.getDate() &&
         date.getMonth() === today.getMonth() &&
         date.getFullYear() === today.getFullYear()
}

function isSelected(date) {
  if (!selectedDate.value) return false
  return date.getDate() === selectedDate.value.getDate() &&
         date.getMonth() === selectedDate.value.getMonth() &&
         date.getFullYear() === selectedDate.value.getFullYear()
}

function getSchedulesForDate(date) {
  if (!date) return []
  const dateStr = date.toISOString().split('T')[0]
  return schedules.value.filter(s => {
    const scheduleDate = new Date(s.start_time).toISOString().split('T')[0]
    return scheduleDate === dateStr
  }).sort((a, b) => new Date(a.start_time) - new Date(b.start_time))
}

function previousMonth() {
  currentDate.value = new Date(currentDate.value.getFullYear(), currentDate.value.getMonth() - 1, 1)
  selectedDate.value = null
}

function nextMonth() {
  currentDate.value = new Date(currentDate.value.getFullYear(), currentDate.value.getMonth() + 1, 1)
  selectedDate.value = null
}

function selectDate(dayObj) {
  if (dayObj.isPadding) return
  selectedDate.value = dayObj.date
}

function formatMonthYear(date) {
  return date.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long' })
}

function getPriorityColor(priority) {
  const colors = {
    1: '#e0e0e0', // 普通
    2: '#90caf9', // 一般
    3: '#ffcc80', // 重要
    4: '#ef9a9a', // 紧急
    5: '#e57373'  // 非常重要
  }
  return colors[priority] || '#e0e0e0'
}
</script>

<template>
  <div class="calendar-view-container">
    <div class="calendar-header">
      <h2>{{ formatMonthYear(currentDate) }}</h2>
      <div class="header-actions">
        <button @click="previousMonth" class="nav-btn"><ChevronLeft :size="20" /></button>
        <button @click="nextMonth" class="nav-btn"><ChevronRight :size="20" /></button>
        <button class="add-btn" @click="router.push('/')">
          <Plus :size="18" />
          <span>新建日程</span>
        </button>
      </div>
    </div>

    <div class="calendar-grid-wrapper">
      <!-- 星期标题 -->
      <div class="weekdays">
        <div v-for="day in ['日', '一', '二', '三', '四', '五', '六']" :key="day" class="weekday">
          {{ day }}
        </div>
      </div>

      <!-- 日期网格 -->
      <div class="days-grid">
        <div
          v-for="(dayObj, index) in calendarDays"
          :key="index"
          class="day-cell"
          :class="{ 
            'padding': dayObj.isPadding,
            'today': dayObj.isToday,
            'selected': dayObj.isSelected
          }"
          @click="selectDate(dayObj)"
        >
          <div v-if="!dayObj.isPadding" class="day-number">{{ dayObj.date.getDate() }}</div>
          
          <!-- 日程小圆点 -->
          <div v-if="!dayObj.isPadding" class="day-dots">
            <div 
              v-for="schedule in getSchedulesForDate(dayObj.date).slice(0, 4)" 
              :key="schedule.id"
              class="dot"
              :style="{ backgroundColor: getPriorityColor(schedule.priority) }"
              :title="schedule.title"
            ></div>
            <div v-if="getSchedulesForDate(dayObj.date).length > 4" class="more-dot">+</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 选中日期详情面板 -->
    <transition name="slide-up">
      <div v-if="selectedDate" class="details-panel">
        <div class="panel-header">
          <h3>{{ selectedDate.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' }) }}</h3>
          <button class="close-btn" @click="selectedDate = null">×</button>
        </div>
        
        <div class="panel-content">
          <div v-if="getSchedulesForDate(selectedDate).length === 0" class="empty-state">
            <CalendarIcon :size="48" color="#ccc" />
            <p>这一天没有安排日程</p>
          </div>
          
          <div v-else class="schedule-list">
            <div 
              v-for="schedule in getSchedulesForDate(selectedDate)" 
              :key="schedule.id"
              class="schedule-card"
            >
              <div class="time-badge">
                {{ new Date(schedule.start_time).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) }}
              </div>
              <div class="info">
                <div class="title">{{ schedule.title }}</div>
                <div v-if="schedule.content" class="content">{{ schedule.content }}</div>
                <div v-if="schedule.is_recurring" class="recurring-tag">🔄 重复日程</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.calendar-view-container {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
  height: calc(100vh - 80px);
  display: flex;
  flex-direction: column;
}

.calendar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.nav-btn {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.nav-btn:hover {
  background: #f5f5f5;
  border-color: #5E72E4;
  color: #5E72E4;
}

.add-btn {
  background: #5E72E4;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.5rem 1rem;
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.2s;
}

.add-btn:hover {
  background: #4a5fd1;
}

.calendar-grid-wrapper {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(50, 50, 93, 0.11);
  overflow: hidden;
  flex-grow: 1;
  display: flex;
  flex-direction: column;
}

.weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
}

.weekday {
  padding: 1rem;
  text-align: center;
  font-weight: 600;
  color: #8898aa;
  font-size: 0.9rem;
}

.days-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  grid-auto-rows: 1fr;
  flex-grow: 1;
}

.day-cell {
  border-right: 1px solid #f0f0f0;
  border-bottom: 1px solid #f0f0f0;
  padding: 8px;
  cursor: pointer;
  position: relative;
  transition: background 0.2s;
  min-height: 80px;
}

.day-cell:nth-child(7n) {
  border-right: none;
}

.day-cell:hover:not(.padding) {
  background: #f8f9fe;
}

.day-cell.padding {
  background: #fafafa;
  cursor: default;
}

.day-cell.today {
  background: #e3f2fd;
}

.day-cell.selected {
  background: #bbdefb;
  border: 2px solid #5E72E4;
}

.day-number {
  font-weight: 600;
  color: #32325D;
  margin-bottom: 4px;
}

.day-dots {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.more-dot {
  font-size: 10px;
  color: #8898aa;
}

/* 详情面板 */
.details-panel {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: white;
  border-top-left-radius: 20px;
  border-top-right-radius: 20px;
  box-shadow: 0 -4px 20px rgba(0,0,0,0.1);
  z-index: 100;
  max-height: 40vh;
  overflow-y: auto;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 2rem;
  border-bottom: 1px solid #f0f0f0;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #8898aa;
}

.panel-content {
  padding: 1.5rem 2rem;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #8898aa;
}

.schedule-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.schedule-card {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #5E72E4;
}

.time-badge {
  font-weight: 700;
  color: #5E72E4;
  min-width: 60px;
}

.info .title {
  font-weight: 600;
  color: #32325D;
  margin-bottom: 4px;
}

.info .content {
  font-size: 0.9rem;
  color: #8898aa;
}

.recurring-tag {
  font-size: 0.75rem;
  color: #2e7d32;
  background: #e8f5e9;
  padding: 2px 6px;
  border-radius: 4px;
  display: inline-block;
  margin-top: 4px;
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: transform 0.3s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(100%);
}

@media (max-width: 768px) {
  .calendar-view-container {
    padding: 1rem;
  }
  .day-cell {
    min-height: 50px;
  }
}
</style>