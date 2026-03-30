/**
 * 自然语言输入 Composable（包含语音识别）
 * 文件路径：frontend/src/composables/useNaturalLanguage.js
 */

import { ref, onUnmounted } from 'vue'
import axios from 'axios'
import { VOICE_RECOGNITION, GEOLOCATION_OPTIONS } from '@/constants'
import { formatRecordingTime } from '@/utils/timeUtils'

/**
 * 自然语言输入组合式函数
 * @param {string} API_URL - API 基础地址
 * @returns {Object} 自然语言输入相关的方法和状态
 */
export function useNaturalLanguage(API_URL) {
  // 状态
  const isNaturalLanguageMode = ref(false)
  const naturalLanguageInput = ref('')
  const isProcessingNL = ref(false)
  const isAIProcessing = ref(false)
  const conflictDialog = ref(null)
  
  // 录音状态
  const isRecording = ref(false)
  const recordingDuration = ref(0)
  const recordingTimer = ref(null)

  /**
   * 处理自然语言提交
   * @param {number} timezoneOffset - 时区偏移量（分钟）
   * @returns {Promise<Object>} 处理结果
   */
  async function handleNaturalLanguageSubmit(timezoneOffset) {
    if (!naturalLanguageInput.value.trim()) {
      alert('请输入指令内容')
      return { success: false, error: 'empty_input' }
    }
    
    isProcessingNL.value = true
    
    try {
      // 计算时区字符串
      const timezoneHours = Math.floor(Math.abs(timezoneOffset) / 60)
      const timezoneMinutes = Math.abs(timezoneOffset) % 60
      const sign = timezoneOffset >= 0 ? '+' : '-'
      const timezoneStr = `UTC${sign}${timezoneHours}:${String(timezoneMinutes).padStart(2, '0')}`
      
      // 调用后端 API
      const response = await axios.post(`${API_URL}/schedules/natural-language`, {
        text: naturalLanguageInput.value,
        timezone: timezoneStr,
        timezone_offset: timezoneOffset
      })
      
      // 清空输入
      naturalLanguageInput.value = ''
      isNaturalLanguageMode.value = false
      
      // 显示成功消息
      if (response.data.ai_parsed) {
        alert(`✨ AI 智能解析成功！日程已创建：${response.data.schedule.title}`)
      } else {
        alert(`日程已创建：${response.data.schedule.title}`)
      }
      
      return { success: true, data: response.data }
    } catch (error) {
      // 处理冲突情况
      if (error.response?.status === 409) {
        conflictDialog.value = error.response.data
        return { 
          success: false, 
          type: 'conflict', 
          data: error.response.data 
        }
      } else {
        alert('解析失败，请重试')
        console.error(error)
        return { success: false, type: 'error', error }
      }
    } finally {
      isProcessingNL.value = false
    }
  }

  /**
   * 启动语音输入
   * @returns {SpeechRecognition|null} 语音识别实例
   */
  function startVoiceInput() {
    // 检查浏览器支持
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      alert('您的浏览器不支持语音识别，请使用 Chrome、Edge 或其他基于 Chromium 的浏览器')
      return null
    }
    
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    const recognition = new SpeechRecognition()
    
    // 配置参数
    recognition.lang = VOICE_RECOGNITION.LANG
    recognition.continuous = VOICE_RECOGNITION.CONTINUOUS
    recognition.interimResults = VOICE_RECOGNITION.INTERIM_RESULTS
    recognition.maxAlternatives = VOICE_RECOGNITION.MAX_ALTERNATIVES
    
    // 开始录音回调
    recognition.onstart = () => {
      console.log('语音识别已启动')
      isRecording.value = true
      recordingDuration.value = 0
      
      if (recordingTimer.value) {
        clearInterval(recordingTimer.value)
      }
      
      recordingTimer.value = setInterval(() => {
        recordingDuration.value++
      }, 1000)
    }
    
    // 结束录音回调
    recognition.onend = () => {
      console.log('语音识别已结束')
      isRecording.value = false
      
      if (recordingTimer.value) {
        clearInterval(recordingTimer.value)
        recordingTimer.value = null
      }
    }
    
    // 识别结果回调
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript
      naturalLanguageInput.value = transcript
      console.log('识别结果:', transcript)
    }
    
    // 错误处理
    recognition.onerror = (event) => {
      console.error('语音识别错误:', event.error)
      
      let errorMessage = ''
      switch(event.error) {
        case 'no-speech':
          errorMessage = '未检测到语音，请对着麦克风说话'
          break
        case 'audio-capture':
          errorMessage = '无法访问麦克风，请检查权限设置'
          break
        case 'not-allowed':
          errorMessage = '麦克风权限被拒绝，请在浏览器设置中允许麦克风权限'
          break
        case 'network':
          errorMessage = '网络错误，请检查网络连接后重试'
          break
        case 'aborted':
          errorMessage = '语音识别已取消'
          break
        default:
          errorMessage = '语音识别失败：' + event.error
      }
      
      alert(errorMessage)
      stopRecording()
    }
    
    try {
      recognition.start()
      return recognition
    } catch (error) {
      console.error('启动语音识别失败:', error)
      alert('无法启动语音识别，请确保麦克风权限已允许')
      isRecording.value = false
      stopRecording()
      return null
    }
  }

  /**
   * 停止录音
   */
  function stopRecording() {
    isRecording.value = false
    if (recordingTimer.value) {
      clearInterval(recordingTimer.value)
      recordingTimer.value = null
    }
    recordingDuration.value = 0
  }

  /**
   * 取消操作
   */
  function handleCancelClick() {
    if (isRecording.value) {
      stopRecording()
    }
    isNaturalLanguageMode.value = false
    naturalLanguageInput.value = ''
  }

  // 组件卸载时清理定时器
  onUnmounted(() => {
    if (recordingTimer.value) {
      clearInterval(recordingTimer.value)
      recordingTimer.value = null
    }
  })

  return {
    isNaturalLanguageMode,
    naturalLanguageInput,
    isProcessingNL,
    isAIProcessing,
    conflictDialog,
    isRecording,
    recordingDuration,
    handleNaturalLanguageSubmit,
    startVoiceInput,
    stopRecording,
    handleCancelClick,
    formatRecordingTime
  }
}