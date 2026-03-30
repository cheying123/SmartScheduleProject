<script setup>
import { Bell, Sun, Check, Globe } from 'lucide-vue-next'

const props = defineProps({
  recommendations: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['refresh'])

const NOTIFICATION_TITLES = {
  weather: '🌤️ 天气提示',
  time_preference: '⏰ 时间偏好',
  balance: '😌 平衡建议',
  info: 'ℹ️ 提示信息'
}

function getIcon(type) {
  switch(type) {
    case 'weather':
      return Sun
    case 'time_preference':
      return Check
    default:
      return Globe
  }
}

function getTitle(type) {
  return NOTIFICATION_TITLES[type] || '智能推荐'
}
</script>

<template>
  <div class="notifications-panel">
    <button class="refresh-btn" @click="$emit('refresh')">
      <Check :size="18" />
      <span>刷新推荐</span>
    </button>
    
    <div v-if="recommendations.length === 0" class="empty-notifications">
      <Bell :size="64" />
      <h3>暂无新消息</h3>
      <p>点击"刷新推荐"获取智能建议</p>
    </div>
    
    <div v-else class="notifications-list">
      <div 
        v-for="(rec, index) in recommendations" 
        :key="index" 
        class="notification-item"
        :class="'type-' + rec.type"
      >
        <div class="notification-icon">
          <component :is="getIcon(rec.type)" :size="24" />
        </div>
        <div class="notification-content">
          <h4>{{ getTitle(rec.type) }}</h4>
          <p>{{ rec.message }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.notifications-panel {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(50, 50, 93, 0.11), 0 1px 3px rgba(0, 0, 0, 0.08);
}

.refresh-btn {
  background-color: #2dce89;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.75rem 1.5rem;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  transition: all 0.2s;
}

.refresh-btn:hover {
  background-color: #26b87a;
}

.empty-notifications {
  text-align: center;
  padding: 4rem 2rem;
  color: #adb5bd;
}

.empty-notifications h3 {
  color: #32325D;
  margin: 1rem 0 0.5rem 0;
  font-size: 1.2rem;
}

.empty-notifications p {
  color: #8898aa;
  font-size: 0.95rem;
}

.notifications-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.notification-item {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1rem;
  border-radius: 8px;
  background-color: #f8f9fe;
  border-left: 4px solid #5E72E4;
  transition: transform 0.2s;
}

.notification-item:hover {
  transform: translateX(4px);
}

.notification-item.type-weather {
  background-color: #e3f9e5;
  border-left-color: #2dce89;
}

.notification-item.type-balance {
  background-color: #fff3cd;
  border-left-color: #ffc107;
}

.notification-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background-color: rgba(94, 114, 228, 0.1);
  color: #5E72E4;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.type-weather .notification-icon {
  background-color: rgba(45, 206, 137, 0.1);
  color: #2dce89;
}

.type-balance .notification-icon {
  background-color: rgba(255, 193, 7, 0.1);
  color: #ffc107;
}

.notification-content h4 {
  margin: 0 0 0.5rem 0;
  color: #32325D;
  font-size: 1rem;
}

.notification-content p {
  margin: 0;
  color: #525F7F;
  font-size: 0.9rem;
  line-height: 1.5;
}
</style>