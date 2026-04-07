<script setup>
import { Calendar, User, Bell, Settings, LogOut, BarChart } from 'lucide-vue-next'
import { useRouter } from 'vue-router' // ← 新增导入
import { NAVIGATION } from '@/constants'

const props = defineProps({
  isCollapsed: {
    type: Boolean,
    default: false
  },
  activeTab: {
    type: String,
    required: true
  },
  user: {
    type: Object,
    default: null // 允许为 null
  },
  recommendationsCount: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['toggle-collapse', 'tab-change', 'logout'])
const router = useRouter() // ← 新增

function handleTabChange(tab) {
  emit('tab-change', tab)
}

function handleLogout() {
  emit('logout')
}

function goToCalendar() {
  router.push('/calendar') // ← 新增跳转逻辑
}

// 安全获取用户名的首字母
function getUserInitial() {
  return props.user?.username?.charAt(0)?.toUpperCase() || '?'
}

</script>

<template>
  <aside class="sidebar" :class="{ 'collapsed': isCollapsed }">
    <div class="sidebar-header">
      <h2 v-if="!isCollapsed">日程助手</h2>
      <button class="collapse-btn" @click="$emit('toggle-collapse')">
        {{ isCollapsed ? '→' : '←' }}
      </button>
    </div>
    
    <nav class="sidebar-nav">
      <a 
        href="#" 
        class="nav-item" 
        :class="{ 'active': activeTab === NAVIGATION.tabs.SCHEDULE }"
        @click.prevent="handleTabChange(NAVIGATION.tabs.SCHEDULE)"
      >
        <Calendar :size="20" />
        <span v-if="!isCollapsed">你的日程</span>
      </a>

      <!-- 新增：日历视图导航项 -->
      <a 
        href="#" 
        class="nav-item"
        @click.prevent="goToCalendar"
      >
        <Calendar :size="20" />
        <span v-if="!isCollapsed">日历视图</span>
      </a>
      
      <a 
        href="#" 
        class="nav-item" 
        :class="{ 'active': activeTab === NAVIGATION.tabs.PROFILE }"
        @click.prevent="handleTabChange(NAVIGATION.tabs.PROFILE)"
      >
        <User :size="20" />
        <span v-if="!isCollapsed">个人信息</span>
      </a>
      
      <a 
        href="#" 
        class="nav-item" 
        :class="{ 'active': activeTab === NAVIGATION.tabs.NOTIFICATIONS }"
        @click.prevent="handleTabChange(NAVIGATION.tabs.NOTIFICATIONS)"
      >
        <Bell :size="20" />
        <span v-if="!isCollapsed">消息通知</span>
        <span v-if="!isCollapsed && recommendationsCount > 0" class="badge">
          {{ recommendationsCount }}
        </span>
      </a>
      <a 
        href="#" 
        class="nav-item" 
        @click.prevent="$router.push('/statistics')"
      >
        <BarChart :size="20" />
        <span v-if="!isCollapsed">效率分析</span>
      </a>
      <a 
        href="#" 
        class="nav-item" 
        :class="{ 'active': activeTab === NAVIGATION.tabs.SETTINGS }"
        @click.prevent="handleTabChange(NAVIGATION.tabs.SETTINGS)"
      >
        <Settings :size="20" />
        <span v-if="!isCollapsed">系统设置</span>
      </a>
    </nav>
    
    <div class="sidebar-footer">
      <div class="user-info-mini" v-if="!isCollapsed && user">
        <div class="avatar">{{ getUserInitial() }}</div>
        <div class="user-name">{{ user.username || '未登录' }}</div>
      </div>
      <button class="logout-btn-mini" @click="handleLogout" title="退出登录">
        <LogOut :size="18" />
      </button>
    </div>
  </aside>
</template>

<style scoped>
/* 从 HomeView.vue 复制这些完整的样式块 */

/* 侧边栏容器 */
.sidebar {
  width: 250px;
  background: linear-gradient(180deg, #5E72E4 0%, #4c5fd5 100%);
  color: white;
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  flex-shrink: 0;
}

.sidebar.collapsed {
  width: 70px;
}

.sidebar-header {
  padding: 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-header h2 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 600;
}

.collapse-btn {
  background: none;
  border: none;
  color: white;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0.25rem;
  transition: transform 0.2s;
}

.collapse-btn:hover {
  transform: scale(1.1);
}

/* 导航栏 */
.sidebar-nav {
  flex: 1;
  padding: 1rem 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1.5rem;
  color: rgba(255, 255, 255, 0.8);
  text-decoration: none;
  transition: all 0.2s;
  cursor: pointer;
  position: relative;
}

.nav-item:hover {
  background-color: rgba(255, 255, 255, 0.1);
  color: white;
}

.nav-item.active {
  background-color: rgba(255, 255, 255, 0.2);
  color: white;
  font-weight: 600;
}

.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background-color: white;
}

.badge {
  background-color: #f5365c;
  color: white;
  font-size: 0.75rem;
  padding: 0.125rem 0.5rem;
  border-radius: 10px;
  margin-left: auto;
}

/* 侧边栏底部 */
.sidebar-footer {
  padding: 1rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.user-info-mini {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 1.2rem;
}

.user-name {
  font-size: 0.9rem;
  font-weight: 500;
}

.logout-btn-mini {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.8);
  cursor: pointer;
  padding: 0.5rem;
  display: flex;
  align-items: center;
  border-radius: 4px;
  transition: all 0.2s;
}

.logout-btn-mini:hover {
  background-color: rgba(255, 255, 255, 0.1);
  color: white;
}

</style>