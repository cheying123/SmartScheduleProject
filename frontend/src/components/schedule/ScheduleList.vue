<script setup>
import { Sun, Clock, Archive, Search } from 'lucide-vue-next'
import ScheduleCard from './ScheduleCard.vue'

const props = defineProps({
  schedules: {
    type: Array,
    required: true
  },
  upcomingSchedules: {
    type: Array,
    default: () => []
  },
  pastSchedules: {
    type: Array,
    default: () => []
  },
  groupedUpcomingSchedules: {
    type: Object,
    default: () => ({})
  },
  groupedPastSchedules: {
    type: Object,
    default: () => ({})
  },
  isLoading: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: null
  },
  groupedSchedules: {
    type: Object,
    required: true
  },
  searchQuery: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['edit', 'delete', 'complete'])
</script>

<template>
  <div class="content-body">
    <!-- 加载状态 -->
    <div v-if="isLoading" class="loading-spinner"></div>
    
    <!-- 错误提示 -->
    <div v-if="error" class="error-msg">{{ error }}</div>
    
    <!-- 空状态 -->
    <div v-if="!isLoading && !error && schedules.length === 0" class="empty-state">
      <Sun :size="64" />
      <h2 v-if="!searchQuery">今日无事，心随云飞</h2>
      <h2 v-else>未找到匹配的日程</h2>
      <p v-if="!searchQuery">点击上方"新建日程"按钮，开始你的第一个日程吧！</p>
      <p v-else>试试其他关键词？</p>
    </div>

    <!-- 日程列表 -->
    <transition-group name="list" tag="div" v-else>
      <!-- 搜索提示 -->
      <div v-if="searchQuery && schedules.length > 0" class="search-hint">
        <Search :size="16" />
        <span>找到 {{ schedules.length }} 个匹配的日程</span>
      </div>

      <!-- 未过期日程区域 -->
      <div v-if="upcomingSchedules.length > 0" class="schedule-section upcoming-section">
        <div class="section-header">
          <Clock :size="20" />
          <h3>即将开始</h3>
          <span class="count-badge">{{ upcomingSchedules.length }}</span>
        </div>
        
        <div v-for="(schedulesOnDate, date) in groupedUpcomingSchedules" 
             :key="'upcoming-' + date" 
             class="date-group">
          <h4 class="date-header">{{ date }}</h4>
          <ul class="schedule-list">
            <ScheduleCard
              v-for="schedule in schedulesOnDate"
              :key="`${schedule.id}-${schedule.is_completed}`"
              :schedule="schedule"
              @edit="$emit('edit', $event)"
              @delete="$emit('delete', schedule.id)"
              @complete="$emit('complete', $event)"
            />
          </ul>
        </div>
      </div>

      <!-- 已过期日程区域 -->
      <div v-if="pastSchedules.length > 0" class="schedule-section past-section">
        <div class="section-header">
          <Archive :size="20" />
          <h3>历史记录</h3>
          <span class="count-badge">{{ pastSchedules.length }}</span>
        </div>
        
        <div v-for="(schedulesOnDate, date) in groupedPastSchedules" 
             :key="'past-' + date" 
             class="date-group">
          <h4 class="date-header">{{ date }}</h4>
          <ul class="schedule-list">
            <ScheduleCard
              v-for="schedule in schedulesOnDate"
              :key="`${schedule.id}-${schedule.is_completed}`"
              :schedule="schedule"
              @edit="$emit('edit', $event)"
              @delete="$emit('delete', schedule.id)"
              @complete="$emit('complete', $event)"
            />
          </ul>
        </div>
      </div>
    </transition-group>
  </div>
</template>

<style scoped>
/* 加载动画 */
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

/* 错误提示 */
.error-msg {
  text-align: center;
  background-color: #fdd;
  color: #c00;
  padding: 1rem;
  border-radius: 8px;
  margin: 2rem 0;
}

/* 空状态 */
.empty-state {
  text-align: center;
  margin-top: 4rem;
  color: #adb5bd;
  padding: 3rem 1rem;
}

.empty-state h2 {
  color: #32325D;
  margin: 1rem 0 0.5rem 0;
  font-size: 1.5rem;
}

.empty-state p {
  color: #8898aa;
  font-size: 1rem;
}

/* 日期分组 */
.date-group {
  margin-bottom: 2rem;
}

.date-header {
  color: #32325D;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #e9ecef;
  margin-bottom: 1rem;
  font-size: 1.2rem;
  font-weight: 600;
}

/* 搜索提示 */
.search-hint {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background-color: #e8f4fd;
  border-left: 4px solid #5E72E4;
  border-radius: 6px;
  margin-bottom: 1.5rem;
  color: #32325D;
  font-size: 0.9rem;
  font-weight: 500;
}

/* 日程区域分隔 */
.schedule-section {
  margin-bottom: 3rem;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 0;
  margin-bottom: 1.5rem;
  border-bottom: 2px solid #e9ecef;
}

.section-header h3 {
  margin: 0;
  font-size: 1.3rem;
  color: #32325D;
  font-weight: 600;
}

.section-header svg {
  color: #5E72E4;
}

.count-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  height: 28px;
  padding: 0 8px;
  background-color: #5E72E4;
  color: white;
  border-radius: 14px;
  font-size: 0.85rem;
  font-weight: 600;
  margin-left: auto;
}

/* 即将开始区域 */
.upcoming-section {
  animation: fadeIn 0.5s ease;
}

/* 历史记录区域 */
.past-section {
  opacity: 0.85;
  background-color: #f8f9fa;
  padding: 1.5rem;
  border-radius: 12px;
  margin-top: 2rem;
}

.past-section .section-header {
  border-bottom-color: #dee2e6;
}

.past-section .section-header h3 {
  color: #6c757d;
}

.past-section .section-header svg {
  color: #6c757d;
}

.past-section .count-badge {
  background-color: #6c757d;
}

.past-section .date-header {
  color: #6c757d;
  border-bottom-color: #dee2e6;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.schedule-list {
  padding: 0;
  margin: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* 列表过渡动画 */
.list-enter-active, .list-leave-active {
  transition: all 0.5s ease;
}

.list-enter-from, .list-leave-to {
  opacity: 0;
  transform: translateX(30px);
}
</style>