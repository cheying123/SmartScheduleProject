<template>
  <div class="settings-panel">
    <h3>偏好设置</h3>
    
    <div class="setting-item">
      <div class="setting-label">
        <Clock :size="20" />
        <span>时区显示</span>
      </div>
      <div class="setting-value">
        {{ currentTimezone }}
      </div>
    </div>
    
    <div class="setting-item">
      <div class="setting-label">
        <Globe :size="20" />
        <span>默认城市</span>
      </div>
      <div class="setting-value">
        {{ user?.location_name || '北京 (101010100)' }}
      </div>
    </div>
    
    <div class="setting-item">
      <div class="setting-label">
        <Bell :size="20" />
        <span>天气提醒</span>
      </div>
      <label class="switch">
        <input type="checkbox" :checked="user?.weather_alerts_enabled !== false" disabled>
        <span class="slider"></span>
      </label>
    </div>
    
    <div class="setting-section">
      <h4>关于</h4>
      <p class="about-text">
        基于多模态交互的个性化智能日程管理助手<br>
        版本：v1.0.0<br>
        技术栈：Vue 3 + Flask + MySQL
      </p>
    </div>
  </div>
</template>

<script setup>
import { Clock, Globe, Bell } from 'lucide-vue-next';

// 定义组件的 props
defineProps({
  user: {
    type: Object,
    default: null
  },
  currentTimezone: {
    type: String,
    default: ''
  }
});
</script>

<style scoped>
/* ===== 设置面板样式 ===== */
.settings-panel {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(50, 50, 93, 0.11), 0 1px 3px rgba(0, 0, 0, 0.08);
}

.settings-panel h3 {
  margin: 0 0 1.5rem 0;
  color: #32325D;
  font-size: 1.2rem;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 0;
  border-bottom: 1px solid #e9ecef;
}

.setting-label {
  color: #32325D;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.setting-value {
  color: #8898aa;
  font-size: 0.9rem;
}

.setting-section {
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 2px solid #e9ecef;
}

.setting-section h4 {
  margin: 0 0 1rem 0;
  color: #32325D;
  font-size: 1rem;
}

.about-text {
  color: #8898aa;
  font-size: 0.9rem;
  line-height: 1.8;
}

/* Switch 开关样式 */
.switch {
  position: relative;
  display: inline-block;
  width: 50px;
  height: 24px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: .4s;
  border-radius: 24px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 16px;
  width: 16px;
  left: 4px;
  bottom: 4px;
  background-color: white;
  transition: .4s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: #5E72E4;
}

input:checked + .slider:before {
  transform: translateX(26px);
}
</style>