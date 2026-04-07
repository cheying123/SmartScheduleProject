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
export function useNaturalLanguage(API_URL, fetchSchedules) {
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
      const response = await axios.post(`${API_URL}/schedules/natural-language`, {
        text: naturalLanguageInput.value,
        timezone_offset: timezoneOffset
      })
      
      naturalLanguageInput.value = ''
      isNaturalLanguageMode.value = false
      
      // 刷新日程列表（和传统表单创建使用同样的方法）
      if (fetchSchedules) {
        await fetchSchedules()
      }
      
      if (response.data.ai_parsed) {
        alert(`✨ AI 智能解析成功！日程已创建：${response.data.schedule.title}`)
      } else {
        alert(`日程已创建：${response.data.schedule.title}`)
      }
      
      return { success: true, data: response.data }
    } catch (error) {
      if (error.response?.status === 409) {
        const conflictData = error.response.data
        
        // 存储冲突数据，由父组件显示对话框
        conflictDialog.value = conflictData
        
        // 重置处理状态
        isProcessingNL.value = false
        
        return { 
          success: false, 
          type: 'conflict', 
          data: conflictData 
        }
      } else {
        // 其他错误也要重置状态
        isProcessingNL.value = false
        
        const errorMsg = error.response?.data?.error || error.message || '解析失败，请重试'
        alert(`❌ 错误：${errorMsg}`)
        console.error(error)
        return { success: false, type: 'error', error }
      }
    } finally {
      // 确保在 try-catch 之外也重置（成功的情况）
      if (isProcessingNL.value) {
        isProcessingNL.value = false
      }
    }
  }

  /**
   * 启动语音输入
   * @returns {SpeechRecognition|null} 语音识别实例
   */
  function startVoiceInput() {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      alert('您的浏览器不支持语音识别，请使用 Chrome、Edge 或其他基于 Chromium 的浏览器')
      return null
    }
    
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    const recognition = new SpeechRecognition()
    
    recognition.lang = VOICE_RECOGNITION.LANG
    recognition.continuous = VOICE_RECOGNITION.CONTINUOUS
    recognition.interimResults = VOICE_RECOGNITION.INTERIM_RESULTS
    recognition.maxAlternatives = VOICE_RECOGNITION.MAX_ALTERNATIVES
    
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
    
    recognition.onend = () => {
      console.log('语音识别已结束')
      isRecording.value = false
      
      if (recordingTimer.value) {
        clearInterval(recordingTimer.value)
        recordingTimer.value = null
      }
    }
    
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript
      naturalLanguageInput.value = transcript
      console.log('识别结果:', transcript)
    }
    
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