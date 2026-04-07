<script setup>
import { AlertTriangle, Calendar, Clock, CheckCircle, XCircle } from 'lucide-vue-next'

const props = defineProps({
  conflictData: {
    type: Object,
    required: true
  },
  isProcessing: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['confirm', 'cancel'])

function formatTime(isoString) {
  if (!isoString) return '未设置'
  const date = new Date(isoString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function handleConfirm() {
  emit('confirm')
}

function handleCancel() {
  emit('cancel')
}
</script>

<template>
  <div class="conflict-dialog-overlay">
    <div class="conflict-dialog">
      <div class="dialog-header">
        <AlertTriangle :size="32" color="#ff9800" />
        <h2>⚠️ 检测到日程冲突</h2>
      </div>

      <div class="dialog-content">
        <!-- 新日程信息 -->
        <div class="schedule-section new-schedule">
          <h3>📝 您想创建的日程</h3>
          <div class="schedule-info">
            <div class="info-item">
              <span class="label">标题：</span>
              <span class="value">{{ conflictData.parsed_data?.title || '未命名' }}</span>
            </div>
            <div class="info-item">
              <Calendar :size="16" />
              <span class="value">{{ formatTime(conflictData.parsed_data?.start_time) }}</span>
            </div>
            <div v-if="conflictData.parsed_data?.end_time" class="info-item">
              <Clock :size="16" />
              <span class="value">至 {{ formatTime(conflictData.parsed_data.end_time) }}</span>
            </div>
          </div>
        </div>

        <!-- 冲突的日程列表 -->
        <div class="schedule-section conflicting-schedules">
          <h3>⛔ 与以下日程冲突</h3>
          <div v-for="(conflict, index) in conflictData.conflicts" :key="conflict.schedule_id" class="conflict-item">
            <div class="conflict-number">{{ index + 1 }}</div>
            <div class="conflict-details">
              <div class="conflict-title">{{ conflict.title }}</div>
              <div class="conflict-time">
                <Calendar :size="14" />
                {{ formatTime(conflict.start_time) }}
                <span v-if="conflict.end_time"> - {{ formatTime(conflict.end_time) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 提示信息 -->
        <div class="warning-message">
          <p>💡 提示：继续创建将导致时间重叠，建议您调整时间安排以避免冲突。</p>
        </div>
      </div>

      <div class="dialog-actions">
        <button 
          class="btn-cancel" 
          @click="handleCancel"
          :disabled="isProcessing"
        >
          <XCircle :size="18" />
          <span>取消创建</span>
        </button>
        <button 
          class="btn-confirm" 
          @click="handleConfirm"
          :disabled="isProcessing"
        >
          <CheckCircle :size="18" />
          <span>{{ isProcessing ? '创建中...' : '仍要创建' }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.conflict-dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.conflict-dialog {
  background: white;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.dialog-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 24px 24px 16px;
  border-bottom: 2px solid #fff3e0;
  background: linear-gradient(135deg, #fff8e1 0%, #fff3e0 100%);
}

.dialog-header h2 {
  margin: 0;
  font-size: 20px;
  color: #e65100;
}

.dialog-content {
  padding: 24px;
}

.schedule-section {
  margin-bottom: 20px;
  padding: 16px;
  border-radius: 12px;
}

.new-schedule {
  background: #e8f5e9;
  border-left: 4px solid #4caf50;
}

.conflicting-schedules {
  background: #ffebee;
  border-left: 4px solid #f44336;
}

.schedule-section h3 {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: #333;
}

.schedule-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.info-item .label {
  font-weight: 600;
  color: #666;
  min-width: 50px;
}

.info-item .value {
  color: #333;
}

.conflict-item {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
  padding: 12px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.conflict-item:last-child {
  margin-bottom: 0;
}

.conflict-number {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #f44336;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
  flex-shrink: 0;
}

.conflict-details {
  flex: 1;
}

.conflict-title {
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.conflict-time {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #666;
}

.warning-message {
  padding: 12px;
  background: #fff3e0;
  border-radius: 8px;
  border-left: 4px solid #ff9800;
}

.warning-message p {
  margin: 0;
  font-size: 14px;
  color: #e65100;
  line-height: 1.5;
}

.dialog-actions {
  display: flex;
  gap: 12px;
  padding: 20px 24px;
  border-top: 1px solid #e0e0e0;
  background: #fafafa;
}

.dialog-actions button {
  flex: 1;
  padding: 12px 20px;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.2s;
}

.btn-cancel {
  background: #f5f5f5;
  color: #666;
}

.btn-cancel:hover:not(:disabled) {
  background: #e0e0e0;
  color: #333;
}

.btn-confirm {
  background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(255, 152, 0, 0.3);
}

.btn-confirm:hover:not(:disabled) {
  background: linear-gradient(135deg, #f57c00 0%, #ef6c00 100%);
  box-shadow: 0 4px 12px rgba(255, 152, 0, 0.4);
  transform: translateY(-1px);
}

.dialog-actions button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@media (max-width: 640px) {
  .conflict-dialog {
    width: 95%;
    max-height: 90vh;
  }
  
  .dialog-actions {
    flex-direction: column;
  }
}
</style>