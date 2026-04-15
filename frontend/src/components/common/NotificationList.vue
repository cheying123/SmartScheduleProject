<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Bell, Sun, Check, Globe, Clock, Calendar, ArrowRight, X, Filter, Sparkles, AlertCircle, Info } from 'lucide-vue-next'

const props = defineProps({
  recommendations: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['refresh', 'navigate-to-schedule'])

// 定时器引用
let countdownInterval = null

// 响应式数据
const filterType = ref('all') // all, schedule_reminder, weather, time_preference, balance, info
const expandedItems = ref(new Set())

// 通知类型配置
const NOTIFICATION_CONFIG = {
  schedule_reminder: {
    title: '⏰ 日程提醒',
    icon: Clock,
    color: '#f97316',
    bgColor: '#fff7ed',
    borderColor: '#fed7aa',
    description: '即将开始的日程'
  },
  weather: {
    title: '🌤️ 天气提示',
    icon: Sun,
    color: '#0ea5e9',
    bgColor: '#f0f9ff',
    borderColor: '#bae6fd',
    description: '智能天气建议'
  },
  time_preference: {
    title: '⏱️ 时间偏好',
    icon: Check,
    color: '#10b981',
    bgColor: '#f0fdf4',
    borderColor: '#bbf7d0',
    description: '基于您的习惯'
  },
  balance: {
    title: '😌 平衡建议',
    icon: Sparkles,
    color: '#8b5cf6',
    bgColor: '#faf5ff',
    borderColor: '#e9d5ff',
    description: '工作生活平衡'
  },
  info: {
    title: 'ℹ️ 提示信息',
    icon: Info,
    color: '#64748b',
    bgColor: '#f8fafc',
    borderColor: '#e2e8f0',
    description: '系统通知'
  }
}

// 计算属性：过滤后的推荐列表
const filteredRecommendations = computed(() => {
  if (filterType.value === 'all') {
    return props.recommendations
  }
  return props.recommendations.filter(rec => rec.type === filterType.value)
})

// 计算属性：按类型分组
const groupedRecommendations = computed(() => {
  const groups = {}
  
  filteredRecommendations.value.forEach(rec => {
    if (!groups[rec.type]) {
      groups[rec.type] = []
    }
    groups[rec.type].push(rec)
  })
  
  return groups
})

// 计算属性：统计信息
const stats = computed(() => {
  const total = props.recommendations.length
  const urgent = props.recommendations.filter(r => r.priority === 'urgent').length
  const scheduleReminders = props.recommendations.filter(r => r.type === 'schedule_reminder').length
  
  return { total, urgent, scheduleReminders }
})

// 格式化倒计时文本
function formatCountdown(countdown) {
  if (!countdown) return ''
  return countdown.remaining_text || countdown.remind_message || ''
}

// 获取优先级样式
function getPriorityStyle(priority) {
  const styles = {
    urgent: { 
      badgeColor: '#dc2626', 
      badgeBg: '#fee2e2',
      pulse: true 
    },
    high: { 
      badgeColor: '#ea580c', 
      badgeBg: '#ffedd5',
      pulse: false 
    },
    medium: { 
      badgeColor: '#ca8a04', 
      badgeBg: '#fef9c3',
      pulse: false 
    },
    low: { 
      badgeColor: '#0284c7', 
      badgeBg: '#e0f2fe',
      pulse: false 
    },
    info: { 
      badgeColor: '#64748b', 
      badgeBg: '#f1f5f9',
      pulse: false 
    }
  }
  
  return styles[priority] || styles.info
}

// 切换展开/折叠
function toggleExpand(id) {
  if (expandedItems.value.has(id)) {
    expandedItems.value.delete(id)
  } else {
    expandedItems.value.add(id)
  }
}

// 跳转到日程详情
function navigateToSchedule(scheduleId) {
  emit('navigate-to-schedule', scheduleId)
}

// 关闭通知项
function dismissNotification(index) {
  // 这里可以添加逻辑来标记为已读或移除
  console.log('关闭通知:', index)
}

// 启动倒计时更新
function startCountdownUpdate() {
  countdownInterval = setInterval(() => {
    // 触发重新渲染以更新倒计时显示
    // 实际项目中可能需要从后端获取最新数据
  }, 60000) // 每分钟更新一次
}

// 停止倒计时更新
function stopCountdownUpdate() {
  if (countdownInterval) {
    clearInterval(countdownInterval)
    countdownInterval = null
  }
}

onMounted(() => {
  startCountdownUpdate()
})

onUnmounted(() => {
  stopCountdownUpdate()
})
</script>

<template>
  <div class="notifications-panel">
    <!-- 头部区域 -->
    <div class="panel-header">
      <div class="header-title">
        <Bell :size="24" class="bell-icon" />
        <h2>智能通知中心</h2>
      </div>
      
      <!-- 统计徽章 -->
      <div v-if="stats.total > 0" class="stats-badges">
        <span v-if="stats.urgent > 0" class="stat-badge urgent">
          <AlertCircle :size="14" />
          {{ stats.urgent }} 紧急
        </span>
        <span v-if="stats.scheduleReminders > 0" class="stat-badge schedule">
          <Clock :size="14" />
          {{ stats.scheduleReminders }} 日程
        </span>
        <span class="stat-badge total">
          共 {{ stats.total }} 条
        </span>
      </div>
    </div>

    <!-- 刷新和筛选工具栏 -->
    <div class="toolbar">
      <button class="btn-refresh" @click="$emit('refresh')">
        <Check :size="16" />
        <span>刷新推荐</span>
      </button>
      
      <div class="filter-group">
        <Filter :size="16" class="filter-icon" />
        <select v-model="filterType" class="filter-select">
          <option value="all">全部类型</option>
          <option value="schedule_reminder">日程提醒</option>
          <option value="weather">天气提示</option>
          <option value="time_preference">时间偏好</option>
          <option value="balance">平衡建议</option>
          <option value="info">提示信息</option>
        </select>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="filteredRecommendations.length === 0" class="empty-state">
      <div class="empty-icon">
        <Bell :size="80" />
      </div>
      <h3>{{ filterType === 'all' ? '暂无新消息' : '该类型暂无通知' }}</h3>
      <p>{{ filterType === 'all' ? '点击"刷新推荐"获取智能建议' : '尝试切换其他类型查看' }}</p>
      <button v-if="filterType !== 'all'" class="btn-clear-filter" @click="filterType = 'all'">
        查看全部
      </button>
    </div>

    <!-- 通知列表 -->
    <div v-else class="notifications-container">
      <!-- 按类型分组显示 -->
      <div 
        v-for="(items, type) in groupedRecommendations" 
        :key="type"
        class="notification-group"
      >
        <!-- 类型标题 -->
        <div class="group-header">
          <component 
            :is="NOTIFICATION_CONFIG[type]?.icon || Globe" 
            :size="18" 
            class="group-icon"
            :style="{ color: NOTIFICATION_CONFIG[type]?.color }"
          />
          <span class="group-title">{{ NOTIFICATION_CONFIG[type]?.title || '通知' }}</span>
          <span class="group-count">{{ items.length }}</span>
        </div>

        <!-- 该类型的通知列表 -->
        <div class="group-items">
          <div 
            v-for="(rec, index) in items" 
            :key="rec.id || index"
            class="notification-card"
            :class="[
              `type-${rec.type}`,
              `priority-${rec.priority}`,
              { expanded: expandedItems.has(rec.id || index) }
            ]"
            :style="{
              '--card-color': NOTIFICATION_CONFIG[rec.type]?.color,
              '--card-bg': NOTIFICATION_CONFIG[rec.type]?.bgColor,
              '--card-border': NOTIFICATION_CONFIG[rec.type]?.borderColor
            }"
          >
            <!-- 卡片头部 -->
            <div class="card-header" @click="toggleExpand(rec.id || index)">
              <div class="card-main">
                <!-- 优先级徽章 -->
                <div 
                  v-if="rec.priority"
                  class="priority-badge"
                  :class="{ pulse: getPriorityStyle(rec.priority).pulse }"
                  :style="{
                    backgroundColor: getPriorityStyle(rec.priority).badgeBg,
                    color: getPriorityStyle(rec.priority).badgeColor
                  }"
                >
                  {{ rec.priority === 'urgent' ? '紧急' : 
                     rec.priority === 'high' ? '重要' :
                     rec.priority === 'medium' ? '中等' :
                     rec.priority === 'low' ? '一般' : '提示' }}
                </div>

                <!-- 通知内容 -->
                <div class="card-content">
                  <p class="message-text">{{ rec.message }}</p>
                  
                  <!-- 倒计时信息（仅日程提醒） -->
                  <div v-if="rec.type === 'schedule_reminder' && rec.countdown" class="countdown-info">
                    <Clock :size="14" />
                    <span class="countdown-text">{{ formatCountdown(rec.countdown) }}</span>
                    
                    <!-- 进度条 -->
                    <div class="progress-bar">
                      <div 
                        class="progress-fill"
                        :style="{ width: rec.countdown.progress_percentage + '%' }"
                      ></div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 操作按钮 -->
              <div class="card-actions">
                <button 
                  v-if="rec.type === 'schedule_reminder' && rec.schedule_id"
                  class="btn-navigate"
                  @click.stop="navigateToSchedule(rec.schedule_id)"
                  title="查看日程"
                >
                  <Calendar :size="16" />
                  <span>查看</span>
                </button>
                
                <button 
                  class="btn-dismiss"
                  @click.stop="dismissNotification(index)"
                  title="关闭"
                >
                  <X :size="16" />
                </button>
              </div>
            </div>

            <!-- 展开的详细信息 -->
            <div v-if="expandedItems.has(rec.id || index)" class="card-details">
              <div class="detail-item">
                <span class="detail-label">类型：</span>
                <span class="detail-value">{{ NOTIFICATION_CONFIG[rec.type]?.description }}</span>
              </div>
              
              <div v-if="rec.start_time" class="detail-item">
                <span class="detail-label">时间：</span>
                <span class="detail-value">{{ new Date(rec.start_time).toLocaleString('zh-CN') }}</span>
              </div>
              
              <div v-if="rec.created_at" class="detail-item">
                <span class="detail-label">生成时间：</span>
                <span class="detail-value">{{ new Date(rec.created_at).toLocaleString('zh-CN') }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ===== 主容器 ===== */
.notifications-panel {
  background: white;
  border-radius: 16px;
  padding: 0;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

/* ===== 头部区域 ===== */
.panel-header {
  padding: 24px 24px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.bell-icon {
  animation: ring 2s ease-in-out infinite;
}

@keyframes ring {
  0%, 100% { transform: rotate(0); }
  10%, 30% { transform: rotate(-10deg); }
  20%, 40% { transform: rotate(10deg); }
  50% { transform: rotate(0); }
}

.header-title h2 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 700;
}

.stats-badges {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.stat-badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 4px;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
}

.stat-badge.urgent {
  background: rgba(220, 38, 38, 0.3);
}

.stat-badge.schedule {
  background: rgba(249, 115, 22, 0.3);
}

/* ===== 工具栏 ===== */
.toolbar {
  padding: 16px 24px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.btn-refresh {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 8px 16px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.25);
}

.btn-refresh:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.35);
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-icon {
  color: #64748b;
}

.filter-select {
  padding: 6px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 0.875rem;
  background: white;
  cursor: pointer;
  outline: none;
  transition: all 0.2s;
}

.filter-select:hover {
  border-color: #94a3b8;
}

.filter-select:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

/* ===== 空状态 ===== */
.empty-state {
  text-align: center;
  padding: 60px 24px;
  color: #94a3b8;
}

.empty-icon {
  margin-bottom: 20px;
  opacity: 0.3;
}

.empty-state h3 {
  margin: 0 0 8px 0;
  font-size: 1.125rem;
  color: #475569;
}

.empty-state p {
  margin: 0 0 16px 0;
  font-size: 0.875rem;
}

.btn-clear-filter {
  background: #667eea;
  color: white;
  border: none;
  border-radius: 6px;
  padding: 8px 16px;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-clear-filter:hover {
  background: #5568d3;
}

/* ===== 通知容器 ===== */
.notifications-container {
  max-height: 600px;
  overflow-y: auto;
  padding: 16px 24px 24px;
}

/* ===== 分组样式 ===== */
.notification-group {
  margin-bottom: 24px;
}

.notification-group:last-child {
  margin-bottom: 0;
}

.group-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid #f1f5f9;
}

.group-icon {
  flex-shrink: 0;
}

.group-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: #334155;
  flex: 1;
}

.group-count {
  background: #e2e8f0;
  color: #64748b;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 0.75rem;
  font-weight: 600;
}

.group-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* ===== 通知卡片 ===== */
.notification-card {
  background: var(--card-bg, #f8fafc);
  border: 1.5px solid var(--card-border, #e2e8f0);
  border-left: 4px solid var(--card-color, #667eea);
  border-radius: 10px;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.notification-card:hover {
  transform: translateX(4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.notification-card.expanded {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.card-header {
  padding: 14px 16px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  cursor: pointer;
}

.card-main {
  flex: 1;
  min-width: 0;
}

/* 优先级徽章 */
.priority-badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 0.7rem;
  font-weight: 700;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.priority-badge.pulse {
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

/* 卡片内容 */
.card-content {
  flex: 1;
}

.message-text {
  margin: 0 0 8px 0;
  font-size: 0.9rem;
  color: #1e293b;
  line-height: 1.6;
}

/* 倒计时信息 */
.countdown-info {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed rgba(0, 0, 0, 0.1);
}

.countdown-text {
  font-size: 0.8rem;
  color: #64748b;
  font-weight: 500;
}

.progress-bar {
  flex: 1;
  height: 4px;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 2px;
  overflow: hidden;
  margin-left: 8px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--card-color, #667eea), transparent);
  border-radius: 2px;
  transition: width 0.3s ease;
}

/* 卡片操作按钮 */
.card-actions {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.btn-navigate {
  background: white;
  border: 1px solid var(--card-border, #e2e8f0);
  border-radius: 6px;
  padding: 6px 10px;
  font-size: 0.75rem;
  color: var(--card-color, #667eea);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all 0.2s;
}

.btn-navigate:hover {
  background: var(--card-bg, #f8fafc);
  border-color: var(--card-color, #667eea);
}

.btn-dismiss {
  background: transparent;
  border: none;
  border-radius: 6px;
  padding: 6px;
  color: #94a3b8;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.btn-dismiss:hover {
  background: rgba(0, 0, 0, 0.05);
  color: #ef4444;
}

/* 展开的详细信息 */
.card-details {
  padding: 12px 16px;
  background: rgba(0, 0, 0, 0.02);
  border-top: 1px solid var(--card-border, #e2e8f0);
  animation: slideDown 0.2s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.detail-item {
  display: flex;
  gap: 8px;
  margin-bottom: 6px;
  font-size: 0.8rem;
}

.detail-item:last-child {
  margin-bottom: 0;
}

.detail-label {
  color: #64748b;
  font-weight: 500;
  min-width: 70px;
}

.detail-value {
  color: #334155;
  flex: 1;
}

/* ===== 滚动条美化 ===== */
.notifications-container::-webkit-scrollbar {
  width: 6px;
}

.notifications-container::-webkit-scrollbar-track {
  background: #f1f5f9;
}

.notifications-container::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.notifications-container::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* ===== 响应式适配 ===== */
@media (max-width: 640px) {
  .panel-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-group {
    justify-content: space-between;
  }

  .card-header {
    flex-direction: column;
  }

  .card-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
