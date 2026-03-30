<script setup>
import { PlusCircle, Globe } from 'lucide-vue-next'
import { PRIORITY_LEVELS, RECURRING_PATTERNS } from '@/constants'

const props = defineProps({
  schedule: {
    type: Object,
    required: true
  },
  mode: {
    type: String,
    default: 'create', // 'create' or 'edit'
    validator: (value) => ['create', 'edit'].includes(value)
  }
})

const emit = defineEmits(['submit', 'cancel', 'switch-mode'])
</script>

<template>
  <div class="form-container">
    <div class="form-header">
      <h2>
        <PlusCircle :size="24" />
        {{ mode === 'create' ? '传统日常创建' : '编辑日程' }}
      </h2>
      <button 
        v-if="mode === 'create'"
        class="mode-switch-btn" 
        @click="$emit('switch-mode')"
        title="切换到智能输入模式"
      >
        <Globe :size="18" />
        <span>试试智能输入</span>
      </button>
    </div>
    
    <form @submit.prevent="$emit('submit')">
      <div class="form-group">
        <label for="title">标题</label>
        <input 
          id="title" 
          type="text" 
          :value="schedule.title"
          @input="$emit('update:schedule', { ...schedule, title: $event.target.value })"
          placeholder="例如：团队周会" 
          required
        >
      </div>
      
      <div class="form-group">
        <label for="content">内容</label>
        <textarea 
          id="content" 
          :value="schedule.content"
          @input="$emit('update:schedule', { ...schedule, content: $event.target.value })"
          placeholder="例如：讨论项目进展 (可选)"
        ></textarea>
      </div>
      
      <div class="form-group">
        <label for="start_time">开始时间</label>
        <input 
          id="start_time" 
          type="datetime-local" 
          :value="schedule.start_time"
          @input="$emit('update:schedule', { ...schedule, start_time: $event.target.value })"
          required
        >
      </div>
      
      <div class="form-group">
        <label for="priority">优先级</label>
        <select 
          id="priority" 
          :value="schedule.priority"
          @change="$emit('update:schedule', { ...schedule, priority: parseInt($event.target.value) })"
          class="form-select"
        >
          <option v-for="level in PRIORITY_LEVELS" 
                  :key="level.value" 
                  :value="level.value">
            {{ level.label }}
          </option>
        </select>
      </div>
      
      <div class="form-group">
        <label class="checkbox-label">
          <input 
            type="checkbox" 
            :checked="schedule.is_recurring"
            @change="$emit('update:schedule', { ...schedule, is_recurring: $event.target.checked })"
            class="checkbox-input"
          >
          <span>重复日程</span>
        </label>
      </div>
      
      <div v-if="schedule.is_recurring" class="form-group">
        <label for="recurring_pattern">重复模式</label>
        <select 
          id="recurring_pattern" 
          :value="schedule.recurring_pattern"
          @change="$emit('update:schedule', { ...schedule, recurring_pattern: $event.target.value })"
          class="form-select"
        >
          <option v-for="pattern in RECURRING_PATTERNS" 
                  :key="pattern.value" 
                  :value="pattern.value">
            {{ pattern.label }}
          </option>
        </select>
      </div>
      
      <div class="form-actions">
        <button type="button" class="btn-cancel" @click="$emit('cancel')">取消</button>
        <button type="submit" class="btn-submit">
          {{ mode === 'create' ? '确认添加' : '保存修改' }}
        </button>
      </div>
    </form>
  </div>
</template>

<style scoped>
/* 从 HomeView.vue 复制表单相关样式 */
/* 表单容器 */
.form-container {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(50, 50, 93, 0.11), 0 1px 3px rgba(0, 0, 0, 0.08);
  width: 100%;
  max-width: 500px;
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

/* 表单组 */
.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: #32325D;
  font-weight: 500;
}

.form-group input[type="text"],
.form-group textarea,
.form-group input[type="datetime-local"],
.form-group select {
  width: 100%;
  padding: 0.75rem;
  border: 2px solid #e9ecef;
  border-radius: 6px;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
  outline: none;
  border-color: #5E72E4;
}

.form-select {
  width: 100%;
  padding: 0.75rem;
  border: 2px solid #e9ecef;
  border-radius: 6px;
  font-size: 1rem;
  background-color: white;
  cursor: pointer;
  transition: border-color 0.2s;
}

.form-select:focus {
  outline: none;
  border-color: #5E72E4;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  user-select: none;
  font-weight: 500;
  color: #32325D;
}

.checkbox-input {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: #5E72E4;
}

/* 表单按钮 */
.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 1.5rem;
}

.btn-cancel, .btn-submit {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
}

.btn-cancel {
  background-color: #f4f5f7;
  color: #525F7F;
}

.btn-submit {
  background-color: #5E72E4;
  color: white;
}

.btn-submit:hover {
  background-color: #4a5fd6;
}
</style>