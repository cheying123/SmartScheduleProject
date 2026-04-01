/**
 * 推荐和通知 Composable
 * 文件路径：frontend/src/composables/useNotifications.js
 */

import { ref } from 'vue'
import axios from 'axios'
import { NOTIFICATION_TITLES } from '@/constants'

/**
 * 通知管理组合式函数
 * @param {string} API_URL - API 基础地址
 * @returns {Object} 通知管理相关的方法和状态
 */
export function useNotifications(API_URL) {
  const recommendations = ref([])
  const showRecommendations = ref(false)
  const hasUnreadNotifications = ref(false)

  /**
   * 加载推荐列表
   * @returns {Promise<boolean>} 是否成功
   */
  async function loadRecommendations() {
    try {
      const response = await axios.get(`${API_URL}/recommendations`)
      // 修改：后端直接返回数组，不需要 .recommendations
      recommendations.value = Array.isArray(response.data) ? response.data : []
      showRecommendations.value = true
      hasUnreadNotifications.value = false
      return true
    } catch (error) {
      console.error('加载推荐失败:', error)
      recommendations.value = []  // 确保即使出错也是空数组而不是 undefined
      return false
    }
  }

  /**
   * 清除通知
   */
  function clearNotifications() {
    recommendations.value = []
    showRecommendations.value = false
  }

  /**
   * 获取通知标题
   * @param {string} type - 通知类型
   * @returns {string} 通知标题
   */
  function getNotificationTitle(type) {
    return NOTIFICATION_TITLES[type] || '智能推荐'
  }

  return {
    recommendations,
    showRecommendations,
    hasUnreadNotifications,
    loadRecommendations,
    clearNotifications,
    getNotificationTitle
  }
}