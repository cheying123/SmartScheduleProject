<template>
  <div class="export-modal" v-if="visible">
    <div class="export-content">
      <div class="export-header">
        <h3><Download :size="20" /> 导出日程</h3>
        <button class="close-btn" @click="onClose">
          <X :size="20" />
        </button>
      </div>
      
      <div class="export-body">
        <div class="export-options">
          <div class="option-group">
            <label class="option">
              <input type="radio" v-model="exportType" value="all" />
              <span class="option-text">导出所有日程</span>
            </label>
            
            <label class="option">
              <input type="radio" v-model="exportType" value="range" />
              <span class="option-text">按时间范围导出</span>
            </label>
            
            <label class="option">
              <input type="radio" v-model="exportType" value="selected" />
              <span class="option-text">选择特定日程导出</span>
            </label>
          </div>
          
          <div v-if="exportType === 'range'" class="date-range">
            <div class="date-inputs">
              <div class="input-group">
                <label>开始日期</label>
                <input 
                  type="date" 
                  v-model="dateRange.start" 
                  class="date-input"
                />
              </div>
              <div class="input-group">
                <label>结束日期</label>
                <input 
                  type="date" 
                  v-model="dateRange.end" 
                  class="date-input"
                />
              </div>
            </div>
          </div>
          
          <!-- 筛选选项 -->
          <div class="filter-options" v-if="exportType !== 'selected'">
            <h4>筛选选项</h4>
            <div class="filter-option">
              <label class="checkbox-label">
                <input 
                  type="checkbox" 
                  v-model="filters.includeRecurring"
                />
                <span class="checkmark"></span>
                <span class="label-text">包含重复日程</span>
              </label>
            </div>
            <div class="filter-option">
              <label class="checkbox-label">
                <input 
                  type="checkbox" 
                  v-model="filters.includeExpired"
                />
                <span class="checkmark"></span>
                <span class="label-text">包含已过期日程</span>
              </label>
            </div>
          </div>
        </div>

        <!-- 选择日程组件 -->
        <div v-if="exportType === 'selected'" class="selection-container">
          <ScheduleSelection
            :visible="true"
            :API_URL="props.API_URL"
            :token="props.token"
            @close="onClose"
            @export-selected="handleSelectedExport"
          />
        </div>
      </div>
      
      <div class="export-actions" v-if="exportType !== 'selected'">
        <button class="btn-cancel" @click="onClose">取消</button>
        <button 
          class="btn-export" 
          @click="handleExport"
          :disabled="isExporting"
        >
          <Download :size="16" v-if="!isExporting" />
          <Loader2 :size="16" v-else class="animate-spin" />
          {{ isExporting ? '导出中...' : '导出日程' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, defineProps, defineEmits } from 'vue'
import { Download, X, Loader2 } from 'lucide-vue-next'
import axios from 'axios'
import ScheduleSelection from './ScheduleSelection.vue'

// Props
const props = defineProps({
  visible: {
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
})

// Emits
const emit = defineEmits(['close'])

// 响应式数据
const exportType = ref('all')

// 获取今天的日期字符串（格式为 YYYY-MM-DD）
const getTodayString = () => {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, '0');
  const day = String(today.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

// 获取30天后的日期字符串
const getFutureDateString = (days = 30) => {
  const futureDate = new Date();
  futureDate.setDate(futureDate.getDate() + days);
  const year = futureDate.getFullYear();
  const month = String(futureDate.getMonth() + 1).padStart(2, '0');
  const day = String(futureDate.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

const dateRange = ref({
  start: getTodayString(),
  end: getFutureDateString()
});
const isExporting = ref(false)

// 筛选选项
const filters = ref({
  includeRecurring: true,
  includeExpired: true
})

// 处理导出
async function handleExport() {
  if (exportType.value === 'selected') {
    // 这个分支不应该执行，因为我们直接显示了选择界面
    return
  }

  isExporting.value = true
  
  try {
    let url = `${props.API_URL}/schedules/export`
    
    // 构建查询参数
    const params = new URLSearchParams()
    
    if (exportType.value === 'range') {
      // 转换本地日期为UTC日期，因为后端需要与数据库中的UTC时间比较
      const startDate = new Date(dateRange.value.start)
      const endDate = new Date(dateRange.value.end)
      
      // 将本地日期转换为UTC日期字符串
      const utcStart = new Date(startDate.getTime() + startDate.getTimezoneOffset() * 60000).toISOString().split('T')[0]
      const utcEnd = new Date(endDate.getTime() + endDate.getTimezoneOffset() * 60000).toISOString().split('T')[0]
      
      params.append('start', utcStart)
      params.append('end', utcEnd)
    }
    
    params.append('include_recurring', filters.value.includeRecurring)
    params.append('include_expired', filters.value.includeExpired)
    
    // 如果有参数，添加到URL
    if (params.toString()) {
      url += `?${params.toString()}`
    }
    
    const response = await axios.get(url, {
      headers: { 
        'Authorization': `Bearer ${props.token}`,
        'Content-Type': 'text/calendar; charset=utf-8'
      },
      responseType: 'blob' // 重要：指定响应类型为blob
    })
    
    // 创建下载链接
    const blob = new Blob([response.data], { type: 'text/calendar; charset=utf-8' })
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.setAttribute('download', `schedules_${new Date().toISOString().substr(0, 10)}.ics`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(downloadUrl)
    
    // 关闭模态框
    emit('close')
  } catch (error) {
    console.error('导出失败:', error)
    alert('导出日程失败，请稍后重试')
  } finally {
    isExporting.value = false
  }
}

// 处理选择特定日程的导出
async function handleSelectedExport(selectedIds) {
  try {
    // 发送POST请求导出选中的日程
    const response = await axios.post(
      `${props.API_URL}/schedules/export`,
      {
        schedule_ids: selectedIds,
        include_recurring: filters.value.includeRecurring,
        include_expired: filters.value.includeExpired,
        include_completed: true  // 默认包含已完成的日程
      },
      {
        headers: {
          'Authorization': `Bearer ${props.token}`,
          'Content-Type': 'application/json'
        },
        responseType: 'blob'  // 重要：指定响应类型为blob
      }
    );
    
    // 创建下载链接
    const blob = new Blob([response.data], { type: 'text/calendar; charset=utf-8' })
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.setAttribute('download', `selected_schedules_${new Date().toISOString().substr(0, 10)}.ics`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(downloadUrl)
    
    emit('close')
  } catch (error) {
    console.error('导出选中日程失败:', error)
    alert('导出选中日程失败，请稍后重试')
  }
}

// 关闭模态框
function onClose() {
  exportType.value = 'all'  // 重置选项
  emit('close')
}
</script>

<style scoped>
.export-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.export-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 4px 6px rgba(50, 50, 93, 0.11), 0 1px 3px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.export-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e9ecef;
}

.export-header h3 {
  margin: 0;
  color: #32325D;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.close-btn {
  background: none;
  border: none;
  color: #8898aa;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  transition: all 0.2s;
}

.close-btn:hover {
  background-color: #f8f9fa;
  color: #525F7F;
}

.export-body {
  padding: 1.5rem;
  max-height: 70vh;
  overflow-y: auto;
}

.export-options {
  margin-bottom: 1rem;
}

.option-group {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.option {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.option:hover {
  background-color: #f8f9fa;
}

.option input[type="radio"] {
  margin: 0;
}

.option-text {
  flex: 1;
  color: #525F7F;
}

.date-range {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e9ecef;
}

.date-inputs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-top: 0.75rem;
}

.input-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: #525F7F;
  font-size: 0.9rem;
}

.date-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  font-size: 0.9rem;
}

.date-input:focus {
  outline: none;
  border-color: #5E72E4;
  box-shadow: 0 0 0 3px rgba(94, 114, 228, 0.1);
}

.selection-container {
  margin-top: 1rem;
  border-top: 1px solid #e9ecef;
  padding-top: 1rem;
}

/* 新增：筛选选项样式 */
.filter-options {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid #e9ecef;
}

.filter-options h4 {
  margin: 0 0 1rem 0;
  color: #32325D;
  font-size: 1rem;
}

.filter-option {
  margin-bottom: 0.75rem;
}

.checkbox-label {
  display: flex;
  align-items: center;
  cursor: pointer;
  position: relative;
  padding-left: 2.25rem;
  margin-bottom: 0;
  font-size: 0.9rem;
  color: #525F7F;
  user-select: none;
}

.checkbox-label input {
  position: absolute;
  opacity: 0;
  cursor: pointer;
  height: 0;
  width: 0;
}

.checkmark {
  position: absolute;
  left: 0;
  top: 0;
  height: 20px;
  width: 20px;
  background-color: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 4px;
  transition: all 0.2s;
}

.checkbox-label:hover input ~ .checkmark {
  background-color: #edf2f9;
  border-color: #5E72E4;
}

.checkbox-label input:checked ~ .checkmark {
  background-color: #5E72E4;
  border-color: #5E72E4;
}

.checkmark:after {
  content: "";
  position: absolute;
  display: none;
}

.checkbox-label input:checked ~ .checkmark:after {
  display: block;
}

.checkbox-label .checkmark:after {
  left: 7px;
  top: 3px;
  width: 5px;
  height: 10px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.label-text {
  margin-left: 0.5rem;
}

.export-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding: 1.5rem;
  border-top: 1px solid #e9ecef;
  background-color: #f8f9fa;
}

.btn-cancel, .btn-export {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-cancel {
  background-color: #f4f5f7;
  color: #525F7F;
}

.btn-cancel:hover {
  background-color: #e9ecef;
}

.btn-export {
  background-color: #5E72E4;
  color: white;
}

.btn-export:hover:not(:disabled) {
  background-color: #4a5fd6;
  transform: translateY(-1px);
}

.btn-export:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .date-inputs {
    grid-template-columns: 1fr;
  }
}
</style>