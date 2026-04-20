<template>
  <div class="fab-container">
    <!-- 展开菜单 -->
    <div v-if="showMenu" class="fab-menu">
      <button class="fab-menu-item" @click="handleVoiceInput">
        <span class="menu-icon">🎤</span>
        <span>语音输入</span>
      </button>
      <button class="fab-menu-item" @click="handleManualInput">
        <span class="menu-icon">📝</span>
        <span>手动创建</span>
      </button>
      <button class="fab-menu-item" @click="handleAutoSchedule">
        <span class="menu-icon">🤖</span>
        <span>智能排程</span>
      </button>
    </div>
    
    <!-- 主按钮 -->
    <button class="fab-main-btn" @click="toggleMenu" title="快速添加">
      <PlusCircle :size="28" />
    </button>
  </div>
</template>

<script setup>
import { PlusCircle } from 'lucide-vue-next';

// 定义组件的 props
const props = defineProps({
  showMenu: {
    type: Boolean,
    default: false
  }
});

// 定义组件的 emits
const emit = defineEmits([
  'toggle-menu',
  'voice-input',
  'manual-input',
  'auto-schedule'
]);

// 切换菜单显示
function toggleMenu() {
  emit('toggle-menu');
}

// 处理语音输入
function handleVoiceInput() {
  emit('voice-input');
  emit('toggle-menu'); // 触发后关闭菜单
}

// 处理手动输入
function handleManualInput() {
  emit('manual-input');
  emit('toggle-menu'); // 触发后关闭菜单
}

// 处理智能排程
function handleAutoSchedule() {
  emit('auto-schedule');
  emit('toggle-menu'); // 触发后关闭菜单
}
</script>

<style scoped>
.fab-container {
  position: fixed;
  bottom: 30px;
  right: 30px;
  z-index: 999;
}

.fab-menu {
  position: absolute;
  bottom: 60px;
  right: 0;
  display: flex;
  flex-direction: column-reverse;
  gap: 12px;
  padding: 16px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(10px);
  transform-origin: bottom right;
  animation: slideUp 0.3s ease-out;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.fab-menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
  color: #2d3748;
  transition: all 0.2s;
  white-space: nowrap;
}

.fab-menu-item:hover {
  background: #f7fafc;
  transform: translateX(-4px);
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
}

.menu-icon {
  font-size: 1.2rem;
}

.fab-main-btn {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 20px rgba(118, 75, 162, 0.4);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  z-index: 1000;
}

.fab-main-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 8px 30px rgba(118, 75, 162, 0.6);
}

.fab-main-btn:active {
  transform: scale(0.95);
}
</style>