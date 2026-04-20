<template>
  <div v-if="dailyBriefing && dailyBriefing.message" class="briefing-card-modern">
    <div class="briefing-icon-wrapper">
      <MessageSquare :size="24" color="#667eea" />
    </div>
    <div class="briefing-body">
      <div class="briefing-header-row">
        <h3>🌤️ 今日智能提醒</h3>
        <button 
          v-if="dailyBriefing.ai_advice" 
          class="speak-btn-mini" 
          @click="handleSpeak(dailyBriefing.ai_advice)"
          title="语音播报"
        >
          🔊
        </button>
      </div>
      
      <p class="briefing-text">
        {{ dailyBriefing.ai_advice || dailyBriefing.message || '暂无今日建议' }}
      </p>
      
      <div class="briefing-meta">
        <span class="meta-item">
          <Calendar :size="14" /> 
          {{ dailyBriefing.schedule_count || 0 }} 个日程
        </span>
        
        <span v-if="dailyBriefing.weather && dailyBriefing.weather.text !== '未知'" class="meta-item weather-item">
          <Sun :size="14" /> 
          {{ dailyBriefing.weather.text }} {{ dailyBriefing.weather.temperature }}°C
        </span>

        <button 
          class="refresh-briefing" 
          @click="refreshBriefing" 
          :disabled="isBriefingLoading"
        >
          <Sparkles :size="14" /> 
          {{ isBriefingLoading ? '生成中...' : '刷新建议' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { MessageSquare, Calendar, Sun, Sparkles } from 'lucide-vue-next';

// 定义组件的 props
const props = defineProps({
  dailyBriefing: {
    type: Object,
    default: null
  },
  isBriefingLoading: {
    type: Boolean,
    default: false
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
const emit = defineEmits(['refresh-briefing']);

// 语音播报函数
function handleSpeak(text) {
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel(); // 停止之前的播报
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'zh-CN';
    window.speechSynthesis.speak(utterance);
  } else {
    alert('您的浏览器不支持语音播报');
  }
}

// 刷新摘要函数
async function refreshBriefing() {
  emit('refresh-briefing');
}
</script>

<style scoped>
/* ✅ 优化：现代简报卡片样式 */
.briefing-card-modern {
  display: flex;
  gap: 20px;
  background: white;
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 24px;
  border: 1px solid #eef2f7;
  box-shadow: 0 10px 30px -10px rgba(102, 126, 234, 0.15);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.briefing-card-modern::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: linear-gradient(to bottom, #667eea, #764ba2);
}

.briefing-card-modern:hover {
  transform: translateY(-4px);
  box-shadow: 0 20px 40px -10px rgba(102, 126, 234, 0.25);
}

.briefing-icon-wrapper {
  flex-shrink: 0;
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, #f6f9fc 0%, #eef2f9 100%);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: inset 0 2px 4px rgba(255, 255, 255, 0.8);
}

.briefing-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.briefing-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.briefing-header-row h3 {
  margin: 0;
  font-size: 1.25rem;
  color: #2d3748;
  font-weight: 700;
  letter-spacing: -0.025em;
}

.speak-btn-mini {
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 1.2rem;
  opacity: 0.6;
  transition: opacity 0.2s;
  padding: 4px;
}

.speak-btn-mini:hover {
  opacity: 1;
}

.briefing-text {
  margin: 0 0 16px 0;
  color: #4a5568;
  font-size: 1rem;
  line-height: 1.6;
}

.briefing-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  padding-top: 12px;
  border-top: 1px dashed #e2e8f0;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.875rem;
  color: #718096;
  font-weight: 500;
}

.weather-item {
  color: #ed8936;
}

.refresh-briefing {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 6px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 5px rgba(118, 75, 162, 0.2);
}

.refresh-briefing:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 4px 8px rgba(118, 75, 162, 0.3);
}

.refresh-briefing:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  filter: grayscale(0.5);
}
</style>