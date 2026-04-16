/**
 * 日程管理 Composable
 * 文件路径：frontend/src/composables/useSchedule.js
 */

import { ref } from 'vue'
import axios from 'axios'
import { getCurrentDateTime, formatDateForInput } from '@/utils/timeUtils'

/**
 * 日程管理组合式函数
 * @param {Object} userStore - Pinia 用户状态 store
 * @param {string} API_URL - API 基础地址
 * @returns {Object} 日程管理相关的方法和状态
 */
export function useSchedule(userStore, API_URL) {
  // 状态
  const schedules = ref([])
  const isLoading = ref(false)
  const error = ref(null)
  const editingSchedule = ref(null)
  
  // 默认表单数据
  const defaultScheduleForm = () => ({
    title: '',
    content: '',
    start_time: getCurrentDateTime(),
    end_time: '',
    priority: 1,
    is_recurring: false,
    recurring_pattern: '',
    tags: [] // 新增：标签数组
  })
  
  // 表单引用
  const newSchedule = ref(defaultScheduleForm())
  const editForm = ref({
    title: '',
    content: '',
    start_time: '',
    end_time: '',
    priority: 1,
    is_recurring: false,
    recurring_pattern: '',
    tags: [] // 新增：标签数组
  })

  /**
   * 获取日程列表
   * @returns {Promise<boolean>} 是否成功
   */
  async function fetchSchedules() {
    try {
      isLoading.value = true
      const response = await axios.get(`${API_URL}/schedules`)
      
      // 按时间排序
      schedules.value = response.data.sort((a, b) => 
        new Date(a.start_time) - new Date(b.start_time)
      )
      
      error.value = null
      return true
    } catch (err) {
      if (err.response?.status === 401) {
        // 未授权，退出登录
        userStore.logout()
        window.location.href = '/login'
        return false
      }
      
      error.value = '无法加载日程。请确保后端服务已启动。'
      console.error(err)
      return false
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 添加新日程
   * @returns {Promise<Object>} 返回结果对象 { success: boolean, conflict?: Object }
   */
  async function addSchedule() {
    // 验证必填字段
    if (!newSchedule.value.title || !newSchedule.value.start_time) {
      alert('标题和开始时间不能为空！')
      return { success: false }
    }
    
    try {
      // 构建请求数据
      const payload = {
        ...newSchedule.value,
        start_time: new Date(newSchedule.value.start_time).toISOString(),
        end_time: newSchedule.value.end_time ? new Date(newSchedule.value.end_time).toISOString() : null,
        priority: parseInt(newSchedule.value.priority),
        is_recurring: newSchedule.value.is_recurring || false,
        recurring_pattern: newSchedule.value.is_recurring 
          ? (newSchedule.value.recurring_pattern || 'weekly') 
          : null,
        tags: Array.isArray(newSchedule.value.tags) ? newSchedule.value.tags : []
      }
      
      console.log('创建日程 payload:', payload)
      await axios.post(`${API_URL}/schedules`, payload)
      
      // 重置表单
      newSchedule.value = defaultScheduleForm()
      
      // 重新加载列表
      await fetchSchedules()
      return { success: true }
    } catch (err) {
      // 【新增】处理409冲突响应
      if (err.response?.status === 409) {
        const conflictData = err.response.data
        console.log('⚠️ 检测到日程冲突:', conflictData)
        
        // 返回冲突数据，由调用方处理
        return { 
          success: false, 
          conflict: conflictData 
        }
      }
      
      // 其他错误
      alert('添加失败，请检查控制台信息。')
      console.error(err)
      return { success: false }
    }
  }

  /**
   * 删除日程
   * @param {number} id - 日程 ID
   * @returns {Promise<boolean>} 是否成功
   */
  async function deleteSchedule(id) {
    if (!confirm('确定要删除这个日程吗？')) {
      return false
    }
    
    try {
      await axios.delete(`${API_URL}/schedules/${id}`)
      await fetchSchedules()
      return true
    } catch (err) {
      alert('删除失败，请重试。')
      console.error(err)
      return false
    }
  }

  /**
   * 打开编辑弹窗
   * @param {Object} schedule - 日程对象
   */
  function openEditModal(schedule) {
    editingSchedule.value = schedule
    
    // 转换时间为本地格式
    const scheduleDate = new Date(schedule.start_time)
    const year = String(scheduleDate.getFullYear())
    const month = String(scheduleDate.getMonth() + 1).padStart(2, '0')
    const day = String(scheduleDate.getDate()).padStart(2, '0')
    const hours = String(scheduleDate.getHours()).padStart(2, '0')
    const minutes = String(scheduleDate.getMinutes()).padStart(2, '0')
    
    // 转换结束时间为本地格式（如果有）
    let localEndTime = ''
    if (schedule.end_time) {
      const endDate = new Date(schedule.end_time)
      const endYear = String(endDate.getFullYear())
      const endMonth = String(endDate.getMonth() + 1).padStart(2, '0')
      const endDay = String(endDate.getDate()).padStart(2, '0')
      const endHours = String(endDate.getHours()).padStart(2, '0')
      const endMinutes = String(endDate.getMinutes()).padStart(2, '0')
      localEndTime = `${endYear}-${endMonth}-${endDay}T${endHours}:${endMinutes}`
    }
    
    editForm.value = {
      title: schedule.title,
      content: schedule.content || '',
      start_time: `${year}-${month}-${day}T${hours}:${minutes}`,
      end_time: localEndTime,
      priority: schedule.priority || 1,
      is_recurring: schedule.is_recurring || false,
      recurring_pattern: schedule.recurring_pattern || '',
      tags: Array.isArray(schedule.tags) ? schedule.tags : [] // 确保 tags 是数组
    }
  }

  /**
   * 关闭编辑弹窗
   */
  function closeEditModal() {
    editingSchedule.value = null
    editForm.value = {
      title: '',
      content: '',
      start_time: '',
      end_time: '',
      priority: 1,
      is_recurring: false,
      recurring_pattern: ''
    }
  }

  /**
   * 保存编辑的日程
   * @returns {Promise<boolean>} 是否成功
   */
  async function saveEdit() {
    // 验证必填字段
    if (!editForm.value.title || !editForm.value.start_time) {
      alert('标题和开始时间不能为空！')
      return false
    }
    
    try {
      const payload = {
        ...editForm.value,
        start_time: new Date(editForm.value.start_time).toISOString(),
        end_time: editForm.value.end_time ? new Date(editForm.value.end_time).toISOString() : null,
        priority: parseInt(editForm.value.priority),
        is_recurring: !!editForm.value.is_recurring,
        recurring_pattern: editForm.value.is_recurring 
          ? (editForm.value.recurring_pattern || 'weekly') 
          : null,
        tags: Array.isArray(editForm.value.tags) ? editForm.value.tags : []
      }

      console.log('更新日程 payload:', payload)
      await axios.put(`${API_URL}/schedules/${editingSchedule.value.id}`, payload)
      
      closeEditModal()
      await fetchSchedules()
      return true
    } catch (err) {
      console.error('更新失败:', err)
      const errorMsg = err.response?.data?.error || err.message || '更新失败，请重试'
      alert(`更新失败：${errorMsg}`)
      return false
    }
  }

  /**
   * 标记日程为已完成/未完成
   * @param {number} id - 日程 ID
   * @returns {Promise<boolean>} 是否成功
   */
  async function markScheduleComplete(id) {
    try {
      await axios.patch(`${API_URL}/schedules/${id}/complete`)
      await fetchSchedules()
      return true
    } catch (err) {
      console.error('更新完成状态失败:', err)
      alert('更新状态失败，请重试')
      return false
    }
  }

  /**
   * 重置日程表单
   */
  function resetScheduleForm() {
    newSchedule.value = defaultScheduleForm()
  }

  // 暴露给外部使用的方法和状态
  return {
    schedules,
    isLoading,
    error,
    editingSchedule,
    newSchedule,
    editForm,
    fetchSchedules,
    addSchedule,
    deleteSchedule,
    markScheduleComplete,
    openEditModal,
    closeEditModal,
    saveEdit,
    resetScheduleForm
  }
}