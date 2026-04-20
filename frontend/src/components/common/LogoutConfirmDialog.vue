<template>
  <transition name="fade">
    <div v-if="isVisible" class="form-overlay" @click.self="onCancel">
      <div class="form-container logout-confirm">
        <h2>确认退出</h2>
        <p>确定要退出登录吗？</p>
        <div class="form-actions">
          <button type="button" class="btn-cancel" @click="onCancel">取消</button>
          <button type="button" class="btn-submit btn-logout" @click="onConfirm">
            <LogOut :size="16" style="vertical-align: middle; margin-right: 4px;" />
            退出登录
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { LogOut } from 'lucide-vue-next';

// 定义组件的 props
defineProps({
  isVisible: {
    type: Boolean,
    default: false
  }
});

// 定义组件的 emits
const emit = defineEmits(['confirm', 'cancel']);

// 确认登出
function onConfirm() {
  emit('confirm');
}

// 取消登出
function onCancel() {
  emit('cancel');
}
</script>

<style scoped>
.form-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.form-container {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(50, 50, 93, 0.11), 0 1px 3px rgba(0, 0, 0, 0.08);
  width: 100%;
  max-width: 500px;
}

.form-container h2 {
  text-align: center;
  margin-top: 0;
  color: #32325D;
}

.form-container p {
  color: #525F7F;
  margin: 1rem 0;
  text-align: center;
}

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
  transition: all 0.2s;
}

.btn-cancel {
  background-color: #f4f5f7;
  color: #525F7F;
}

.btn-cancel:hover {
  background-color: #e9ecef;
}

.btn-submit {
  background-color: #5E72E4;
  color: white;
}

.btn-submit:hover {
  background-color: #4a5fd6;
  transform: translateY(-1px);
}

.btn-logout {
  background-color: #f5365c;
}

.btn-logout:hover {
  background-color: #ec1a42;
}

.logout-confirm {
  text-align: center;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>