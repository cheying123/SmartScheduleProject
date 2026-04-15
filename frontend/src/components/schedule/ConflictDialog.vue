<script setup>
import { AlertTriangle, Calendar, Clock, CheckCircle, XCircle, Sparkles, ArrowRight, Info } from 'lucide-vue-next'

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

const emit = defineEmits(['confirm', 'cancel', 'apply-suggestion'])

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
  <div class="conflict-dialog-overlay" @click.self="handleCancel">
    <div class="conflict-dialog">
      <!-- 头部区域 -->
      <div class="dialog-header">
        <div class="header-icon-wrapper">
          <AlertTriangle :size="28" />
        </div>
        <div class="header-content">
          <h2>检测到日程冲突</h2>
          <p class="header-subtitle">您的新日程与现有安排存在时间重叠</p>
        </div>
      </div>

      <div class="dialog-body">
        <!-- 新日程卡片 -->
        <div class="card new-schedule-card">
          <div class="card-header">
            <Calendar :size="18" class="card-icon" />
            <h3>您想创建的日程</h3>
          </div>
          <div class="card-content">
            <div class="schedule-title">{{ conflictData.parsed_data?.title || '未命名' }}</div>
            <div class="schedule-time">
              <Clock :size="14" />
              <span>{{ formatTime(conflictData.parsed_data?.start_time) }}</span>
              <span v-if="conflictData.parsed_data?.end_time" class="time-separator">至</span>
              <span v-if="conflictData.parsed_data?.end_time">{{ formatTime(conflictData.parsed_data.end_time) }}</span>
            </div>
          </div>
        </div>

        <!-- AI 智能建议区域 -->
        <div v-if="conflictData.suggestions && conflictData.suggestions.length > 0" class="card suggestion-card">
          <div class="card-header">
            <Sparkles :size="18" class="card-icon sparkle" />
            <h3>AI 智能推荐</h3>
            <span class="badge">{{ conflictData.suggestions.length }} 个空闲时段</span>
          </div>
          <div class="card-content">
            <div 
              v-for="(item, index) in conflictData.suggestions" 
              :key="index" 
              class="suggestion-item"
              @click="handleApplySuggestion(item)"
            >
              <div class="suggestion-main">
                <div class="suggestion-time-slot">
                  <Clock :size="16" />
                  <span class="time-range">{{ formatTime(item.start_time) }} - {{ formatTime(item.end_time) }}</span>
                </div>
                <button class="btn-adopt" @click.stop="handleApplySuggestion(item)">
                  采纳
                  <ArrowRight :size="14" />
                </button>
              </div>
              <div class="suggestion-reason">
                <Info :size="12" />
                <span>{{ item.reason }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 冲突日程列表 -->
        <div class="card conflict-card">
          <div class="card-header">
            <XCircle :size="18" class="card-icon danger" />
            <h3>冲突的日程 ({{ conflictData.conflicts?.length || 0 }})</h3>
          </div>
          <div class="card-content">
            <div 
              v-for="(conflict, index) in conflictData.conflicts" 
              :key="conflict.schedule_id" 
              class="conflict-item"
            >
              <div class="conflict-index">{{ index + 1 }}</div>
              <div class="conflict-info">
                <div class="conflict-title">{{ conflict.title }}</div>
                <div class="conflict-time">
                  <Calendar :size="12" />
                  <span>{{ formatTime(conflict.start_time) }}</span>
                  <span v-if="conflict.end_time" class="time-separator">至</span>
                  <span v-if="conflict.end_time">{{ formatTime(conflict.end_time) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 提示说明 -->
        <div class="info-banner">
          <Info :size="16" />
          <p>您可以选择采纳 AI 推荐的空闲时段，或点击下方按钮强制创建（可能导致时间重叠）</p>
        </div>
      </div>

      <!-- 底部操作区 -->
      <div class="dialog-footer">
        <button 
          class="btn btn-secondary" 
          @click="handleCancel"
          :disabled="isProcessing"
        >
          <XCircle :size="18" />
          <span>取消创建</span>
        </button>
        <button 
          class="btn btn-primary" 
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
/* ===== 遮罩层 ===== */
.conflict-dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

/* ===== 对话框主体 ===== */
.conflict-dialog {
  background: white;
  border-radius: 16px;
  width: 90%;
  max-width: 560px;
  max-height: 85vh;
  min-height: 400px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.1);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  animation: slideUp 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* ===== 头部区域 ===== */
.dialog-header {
  padding: 24px 28px;
  background: linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%);
  border-bottom: 1px solid #fed7aa;
  display: flex;
  align-items: flex-start;
  gap: 16px;
  flex-shrink: 0;
}

.header-icon-wrapper {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(249, 115, 22, 0.3);
}

.header-content h2 {
  margin: 0 0 4px 0;
  font-size: 1.25rem;
  font-weight: 700;
  color: #1e293b;
}

.header-subtitle {
  margin: 0;
  font-size: 0.875rem;
  color: #64748b;
  line-height: 1.5;
}

/* ===== 内容区域 ===== */
.dialog-body {
  padding: 24px 28px;
  overflow-y: auto;
  overflow-x: hidden;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 0;
}

/* ===== 卡片通用样式 ===== */
.card {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  overflow: visible;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.card-header {
  padding: 14px 18px;
  display: flex;
  align-items: center;
  gap: 10px;
  border-bottom: 1px solid #f1f5f9;
}

.card-header h3 {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 600;
  color: #334155;
  flex: 1;
}

.card-icon {
  color: #64748b;
}

.card-icon.sparkle {
  color: #10b981;
}

.card-icon.danger {
  color: #ef4444;
}

.badge {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
}

.card-content {
  padding: 16px 18px;
}

/* ===== AI 建议卡片特殊处理 ===== */
.suggestion-card .card-content {
  max-height: 300px;
  overflow-y: auto;
  overflow-x: hidden;
}

.suggestion-card .card-content::-webkit-scrollbar {
  width: 4px;
}

.suggestion-card .card-content::-webkit-scrollbar-track {
  background: #f0fdf4;
  border-radius: 2px;
}

.suggestion-card .card-content::-webkit-scrollbar-thumb {
  background: #86efac;
  border-radius: 2px;
}

.suggestion-card .card-content::-webkit-scrollbar-thumb:hover {
  background: #10b981;
}

/* ===== 冲突日程卡片特殊处理 ===== */
.conflict-card .card-content {
  max-height: 250px;
  overflow-y: auto;
  overflow-x: hidden;
}

.conflict-card .card-content::-webkit-scrollbar {
  width: 4px;
}

.conflict-card .card-content::-webkit-scrollbar-track {
  background: #fef2f2;
  border-radius: 2px;
}

.conflict-card .card-content::-webkit-scrollbar-thumb {
  background: #fca5a5;
  border-radius: 2px;
}

.conflict-card .card-content::-webkit-scrollbar-thumb:hover {
  background: #ef4444;
}

/* ===== 新日程卡片 ===== */
.new-schedule-card {
  border-left: 4px solid #3b82f6;
  background: linear-gradient(to right, #eff6ff 0%, white 100%);
}

.new-schedule-card .card-icon {
  color: #3b82f6;
}

.schedule-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 8px;
}

.schedule-time {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.875rem;
  color: #64748b;
}

.time-separator {
  color: #cbd5e1;
  margin: 0 4px;
}

/* ===== AI 建议卡片 ===== */
.suggestion-card {
  border-left: 4px solid #10b981;
  background: linear-gradient(to right, #f0fdf4 0%, white 100%);
}

.suggestion-item {
  padding: 14px;
  background: white;
  border: 1.5px solid #d1fae5;
  border-radius: 10px;
  margin-bottom: 12px;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.suggestion-item:last-child {
  margin-bottom: 0;
}

.suggestion-item:hover {
  border-color: #10b981;
  transform: translateX(4px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.15);
}

.suggestion-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  gap: 12px;
}

.suggestion-time-slot {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #065f46;
  font-size: 0.9rem;
  flex: 1;
  min-width: 0;
}

.time-range {
  font-family: 'Courier New', monospace;
  letter-spacing: 0.5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.btn-adopt {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border: none;
  padding: 6px 14px;
  border-radius: 8px;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all 0.2s;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.25);
  flex-shrink: 0;
  white-space: nowrap;
}

.btn-adopt:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.35);
}

.btn-adopt:active {
  transform: translateY(0);
}

.suggestion-reason {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: 0.8rem;
  color: #6b7280;
  line-height: 1.5;
  padding-left: 24px;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.suggestion-reason svg {
  margin-top: 2px;
  flex-shrink: 0;
  color: #9ca3af;
}

/* ===== 冲突日程卡片 ===== */
.conflict-card {
  border-left: 4px solid #ef4444;
  background: linear-gradient(to right, #fef2f2 0%, white 100%);
}

.conflict-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: white;
  border: 1px solid #fecaca;
  border-radius: 8px;
  margin-bottom: 10px;
  transition: all 0.2s;
}

.conflict-item:last-child {
  margin-bottom: 0;
}

.conflict-item:hover {
  border-color: #fca5a5;
  background: #fff5f5;
}

.conflict-index {
  width: 28px;
  height: 28px;
  background: #fee2e2;
  color: #dc2626;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.85rem;
  flex-shrink: 0;
}

.conflict-info {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.conflict-title {
  font-weight: 600;
  color: #991b1b;
  font-size: 0.9rem;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.conflict-time {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8rem;
  color: #b91c1c;
  flex-wrap: wrap;
}

.conflict-time svg {
  flex-shrink: 0;
}

/* ===== 提示横幅 ===== */
.info-banner {
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border: 1px solid #bae6fd;
  border-radius: 10px;
  padding: 12px 16px;
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.info-banner svg {
  color: #0284c7;
  flex-shrink: 0;
  margin-top: 2px;
}

.info-banner p {
  margin: 0;
  font-size: 0.85rem;
  color: #0369a1;
  line-height: 1.6;
}

/* ===== 底部操作区 ===== */
.dialog-footer {
  padding: 20px 28px;
  border-top: 1px solid #e2e8f0;
  background: #f8fafc;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.btn {
  padding: 10px 20px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  gap: 8px;
  border: none;
  min-width: 120px;
  justify-content: center;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: white;
  border: 1.5px solid #cbd5e1;
  color: #475569;
}

.btn-secondary:hover:not(:disabled) {
  background: #f1f5f9;
  border-color: #94a3b8;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.btn-primary {
  background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(249, 115, 22, 0.3);
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(249, 115, 22, 0.4);
}

.btn-primary:active:not(:disabled) {
  transform: translateY(0);
}

/* ===== 滚动条美化 ===== */
.dialog-body::-webkit-scrollbar {
  width: 6px;
}

.dialog-body::-webkit-scrollbar-track {
  background: #f1f5f9;
}

.dialog-body::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.dialog-body::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* ===== 响应式适配 ===== */
@media (max-width: 640px) {
  .conflict-dialog {
    width: 95%;
    max-height: 90vh;
    min-height: 350px;
  }

  .dialog-header {
    padding: 20px;
  }

  .dialog-body {
    padding: 20px;
    gap: 12px;
  }

  /* 移动端卡片内容区域高度调整 */
  .suggestion-card .card-content {
    max-height: 250px;
  }

  .conflict-card .card-content {
    max-height: 200px;
  }

  .dialog-footer {
    padding: 16px 20px;
    flex-direction: column-reverse;
    gap: 10px;
  }

  .btn {
    width: 100%;
  }

  .suggestion-main {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .btn-adopt {
    width: 100%;
    justify-content: center;
  }

  .header-content h2 {
    font-size: 1.1rem;
  }

  .header-subtitle {
    font-size: 0.8rem;
  }
}

/* ===== 超小屏幕适配 ===== */
@media (max-width: 375px) {
  .conflict-dialog {
    width: 98%;
    max-height: 92vh;
  }

  .dialog-header {
    padding: 16px;
    gap: 12px;
  }

  .dialog-body {
    padding: 16px;
  }

  .header-icon-wrapper {
    width: 40px;
    height: 40px;
  }

  .header-icon-wrapper svg {
    width: 24px;
    height: 24px;
  }
}
</style>