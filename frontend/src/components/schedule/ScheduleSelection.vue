<template>
  <div class="selection-modal" v-if="visible">
    <div class="selection-content">
      <div class="selection-header">
        <h3><List :size="20" /> 选择要导出的日程</h3>
        <button class="close-btn" @click="onClose">
          <X :size="20" />
        </button>
      </div>
      
      <div class="selection-controls">
        <div class="search-section">
          <input 
            v-model="searchQuery" 
            type="text" 
            placeholder="搜索日程..." 
            class="search-input"
          />
          <button class="select-all-btn" @click="toggleSelectAll">
            {{ allSelected ? '取消全选' : '全选' }}
          </button>
        </div>
        
        <div class="filter-section">
          <!-- 额外筛选选项 -->
          <div class="advanced-filters">
            <div class="filter-option">
              <label class="checkbox-label">
                <input 
                  type="checkbox" 
                  v-model="extraFilters.includeRecurring"
                />
                <span class="checkmark"></span>
                <span class="label-text">包含重复日程</span>
              </label>
            </div>
            <div class="filter-option">
              <label class="checkbox-label">
                <input 
                  type="checkbox" 
                  v-model="extraFilters.includeExpired"
                />
                <span class="checkmark"></span>
                <span class="label-text">包含已过期</span>
              </label>
            </div>
            <div class="filter-option">
              <label class="checkbox-label">
                <input 
                  type="checkbox" 
                  v-model="extraFilters.includeCompleted"
                />
                <span class="checkmark"></span>
                <span class="label-text">包含已完成</span>
              </label>
            </div>
          </div>
          
          <div class="date-filters-row">
            <div class="date-filter">
              <label>选择日期</label>
              <input 
                type="date" 
                v-model="dateFilter" 
                class="date-input"
                placeholder="选择日期"
              />
            </div>
            <button class="today-btn" @click="setTodayFilter" title="选择今天">
              <Calendar :size="16" />
              今天
            </button>
          </div>
        </div>
      </div>
      
      <div class="schedule-list">
        <div 
          v-for="schedule in filteredSchedules" 
          :key="schedule.id"
          class="schedule-item"
          :class="{ 'selected': selectedSchedules.includes(schedule.id) }"
        >
          <label class="checkbox-label">
            <input 
              type="checkbox" 
              :value="schedule.id"
              v-model="selectedSchedules"
            />
            <span class="checkmark"></span>
            <div class="schedule-info">
              <div class="schedule-title">{{ schedule.title }}</div>
              <div class="schedule-details">
                <Calendar :size="14" />
                <span>{{ formatDate(schedule.start_time) }}</span>
                <Clock :size="14" class="time-icon" />
                <span>{{ formatTime(schedule.start_time) }}</span>
                <MapPin :size="14" class="location-icon" v-if="schedule.location" />
                <span v-if="schedule.location">{{ schedule.location }}</span>
                
                <!-- 重要日程标识 -->
                <span v-if="schedule.priority === 1" class="priority-badge priority-1" title="普通">
                  <Tag :size="12" />
                  <span class="badge-text">普通</span>
                </span>
                <span v-else-if="schedule.priority === 2" class="priority-badge priority-2" title="一般">
                  <Tag :size="12" />
                  <span class="badge-text">一般</span>
                </span>
                <span v-else-if="schedule.priority === 3" class="priority-badge priority-3" title="重要">
                  <Tag :size="12" />
                  <span class="badge-text">重要</span>
                </span>
                <span v-else-if="schedule.priority === 4" class="priority-badge priority-4" title="非常重要">
                  <Tag :size="12" />
                  <span class="badge-text">重要+</span>
                </span>
                <span v-else-if="schedule.priority === 5" class="priority-badge priority-5" title="紧急">
                  <AlertTriangle :size="12" />
                  <span class="badge-text">紧急</span>
                </span>
                
                <!-- 循环日程标识 - 显示具体循环模式 -->
                <span v-if="schedule.is_recurring" class="recurring-badge" :title="getRecurringPatternTitle(schedule)">
                  <RefreshCw :size="12" />
                  <span class="badge-text">{{ getRecurringPatternDisplay(schedule) }}</span>
                </span>
                
                <!-- 完成状态标识 -->
                <span v-if="schedule.is_completed" class="completed-badge" title="已完成">
                  <Check :size="12" />
                  <span class="badge-text">完成</span>
                </span>
              </div>
            </div>
          </label>
        </div>
        
        <div v-if="filteredSchedules.length === 0" class="no-results">
          <FileText :size="48" class="icon" />
          <p>没有找到匹配的日程</p>
        </div>
      </div>
      
      <div class="selection-footer">
        <div class="selected-count">
          已选择 {{ selectedSchedules.length }} 个日程
        </div>
        <div class="actions">
          <button class="btn-cancel" @click="onClose">取消</button>
          <button 
            class="btn-export" 
            @click="onExport"
            :disabled="selectedSchedules.length === 0"
          >
            <Download :size="16" />
            导出选中 ({{ selectedSchedules.length }})
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, defineProps, defineEmits, onMounted, watch } from 'vue'
import { List, X, Download, Calendar, Clock, MapPin, FileText, Tag, RefreshCw, Check, AlertTriangle } from 'lucide-vue-next'
import axios from 'axios'

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
const emit = defineEmits(['close', 'export-selected'])

// 响应式数据
const allSchedules = ref([])
const selectedSchedules = ref([])
const searchQuery = ref('')

// 单个日期筛选器
const dateFilter = ref('')  // 初始值设为空

// 额外筛选选项
const extraFilters = ref({
  includeRecurring: true,
  includeExpired: true,
  includeCompleted: true
})

// 监听组件可见性，当组件变为可见时设置默认日期为今天
watch(() => props.visible, (newVal) => {
  if (newVal) {
    // 设置默认日期为今天
    setTodayFilter();
  }
});

// 计算属性
const filteredSchedules = computed(() => {
  let result = allSchedules.value
  
  // 按搜索关键词过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(schedule => 
      schedule.title.toLowerCase().includes(query) || 
      (schedule.content && schedule.content.toLowerCase().includes(query)) ||
      (schedule.location && schedule.location.toLowerCase().includes(query))
    )
  }
  
  // 按日期筛选（将本地日期转换为UTC进行比较）
  if (dateFilter.value) {
    // 将本地日期转换为UTC进行比较
    const localDate = new Date(dateFilter.value)
    // 转换为UTC时间进行比较（因为数据库存储的是UTC时间）
    const utcDateStart = new Date(localDate.getTime() + localDate.getTimezoneOffset() * 60000)
    const utcDateEnd = new Date(utcDateStart.getTime() + 24 * 60 * 60 * 1000) // 加一天
    
    result = result.filter(schedule => {
      const scheduleDate = new Date(schedule.start_time)
      return scheduleDate >= utcDateStart && scheduleDate < utcDateEnd
    })
  }
  
  // 应用额外筛选条件
  result = result.filter(schedule => {
    // 重复日程筛选 - 如果用户选择不包含重复日程，则过滤掉
    if (!extraFilters.value.includeRecurring && schedule.is_recurring) {
      return false
    }
    
    // 已过期筛选（注意时区转换）
    const scheduleTime = new Date(schedule.start_time)
    const localScheduleTime = new Date(scheduleTime.getTime() - scheduleTime.getTimezoneOffset() * 60000)
    if (!extraFilters.value.includeExpired && localScheduleTime < new Date()) {
      return false
    }
    
    // 完成状态筛选
    if (!extraFilters.value.includeCompleted && schedule.is_completed) {
      return false
    }
    
    return true
  })
  
  return result
})

const allSelected = computed(() => {
  return filteredSchedules.value.length > 0 && 
         filteredSchedules.value.every(schedule => selectedSchedules.value.includes(schedule.id))
})

// 方法
function toggleSelectAll() {
  if (allSelected.value) {
    // 取消全选，移除当前过滤结果中的所有ID
    selectedSchedules.value = selectedSchedules.value.filter(
      id => !filteredSchedules.value.some(s => s.id === id)
    )
  } else {
    // 全选，添加当前过滤结果中的所有ID（不去重）
    const newIds = filteredSchedules.value.map(s => s.id)
    selectedSchedules.value = [...new Set([...selectedSchedules.value, ...newIds])]
  }
}

function formatDate(dateStr) {
  // 将UTC时间转换为本地时间显示
  const utcDate = new Date(dateStr)
  const localDate = new Date(utcDate.getTime() - utcDate.getTimezoneOffset() * 60000)
  return localDate.toLocaleDateString('zh-CN', { 
    year: 'numeric', 
    month: 'short', 
    day: 'numeric' 
  })
}

function formatTime(dateStr) {
  // 将UTC时间转换为本地时间显示
  const utcDate = new Date(dateStr)
  const localDate = new Date(utcDate.getTime() - utcDate.getTimezoneOffset() * 60000)
  return localDate.toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

async function loadSchedules() {
  try {
    const response = await axios.get(`${props.API_URL}/schedules`, {
      headers: { 'Authorization': `Bearer ${props.token}` }
    })
    allSchedules.value = response.data
    
    // 调试代码：打印返回的数据结构
    console.log('API返回的日程数据:', response.data)
    
    // 检查是否包含循环日程
    const recurringSchedules = response.data.filter(schedule => schedule.is_recurring)
    console.log(`找到 ${recurringSchedules.length} 个循环日程:`, recurringSchedules)
    
    // 检查第一个日程的数据结构
    if(response.data.length > 0) {
      console.log('第一个日程的详细数据:', response.data[0])
      console.log('第一个日程的is_recurring值:', response.data[0].is_recurring)
      console.log('第一个日程的priority值:', response.data[0].priority)
      console.log('第一个日程的is_completed值:', response.data[0].is_completed)
    }
  } catch (error) {
    console.error('加载日程失败:', error)
  }
}

function onExport() {
  emit('export-selected', selectedSchedules.value)
  onClose()
}

function onClose() {
  selectedSchedules.value = []
  searchQuery.value = ''
  dateFilter.value = ''  // 重置为初始值
  extraFilters.value = {
    includeRecurring: true,
    includeExpired: true,
    includeCompleted: true
  }
  emit('close')
}

// 设置今天为日期筛选条件（考虑时区）
function setTodayFilter() {
  // 获取当前UTC时间对应的本地日期
  const now = new Date()
  // 转换为本地时间的日期字符串
  const localDate = new Date(now.getTime() - now.getTimezoneOffset() * 60000)
  const todayStr = localDate.toISOString().split('T')[0]
  dateFilter.value = todayStr
}

// 获取循环模式显示文本
function getRecurringPatternDisplay(schedule) {
  if (!schedule.is_recurring || !schedule.recurring_pattern) {
    return '循环'
  }
  
  switch (schedule.recurring_pattern) {
    case 'daily':
      return '每日'
    case 'weekly':
      return '每周'
    case 'monthly':
      return '每月'
    case 'yearly':
      return '每年'
    default:
      return '循环'
  }
}

// 获取循环模式提示文本
function getRecurringPatternTitle(schedule) {
  if (!schedule.is_recurring || !schedule.recurring_pattern) {
    return '循环日程'
  }
  
  switch (schedule.recurring_pattern) {
    case 'daily':
      return '每日循环'
    case 'weekly':
      return '每周循环'
    case 'monthly':
      return '每月循环'
    case 'yearly':
      return '每年循环'
    default:
      return '循环日程'
  }
}

// 组件挂载时加载日程
onMounted(() => {
  if (props.visible) {
    loadSchedules()
  }
})
</script>

<style scoped>
.selection-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1100;
}

.selection-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 800px;
  height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 6px rgba(50, 50, 93, 0.11), 0 1px 3px rgba(0, 0, 0, 0.08);
}

.selection-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e9ecef;
}

.selection-header h3 {
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

.selection-controls {
  padding: 1.5rem;
  border-bottom: 1px solid #e9ecef;
  background-color: #f8f9fa;
}

.search-section {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
  align-items: center;
}

.search-input {
  flex: 1;
  padding: 0.6rem 1rem;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  font-size: 0.9rem;
}

.select-all-btn, .today-btn {
  padding: 0.6rem 1rem;
  background: #5E72E4;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.select-all-btn:hover, .today-btn:hover {
  background: #4a5fd6;
}

.today-btn {
  background: #2dce89;
}

.today-btn:hover {
  background: #26af74;
}

.advanced-filters {
  display: flex;
  gap: 1.5rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.filter-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.date-filters-row {
  display: flex;
  gap: 1rem;
  align-items: end;
}

.date-filter {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex: 1;
  min-width: 150px;
}

.date-filter label {
  font-size: 0.85rem;
  color: #525F7F;
  font-weight: 500;
}

.date-input {
  padding: 0.6rem;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  font-size: 0.9rem;
}

.date-input:focus {
  outline: none;
  border-color: #5E72E4;
  box-shadow: 0 0 0 3px rgba(94, 114, 228, 0.1);
}

.filter-option {
  display: flex;
  align-items: center;
}

.checkbox-label {
  display: flex;
  align-items: center;
  cursor: pointer;
  position: relative;
  padding-left: 1.5rem;
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
  height: 18px;
  width: 18px;
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
  left: 6px;
  top: 2px;
  width: 4px;
  height: 8px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.checkbox-label input:checked ~ .checkmark:after {
  display: block;
}

.label-text {
  margin-left: 0.5rem;
}

.schedule-list {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.schedule-item {
  padding: 0.75rem;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  margin-bottom: 0.75rem;
  transition: all 0.2s;
}

.schedule-item.selected {
  border-color: #5E72E4;
  background-color: #f0f4ff;
}

.schedule-item.selected .checkmark {
  background-color: #5E72E4;
  border-color: #5E72E4;
}

.checkbox-label {
  display: flex;
  align-items: flex-start;
  cursor: pointer;
  gap: 0.75rem;
  width: 100%;
}

.checkbox-label input {
  margin: 0;
  margin-top: 0.25rem;
}

.checkmark {
  position: relative;
  top: 0;
  left: 0;
  height: 20px;
  width: 20px;
  background-color: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 4px;
  transition: all 0.2s;
  flex-shrink: 0;
}

.checkbox-label input:checked ~ .checkmark {
  background-color: #5E72E4;
  border-color: #5E72E4;
}

.checkmark:after {
  content: "";
  position: absolute;
  display: none;
  left: 7px;
  top: 3px;
  width: 5px;
  height: 10px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.checkbox-label input:checked ~ .checkmark:after {
  display: block;
}

.schedule-info {
  flex: 1;
}

.schedule-title {
  font-weight: 600;
  color: #32325D;
  margin-bottom: 0.25rem;
  font-size: 1rem;
}

.schedule-details {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #8898aa;
  font-size: 0.85rem;
  flex-wrap: wrap;
}

.time-icon, .location-icon {
  margin-left: 0.5rem;
}

.priority-badge, .recurring-badge, .completed-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  border-radius: 1rem;  /* 圆角矩形，类似胶囊形状 */
  font-size: 0.75rem;
  font-weight: 500;
  margin-left: 0.5rem;
  vertical-align: middle;
}

.priority-badge {
  background-color: #adb5bd;  /* 默认浅灰色 */
  color: #333;
}

.priority-1 { 
  background-color: #f8f9fa;  /* 浅灰色表示普通 */
  color: #333;
} 

.priority-2 { 
  background-color: #e9ecef;  /* 稍深一点的灰色表示一般 */
  color: #333;
} 

.priority-3 { 
  background-color: #5E72E4;  /* 蓝色表示重要 */
  color: white;
}

.priority-4 { 
  background-color: #f5365c;  /* 红色表示非常重要 */
  color: white;
}

.priority-5 { 
  background-color: #fb6340;  /* 深红色表示紧急 */
  color: white;
}

.recurring-badge {
  background-color: #ffd600;  /* 黄色背景表示循环 */
  color: #333;
}

.completed-badge {
  background-color: #2dce89;  /* 绿色背景表示完成 */
  color: white;
}

.badge-text {
  font-size: 0.7rem;
  line-height: 1;
}

.no-results {
  text-align: center;
  padding: 2rem;
  color: #8898aa;
}

.no-results .icon {
  margin-bottom: 1rem;
  opacity: 0.5;
}

.selection-footer {
  padding: 1.5rem;
  border-top: 1px solid #e9ecef;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #f8f9fa;
}

.selected-count {
  color: #525F7F;
  font-weight: 500;
}

.actions {
  display: flex;
  gap: 1rem;
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
}

.btn-export:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .selection-content {
    width: 95%;
    height: 90vh;
  }
  
  .search-section {
    flex-direction: column;
  }
  
  .date-filters-row {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .advanced-filters {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .date-filter {
    min-width: auto;
  }
}
</style>