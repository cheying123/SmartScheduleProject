<script setup>
import { Sun } from 'lucide-vue-next'
import ScheduleCard from './ScheduleCard.vue'

const props = defineProps({
  schedules: {
    type: Array,
    required: true
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
  }
})

const emit = defineEmits(['edit', 'delete'])
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
      <h2>今日无事，心随云飞</h2>
      <p>点击上方"新建日程"按钮，开始你的第一个日程吧！</p>
    </div>

    <!-- 日程列表 -->
    <transition-group name="list" tag="div" v-else>
      <div v-for="(schedulesOnDate, date) in groupedSchedules" 
           :key="date" 
           class="date-group">
        <h3 class="date-header">{{ date }}</h3>
        <ul class="schedule-list">
          <ScheduleCard
            v-for="schedule in schedulesOnDate"
            :key="schedule.id"
            :schedule="schedule"
            @edit="$emit('edit', $event)"
            @delete="$emit('delete', $event)"
          />
        </ul>
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