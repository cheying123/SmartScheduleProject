<template>
  <div class="notifications-panel">
    <!-- 头部统计 -->
    <div class="notifications-header">
      <div class="header-title">
        <Bell :size="24" class="bell-icon" />
        <h3>智能通知中心</h3>
      </div>
      
      <!-- 统计徽章 -->
      <div v-if="recommendations && recommendations.length > 0" class="stats-badges">
        <span v-if="timePreferenceCount > 0" class="stat-badge time-pref">
          <Check :size="14" />
          {{ timePreferenceCount }} 习惯
        </span>
        <span v-if="balanceCount > 0" class="stat-badge balance">
          <Globe :size="14" />
          {{ balanceCount }} 建议
        </span>
        <span v-if="urgentCount > 0" class="stat-badge urgent">
          <AlertCircle :size="14" />
          {{ urgentCount }} 紧急
        </span>
        <span v-if="scheduleReminderCount > 0" class="stat-badge schedule">
          <Clock :size="14" />
          {{ scheduleReminderCount }} 日程
        </span>
        <span class="stat-badge total">
          共 {{ recommendations.length }} 条
        </span>
      </div>
    </div>

    <!-- 工具栏 -->
    <div class="notifications-toolbar">
      <button class="btn-refresh" @click="loadRecommendations">
        <Sparkles :size="16" />
        <span>刷新推荐</span>
      </button>
      
      <div class="filter-group">
        <Filter :size="16" class="filter-icon" />
        <select v-model="notificationFilter" class="filter-select">
          <option value="all">全部类型</option>
          <option value="time_preference">时间偏好</option>
          <option value="balance">平衡建议</option>
          <option value="schedule_reminder">日程提醒</option>
          <option value="weather">天气提示</option>
          <option value="info">提示信息</option>
        </select>
      </div>
    </div>
    
    <!-- 空状态 -->
    <div v-if="!filteredRecommendations || filteredRecommendations.length === 0" class="empty-notifications">
      <div class="empty-icon">
        <Bell :size="80" />
      </div>
      <h3>{{ notificationFilter === 'all' ? '暂无新消息' : '该类型暂无通知' }}</h3>
      <p>{{ notificationFilter === 'all' ? '点击"刷新推荐"获取智能建议' : '尝试切换其他类型查看' }}</p>
      <button v-if="notificationFilter !== 'all'" class="btn-clear-filter" @click="notificationFilter = 'all'">
        查看全部
      </button>
    </div>
    
    <!-- 通知列表 -->
    <div v-else class="notifications-list">
      <!-- 按类型分组显示 -->
      <div 
        v-for="(items, type) in groupedNotifications" 
        :key="type"
        class="notification-group"
      >
        <!-- 类型标题 -->
        <div class="group-header">
          <component 
            :is="getNotificationIcon(type)" 
            :size="18" 
            class="group-icon"
            :style="{ color: getNotificationColor(type) }"
          />
          <span class="group-title">{{ getNotificationTitle(type) }}</span>
          <span class="group-count">{{ items.length }}</span>
        </div>

        <!-- 该类型的通知列表 -->
        <div class="group-items">
          <div 
            v-for="(rec, index) in items" 
            :key="rec.id || index"
            class="notification-item"
            :class="[
              rec.type === 'schedule_reminder' ? 'type-schedule-reminder' : ('type-' + rec.type),
              getReminderStyle(rec.priority)
            ]"
          >
            <div class="notification-icon">
              <component 
                v-if="rec.type === 'schedule_reminder'"
                :is="getReminderIcon(rec.priority)" 
                :size="24"
              />
              <Check v-else-if="rec.type === 'time_preference'" :size="24" />
              <Globe v-else-if="rec.type === 'balance'" :size="24" />
              <Sun v-else-if="rec.type === 'weather'" :size="24" />
              <Bell v-else :size="24" />
            </div>
            <div class="notification-content">
              <h4>
                {{ rec.type === 'schedule_reminder' ? '⏰ 日程提醒' : getNotificationTitle(rec.type) }}
              </h4>
              <p>{{ rec.message }}</p>
              
              <!-- 额外信息 -->
              <div v-if="rec.suggested_hour" class="extra-info">
                <Clock :size="14" />
                <span>推荐时间: {{ rec.suggested_hour }}:00</span>
              </div>
              
              <!-- 倒计时详情（仅日程提醒显示） -->
              <div v-if="rec.type === 'schedule_reminder' && rec.countdown" class="countdown-details">
                <div class="countdown-time-display">
                  <Clock :size="14" />
                  <span class="time-text">{{ rec.countdown.remaining_text }}</span>
                  <span class="relative-time">{{ formatRelativeTime(rec.start_time) }}</span>
                </div>
                
                <!-- 进度条（可视化剩余时间） -->
                <div class="countdown-progress">
                  <div 
                    class="progress-bar"
                    :style="{ width: getProgressWidth(rec.countdown) }"
                  ></div>
                </div>
                
                <!-- 快速操作按钮 -->
                <div class="quick-actions">
                  <button 
                    class="view-schedule-btn"
                    @click="navigateToSchedule(rec.schedule_id)"
                  >
                    <Calendar :size="14" />
                    <span>查看日程</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import { 
  Bell, 
  AlertCircle, 
  Clock, 
  Check, 
  Sun, 
  Globe, 
  Calendar, 
  Filter,
  Sparkles
} from 'lucide-vue-next';

// 定义组件的 props
const props = defineProps({
  recommendations: {
    type: Array,
    default: () => []
  },
  API_URL: {
    type: String,
    required: true
  },
  token: {
    type: String,
    required: true
  }
});

// 定义组件的 emits
const emit = defineEmits(['navigate-to-schedule', 'load-recommendations']);

// 通知过滤器
const notificationFilter = ref('all');

// 计算各类推荐的数量
const timePreferenceCount = computed(() => {
  if (!props.recommendations) return 0;
  return props.recommendations.filter(r => r.type === 'time_preference').length;
});

const balanceCount = computed(() => {
  if (!props.recommendations) return 0;
  return props.recommendations.filter(r => r.type === 'balance').length;
});

const urgentCount = computed(() => {
  if (!props.recommendations) return 0;
  return props.recommendations.filter(r => r.priority === 'urgent').length;
});

// 计算日程提醒数量
const scheduleReminderCount = computed(() => {
  if (!props.recommendations) return 0;
  return props.recommendations.filter(r => r.type === 'schedule_reminder').length;
});

// 过滤后的通知
const filteredRecommendations = computed(() => {
  if (!props.recommendations) return [];
  if (notificationFilter.value === 'all') return props.recommendations;
  return props.recommendations.filter(r => r.type === notificationFilter.value);
});

// 按类型分组的通知
const groupedNotifications = computed(() => {
  const groups = {};
  filteredRecommendations.value.forEach(rec => {
    if (!groups[rec.type]) {
      groups[rec.type] = [];
    }
    groups[rec.type].push(rec);
  });
  return groups;
});

// 获取通知图标
function getNotificationIcon(type) {
  const icons = {
    'schedule_reminder': Clock,
    'weather': Sun,
    'time_preference': Check,
    'balance': Sparkles,
    'info': Globe
  };
  return icons[type] || Bell;
}

// 获取通知颜色
function getNotificationColor(type) {
  const colors = {
    'schedule_reminder': '#f97316',  // 橙色 - 日程提醒
    'weather': '#0ea5e9',           // 蓝色 - 天气
    'time_preference': '#10b981',   // 绿色 - 时间偏好
    'balance': '#8b5cf6',           // 紫色 - 平衡建议
    'info': '#667eea'               // 靛蓝色 - 信息提示
  };
  return colors[type] || '#667eea';
}

// 获取提醒图标
function getReminderIcon(priority) {
  switch(priority) {
    case 'urgent':
      return AlertCircle;
    case 'high':
      return Bell;
    default:
      return Calendar;
  }
}

// 获取提醒样式
function getReminderStyle(priority) {
  const styles = {
    urgent: 'reminder-urgent',
    high: 'reminder-high',
    medium: 'reminder-medium',
    low: 'reminder-low'
  };
  return styles[priority] || 'reminder-low';
}

// 格式化相对时间
function formatRelativeTime(isoString) {
  if (!isoString) return '';
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = date - now;
  const diffMins = Math.floor(diffMs / 60000);
  
  if (diffMins < 1) return '刚刚';
  if (diffMins < 60) return `${diffMins}分钟后`;
  if (diffMins < 1440) return `${Math.floor(diffMins / 60)}小时后`;
  return `${Math.floor(diffMins / 1440)}天后`;
}

// 计算进度条宽度
function getProgressWidth(countdown) {
  if (!countdown) return '0%';
  
  const remainingSeconds = countdown.remaining_seconds;
  const totalSeconds = 24 * 60 * 60; // 24 小时作为最大值
  
  if (remainingSeconds <= 0) return '100%';
  if (remainingSeconds > totalSeconds) return '10%';
  
  const percentage = ((totalSeconds - remainingSeconds) / totalSeconds) * 100;
  return `${Math.min(100, Math.max(10, percentage))}%`;
}

// 获取通知标题
function getNotificationTitle(type) {
  const titles = {
    'weather': '🌦️ 天气提醒',
    'time_preference': '⏰ 时间偏好',
    'balance': '⚖️ 日程平衡',
    'schedule_reminder': '📅 日程提醒',
    'info': 'ℹ️ 提示信息'
  };
  return titles[type] || '消息通知';
}

// 导航到指定日程
function navigateToSchedule(scheduleId) {
  emit('navigate-to-schedule', scheduleId);
}

// 加载推荐
function loadRecommendations() {
  emit('load-recommendations');
}
</script>

<style scoped>
/* ===== 通知面板样式 ===== */
.notifications-panel {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(50, 50, 93, 0.11), 0 1px 3px rgba(0, 0, 0, 0.08);
  min-height: 500px;
  display: flex;
  flex-direction: column;
}

.notifications-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e9ecef;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: #32325D;
}

.bell-icon {
  color: #5E72E4;
}

.header-title h3 {
  margin: 0;
  font-size: 1.25rem;
}

.stats-badges {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.stat-badge {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.4rem 0.8rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 500;
}

.stat-badge.time-pref {
  background-color: #dcfce7;
  color: #166534;
}

.stat-badge.balance {
  background-color: #ede9fe;
  color: #5b21b6;
}

.stat-badge.urgent {
  background-color: #fee2e2;
  color: #dc2626;
}

.stat-badge.schedule {
  background-color: #dbeafe;
  color: #2563eb;
}

.stat-badge.total {
  background-color: #f3f4f6;
  color: #4b5563;
}

.notifications-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.btn-refresh {
  background: linear-gradient(135deg, #5E72E4 0%, #825EE4 100%);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.6rem 1.2rem;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s;
}

.btn-refresh:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(94, 114, 228, 0.4);
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background-color: #f8f9fe;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.filter-icon {
  color: #8898aa;
}

.filter-select {
  border: none;
  background: transparent;
  font-size: 0.9rem;
  color: #32325D;
  outline: none;
  cursor: pointer;
  min-width: 120px;
}

.empty-notifications {
  text-align: center;
  padding: 4rem 2rem;
  color: #adb5bd;
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.empty-icon {
  margin-bottom: 1.5rem;
  opacity: 0.5;
}

.empty-notifications h3 {
  margin: 0 0 0.5rem 0;
  color: #32325D;
  font-size: 1.2rem;
}

.empty-notifications p {
  color: #8898aa;
  margin-bottom: 1.5rem;
}

.btn-clear-filter {
  background-color: transparent;
  border: 1px solid #5E72E4;
  color: #5E72E4;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-clear-filter:hover {
  background-color: #5E72E4;
  color: white;
}

.notifications-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.notification-group {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.group-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px dashed #e9ecef;
}

.group-icon {
  opacity: 0.8;
}

.group-title {
  font-weight: 600;
  color: #32325D;
  font-size: 0.95rem;
}

.group-count {
  background-color: #e9ecef;
  color: #525F7F;
  font-size: 0.75rem;
  padding: 0.1rem 0.5rem;
  border-radius: 10px;
  margin-left: auto;
}

.group-items {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.notification-item {
  display: flex;
  gap: 1rem;
  padding: 1.25rem;
  border-radius: 8px;
  border-left-width: 6px;
  border-left-style: solid;
  background-color: #f8f9fa;
  transition: all 0.3s ease;
  border: 1px solid #e9ecef;
}

.notification-item:hover {
  transform: translateX(5px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.notification-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background-color: rgba(94, 114, 228, 0.1);
  color: #5E72E4;
}

/* 为不同类型的通知定制图标背景色 */
.type-time-preference .notification-icon {
  background-color: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.type-balance .notification-icon {
  background-color: rgba(139, 92, 246, 0.1);
  color: #8b5cf6;
}

.type-weather .notification-icon {
  background-color: rgba(14, 165, 233, 0.1);
  color: #0ea5e9;
}

.type-info .notification-icon {
  background-color: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.type-schedule-reminder .notification-icon {
  background-color: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

/* 日程提醒特殊样式 */
.type-schedule-reminder {
  animation: none;
}

/* 不同类型的推荐样式 */
.type-time-preference {
  background-color: #ecfdf5;
  border-left-color: #10b981;
  border: 1px solid #d1fae5;
}

.type-balance {
  background-color: #faf5ff;
  border-left-color: #8b5cf6;
  border: 1px solid #f3e8ff;
}

.type-weather {
  background-color: #e0f2fe;
  border-left-color: #0ea5e9;
  border: 1px solid #bae6fd;
}

.type-info {
  background-color: #eff6ff;
  border-left-color: #3b82f6;
  border: 1px solid #dbeafe;
}

.type-schedule-reminder {
  background-color: #fffbeb;
  border-left-color: #f59e0b;
  border: 1px solid #fde68a;
}

/* 不同优先级的样式 */
.reminder-urgent {
  background-color: #ffebee;
  border-left-color: #f44336;
  border: 1px solid #ffcdd2;
  animation: pulse-border 2s infinite;
}

.reminder-high {
  background-color: #fff3e0;
  border-left-color: #ff9800;
  border: 1px solid #ffe0b2;
}

.reminder-medium {
  background-color: #fff9c4;
  border-left-color: #ffc107;
  border: 1px solid #ffecb3;
}

.reminder-low {
  background-color: #e3f2fd;
  border-left-color: #2196F3;
  border: 1px solid #bbdefb;
}

@keyframes pulse-border {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(244, 67, 54, 0.4);
  }
  50% {
    box-shadow: 0 0 0 10px rgba(244, 67, 54, 0);
  }
}

/* 倒计时详情区域 */
.countdown-details {
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
}

.countdown-time-display {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: #525F7F;
  margin-bottom: 0.5rem;
}

.countdown-time-display svg {
  color: #5E72E4;
}

.time-text {
  font-weight: 600;
  color: #32325D;
}

.relative-time {
  font-size: 0.85em;
  color: #8898aa;
  margin-left: auto;
}

/* 进度条 */
.countdown-progress {
  width: 100%;
  height: 6px;
  background-color: rgba(0, 0, 0, 0.05);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 0.75rem;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #5E72E4 0%, #825EE4 100%);
  border-radius: 3px;
  transition: width 1s ease;
}

.reminder-urgent .progress-bar {
  background: linear-gradient(90deg, #f44336 0%, #ff6659 100%);
}

.reminder-high .progress-bar {
  background: linear-gradient(90deg, #ff9800 0%, #ffb74d 100%);
}

.reminder-medium .progress-bar {
  background: linear-gradient(90deg, #ffc107 0%, #ffd54f 100%);
}

/* 快速操作按钮 */
.quick-actions {
  display: flex;
  gap: 0.5rem;
}

.view-schedule-btn {
  padding: 0.4rem 0.8rem;
  font-size: 0.85rem;
  background-color: rgba(94, 114, 228, 0.1);
  color: #5E72E4;
  border: 1px solid rgba(94, 114, 228, 0.3);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.view-schedule-btn:hover {
  background-color: #5E72E4;
  color: white;
}

/* ===== 通知面板响应式样式 ===== */
@media (max-width: 768px) {
  .notifications-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }

  .stats-badges {
    width: 100%;
    justify-content: flex-start;
    flex-wrap: wrap;
  }

  .notifications-toolbar {
    flex-direction: column;
    gap: 1rem;
  }

  .btn-refresh {
    width: 100%;
    justify-content: center;
  }

  .filter-group {
    width: 100%;
  }

  .filter-select {
    flex: 1;
  }

  .notification-item {
    flex-direction: column;
  }

  .notification-icon {
    align-self: flex-start;
  }

  .quick-actions {
    margin-top: 0.75rem;
  }

  .view-schedule-btn {
    width: 100%;
    justify-content: center;
  }
}
</style>