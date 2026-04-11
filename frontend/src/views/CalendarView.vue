<script setup>
import { ref, onMounted, onUnmounted, computed,watch  } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useUserStore } from '@/stores/user'
import { ChevronLeft, ChevronRight, Plus, Calendar as CalendarIcon, Clock, MapPin, Edit2, Trash2, X, ArrowLeft, CalendarDays, Filter, RefreshCw } from 'lucide-vue-next'

const router = useRouter()
const userStore = useUserStore()
const API_URL = 'http://127.0.0.1:5000/api'

const currentDate = ref(new Date())
const schedules = ref([])
const selectedDate = ref(null)
const isLoading = ref(false)
const hoveredDate = ref(null)
const showFilterMenu = ref(false)
const filterPriority = ref('all')
const filterRecurring = ref(false)

// 表单相关状态
const showFormModal = ref(false)
const isEditMode = ref(false)
const editingSchedule = ref(null)
const formState = ref({
  title: '',
  content: '',
  start_time: '',
  end_time: '',
  priority: 2,
  location: '',
  is_recurring: false,
  recurring_type: 'none',
  recurring_interval: 1
})

// 监听用户信息变化，更新标题
watch(() => userStore.user, (newUser) => {
  if (newUser?.username) {
    document.title = `${newUser.username} - 日历视图`
  }
}, { immediate: true })

onMounted(async () => {
  // 设置页面标题
  if (userStore.user?.username) {
    document.title = `${userStore.user.username} - 日历视图`
  }
  
  await fetchSchedules()
})

async function fetchSchedules() {
  try {
    isLoading.value = true
    const response = await axios.get(`${API_URL}/schedules`, {
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    })
    schedules.value = response.data
  } catch (error) {
    console.error('获取日程失败:', error)
  } finally {
    isLoading.value = false
  }
}

const calendarDays = computed(() => {
  const year = currentDate.value.getFullYear()
  const month = currentDate.value.getMonth()
  
  const firstDayOfMonth = new Date(year, month, 1)
  const lastDayOfMonth = new Date(year, month + 1, 0)
  
  const daysInMonth = lastDayOfMonth.getDate()
  const startingDayOfWeek = firstDayOfMonth.getDay()
  
  const days = []
  
  for (let i = 0; i < startingDayOfWeek; i++) {
    days.push({ date: null, isPadding: true })
  }
  
  for (let day = 1; day <= daysInMonth; day++) {
    const date = new Date(year, month, day)
    days.push({ 
      date, 
      isPadding: false,
      isToday: isToday(date),
      isSelected: isSelected(date),
      scheduleCount: getSchedulesForDate(date).length
    })
  }
  
  return days
})

function isToday(date) {
  const today = new Date()
  return date.getDate() === today.getDate() &&
         date.getMonth() === today.getMonth() &&
         date.getFullYear() === today.getFullYear()
}

function isSelected(date) {
  if (!selectedDate.value) return false
  return date.getDate() === selectedDate.value.getDate() &&
         date.getMonth() === selectedDate.value.getMonth() &&
         date.getFullYear() === selectedDate.value.getFullYear()
}

function goToToday() {
  currentDate.value = new Date()
  selectedDate.value = new Date()
}

function goBackToHome() {
  router.push('/')
}

async function refreshSchedules() {
  await fetchSchedules()
}

function toggleFilterMenu() {
  showFilterMenu.value = !showFilterMenu.value
}

const filteredSchedules = computed(() => {
  let result = schedules.value
  
  // 按优先级筛选
  if (filterPriority.value !== 'all') {
    result = result.filter(s => s.priority === parseInt(filterPriority.value))
  }
  
  // 按重复日程筛选
  if (filterRecurring.value) {
    result = result.filter(s => s.is_recurring === true)
  }
  
  return result
})


function setPriorityFilter(priority) {
  filterPriority.value = priority
  // 不关闭菜单，允许继续选择其他筛选条件
}

function toggleRecurringFilter() {
  filterRecurring.value = !filterRecurring.value
  // 不关闭菜单，允许继续选择其他筛选条件
}

function resetFilters() {
  filterPriority.value = 'all'
  filterRecurring.value = false
}

function getActiveFilterCount() {
  let count = 0
  if (filterPriority.value !== 'all') count++
  if (filterRecurring.value) count++
  return count
}


function getSchedulesForDate(date) {
  if (!date) return []
  
  // 获取目标日期的本地年月日
  const targetYear = date.getFullYear()
  const targetMonth = date.getMonth()
  const targetDay = date.getDate()
  
  return filteredSchedules.value.filter(s => {
    // 将日程开始时间转换为本地 Date 对象
    const scheduleDate = new Date(s.start_time)
    
    // 比较本地时间的年月日
    return scheduleDate.getFullYear() === targetYear &&
           scheduleDate.getMonth() === targetMonth &&
           scheduleDate.getDate() === targetDay
  }).sort((a, b) => new Date(a.start_time) - new Date(b.start_time))
}

function previousMonth() {
  currentDate.value = new Date(currentDate.value.getFullYear(), currentDate.value.getMonth() - 1, 1)
  selectedDate.value = null
}

function nextMonth() {
  currentDate.value = new Date(currentDate.value.getFullYear(), currentDate.value.getMonth() + 1, 1)
  selectedDate.value = null
}

function selectDate(dayObj) {
  if (dayObj.isPadding) return
  selectedDate.value = dayObj.date
}

function formatMonthYear(date) {
  return date.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long' })
}

function getPriorityColor(priority) {
  const colors = {
    1: '#9e9e9e',
    2: '#42a5f5',
    3: '#ffa726',
    4: '#ef5350',
    5: '#c62828'
  }
  return colors[priority] || '#9e9e9e'
}

function getPriorityLabel(priority) {
  const labels = {
    1: '普通',
    2: '一般',
    3: '重要',
    4: '紧急',
    5: '非常重要'
  }
  return labels[priority] || '普通'
}

function formatTime(isoString) {
  return new Date(isoString).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

function formatDateForInput(isoString) {
  if (!isoString) return ''
  const date = new Date(isoString)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day}T${hours}:${minutes}`
}

function openCreateForm(date) {
  isEditMode.value = false
  editingSchedule.value = null
  
  const now = date || new Date()
  
  // 使用本地时间格式化，避免时区问题
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  const hours = String(now.getHours()).padStart(2, '0')
  const minutes = String(now.getMinutes()).padStart(2, '0')
  const startTime = `${year}-${month}-${day}T${hours}:${minutes}`
  
  // 计算结束时间为开始时间的下一个小时
  const endTimeDate = new Date(now.getTime() + 60 * 60 * 1000)
  const endYear = endTimeDate.getFullYear()
  const endMonth = String(endTimeDate.getMonth() + 1).padStart(2, '0')
  const endDay = String(endTimeDate.getDate()).padStart(2, '0')
  const endHours = String(endTimeDate.getHours()).padStart(2, '0')
  const endMinutes = String(endTimeDate.getMinutes()).padStart(2, '0')
  const endTimeStr = `${endYear}-${endMonth}-${endDay}T${endHours}:${endMinutes}`
  
  formState.value = {
    title: '',
    content: '',
    start_time: startTime,
    end_time: endTimeStr,
    priority: 2,
    location: '',
    is_recurring: false,
    recurring_type: 'none',
    recurring_interval: 1
  }
  showFormModal.value = true
}

function openEditForm(schedule) {
  isEditMode.value = true
  editingSchedule.value = schedule
  formState.value = {
    title: schedule.title,
    content: schedule.content || '',
    start_time: formatDateForInput(schedule.start_time),
    end_time: schedule.end_time ? formatDateForInput(schedule.end_time) : '',
    priority: schedule.priority || 2,
    location: schedule.location || '',
    is_recurring: schedule.is_recurring || false,
    recurring_type: schedule.recurring_type || 'none',
    recurring_interval: schedule.recurring_interval || 1
  }
  showFormModal.value = true
}

function closeFormModal() {
  showFormModal.value = false
  isEditMode.value = false
  editingSchedule.value = null
  formState.value = {
    title: '',
    content: '',
    start_time: '',
    end_time: '',
    priority: 2,
    location: '',
    is_recurring: false,
    recurring_type: 'none',
    recurring_interval: 1
  }
}

async function submitForm() {
  if (!formState.value.title || !formState.value.start_time) {
    alert('标题和开始时间不能为空！')
    return
  }
  
  try {
    // 构造 payload 时，确保时间字符串被正确解析为本地时间再转 ISO
    // 如果后端期望的是 UTC，axios 发送 ISO 字符串通常没问题
    // 但为了保险，我们手动处理一下时区偏移，或者依赖浏览器的 new Date(string) 行为
    
    const startDateTime = new Date(formState.value.start_time)
    const endDateTime = formState.value.end_time ? new Date(formState.value.end_time) : null
    
    const payload = {
      ...formState.value,
      start_time: startDateTime.toISOString(),
      end_time: endDateTime ? endDateTime.toISOString() : null
    }
    
    if (isEditMode.value && editingSchedule.value) {
      await axios.put(`${API_URL}/schedules/${editingSchedule.value.id}`, payload, {
        headers: {
          'Authorization': `Bearer ${userStore.token}`
        }
      })
    } else {
      await axios.post(`${API_URL}/schedules`, payload, {
        headers: {
          'Authorization': `Bearer ${userStore.token}`
        }
      })
    }
    
    closeFormModal()
    await fetchSchedules()
  } catch (error) {
    console.error('保存失败:', error)
    alert(isEditMode.value ? '更新失败，请重试' : '创建失败，请重试')
  }
}


async function handleDeleteSchedule(scheduleId) {
  if (!confirm('确定要删除这个日程吗？')) return
  
  try {
    await axios.delete(`${API_URL}/schedules/${scheduleId}`, {
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    })
    await fetchSchedules()
    if (selectedDate.value) {
      const remainingSchedules = getSchedulesForDate(selectedDate.value)
      if (remainingSchedules.length === 0) {
        selectedDate.value = null
      }
    }
  } catch (error) {
    console.error('删除失败:', error)
    alert('删除失败，请重试')
  }
}

// 点击外部关闭筛选菜单
function handleClickOutside(event) {
  const dropdown = document.querySelector('.dropdown-wrapper')
  if (dropdown && !dropdown.contains(event.target)) {
    showFilterMenu.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div class="calendar-view-container">
    <div class="calendar-header">
      <div class="header-left">
        <button @click="goBackToHome" class="back-btn" title="返回主页">
          <ArrowLeft :size="20" />
          <span>返回</span>
        </button>
        <h2 class="month-title">{{ formatMonthYear(currentDate) }}</h2>
        
        <div class="quick-actions">
          <button @click="goToToday" class="action-btn today-btn" title="回到今天">
            <CalendarDays :size="18" />
            <span>今天</span>
          </button>
          
          <div class="dropdown-wrapper">
            <button @click.stop="toggleFilterMenu" class="action-btn filter-btn" :class="{ 'active': showFilterMenu || filterPriority !== 'all' || filterRecurring }" title="筛选日程">
              <Filter :size="18" />
              <span>筛选</span>
              <span v-if="filterPriority !== 'all' || filterRecurring" class="filter-badge">
                {{ getActiveFilterCount() }}
              </span>
            </button>
            
            <transition name="dropdown-fade">
              <div v-if="showFilterMenu" class="filter-dropdown">
                <div class="filter-section">
                  <div class="filter-section-title">优先级</div>
                  <div class="filter-option" @click="setPriorityFilter('all')">
                    <span class="dot all"></span>
                    <span>全部日程</span>
                    <span v-if="filterPriority === 'all'" class="check-mark">✓</span>
                  </div>
                  <div class="divider"></div>
                  <div class="filter-option" @click="setPriorityFilter('1')">
                    <span class="dot priority-1"></span>
                    <span>普通</span>
                    <span v-if="filterPriority === '1'" class="check-mark">✓</span>
                  </div>
                  <div class="filter-option" @click="setPriorityFilter('2')">
                    <span class="dot priority-2"></span>
                    <span>一般</span>
                    <span v-if="filterPriority === '2'" class="check-mark">✓</span>
                  </div>
                  <div class="filter-option" @click="setPriorityFilter('3')">
                    <span class="dot priority-3"></span>
                    <span>重要</span>
                    <span v-if="filterPriority === '3'" class="check-mark">✓</span>
                  </div>
                  <div class="filter-option" @click="setPriorityFilter('4')">
                    <span class="dot priority-4"></span>
                    <span>紧急</span>
                    <span v-if="filterPriority === '4'" class="check-mark">✓</span>
                  </div>
                  <div class="filter-option" @click="setPriorityFilter('5')">
                    <span class="dot priority-5"></span>
                    <span>非常重要</span>
                    <span v-if="filterPriority === '5'" class="check-mark">✓</span>
                  </div>
                </div>
                
                <div class="divider"></div>
                
                <div class="filter-section">
                  <div class="filter-section-title">类型</div>
                  <div class="filter-option checkbox-option" @click="toggleRecurringFilter">
                    <input 
                      type="checkbox" 
                      :checked="filterRecurring" 
                      @click.stop
                      class="filter-checkbox"
                    />
                    <span class="checkbox-label">仅显示重复日程</span>
                    <span v-if="filterRecurring" class="check-mark">✓</span>
                  </div>
                </div>
                
                <div class="filter-actions">
                  <button class="reset-filter-btn" @click="resetFilters">重置筛选</button>
                  <button class="apply-filter-btn" @click="showFilterMenu = false">应用</button>
                </div>
              </div>
            </transition>
          </div>
          
          <button @click="refreshSchedules" class="action-btn refresh-btn" :class="{ 'loading': isLoading }" title="刷新数据">
            <RefreshCw :size="18" />
            <span>{{ isLoading ? '刷新中...' : '刷新' }}</span>
          </button>
        </div>
      </div>
      
      <div class="header-actions">
        <button @click="previousMonth" class="nav-btn" title="上个月">
          <ChevronLeft :size="20" />
        </button>
        <button @click="nextMonth" class="nav-btn" title="下个月">
          <ChevronRight :size="20" />
        </button>
        <button class="add-btn" @click="openCreateForm()">
          <Plus :size="18" />
          <span>新建日程</span>
        </button>
      </div>
    </div>

    <div class="calendar-grid-wrapper">
      <div class="weekdays">
        <div v-for="day in ['日', '一', '二', '三', '四', '五', '六']" :key="day" class="weekday">
          {{ day }}
        </div>
      </div>

      <div class="days-grid">
        <div
          v-for="(dayObj, index) in calendarDays"
          :key="index"
          class="day-cell"
          :class="{ 
            'padding': dayObj.isPadding,
            'today': dayObj.isToday,
            'selected': dayObj.isSelected,
            'has-schedules': !dayObj.isPadding && dayObj.scheduleCount > 0
          }"
          @click="selectDate(dayObj)"
          @dblclick="!dayObj.isPadding && openCreateForm(dayObj.date)"
          @mouseenter="!dayObj.isPadding && (hoveredDate = dayObj.date)"
          @mouseleave="hoveredDate = null"
        >
          <div v-if="!dayObj.isPadding" class="day-content">
            <div class="day-number">{{ dayObj.date.getDate() }}</div>
            
            <div v-if="getSchedulesForDate(dayObj.date).length > 0" class="mini-schedule-list">
              <div 
                v-for="schedule in getSchedulesForDate(dayObj.date).slice(0, 3)" 
                :key="schedule.id"
                class="mini-schedule-item"
                :style="{ borderLeftColor: getPriorityColor(schedule.priority) }"
                :title="`${schedule.title}\n${formatTime(schedule.start_time)}`"
              >
                <span class="mini-time">{{ formatTime(schedule.start_time) }}</span>
                <span class="mini-title">{{ schedule.title }}</span>
              </div>
              <div v-if="getSchedulesForDate(dayObj.date).length > 3" class="more-indicator">
                +{{ getSchedulesForDate(dayObj.date).length - 3 }} 更多
              </div>
            </div>
            
            <div v-else class="empty-day"></div>
          </div>
        </div>
      </div>
    </div>

    <transition name="slide-up">
      <div v-if="selectedDate" class="details-panel-overlay" @click.self="selectedDate = null">
        <div class="details-panel">
          <div class="panel-header">
            <div class="panel-title-section">
              <h3>{{ selectedDate.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' }) }}</h3>
              <p class="schedule-count">{{ getSchedulesForDate(selectedDate).length }} 个日程</p>
            </div>
            <div class="panel-actions">
              <button class="quick-add-small-btn" @click="openCreateForm(selectedDate)" title="快速添加">
                <Plus :size="18" />
              </button>
              <button class="close-btn" @click="selectedDate = null" title="关闭">×</button>
            </div>
          </div>
          
          <div class="panel-content">
            <div v-if="getSchedulesForDate(selectedDate).length === 0" class="empty-state">
              <div class="empty-icon">
                <CalendarIcon :size="64" />
              </div>
              <h4>这一天没有安排日程</h4>
              <p>双击日期格子或点击按钮添加新安排</p>
              <button class="quick-add-btn" @click="openCreateForm(selectedDate)">
                <Plus :size="16" />
                <span>立即添加</span>
              </button>
            </div>
            
            <div v-else class="schedule-list">
              <div 
                v-for="schedule in getSchedulesForDate(selectedDate)" 
                :key="schedule.id"
                class="schedule-card"
                :class="`priority-${schedule.priority}`"
              >
                <div class="card-left">
                  <div class="time-section">
                    <Clock :size="16" />
                    <span class="time-text">{{ formatTime(schedule.start_time) }}</span>
                  </div>
                  <div class="priority-badge" :style="{ backgroundColor: getPriorityColor(schedule.priority) }">
                    {{ getPriorityLabel(schedule.priority) }}
                  </div>
                </div>
                
                <div class="card-center">
                  <div class="title-row">
                    <h4 class="schedule-title">{{ schedule.title }}</h4>
                    <div v-if="schedule.is_recurring" class="recurring-badge" title="重复日程">
                      🔄
                    </div>
                  </div>
                  <p v-if="schedule.content" class="schedule-content">{{ schedule.content }}</p>
                  <div v-if="schedule.location" class="location-info">
                    <MapPin :size="14" />
                    <span>{{ schedule.location }}</span>
                  </div>
                </div>
                
                <div class="card-actions">
                  <button 
                    class="action-btn edit-btn" 
                    @click.stop="openEditForm(schedule)"
                    title="编辑"
                  >
                    <Edit2 :size="16" />
                  </button>
                  <button 
                    class="action-btn delete-btn" 
                    @click.stop="handleDeleteSchedule(schedule.id)"
                    title="删除"
                  >
                    <Trash2 :size="16" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <transition name="fade">
      <div v-if="showFormModal" class="form-modal-overlay" @click.self="closeFormModal">
        <div class="form-modal">
          <div class="form-header">
            <h3>{{ isEditMode ? '编辑日程' : '新建日程' }}</h3>
            <button class="form-close-btn" @click="closeFormModal">
              <X :size="20" />
            </button>
          </div>
          
          <div class="form-body">
            <div class="form-group">
              <label>标题 *</label>
              <input 
                v-model="formState.title" 
                type="text" 
                placeholder="输入日程标题"
                class="form-input"
              />
            </div>
            
            <div class="form-group">
              <label>内容</label>
              <textarea 
                v-model="formState.content" 
                placeholder="输入详细内容（可选）"
                class="form-textarea"
                rows="3"
              ></textarea>
            </div>
            
            <div class="form-row">
              <div class="form-group">
                <label>开始时间 *</label>
                <input 
                  v-model="formState.start_time" 
                  type="datetime-local" 
                  class="form-input"
                />
              </div>
              
              <div class="form-group">
                <label>结束时间</label>
                <input 
                  v-model="formState.end_time" 
                  type="datetime-local" 
                  class="form-input"
                />
              </div>
            </div>
            
            <div class="form-row">
              <div class="form-group">
                <label>优先级</label>
                <select v-model="formState.priority" class="form-select">
                  <option :value="1">普通</option>
                  <option :value="2">一般</option>
                  <option :value="3">重要</option>
                  <option :value="4">紧急</option>
                  <option :value="5">非常重要</option>
                </select>
              </div>
              
              <div class="form-group">
                <label>地点</label>
                <input 
                  v-model="formState.location" 
                  type="text" 
                  placeholder="输入地点（可选）"
                  class="form-input"
                />
              </div>
            </div>
            
            <div class="form-group checkbox-group">
              <label class="checkbox-label">
                <input 
                  type="checkbox" 
                  v-model="formState.is_recurring"
                />
                <span>重复日程</span>
              </label>
            </div>
            
            <div v-if="formState.is_recurring" class="form-row">
              <div class="form-group">
                <label>重复类型</label>
                <select v-model="formState.recurring_type" class="form-select">
                  <option value="daily">每天</option>
                  <option value="weekly">每周</option>
                  <option value="monthly">每月</option>
                </select>
              </div>
              
              <div class="form-group">
                <label>间隔</label>
                <input 
                  v-model.number="formState.recurring_interval" 
                  type="number" 
                  min="1"
                  class="form-input"
                />
              </div>
            </div>
          </div>
          
          <div class="form-footer">
            <button class="btn-cancel" @click="closeFormModal">取消</button>
            <button class="btn-submit" @click="submitForm">
              {{ isEditMode ? '保存修改' : '创建日程' }}
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.calendar-view-container {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
  height: calc(100vh - 80px);
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.calendar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding: 0 0.5rem;
  gap: 1rem;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1.2rem;
  flex-wrap: wrap;
}

.back-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 0.5rem 0.9rem;
  background: white;
  border: 1.5px solid #e2e8f0;
  border-radius: 8px;
  color: #4a5568;
  font-weight: 500;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s ease;
  min-width: 70px;
}

.back-btn:hover {
  background: #f7fafc;
  border-color: #cbd5e0;
  color: #2d3748;
}

.month-title {
  font-size: 1.6rem;
  font-weight: 700;
  color: #2d3748;
  margin: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  white-space: nowrap;
}

.quick-actions {
  display: flex;
  gap: 0.6rem;
  align-items: center;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 0.5rem 0.9rem;
  background: white;
  border: 1.5px solid #e2e8f0;
  border-radius: 8px;
  color: #4a5568;
  font-weight: 500;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  white-space: nowrap;
  min-width: 75px;
  height: 36px;
  box-sizing: border-box;
}

.action-btn:hover {
  background: #f7fafc;
  border-color: #cbd5e0;
  color: #2d3748;
  transform: translateY(-1px);
}

.today-btn {
  border-color: #667eea;
  color: #667eea;
}

.today-btn:hover {
  background: #667eea;
  border-color: #667eea;
  color: white;
}

.filter-btn {
  position: relative;
}

.filter-btn.active {
  background: #ebf4ff;
  border-color: #667eea;
  color: #667eea;
}

.filter-badge {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-size: 0.65rem;
  padding: 1px 5px;
  border-radius: 8px;
  margin-left: 2px;
  font-weight: 600;
}

.refresh-btn {
  border-color: #38b2ac;
  color: #38b2ac;
}

.refresh-btn:hover {
  background: #38b2ac;
  border-color: #38b2ac;
  color: white;
}

.refresh-btn.loading {
  opacity: 0.6;
  cursor: not-allowed;
}

.refresh-btn.loading svg {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.dropdown-wrapper {
  position: relative;
}

.filter-dropdown {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  background: white;
  border: 1.5px solid #e2e8f0;
  border-radius: 10px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
  min-width: 200px;
  z-index: 100;
  overflow: hidden;
  animation: dropdownSlide 0.2s ease-out;
}

@keyframes dropdownSlide {
  from {
    opacity: 0;
    transform: translateY(-8px) scale(0.96);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.filter-section {
  padding: 0.5rem 0;
}

.filter-section-title {
  padding: 0.4rem 1rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: #a0aec0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.filter-option {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0.75rem 1rem;
  cursor: pointer;
  transition: all 0.15s;
  font-size: 0.85rem;
  color: #4a5568;
}

.filter-option:hover {
  background: #f7fafc;
}

.checkbox-option {
  gap: 8px;
}

.filter-checkbox {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: #667eea;
  flex-shrink: 0;
}

.checkbox-label {
  flex: 1;
}

.check-mark {
  margin-left: auto;
  color: #667eea;
  font-weight: 700;
  font-size: 0.9rem;
}

.divider {
  height: 1px;
  background: #e2e8f0;
  margin: 0.2rem 0;
}

.filter-actions {
  display: flex;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border-top: 1px solid #e2e8f0;
  background: #f7fafc;
}

.reset-filter-btn {
  flex: 1;
  padding: 0.5rem;
  border: 1px solid #cbd5e0;
  background: white;
  color: #4a5568;
  border-radius: 6px;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.15s;
}

.reset-filter-btn:hover {
  background: #edf2f7;
  border-color: #a0aec0;
}

.apply-filter-btn {
  flex: 1;
  padding: 0.5rem;
  border: none;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.apply-filter-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
  flex-shrink: 0;
}

.dot.all {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.dot.priority-1 {
  background: #9e9e9e;
}

.dot.priority-2 {
  background: #42a5f5;
}

.dot.priority-3 {
  background: #ffa726;
}

.dot.priority-4 {
  background: #ef5350;
}

.dot.priority-5 {
  background: #c62828;
}

.dropdown-fade-enter-active,
.dropdown-fade-leave-active {
  transition: all 0.2s ease;
}

.dropdown-fade-enter-from,
.dropdown-fade-leave-to {
  opacity: 0;
  transform: translateY(-8px) scale(0.96);
}

.header-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.nav-btn {
  background: white;
  border: 1.5px solid #e2e8f0;
  border-radius: 8px;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #4a5568;
}

.nav-btn:hover {
  background: #667eea;
  border-color: #667eea;
  color: white;
}

.add-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.5rem 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.85rem;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.25);
  min-height: 36px;
}

.add-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.35);
}




.today-btn {
  padding: 0.5rem 1rem;
  background: white;
  border: 2px solid #667eea;
  border-radius: 8px;
  color: #667eea;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
}

.today-btn:hover {
  background: #667eea;
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.nav-btn {
  background: white;
  border: none;
  border-radius: 10px;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  color: #4a5568;
}

.nav-btn:hover {
  background: #667eea;
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.add-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 10px;
  padding: 0.6rem 1.2rem;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.add-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.calendar-grid-wrapper {
  background: white;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  flex-grow: 1;
  display: flex;
  flex-direction: column;
}

.weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.weekday {
  padding: 1rem;
  text-align: center;
  font-weight: 700;
  color: white;
  font-size: 0.95rem;
  letter-spacing: 0.5px;
}

.days-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  grid-auto-rows: 1fr;
  flex-grow: 1;
  background: #f7fafc;
}

.day-cell {
  border-right: 1px solid #e2e8f0;
  border-bottom: 1px solid #e2e8f0;
  padding: 6px;
  cursor: pointer;
  position: relative;
  transition: all 0.2s ease;
  min-height: 100px;
  background: white;
}

.day-cell:nth-child(7n) {
  border-right: none;
}

.day-cell:not(.padding):hover {
  background: linear-gradient(135deg, #ebf4ff 0%, #e9d8fd 100%);
  transform: scale(1.02);
  z-index: 10;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
}

.day-cell.padding {
  background: #f7fafc;
  cursor: default;
  opacity: 0.5;
}

.day-cell.today {
  background: linear-gradient(135deg, #fff5f5 0%, #fed7d7 100%);
  border: 2px solid #fc8181;
}

.day-cell.selected {
  background: linear-gradient(135deg, #ebf8ff 0%, #bee3f8 100%);
  border: 2px solid #667eea;
  box-shadow: inset 0 0 0 2px #667eea;
}

.day-cell.has-schedules {
  background: linear-gradient(to bottom, white 0%, #f7fafc 100%);
}

.day-content {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.day-number {
  font-weight: 700;
  color: #2d3748;
  font-size: 1rem;
  margin-bottom: 2px;
}

.day-cell.today .day-number {
  color: #e53e3e;
  font-size: 1.1rem;
}

.mini-schedule-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow: hidden;
}

.mini-schedule-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 4px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 4px;
  border-left: 3px solid;
  font-size: 0.7rem;
  transition: all 0.2s;
}

.mini-schedule-item:hover {
  background: white;
  transform: translateX(2px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.mini-time {
  font-weight: 600;
  color: #4a5568;
  min-width: 35px;
  font-size: 0.65rem;
}

.mini-title {
  color: #2d3748;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.more-indicator {
  font-size: 0.65rem;
  color: #667eea;
  font-weight: 600;
  padding: 2px 4px;
  text-align: center;
}

.empty-day {
  flex: 1;
}

.details-panel-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  z-index: 100;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.details-panel {
  background: white;
  border-top-left-radius: 24px;
  border-top-right-radius: 24px;
  box-shadow: 0 -10px 40px rgba(0, 0, 0, 0.2);
  width: 100%;
  max-width: 800px;
  max-height: 60vh;
  overflow-y: auto;
  animation: slideUp 0.3s ease-out;
}

@keyframes slideUp {
  from {
    transform: translateY(100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 1.5rem 2rem;
  border-bottom: 2px solid #e2e8f0;
  background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
}

.panel-title-section h3 {
  margin: 0 0 0.25rem 0;
  color: #2d3748;
  font-size: 1.3rem;
  font-weight: 700;
}

.schedule-count {
  margin: 0;
  color: #718096;
  font-size: 0.9rem;
}

.panel-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.quick-add-small-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.quick-add-small-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.close-btn {
  background: white;
  border: 2px solid #e2e8f0;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  font-size: 1.5rem;
  cursor: pointer;
  color: #718096;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.close-btn:hover {
  background: #fc8181;
  border-color: #fc8181;
  color: white;
  transform: rotate(90deg);
}

.panel-content {
  padding: 1.5rem 2rem;
}

.empty-state {
  text-align: center;
  padding: 3rem 2rem;
  color: #718096;
}

.empty-icon {
  margin-bottom: 1rem;
  color: #cbd5e0;
}

.empty-state h4 {
  margin: 0 0 0.5rem 0;
  color: #4a5568;
  font-size: 1.2rem;
}

.empty-state p {
  margin: 0 0 1.5rem 0;
  font-size: 0.95rem;
}

.quick-add-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.quick-add-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.schedule-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.schedule-card {
  display: flex;
  gap: 1rem;
  padding: 1.25rem;
  background: white;
  border-radius: 12px;
  border: 2px solid #e2e8f0;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.schedule-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: linear-gradient(to bottom, #667eea, #764ba2);
}

.schedule-card:hover {
  border-color: #667eea;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
  transform: translateX(4px);
}

.card-left {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  min-width: 80px;
}

.time-section {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #667eea;
  font-weight: 600;
  font-size: 0.95rem;
}

.time-text {
  font-family: 'Courier New', monospace;
}

.priority-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 6px;
  color: white;
  font-size: 0.7rem;
  font-weight: 600;
  text-align: center;
}

.card-center {
  flex: 1;
  min-width: 0;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.schedule-title {
  margin: 0;
  color: #2d3748;
  font-size: 1.1rem;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recurring-badge {
  font-size: 1rem;
  flex-shrink: 0;
}

.schedule-content {
  margin: 0 0 0.5rem 0;
  color: #718096;
  font-size: 0.9rem;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.location-info {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #a0aec0;
  font-size: 0.85rem;
}

.card-actions {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.action-btn {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  background: #f7fafc;
  color: #718096;
}

.edit-btn:hover {
  background: #667eea;
  color: white;
  transform: scale(1.1);
}

.delete-btn:hover {
  background: #fc8181;
  color: white;
  transform: scale(1.1);
}

.form-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(5px);
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.form-modal {
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  width: 100%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
  animation: modalSlideIn 0.3s ease-out;
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: scale(0.9) translateY(-20px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 2rem;
  border-bottom: 2px solid #e2e8f0;
  background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
}

.form-header h3 {
  margin: 0;
  color: #2d3748;
  font-size: 1.4rem;
  font-weight: 700;
}

.form-close-btn {
  background: white;
  border: 2px solid #e2e8f0;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  cursor: pointer;
  color: #718096;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.form-close-btn:hover {
  background: #fc8181;
  border-color: #fc8181;
  color: white;
  transform: rotate(90deg);
}

.form-body {
  padding: 2rem;
}

.form-group {
  margin-bottom: 1.25rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: #4a5568;
  font-weight: 600;
  font-size: 0.9rem;
}

.form-input,
.form-textarea,
.form-select {
  width: 100%;
  padding: 0.75rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.95rem;
  transition: all 0.3s ease;
  font-family: inherit;
}

.form-input:focus,
.form-textarea:focus,
.form-select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.checkbox-group {
  margin-top: 1rem;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  user-select: none;
}

.checkbox-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: #667eea;
}

.form-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding: 1.5rem 2rem;
  border-top: 2px solid #e2e8f0;
  background: #f7fafc;
}

.btn-cancel,
.btn-submit {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.95rem;
}

.btn-cancel {
  background: white;
  color: #718096;
  border: 2px solid #e2e8f0;
}

.btn-cancel:hover {
  background: #f7fafc;
  border-color: #cbd5e0;
}

.btn-submit {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.btn-submit:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
}

.slide-up-enter-from .details-panel,
.slide-up-leave-to .details-panel {
  transform: translateY(100%);
}

@media (max-width: 768px) {
  .calendar-view-container {
    padding: 1rem;
  }
  
  .calendar-header {
    flex-direction: column;
    gap: 0.8rem;
    align-items: stretch;
  }
  
  .header-left {
    flex-direction: column;
    align-items: stretch;
    gap: 0.8rem;
  }
  
  .month-title {
    font-size: 1.3rem;
    text-align: center;
  }
  
  .quick-actions {
    justify-content: center;
  }
  
  .action-btn span {
    display: none;
  }
  
  .action-btn {
    padding: 0.5rem;
    min-width: 36px;
  }
  
  .day-cell {
    min-height: 70px;
    padding: 4px;
  }
  
  .day-number {
    font-size: 0.85rem;
  }
  
  .mini-schedule-item {
    font-size: 0.6rem;
  }
  
  .mini-time {
    min-width: 28px;
    font-size: 0.6rem;
  }
  
  .details-panel {
    max-height: 70vh;
  }
  
  .schedule-card {
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .card-left {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }
  
  .card-actions {
    flex-direction: row;
    justify-content: flex-end;
  }
  
  .form-row {
    grid-template-columns: 1fr;
  }
  
  .form-modal {
    max-height: 95vh;
  }
  
  .form-body {
    padding: 1.5rem;
  }
}
</style>