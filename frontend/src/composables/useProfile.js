/**
 * 用户资料管理 Composable
 * 文件路径：frontend/src/composables/useProfile.js
 */

import { ref } from 'vue'
import axios from 'axios'
import { GEOLOCATION_OPTIONS } from '@/constants'

/**
 * 用户资料管理组合式函数
 * @param {Object} userStore - Pinia 用户状态 store
 * @param {string} API_URL - API 基础地址
 * @returns {Object} 用户资料管理相关的方法和状态
 */
export function useProfile(userStore, API_URL) {
  // 状态
  const isProfileEditModalVisible = ref(false)
  const profileForm = ref({
    username: '',
    email: '',
    location: '',
    location_name: '',
    weather_alerts_enabled: true,
    preferred_work_hours: {
      start: '09:00',
      end: '18:00'
    }
  })
  
  const isLocating = ref(false)
  const locationStatus = ref('')

  /**
   * 打开个人资料编辑弹窗
   */
  function openProfileEdit() {
    profileForm.value = {
      username: userStore.user?.username || '',
      email: userStore.user?.email || '',
      location: userStore.user?.location || '',
      location_name: userStore.user?.location_name || '',
      weather_alerts_enabled: userStore.user?.weather_alerts_enabled !== false,
      preferred_work_hours: userStore.user?.preferred_work_hours || {
        start: '09:00',
        end: '18:00'
      }
    }
    isProfileEditModalVisible.value = true
  }

  /**
   * 保存个人资料
   * @returns {Promise<boolean>} 是否成功
   */
  async function saveProfile() {
    try {
      const response = await axios.put(`${API_URL}/users/profile`, profileForm.value, {
        headers: {
          'Authorization': `Bearer ${userStore.token}`
        }
      })
      userStore.user = response.data
      isProfileEditModalVisible.value = false
      alert('个人资料已更新')
      return true
    } catch (error) {
      console.error('更新失败:', error)
      alert('更新失败，请重试')
      return false
    }
  }

  /**
   * 定位用户位置
   * @returns {Promise<Object>} 定位结果
   */
  async function locateUser() {
    if (!navigator.geolocation) {
      alert('您的浏览器不支持地理定位功能')
      return { success: false, error: 'not_supported' }
    }
    
    isLocating.value = true
    locationStatus.value = '正在获取您的位置...'
    
    return new Promise((resolve) => {
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          try {
            const { latitude, longitude } = position.coords
            
            locationStatus.value = '正在查询位置信息...'
            
            const response = await axios.post(`${API_URL}/location/geocode`, {
              latitude,
              longitude
            }, {
              headers: {
                'Authorization': `Bearer ${userStore.token}`
              }
            })
            
            const { city_location_id, city_name } = response.data
            
            profileForm.value.location = city_location_id
            profileForm.value.location_name = city_name
            locationStatus.value = `定位成功！${city_name}`
            
            setTimeout(() => {
              locationStatus.value = ''
            }, 3000)
            
            resolve({ success: true, data: response.data })
          } catch (error) {
            console.error('定位失败:', error)
            locationStatus.value = '定位失败：' + (error.response?.data?.error || '网络错误')
            setTimeout(() => {
              locationStatus.value = ''
            }, 5000)
            
            resolve({ success: false, error })
          } finally {
            isLocating.value = false
          }
        },
        (error) => {
          isLocating.value = false
          locationStatus.value = '定位失败：' + error.message
          setTimeout(() => {
            locationStatus.value = ''
          }, 5000)
          
          resolve({ success: false, error })
        },
        GEOLOCATION_OPTIONS
      )
    })
  }

  /**
   * 刷新天气信息
   * @returns {Promise<boolean>} 是否成功
   */
  async function refreshWeather() {
    if (!profileForm.value.location) {
      alert('请先设置城市位置')
      return false
    }
    
    try {
      const response = await axios.post(`${API_URL}/weather/update-all`, {}, {
        headers: {
          'Authorization': `Bearer ${userStore.token}`
        }
      })
      
      alert(response.data.message)
      return true
    } catch (error) {
      console.error('刷新天气失败:', error)
      alert('刷新天气失败，请重试')
      return false
    }
  }

  /**
   * 从个人资料刷新天气
   * @returns {Promise<boolean>} 是否成功
   */
  async function refreshWeatherFromProfile() {
    if (!userStore.user?.location) {
      alert('请先在个人资料中设置城市位置')
      openProfileEdit()
      return false
    }
    
    try {
      const response = await axios.post(`${API_URL}/weather/update-all`, {}, {
        headers: {
          'Authorization': `Bearer ${userStore.token}`
        }
      })
      
      alert(response.data.message)
      return true
    } catch (error) {
      console.error('刷新天气失败:', error)
      alert('刷新天气失败，请重试')
      return false
    }
  }

  return {
    isProfileEditModalVisible,
    profileForm,
    isLocating,
    locationStatus,
    openProfileEdit,
    saveProfile,
    locateUser,
    refreshWeather,
    refreshWeatherFromProfile
  }
}