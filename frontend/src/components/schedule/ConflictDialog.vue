<script setup>
import { AlertTriangle, Calendar, Clock, CheckCircle, XCircle,Sparkles } from 'lucide-vue-next'

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

function handleApplySuggestion(suggestion) {
  emit('apply-suggestion', suggestion)
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

        <!-- 【新增】AI 智能建议区域 -->
        <div v-if="conflictData.suggestions && conflictData.suggestions.length > 0" class="suggestion-section">
          <h3><Sparkles :size="18" class="sparkle-icon" /> AI 智能调整建议</h3>
          <p class="suggestion-desc">根据您的历史习惯，我们为您找到了以下空闲时段：</p>
          
          <div v-for="(item, index) in conflictData.suggestions" :key="index" class="suggestion-item" @click="handleApplySuggestion(item)">
            <div class="suggestion-time">
              <Clock :size="16" />
              <span>{{ formatTime(item.start_time) }} - {{ formatTime(item.end_time) }}</span>
            </div>
            <div class="suggestion-reason">{{ item.reason }}</div>
            <button class="btn-apply">一键采纳</button>
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
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.conflict-dialog {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
  overflow: hidden;
}

.dialog-header {
  padding: 1.5rem;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  gap: 1rem;
  background: #fff7ed;
}

.dialog-header h2 {
  margin: 0;
  font-size: 1.25rem;
  color: #c2410c;
}

.dialog-content {
  padding: 1.5rem;
  max-height: 60vh;
  overflow-y: auto;
}

.schedule-section {
  margin-bottom: 1.5rem;
}

.schedule-section h3 {
  font-size: 1rem;
  color: #475569;
  margin-bottom: 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.schedule-info {
  background: #f8fafc;
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  color: #334155;
}

.info-item:last-child {
  margin-bottom: 0;
}

/* 智能建议样式 */
.suggestion-section {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1.5rem;
}

.sparkle-icon {
  color: #16a34a;
}

.suggestion-desc {
  font-size: 0.85rem;
  color: #15803d;
  margin-top: -0.5rem;
  margin-bottom: 0.75rem;
}

.suggestion-item {
  background: white;
  padding: 0.75rem;
  margin-top: 0.5rem;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid #dcfce7;
  position: relative;
}

.suggestion-item:hover {
  border-color: #16a34a;
  transform: translateY(-2px);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.suggestion-time {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  color: #166534;
  margin-bottom: 4px;
}

.suggestion-reason {
  font-size: 0.8rem;
  color: #6b7280;
  margin-bottom: 8px;
}

.btn-apply {
  background: #16a34a;
  color: white;
  border: none;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 0.8rem;
  cursor: pointer;
  float: right;
  transition: background 0.2s;
}

.btn-apply:hover {
  background: #15803d;
}

.conflict-item {
  background: #fef2f2;
  border: 1px solid #fecaca;
  padding: 0.75rem;
  border-radius: 6px;
  margin-bottom: 0.5rem;
}

.conflict-item-title {
  font-weight: 600;
  color: #991b1b;
  margin-bottom: 0.25rem;
}

.conflict-item-time {
  font-size: 0.85rem;
  color: #b91c1c;
}

.dialog-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  background: #f8fafc;
}

.btn-cancel, .btn-confirm {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel {
  background: white;
  border: 1px solid #cbd5e1;
  color: #475569;
}

.btn-cancel:hover {
  background: #f1f5f9;
}

.btn-confirm {
  background: #f97316;
  border: 1px solid #f97316;
  color: white;
}

.btn-confirm:hover {
  background: #ea580c;
}

.btn-cancel:disabled, .btn-confirm:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>