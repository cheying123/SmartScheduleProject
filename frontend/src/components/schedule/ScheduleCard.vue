<script setup>
import { Edit2, Trash2, Clock, Sun, Check, Globe, MapPin } from 'lucide-vue-next'
import WeatherAlertList from '../common/WeatherAlertList.vue'
import CountdownDisplay from '../common/CountdownDisplay.vue'

const props = defineProps({
  schedule: {
    type: Object,
    required: true
  },
  showWeatherAlerts: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['edit', 'delete', 'complete'])

function handleEdit() {
  emit('edit', props.schedule)
}

function handleDelete() {
  emit('delete', props.schedule.id)
}

function handleComplete() {
  emit('complete', props.schedule.id)
}

/**
 * 判断日程是否已开始（当前时间 >= 开始时间）
 */
function isPastSchedule(startTime) {
  if (!startTime) return false
  return new Date(startTime) < new Date()
}

/**
 * 判断日程是否已结束（当前时间 > 结束时间，或没有结束时间但已开始超过1小时）
 */
function isScheduleEnded(startTime, endTime) {
  if (!startTime) return false
  
  const now = new Date()
  const start = new Date(startTime)
  
  // 如果有结束时间，判断当前时间是否超过结束时间
  if (endTime) {
    const end = new Date(endTime)
    return now > end
  }
  
  // 如果没有结束时间，假设持续时间为1小时，判断是否已超过
  const assumedEndTime = new Date(start.getTime() + 60 * 60 * 1000) // 开始时间 + 1小时
  return now > assumedEndTime
}

/**
 * 获取日程状态文本
 */
function getScheduleStatusText() {
  const startTime = props.schedule.start_time
  const endTime = props.schedule.end_time
  
  if (!startTime) return ''
  
  // 先判断是否已结束
  if (isScheduleEnded(startTime, endTime)) {
    return '已结束'
  }
  
  // 再判断是否已开始但未结束
  if (isPastSchedule(startTime)) {
    return '进行中'
  }
  
  // 还未开始
  return ''
}

/**
 * 根据状态返回对应的 CSS 类名
 */
function getStatusClass() {
  const status = getScheduleStatusText()
  if (status === '已结束') return 'status-ended'
  if (status === '进行中') return 'status-ongoing'
  return ''
}

function isExpiredDate(startTime) {
  if (!startTime) return false
  
  const scheduleDate = new Date(startTime)
  const today = new Date()
  
  // 只比较日期部分，不比较时间
  const scheduleDateOnly = new Date(scheduleDate.getFullYear(), scheduleDate.getMonth(), scheduleDate.getDate())
  const todayDateOnly = new Date(today.getFullYear(), today.getMonth(), today.getDate())
  
  // 只有昨天的日期及之前才算过期
  return scheduleDateOnly < todayDateOnly
}

function formatTime(isoString) {
  if (!isoString) return ''
  // 修复：确保带 Z 后缀，强制浏览器按 UTC 解析后再转为本地时间显示
  const utcString = isoString.endsWith('Z') ? isoString : isoString + 'Z'
  const date = new Date(utcString)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false })
}

function getRecurringText(pattern) {
  const map = {
    'daily': '每日',
    'weekly': '每周',
    'monthly': '每月'
  }
  return map[pattern] || '重复'
}

</script>

<template>
  <li class="schedule-item" :class="{ 'past-schedule': isPastSchedule(schedule.start_time) }">
    <!-- 时间显示 -->
    <div class="item-time">
      <span class="time-text">{{ formatTime(schedule.start_time) }}</span>
      <span v-if="getScheduleStatusText()" class="status-badge" :class="getStatusClass()">
        {{ getScheduleStatusText() }}
      </span>
    </div>
    
    <!-- 内容区域 -->
    <div class="item-content">
      <h4>{{ schedule.title }}</h4>
      <p v-if="schedule.content">{{ schedule.content }}</p>
      
      <!-- 倒计时显示（新增） -->
      <CountdownDisplay 
        v-if="schedule.countdown"
        :target-time="schedule.start_time"
        :title="schedule.title"
        size="small"
        :show-icon="true"
        class="schedule-countdown"
      />
      
      <!-- 位置信息 -->
      <div v-if="schedule.location" class="item-location">
        <MapPin :size="14" />
        <span>{{ schedule.location }}</span>
      </div>
      
      <!-- 天气信息 -->
      <div v-if="schedule.weather_info" class="item-weather">
        {{ schedule.weather_info }}
        <span v-if="isExpiredDate(schedule.start_time)" class="expired-tag">
        (已过期)
      </span>
      </div>
      
      <!-- 智能天气提醒 -->
      <WeatherAlertList 
        v-if="showWeatherAlerts && schedule.weather_alerts && schedule.weather_alerts.length > 0"
        :alerts="schedule.weather_alerts"
        :compact="true"
        :max-visible="1"
      />
      
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
      <!-- 完成按钮（仅在未完成且未结束时显示） -->
      <button 
        v-if="!schedule.is_completed && !isScheduleEnded(schedule.start_time, schedule.end_time)"
        class="action-btn action-btn-complete" 
        @click="handleComplete" 
        title="标记为已完成"
      >
        <Check :size="20"/>
      </button>
      
      <!-- 已完成标记（已完成后显示） -->
      <div v-if="schedule.is_completed" class="completed-badge" title="已完成">
        <Check :size="18"/>
      </div>
      
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

.schedule-item.past-schedule {
  opacity: 0.7;
  background-color: #f8f9fa;
}

.item-time {
  font-size: 1.2rem;
  font-weight: 700;
  color: #5E72E4;
  margin-right: 1.5rem;
  width: 70px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.3rem;
}

.time-text {
  font-size: 1.2rem;
  font-weight: 700;
}

/* 状态徽章样式 */
.status-badge {
  display: inline-block;
  padding: 0.15rem 0.5rem;
  border-radius: 10px;
  font-size: 0.65rem;
  font-weight: 600;
  white-space: nowrap;
  animation: fadeIn 0.3s ease;
}

/* 进行中的状态 - 橙色 */
.status-ongoing {
  background-color: #fff3e0;
  color: #f57c00;
  border: 1px solid #ffb74d;
}

/* 已结束的状态 - 灰色 */
.status-ended {
  background-color: #f5f5f5;
  color: #757575;
  border: 1px solid #bdbdbd;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: scale(0.9);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
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

.schedule-countdown {
  margin-top: 0.5rem;
}

.item-location {
  margin-top: 0.5rem;
  font-size: 0.8rem;
  display: flex;
  align-items: center;
  gap: 0.3rem;
  color: #525F7F;
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
  margin-left: 1rem;
}

.action-btn {
  width: 36px;
  height: 36px;
  border: none;
  background-color: #f0f0f0;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.action-btn:hover {
  background-color: #5E72E4;
  color: white;
}

.action-btn-delete:hover {
  background-color: #f44336;
  color: white;
}

/* 完成按钮样式 */
.action-btn-complete {
  background-color: #e8f5e9;
  color: #2e7d32;
}

.action-btn-complete:hover {
  background-color: #4caf50;
  color: white;
}

/* 已完成标记徽章 */
.completed-badge {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #4caf50;
  color: white;
  border-radius: 6px;
  animation: completePulse 0.5s ease;
}

@keyframes completePulse {
  0% {
    transform: scale(0.8);
    opacity: 0;
  }
  50% {
    transform: scale(1.1);
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

.recurring-badge {
  font-size: 0.75rem;
  background-color: #e3f2fd;
  color: #1976d2;
  padding: 2px 8px;
  border-radius: 12px;
  margin-right: 8px;
  font-weight: 600;
}

.status-badge {
  font-size: 0.75rem;
  background-color: #e3f2fd;
  color: #1976d2;
  padding: 2px 8px;
  border-radius: 12px;
  margin-left: 8px;
  font-weight: 600;
}

.status-ended {
  background-color: #ffebee;
  color: #c62828;
}

.status-ongoing {
  background-color: #e8f5e9;
  color: #2e7d32;
}
</style>