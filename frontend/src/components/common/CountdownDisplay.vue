<!-- 文件路径：d:\SmartScheduleProject\frontend\src\components\common\CountdownDisplay.vue -->
<!-- 操作：新建此文件 -->

<script setup>
import { Clock, AlertCircle, Bell, Calendar } from 'lucide-vue-next'
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  targetTime: {
    type: String,
    required: true
  },
  title: {
    type: String,
    default: ''
  },
  showIcon: {
    type: Boolean,
    default: true
  },
  size: {
    type: String,
    default: 'normal', // small, normal, large
    validator: (value) => ['small', 'normal', 'large'].includes(value)
  },
  reminderConfig: {
    type: String,
    default: 'standard', // minimal, standard, comprehensive, important
    validator: (value) => ['minimal', 'standard', 'comprehensive', 'important'].includes(value)
  }
})

const remainingSeconds = ref(0)
const isStarted = ref(false)
const shouldRemind = ref(false)
const urgencyLevel = ref('low')
let timer = null

// 更新倒计时
function updateCountdown() {
  const target = new Date(props.targetTime)
  const now = new Date()
  const diff = target - now
  
  remainingSeconds.value = Math.floor(diff / 1000)
  isStarted.value = remainingSeconds.value <= 0
  
  // 计算紧急程度
  const minutes = Math.abs(remainingSeconds.value) / 60
  if (minutes <= 5) {
    urgencyLevel.value = 'urgent'
  } else if (minutes <= 15) {
    urgencyLevel.value = 'high'
  } else if (minutes <= 60) {
    urgencyLevel.value = 'medium'
  } else if (minutes <= 1440) {
    urgencyLevel.value = 'low'
  } else {
    urgencyLevel.value = 'info'
  }
  
  // 检查是否需要提醒（在提醒点前后 1 分钟内）
  const reminderPoints = getReminderPoints(props.reminderConfig)
  shouldRemind.value = reminderPoints.some(point => {
    return Math.abs(minutes - point) <= 1 && remainingSeconds.value > 0
  })
}

// 获取提醒点配置
function getReminderPoints(config) {
  const configs = {
    minimal: [5, 15],
    standard: [15, 30, 60],
    comprehensive: [15, 30, 60, 120, 1440],
    important: [30, 60, 120, 1440, 2880]
  }
  return configs[config] || configs.standard
}

// 格式化倒计时文本
const countdownText = computed(() => {
  const seconds = Math.abs(remainingSeconds.value)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)
  
  if (remainingSeconds.value >= 0) {
    // 还未开始
    if (days > 0) {
      const remainingHours = hours % 24
      return `${days}天${remainingHours}小时`
    } else if (hours > 0) {
      const remainingMinutes = minutes % 60
      return `${hours}小时${remainingMinutes}分钟`
    } else if (minutes > 0) {
      return `${minutes}分钟`
    } else {
      return `${seconds}秒`
    }
  } else {
    // 已开始
    if (days > 0) {
      return `已开始${days}天`
    } else if (hours > 0) {
      return `已开始${hours}小时`
    } else if (minutes > 0) {
      return `已开始${minutes}分钟`
    } else {
      return `刚开始`
    }
  }
})

// 提醒消息
const remindMessage = computed(() => {
  if (!shouldRemind.value) return ''
  
  const minutes = Math.floor(Math.abs(remainingSeconds.value) / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)
  
  if (days >= 1) {
    return days === 1 ? '明天这个时候就要开始了' : `还有${days}天就要开始了`
  } else if (hours >= 1) {
    return `还有${hours}小时就要开始了`
  } else if (minutes >= 30) {
    return `还有${minutes}分钟，请尽快准备`
  } else {
    return `还有${minutes}分钟，请立即准备`
  }
})

// 样式类
const containerClass = computed(() => {
  const baseClass = 'countdown-container'
  const sizeClass = `countdown-${props.size}`
  const urgencyClass = `urgency-${urgencyLevel.value}`
  const remindClass = shouldRemind.value ? 'should-remind' : ''
  
  return `${baseClass} ${sizeClass} ${urgencyClass} ${remindClass}`
})

const iconComponent = computed(() => {
  if (shouldRemind.value) return Bell
  if (isStarted.value) return Clock
  if (urgencyLevel.value === 'urgent') return AlertCircle
  if (urgencyLevel.value === 'high') return Bell
  return Calendar
})

onMounted(() => {
  updateCountdown()
  timer = setInterval(updateCountdown, 1000) // 每秒更新
})

onUnmounted(() => {
  if (timer) {
    clearInterval(timer)
  }
})
</script>

<template>
  <div :class="containerClass">
    <component 
      v-if="showIcon" 
      :is="iconComponent" 
      :size="size === 'small' ? 14 : (size === 'large' ? 24 : 18)"
      class="countdown-icon"
    />
    <div class="countdown-content">
      <div class="countdown-time">
        {{ countdownText }}
      </div>
      <div v-if="remindMessage" class="countdown-message">
        {{ remindMessage }}
      </div>
      <div v-if="title && !remindMessage" class="countdown-title">
        {{ title }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.countdown-container {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  font-size: 0.9rem;
  transition: all 0.3s ease;
  background-color: #f8f9fe;
  border-left: 3px solid #5E72E4;
}

.countdown-small {
  padding: 0.5rem 0.75rem;
  font-size: 0.8rem;
  gap: 0.5rem;
}

.countdown-large {
  padding: 1rem 1.25rem;
  font-size: 1rem;
  gap: 1rem;
}

/* 紧急程度样式 */
.urgency-info {
  background-color: #f8f9fa;
  border-left-color: #6c757d;
}

.urgency-low {
  background-color: #e7f3ff;
  border-left-color: #2196F3;
}

.urgency-medium {
  background-color: #fff3cd;
  border-left-color: #ffc107;
}

.urgency-high {
  background-color: #ffe5cc;
  border-left-color: #ff9800;
}

.urgency-urgent {
  background-color: #ffebee;
  border-left-color: #f44336;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(244, 67, 54, 0.4);
  }
  50% {
    box-shadow: 0 0 0 10px rgba(244, 67, 54, 0);
  }
}

.should-remind {
  animation: shake 0.5s;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-5px); }
  75% { transform: translateX(5px); }
}

.countdown-icon {
  flex-shrink: 0;
}

.urgency-urgent .countdown-icon {
  color: #f44336;
}

.urgency-high .countdown-icon {
  color: #ff9800;
}

.urgency-medium .countdown-icon {
  color: #ffc107;
}

.urgency-low .countdown-icon {
  color: #2196F3;
}

.countdown-content {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.countdown-time {
  font-weight: 600;
  color: #32325D;
}

.countdown-message {
  font-size: 0.85em;
  color: #f44336;
  font-weight: 500;
}

.countdown-title {
  font-size: 0.85em;
  color: #8898aa;
}

/* 小尺寸下的样式调整 */
.countdown-small .countdown-time {
  font-size: 0.9em;
}

.countdown-small .countdown-message,
.countdown-small .countdown-title {
  font-size: 0.8em;
}

/* 大尺寸下的样式调整 */
.countdown-large .countdown-time {
  font-size: 1.2em;
  font-weight: 700;
}

.countdown-large .countdown-message {
  font-size: 1em;
}
</style>