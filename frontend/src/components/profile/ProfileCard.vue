<script setup>
import { Edit2, Sun } from 'lucide-vue-next'
import { computed } from 'vue'

const props = defineProps({
  user: {
    type: Object,
    default: null
  },
  schedules: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['edit', 'refresh-weather'])

// 计算统计数据
const stats = computed(() => ({
  total: props.schedules.length,
  highPriority: props.schedules.filter(s => s.priority >= 4).length,
  recurring: props.schedules.filter(s => s.is_recurring).length
}))

// 格式化注册日期
const joinDate = computed(() => {
  if (!props.user?.created_at) return '未知'
  return new Date(props.user.created_at).toLocaleDateString('zh-CN')
})

function getUserInitial() {
  return props.user?.username?.charAt(0)?.toUpperCase() || '?'
}
</script>

<template>
  <div class="profile-card">
    <div class="profile-header">
      <div class="profile-avatar">
        {{ getUserInitial() }}
      </div>
      <div class="profile-info">
        <h2>{{ user?.username || '未登录' }}</h2>
        <p class="profile-email">{{ user?.email || '未设置邮箱' }}</p>
        <p class="profile-location" v-if="user?.location_name">
          📍 {{ user.location_name }}
        </p>
        <p class="profile-location" v-else-if="user?.location">
          📍 城市 ID: {{ user.location }}
        </p>
        <p class="profile-join-date">
          注册时间：{{ joinDate }}
        </p>
      </div>
      <div class="profile-actions">
        <button class="edit-profile-btn" @click="$emit('edit')">
          <Edit2 :size="18" />
          <span>编辑资料</span>
        </button>
        <button 
          class="refresh-weather-btn" 
          @click="$emit('refresh-weather')"
          title="根据当前位置更新所有日程天气"
        >
          <Sun :size="18" />
          <span>更新天气</span>
        </button>
      </div>
    </div>
    
    <div class="profile-stats">
      <div class="stat-item">
        <div class="stat-value">{{ stats.total }}</div>
        <div class="stat-label">日程总数</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ stats.highPriority }}</div>
        <div class="stat-label">高优先级</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ stats.recurring }}</div>
        <div class="stat-label">重复日程</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.profile-card {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(50, 50, 93, 0.11), 0 1px 3px rgba(0, 0, 0, 0.08);
}

.profile-header {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 2rem;
  padding-bottom: 2rem;
  border-bottom: 2px solid #e9ecef;
}

.profile-avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, #5E72E4 0%, #4c5fd5 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  font-weight: 600;
  flex-shrink: 0;
}

.profile-info {
  flex: 1;
}

.profile-info h2 {
  margin: 0 0 0.5rem 0;
  color: #32325D;
  font-size: 1.5rem;
}

.profile-email, .profile-join-date {
  margin: 0.25rem 0;
  color: #8898aa;
  font-size: 0.9rem;
}

.profile-location {
  margin: 0.25rem 0;
  color: #8898aa;
  font-size: 0.9rem;
}

.edit-profile-btn {
  background-color: #f4f5f7;
  border: none;
  border-radius: 8px;
  padding: 0.75rem 1.5rem;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #5E72E4;
  transition: all 0.2s;
  margin-bottom: 0.75rem;
  width: 100%;
  justify-content: center;
}

.edit-profile-btn:hover {
  background-color: #5E72E4;
  color: white;
}

.refresh-weather-btn {
  background-color: #2dce89;
  border: none;
  border-radius: 8px;
  padding: 0.75rem 1.5rem;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: white;
  transition: all 0.2s;
  width: 100%;
  justify-content: center;
}

.refresh-weather-btn:hover {
  background-color: #26b87a;
  transform: translateY(-2px);
}

.profile-actions {
  display: flex;
  gap: 0.75rem;
  flex-direction: column;
  min-width: 150px;
}

.profile-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
}

.stat-item {
  text-align: center;
  padding: 1.5rem;
  background-color: #f8f9fe;
  border-radius: 8px;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: #5E72E4;
  margin-bottom: 0.5rem;
}

.stat-label {
  color: #8898aa;
  font-size: 0.9rem;
}

@media (max-width: 768px) {
  .profile-header {
    flex-direction: column;
    text-align: center;
  }
  
  .profile-actions {
    width: 100%;
    flex-direction: row;
  }
  
  .profile-stats {
    grid-template-columns: 1fr;
  }
}
</style>