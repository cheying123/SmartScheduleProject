<script setup>
import { Globe, PlusCircle } from 'lucide-vue-next'
import { formatRecordingTime } from '@/utils/timeUtils'

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
  'update:inputValue'
])
</script>

<template>
  <div class="form-container nl-mode">
    <div class="form-header">
      <h2>
        <Globe :size="24" />
        🎤 智能语音/文本输入
      </h2>
      <button class="mode-switch-btn" @click="$emit('switch-mode')" title="切换到传统表单模式">
        <PlusCircle :size="18" />
        <span>使用表单</span>
      </button>
    </div>
    
    <p class="nl-hint">💡 试试这样说：</p>
    <ul class="nl-examples">
      <li>"安排下周三下午两点的团队会议"</li>
      <li>"提醒我每周一早上检查邮箱"</li>
      <li>"明天上午 9 点与客户见面"</li>
    </ul>
    
    <div class="nl-input-group">
      <textarea 
        :value="inputValue"
        @input="$emit('update:inputValue', $event.target.value)"
        placeholder="请输入您的指令，或直接点击麦克风说话..."
        rows="4"
        :disabled="isProcessing || isRecording"
      ></textarea>
      
      <!-- AI 处理状态指示器 -->
      <div v-if="isAIProcessing" class="ai-processing-indicator">
        <span class="ai-icon">🤖</span>
        <span>AI 正在智能解析中...</span>
      </div>
      
      <div class="nl-actions">
        <button 
          type="button" 
          class="voice-btn" 
          @click="$emit('voice-input')"
          :disabled="isProcessing || isRecording"
          :class="{ 'recording': isRecording }"
        >
          <span class="btn-icon">🎤</span>
          <span class="btn-text">{{ isRecording ? '正在录音...' : '语音输入' }}</span>
          <span v-if="isRecording" class="wave-animation">
            <span class="wave-bar"></span>
            <span class="wave-bar"></span>
            <span class="wave-bar"></span>
          </span>
        </button>
        
        <div v-if="isRecording" class="recording-indicator">
          <span class="recording-dot"></span>
          <span class="recording-label">录音中</span>
          <span class="recording-time">{{ formatRecordingTime(recordingDuration) }}</span>
        </div>
        
        <div class="nl-actions-right">
          <button 
            type="button" 
            class="btn-submit" 
            @click="$emit('submit')"
            :disabled="isProcessing || !inputValue.trim() || isRecording"
          >
            {{ isProcessing ? '处理中...' : '✨ 创建日程' }}
          </button>
          <button 
            type="button" 
            class="btn-cancel" 
            @click="$emit('cancel')"
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
  gap: 12px;
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

.nl-actions {
  display: flex;
  gap: 12px;
  margin-top: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.nl-actions-right {
  display: flex;
  gap: 12px;
  margin-left: auto;
  align-items: center;
}

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
  margin-top: 8px;
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

.voice-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 12px;
  padding: 12px 20px;
  font-size: 1rem;
  font-weight: 600;
  color: white;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
  position: relative;
  overflow: hidden;
}

.voice-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
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
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.btn-icon {
  font-size: 1.2rem;
}

.btn-text {
  font-weight: 600;
}

.wave-animation {
  display: flex;
  align-items: center;
  gap: 3px;
  margin-left: 8px;
  height: 20px;
}

.wave-bar {
  width: 3px;
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
    height: 4px;
    opacity: 0.5;
  }
  50% {
    height: 16px;
    opacity: 1;
  }
}

.recording-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
  border-radius: 20px;
  font-size: 14px;
  color: #dc2626;
  font-weight: 500;
  animation: pulse-bg 1.5s infinite;
}

.recording-dot {
  width: 10px;
  height: 10px;
  background-color: #dc2626;
  border-radius: 50%;
  animation: pulse-dot 1s infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

@keyframes pulse-bg {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.recording-label {
  margin-right: 4px;
  font-weight: 500;
}

.recording-time {
  font-family: 'Courier New', monospace;
  font-weight: 700;
  letter-spacing: 1px;
  min-width: 50px;
  text-align: center;
}

.btn-submit {
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 12px 24px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(56, 239, 125, 0.4);
}

.btn-submit:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(56, 239, 125, 0.6);
}

.btn-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.btn-cancel {
  background: linear-gradient(135deg, #e0e0e0 0%, #f5f5f5 100%);
  color: #555;
  border: none;
  border-radius: 8px;
  padding: 12px 24px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.btn-cancel:hover {
  background: linear-gradient(135deg, #d0d0d0 0%, #e8e8e8 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
</style>