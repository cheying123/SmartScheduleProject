/**
 * 自然语言输入 Composable（包含语音识别）
 * 文件路径：frontend/src/composables/useNaturalLanguage.js
 */

import { ref, onUnmounted } from 'vue'
import axios from 'axios'
import { useUserStore } from '@/stores/user'
import { QUERY_KEYWORDS } from '@/constants'

/**
 * 自然语言输入组合式函数
 * @param {string} API_URL - API 基础地址
 * @param {Function} fetchSchedules - 刷新日程列表的方法
 * @returns {Object} 自然语言输入相关的方法和状态
 */
export function useNaturalLanguage(API_URL, fetchSchedules) {
  const userStore = useUserStore()
  
  // 状态
  const isNaturalLanguageMode = ref(false)
  const naturalLanguageInput = ref('')
  const isProcessingNL = ref(false)
  const isAIProcessing = ref(false)
  const conflictDialog = ref(null)
  
  // 录音状态
  const isRecording = ref(false)
  const recordingDuration = ref(0)
  const recordingInterval = ref(null)

  /**
   * 语音合成工具函数 (Text-to-Speech)
   * 实现任务书中的"多模态反馈"
   */
  function speak(text, priority = false) {
    if ('speechSynthesis' in window) {
      // 如果是高优先级（如冲突警告），强制打断当前播报
      if (priority) {
        window.speechSynthesis.cancel()
      } else if (window.speechSynthesis.speaking && !priority) {
        // 普通消息排队，不强行打断
        return 
      }
      
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.lang = 'zh-CN'
      utterance.rate = 1.0 // 语速
      utterance.pitch = 1.0 // 音调
      window.speechSynthesis.speak(utterance)
    }
  }

  /**
   * 解析自然语言并创建日程
   * @param {number} timezoneOffset - 时区偏移量（分钟）
   * @returns {Promise<Object>} - 创建的日程对象
   */
  async function parseAndCreate(timezoneOffset) {
    if (!naturalLanguageInput.value || !naturalLanguageInput.value.trim()) {
      speak('请输入内容', true)
      return { success: false, error: '请输入内容' }
    }

    isProcessingNL.value = true
    isAIProcessing.value = true
    
    try {
      const response = await axios.post(
        `${API_URL}/schedules/nlp-parse`,
        { 
          text: naturalLanguageInput.value,
          timezone_offset: timezoneOffset
        },
        { 
          headers: { 
            'Authorization': `Bearer ${userStore.token}`,
            'Content-Type': 'application/json'
          } 
        }
      )
      
      const scheduleData = response.data
      
      // 成功反馈：语音 + 视觉
      const timeStr = new Date(scheduleData.start_time).toLocaleString('zh-CN', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
      speak(`好的，已为您安排${scheduleData.title}，时间是${timeStr}`)
      
      // 清空输入框
      naturalLanguageInput.value = ''
      
      // 刷新日程列表
      if (fetchSchedules) {
        await fetchSchedules()
      }
      
      return { success: true, data: scheduleData }
    } catch (err) {
      console.error('NLP 解析失败:', err)
      const errMsg = err.response?.data?.error || '智能解析失败，请尝试手动输入'
      
      // 错误反馈：语音提示
      speak('抱歉，我没听懂，请您再说清楚一点')
      
      return { success: false, error: errMsg }
    } finally {
      isProcessingNL.value = false
      isAIProcessing.value = false
    }
  }

  /**
   * 通过自然语言查询日程
   * @param {string} queryText - 查询文本
   * @param {number} timezoneOffset - 时区偏移量（分钟）
   * @returns {Promise<Object>} - 查询结果
   */
  async function queryExistingSchedules(queryText, timezoneOffset) {
    if (!queryText || !queryText.trim()) {
      speak('请输入查询内容', true)
      return { success: false, error: '请输入查询内容' }
    }

    isAIProcessing.value = true
    
    try {
      const response = await axios.post(
        `${API_URL}/schedules/query`,
        { 
          query: queryText,
          timezone_offset: timezoneOffset
        },
        { 
          headers: { 
            'Authorization': `Bearer ${userStore.token}`,
            'Content-Type': 'application/json'
          } 
        }
      )
      
      if (response.data.success) {
        const result = response.data.data
        speak(result.response)
        return { success: true, data: result }
      } else {
        const errMsg = response.data.error || '查询失败'
        speak('查询失败，请重试')
        return { success: false, error: errMsg }
      }
    } catch (err) {
      console.error('查询日程失败:', err)
      const errMsg = err.response?.data?.error || '查询失败，请稍后重试'
      speak('查询失败，请稍后重试')
      return { success: false, error: errMsg }
    } finally {
      isAIProcessing.value = false
    }
  }

  /**
   * 启动语音输入
   */
  function startVoiceInput() {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      speak('您的浏览器不支持语音识别', true)
      return
    }
    
    isRecording.value = true
    recordingDuration.value = 0
    
    // 开始计时
    recordingInterval.value = setInterval(() => {
      recordingDuration.value += 1
    }, 1000)
    
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    const recognition = new SpeechRecognition()
    
    recognition.lang = 'zh-CN'
    recognition.continuous = false
    recognition.interimResults = false
    
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript
      naturalLanguageInput.value = transcript

      stopRecording()

      if (isQueryIntent(transcript) && onVoiceQueryCallback) {
        onVoiceQueryCallback(transcript)
      }
    }
    
    recognition.onerror = (event) => {
      console.error('语音识别错误:', event.error)
      speak('语音识别失败，请重试')
      stopRecording()
    }
    
    recognition.onend = () => {
       isRecording.value = false
       if (recordingInterval.value) {
         clearInterval(recordingInterval.value)
         recordingInterval.value = null
       }
    }

    try {
      recognition.start()
    } catch (error) {
      console.error('启动语音识别失败:', error)
      speak('无法启动语音识别')
      stopRecording()
    }
  }

  /**
   * 停止语音输入
   */
  function stopRecording() {
    isRecording.value = false
    if (recordingInterval.value) {
      clearInterval(recordingInterval.value)
      recordingInterval.value = null
    }
    recordingDuration.value = 0
  }

  /**
   * 取消自然语言输入
   */
  function handleCancelClick() {
    if (isRecording.value) {
      stopRecording()
    }
    naturalLanguageInput.value = ''
    isNaturalLanguageMode.value = false
  }

  // 语音识别完成后的查询回调
  let onVoiceQueryCallback = null

  /**
   * 简单的指令识别（用于区分是"查询"还是"创建"）
   * @param {string} text
   * @returns {boolean} - 是否为查询指令
   */
  function isQueryIntent(text) {
    if (!text) return false
    return QUERY_KEYWORDS.some(keyword => text.includes(keyword))
  }

  /**
   * 设置语音识别完成后的查询回调
   * @param {Function} callback - 当语音识别结果为查询意图时调用
   */
  function setVoiceQueryCallback(callback) {
    onVoiceQueryCallback = callback
  }

  onUnmounted(() => {
    if (recordingInterval.value) {
      clearInterval(recordingInterval.value)
      recordingInterval.value = null
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
    parseAndCreate, // Replaced parseNaturalLanguage/handleNaturalLanguageSubmit with unified parseAndCreate for creation
    queryExistingSchedules,
    startVoiceInput,
    stopRecording,
    handleCancelClick,
    isQueryIntent,
    setVoiceQueryCallback,
    speak
  }
}