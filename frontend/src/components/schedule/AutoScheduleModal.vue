<template>
  <transition name="fade">
    <div v-if="isVisible" class="form-overlay" @click.self="closeModal">
      <div class="form-container auto-schedule-modal">
        <div class="modal-header">
          <Sparkles :size="24" color="#667eea" />
          <h2>✨ 智能一键排程</h2>
        </div>
        <div class="modal-body">
          <p class="modal-desc">请输入待办事项，格式：<strong>任务名称 时长(分钟)</strong>，多个任务用逗号或换行分隔。</p>
          <textarea 
            v-model="tasksInput" 
            placeholder="例如：&#10;复习数学 60&#10;跑步 30&#10;阅读英语 45"
            class="auto-schedule-textarea"
          ></textarea>
          <div class="schedule-preview-hint">
            💡 系统将根据您的空闲时间自动安排在未来 3 天内。
          </div>
        </div>
        <div class="form-actions">
          <button type="button" class="btn-cancel" @click="closeModal">取消</button>
          <button 
            type="button" 
            class="btn-submit btn-auto-schedule" 
            @click="handleSubmit"
            :disabled="isProcessing || !tasksInput.trim()"
          >
            <Sparkles :size="16" />
            {{ isProcessing ? '正在排程...' : '开始智能排程' }}
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, watch } from 'vue';
import { Sparkles } from 'lucide-vue-next';

// 定义组件的 props
const props = defineProps({
  isVisible: {
    type: Boolean,
    default: false
  },
  isProcessing: {
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
const emit = defineEmits(['close', 'submit']);

// 任务输入响应式数据
const tasksInput = ref('');

// 监听组件可见性变化，重置输入框
watch(
  () => props.isVisible,
  (newVal) => {
    if (!newVal) {
      tasksInput.value = '';
    }
  }
);

// 关闭模态框
function closeModal() {
  emit('close');
}

// 提交任务
function handleSubmit() {
  if (!tasksInput.value.trim()) return;

  // 解析输入字符串为任务数组
  const tasks = tasksInput.value.split(/[,\n]/).map(item => {
    const parts = item.trim().split(/\s+/);
    const duration = parseInt(parts.pop()) || 30; // 默认30分钟
    const title = parts.join(' ');
    return { title, duration_minutes: duration };
  }).filter(t => t.title);

  emit('submit', tasks);
}
</script>

<style scoped>
.form-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.form-container {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  position: relative;
}

.auto-schedule-modal {
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.modal-header h2 {
  margin: 0;
  color: #32325D;
}

.modal-body {
  margin-bottom: 1.5rem;
}

.modal-desc {
  margin: 0 0 1rem 0;
  color: #525f7f;
  line-height: 1.6;
}

.modal-desc strong {
  color: #32325D;
  font-weight: 600;
}

.auto-schedule-textarea {
  width: 100%;
  min-height: 150px;
  padding: 1rem;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  resize: vertical;
  font-family: inherit;
  font-size: 1rem;
  line-height: 1.5;
  box-sizing: border-box;
  margin-bottom: 0.5rem;
}

.auto-schedule-textarea:focus {
  outline: none;
  border-color: #5E72E4;
  box-shadow: 0 0 0 3px rgba(94, 114, 228, 0.1);
}

.schedule-preview-hint {
  color: #8898aa;
  font-size: 0.9rem;
  font-style: italic;
  margin-top: 0.5rem;
}

.form-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
}

.btn-cancel {
  padding: 0.75rem 1.5rem;
  border: 1px solid #e9ecef;
  background-color: #f8f9fa;
  color: #525f7f;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-cancel:hover {
  background-color: #e9ecef;
  transform: translateY(-1px);
}

.btn-submit {
  padding: 0.75rem 1.5rem;
  border: none;
  background-color: #5E72E4;
  color: white;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s;
}

.btn-submit:hover:not(:disabled) {
  background-color: #4c5fd5;
  transform: translateY(-1px);
}

.btn-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-auto-schedule {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 4px 15px rgba(118, 75, 162, 0.3);
}

.btn-auto-schedule:hover:not(:disabled) {
  transform: translateY(-3px) scale(1.02);
  box-shadow: 0 8px 25px rgba(118, 75, 162, 0.5);
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter, .fade-leave-to {
  opacity: 0;
}
</style>