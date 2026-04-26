<script setup>
import { ref, computed, watch } from 'vue'
import { 
  Mic, 
  Volume2, 
  Send, 
  Loader, 
  CheckCircle, 
  Calendar, 
  Clock,
  X 
} from 'lucide-vue-next'

const props = defineProps({
  inputValue: {
    type: String,
    required: true
  },
  isProcessing: {
    type: Boolean,
    default: false
  },
  isRecording: {
    type: Boolean,
    default: false
  },
  recordingDuration: {
    type: Number,
    default: 0
  },
  isAIProcessing: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits([
  'submit',
  'cancel',
  'switch-mode',
  'voice-input',
  'parse-and-fill',
  'query-schedules',  // 新增查询事件
  'update:inputValue'
])

// 本地状态
const queryResult = ref(null)

// 计算属性
const submitButtonText = computed(() => {
  // 如果输入包含查询关键词，则显示"查询日程"，否则显示"创建日程"
  const queryKeywords = ['查询', '查看', '有没有', '什么时候', '今天', '明天', '后天', '昨天', '前天', '下周', '本周', '上周', '本月', '下个月']
  const isQuery = queryKeywords.some(keyword => props.inputValue.includes(keyword))
  return isQuery ? '🔍 查询日程' : '✨ 创建日程'
})

const isQueryMode = computed(() => {
  const queryKeywords = ['查询', '查看', '有没有', '什么时候', '今天', '明天', '后天', '昨天', '前天', '下周', '本周', '上周', '本月', '下个月']
  return queryKeywords.some(keyword => props.inputValue.includes(keyword))
})

// 格式化时间
function formatTime(timeStr) {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 获取优先级标签
function getPriorityLabel(priority) {
  const labels = {
    1: '低',
    2: '中',
    3: '高'
  }
  return labels[priority] || '中'
}

// 处理提交
function handleSubmit() {
  if (isQueryMode.value) {
    emit('query-schedules')
  } else {
    emit('submit')
  }
}

// 清除查询结果
function clearQueryResult() {
  queryResult.value = null
  emit('update:inputValue', '')
}
</script>

<template>
  <div class="form-container nl-mode">
    <div class="form-header">
      <h2>
        <Mic :size="24" />
        🎤 智能语音/文本输入
      </h2>
      <button class="mode-switch-btn" @click="$emit('switch-mode')" title="切换到传统表单模式">
        <Calendar :size="18" />
        <span>使用表单</span>
      </button>
    </div>
    
    <p class="nl-hint">💡 试试这样说：</p>
    <ul class="nl-examples">
      <li>安排下周三下午两点的团队会议</li>
      <li>查询今天有哪些日程</li>
      <li>明天上午9点与客户见面</li>
      <li>查看本周的日程安排</li>
    </ul>
    
    <div class="nl-input-group">
      <textarea 
        :value="inputValue"
        @input="$emit('update:inputValue', $event.target.value)"
        placeholder="请输入您的指令，或直接点击麦克风说话...（如：安排明天下午3点开会，或查询今天日程）"
        rows="4"
        :disabled="isProcessing || isRecording"
      ></textarea>
      
      <!-- AI 处理状态指示器 -->
      <div v-if="isAIProcessing" class="ai-processing-indicator">
        <span class="ai-icon">🤖</span>
        <span>AI 正在{{ isQueryMode ? '查询' : '解析' }}中...</span>
      </div>
      
      <!-- 录音状态指示器 -->
      <div v-if="isRecording" class="recording-status-bar">
        <span class="recording-dot"></span>
        <span class="recording-label">正在录音</span>
        <span class="recording-time">{{ recordingDuration }}s</span>
      </div>
      
      <!-- 查询结果区域 -->
      <div v-if="queryResult" class="query-result-container">
        <div class="query-result-header">
          <h3>{{ queryResult.query_description }}</h3>
          <button @click="clearQueryResult" class="clear-result-btn">
            <X :size="16" />
          </button>
        </div>
        <div class="query-result-content">
          <div v-if="queryResult.schedules && queryResult.schedules.length > 0" class="result-schedules">
            <div 
              v-for="schedule in queryResult.schedules" 
              :key="schedule.id" 
              class="schedule-card"
            >
              <div class="schedule-info">
                <div class="schedule-title">{{ schedule.title }}</div>
                <div class="schedule-time">
                  <Clock :size="14" />
                  {{ formatTime(schedule.start_time) }}
                </div>
                <div v-if="schedule.content" class="schedule-details">
                  {{ schedule.content }}
                </div>
                <div class="schedule-meta">
                  <span class="priority-badge" :class="`priority-${schedule.priority}`">
                    {{ getPriorityLabel(schedule.priority) }}
                  </span>
                  <span class="completion-status" v-if="schedule.is_completed">
                    <CheckCircle :size="14" />
                    已完成
                  </span>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="no-results">
            <p>没有找到符合条件的日程。</p>
          </div>
          
          <div class="result-summary" v-if="queryResult.response">
            <p>{{ queryResult.response }}</p>
          </div>
        </div>
      </div>
      
      <!-- 操作按钮区域 -->
      <div class="nl-actions">
        <!-- 第一行：语音输入（独立大按钮） -->
        <button 
          type="button" 
          class="voice-btn" 
          @click="$emit('voice-input')"
          :disabled="isProcessing || isRecording"
          :class="{ 'recording': isRecording }"
        >
          <span class="btn-icon">🎤</span>
          <span class="btn-text">{{ isRecording ? '停止录音' : '语音输入' }}</span>
          <span v-if="isRecording" class="wave-animation">
            <span class="wave-bar"></span>
            <span class="wave-bar"></span>
            <span class="wave-bar"></span>
          </span>
        </button>
        
        <!-- 第二行：操作按钮组 -->
        <div class="action-buttons-group">
          <!-- 主要操作区 -->
          <div class="primary-actions">
            <button 
              type="button" 
              class="btn-query" 
              @click="$emit('query-schedules')"
              :disabled="isProcessing || !inputValue.trim() || isRecording || isAIProcessing"
              title="查询现有日程"
              v-if="!isQueryMode"
            >
              <span class="btn-emoji">🔍</span>
              <span class="btn-label">查询日程</span>
            </button>
            
            <button 
              type="button" 
              class="btn-parse" 
              @click="$emit('parse-and-fill')"
              :disabled="isProcessing || !inputValue.trim() || isRecording || isAIProcessing"
              title="AI 解析后预填到表单，供您审查修改"
              v-if="!isQueryMode"
            >
              <span class="btn-emoji">📝</span>
              <span class="btn-label">{{ isAIProcessing ? '解析中...' : '预填表单' }}</span>
            </button>
            
            <button 
              type="button" 
              class="btn-submit" 
              @click="handleSubmit"
              :disabled="isProcessing || !inputValue.trim() || isRecording"
              :title="isQueryMode ? '查询日程' : '创建日程'"
            >
              <span class="btn-emoji">{{ isQueryMode ? '🔍' : '✨' }}</span>
              <span class="btn-label">{{ isProcessing ? '处理中...' : (isQueryMode ? '查询日程' : '创建日程') }}</span>
            </button>
          </div>
          
          <!-- 次要操作区 -->
          <button 
            type="button" 
            class="btn-cancel" 
            @click="$emit('cancel')"
            title="取消操作"
          >
            取消
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.nl-mode {
  max-width: 600px;
}

.form-container {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(50, 50, 93, 0.11), 0 1px 3px rgba(0, 0, 0, 0.08);
  width: 100%;
}

.form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e9ecef;
}

.form-header h2 {
  margin: 0;
  color: #32325D;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.3rem;
}

.mode-switch-btn {
  background-color: #f8f9fe;
  border: 2px solid #5E72E4;
  color: #5E72E4;
  border-radius: 6px;
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s;
}

.mode-switch-btn:hover {
  background-color: #5E72E4;
  color: white;
}

.nl-hint {
  color: #8898aa;
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
  text-align: center;
  background-color: #f8f9fe;
  padding: 0.75rem;
  border-radius: 6px;
  font-weight: 500;
}

.nl-examples {
  background-color: #fff;
  border: 1px dashed #5E72E4;
  padding: 1rem;
  border-radius: 6px;
  margin-bottom: 1.5rem;
  list-style-position: inside;
}

.nl-examples li {
  color: #525F7F;
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
  line-height: 1.5;
}

.nl-input-group {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.nl-input-group textarea {
  width: 100%;
  padding: 16px;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  font-size: 1rem;
  resize: vertical;
  font-family: inherit;
  transition: all 0.3s;
  background: linear-gradient(135deg, #fafafa 0%, #ffffff 100%);
  line-height: 1.6;
}

.nl-input-group textarea:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  background: #fff;
}

.nl-input-group textarea:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

/* AI 处理状态指示器 */
.ai-processing-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-radius: 8px;
  color: #0284c7;
  font-size: 14px;
  font-weight: 500;
  animation: pulse-ai 1.5s infinite;
}

.ai-icon {
  font-size: 18px;
  animation: spin-ai 3s linear infinite;
}

@keyframes spin-ai {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@keyframes pulse-ai {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.02);
  }
}

/* 录音状态条 */
.recording-status-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
  border-radius: 8px;
  border: 2px solid #fca5a5;
  animation: pulse-bg 1.5s infinite;
}

.recording-dot {
  width: 12px;
  height: 12px;
  background-color: #dc2626;
  border-radius: 50%;
  animation: pulse-dot 1s infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.3; transform: scale(0.8); }
}

@keyframes pulse-bg {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.85; }
}

.recording-label {
  color: #dc2626;
  font-weight: 600;
  font-size: 14px;
}

.recording-time {
  font-family: 'Courier New', monospace;
  font-weight: 700;
  letter-spacing: 1px;
  color: #991b1b;
  font-size: 15px;
  min-width: 55px;
  text-align: center;
  background: rgba(255, 255, 255, 0.6);
  padding: 2px 8px;
  border-radius: 4px;
}

/* 查询结果区域 */
.query-result-container {
  margin-top: 1rem;
  padding: 1rem;
  background: #f8f9ff;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.query-result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #e2e8f0;
}

.query-result-header h3 {
  margin: 0;
  color: #32325d;
  font-size: 1.1rem;
}

.clear-result-btn {
  background: none;
  border: none;
  color: #8898aa;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  transition: all 0.2s;
}

.clear-result-btn:hover {
  background: #e9ecef;
  color: #32325d;
}

.result-schedules {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.schedule-card {
  background: white;
  border-radius: 8px;
  padding: 1rem;
  border-left: 3px solid #5e72e4;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.schedule-info {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.schedule-title {
  font-weight: 600;
  color: #32325d;
  font-size: 1.05rem;
}

.schedule-time {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #8898aa;
  font-size: 0.9rem;
}

.schedule-details {
  color: #525f7f;
  font-size: 0.9rem;
  line-height: 1.5;
}

.schedule-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-top: 0.5rem;
}

.priority-badge {
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-weight: 500;
}

.priority-badge.priority-1 {
  background: #e3f2fd;
  color: #1976d2;
}

.priority-badge.priority-2 {
  background: #fff8e1;
  color: #ffa000;
}

.priority-badge.priority-3 {
  background: #ffebee;
  color: #f44336;
}

.completion-status {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.8rem;
  color: #4caf50;
}

.no-results {
  text-align: center;
  padding: 2rem;
  color: #8898aa;
}

.result-summary {
  margin-top: 1rem;
  padding: 0.75rem;
  background: #e8f4f8;
  border-radius: 6px;
  border-left: 3px solid #26c6da;
}

.result-summary p {
  margin: 0;
  color: #32325d;
  font-size: 0.95rem;
}

/* 操作按钮区域 */
.nl-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 8px;
}

/* 语音输入按钮 - 全宽大按钮 */
.voice-btn {
  width: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 12px;
  padding: 16px 24px;
  font-size: 1.05rem;
  font-weight: 600;
  color: white;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
  position: relative;
  overflow: hidden;
  min-height: 56px;
}

.voice-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.5);
}

.voice-btn:active:not(:disabled) {
  transform: translateY(0);
}

.voice-btn.recording {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  box-shadow: 0 4px 20px rgba(245, 87, 108, 0.5);
  animation: recording-pulse 2s infinite;
}

@keyframes recording-pulse {
  0%, 100% {
    box-shadow: 0 4px 20px rgba(245, 87, 108, 0.5);
  }
  50% {
    box-shadow: 0 4px 30px rgba(245, 87, 108, 0.8);
  }
}

.voice-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.btn-icon {
  font-size: 1.4rem;
}

.btn-text {
  font-weight: 600;
  letter-spacing: 0.5px;
}

.wave-animation {
  display: flex;
  align-items: center;
  gap: 3px;
  margin-left: 8px;
  height: 24px;
}

.wave-bar {
  width: 4px;
  height: 100%;
  background-color: rgba(255, 255, 255, 0.9);
  border-radius: 2px;
  animation: wave 1s ease-in-out infinite;
}

.wave-bar:nth-child(1) { animation-delay: 0s; }
.wave-bar:nth-child(2) { animation-delay: 0.1s; }
.wave-bar:nth-child(3) { animation-delay: 0.2s; }

@keyframes wave {
  0%, 100% {
    height: 6px;
    opacity: 0.5;
  }
  50% {
    height: 20px;
    opacity: 1;
  }
}

/* 操作按钮组 */
.action-buttons-group {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.primary-actions {
  display: flex;
  gap: 12px;
  flex: 1;
}

/* 预填表单按钮 */
.btn-parse {
  flex: 1;
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
  border: none;
  border-radius: 10px;
  padding: 14px 20px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(245, 87, 108, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 48px;
}

.btn-parse:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(245, 87, 108, 0.5);
}

.btn-parse:active:not(:disabled) {
  transform: translateY(0);
}

.btn-parse:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

/* 创建日程按钮 */
.btn-submit {
  flex: 1;
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
  color: white;
  border: none;
  border-radius: 10px;
  padding: 14px 20px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(56, 239, 125, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 48px;
}

.btn-submit:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(56, 239, 125, 0.5);
}

.btn-submit:active:not(:disabled) {
  transform: translateY(0);
}

.btn-submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

/* 取消按钮 */
.btn-cancel {
  background: transparent;
  color: #64748b;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  padding: 14px 24px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  min-height: 48px;
  white-space: nowrap;
}

.btn-cancel:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
  color: #475569;
  transform: translateY(-1px);
}

.btn-cancel:active {
  transform: translateY(0);
}

/* Emoji 图标样式 */
.btn-emoji {
  font-size: 1.2rem;
  line-height: 1;
}

.btn-label {
  font-weight: 600;
  letter-spacing: 0.3px;
}

/* 响应式设计 - 平板和手机 */
@media (max-width: 768px) {
  .form-container {
    padding: 1.5rem;
  }
  
  .action-buttons-group {
    flex-direction: column;
    gap: 10px;
  }
  
  .primary-actions {
    width: 100%;
    flex-direction: column;
  }
  
  .btn-parse,
  .btn-submit,
  .btn-cancel {
    width: 100%;
  }
  
  .voice-btn {
    padding: 14px 20px;
    font-size: 1rem;
  }
}

/* 超小屏幕优化 */
@media (max-width: 480px) {
  .form-container {
    padding: 1.2rem;
  }
  
  .form-header h2 {
    font-size: 1.1rem;
  }
  
  .nl-examples {
    padding: 0.8rem;
  }
  
  .nl-examples li {
    font-size: 0.85rem;
  }
}
</style>