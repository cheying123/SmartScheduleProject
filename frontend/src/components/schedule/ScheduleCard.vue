<script setup>
import { Edit2, Trash2 } from 'lucide-vue-next'
import { formatDate, isPastSchedule } from '@/utils/timeUtils'

const props = defineProps({
  schedule: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['edit', 'delete'])

function handleEdit() {
  emit('edit', props.schedule)
}

function handleDelete() {
  if (confirm('确定要删除这个日程吗？')) {
    emit('delete', props.schedule.id)
  }
}
</script>

<template>
  <li class="schedule-item">
    <div class="item-time">{{ formatDate(schedule.start_time, 'time') }}</div>
    <div class="item-content">
      <h4>{{ schedule.title }}</h4>
      <p v-if="schedule.content">{{ schedule.content }}</p>
      
      <!-- 天气信息 -->
      <div v-if="schedule.weather_info" class="item-weather">
        {{ schedule.weather_info }}
        <span v-if="isPastSchedule(schedule.start_time)" class="expired-tag">
          (已过期)
        </span>
      </div>
      <div v-else-if="isPastSchedule(schedule.start_time)" class="item-weather expired">
        已过期
      </div>
      
      <!-- 优先级标签 -->
      <div v-if="schedule.priority >= 4" class="item-priority priority-high">
        🔴 高优先级
      </div>
      
      <!-- 重复日程标签 -->
      <div v-if="schedule.is_recurring" class="item-recurring">
        🔄 
        {{ schedule.recurring_pattern === 'weekly' ? '每周重复' : 
           schedule.recurring_pattern === 'daily' ? '每天重复' : '每月重复' }}
      </div>
    </div>
    
    <!-- 操作按钮 -->
    <div class="item-actions">
      <button class="action-btn" @click="handleEdit" title="编辑">
        <Edit2 :size="20"/>
      </button>
      <button class="action-btn action-btn-delete" @click="handleDelete" title="删除">
        <Trash2 :size="20"/>
      </button>
    </div>
  </li>
</template>

<style scoped>
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
  flex-shrink: 0;
}

.item-content {
  flex-grow: 1;
}

.item-content h4 {
  margin: 0 0 0.25rem 0;
  color: #32325D;
  font-size: 1rem;
}

.item-content p {
  margin: 0;
  font-size: 0.9rem;
  color: #8898aa;
}

.item-weather {
  margin-top: 0.5rem;
  font-size: 0.8rem;
  background-color: #e3f2fd;
  color: #1976d2;
  padding: 0.3rem 0.6rem;
  border-radius: 4px;
  display: inline-block;
}

.item-weather.expired {
  background-color: #ffebee;
  color: #c62828;
  font-style: italic;
}

.expired-tag {
  margin-left: 0.5rem;
  font-size: 0.75rem;
  color: #ff9800;
  font-weight: 600;
  font-style: italic;
}

.item-priority {
  margin-top: 0.5rem;
  font-size: 0.8rem;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  display: inline-block;
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
  margin-left: 0.5rem;
}

.item-actions {
  display: flex;
  gap: 0.5rem;
  flex-shrink: 0;
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
  border-radius: 4px;
}

.action-btn:hover {
  color: #5E72E4;
  background-color: #f8f9fe;
}

.action-btn-delete:hover {
  color: #f5365c;
  background-color: #fff5f5;
}
</style>