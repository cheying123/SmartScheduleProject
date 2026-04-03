// 创建新文件：d:\SmartScheduleProject\frontend\src\composables\useAIChat.js
import { ref } from 'vue'
import axios from 'axios'
import { useUserStore } from '@/stores/user'

const API_URL = 'http://127.0.0.1:5000/api'

export function useAIChat() {
  const chatMessages = ref([])
  const isChatLoading = ref(false)
  const sessionId = ref(null)
  const userStore = useUserStore()

  async function sendMessage(message) {
    isChatLoading.value = true
    
    try {
      const response = await axios.post(
        `${API_URL}/ai/chat`,
        {
          message,
          session_id: sessionId.value
        },
        {
          headers: {
            'Authorization': `Bearer ${userStore.token}`
          }
        }
      )
      
      sessionId.value = response.data.session_id
      
      chatMessages.value.push({
        role: 'user',
        message: message,
        created_at: new Date().toISOString()
      })
      
      chatMessages.value.push({
        role: 'assistant',
        message: response.data.response,
        created_at: new Date().toISOString()
      })
      
      return response.data
    } catch (error) {
      console.error('发送消息失败:', error)
      throw error
    } finally {
      isChatLoading.value = false
    }
  }

  async function loadHistory(sid) {
    if (!sid) return
    
    try {
      const response = await axios.get(
        `${API_URL}/ai/conversations/${sid}`,
        {
          headers: {
            'Authorization': `Bearer ${userStore.token}`
          }
        }
      )
      
      sessionId.value = sid
      chatMessages.value = response.data.messages.map(msg => ({
        role: msg.role,
        message: msg.message,
        created_at: msg.created_at
      }))
    } catch (error) {
      console.error('加载历史失败:', error)
    }
  }

  async function loadSessions() {
    try {
      const response = await axios.get(
        `${API_URL}/ai/conversations`,
        {
          headers: {
            'Authorization': `Bearer ${userStore.token}`
          }
        }
      )
      return response.data.sessions
    } catch (error) {
      console.error('加载会话列表失败:', error)
      return []
    }
  }

  async function deleteSession(sid) {
    try {
      await axios.delete(
        `${API_URL}/ai/conversations/${sid}`,
        {
          headers: {
            'Authorization': `Bearer ${userStore.token}`
          }
        }
      )
      
      if (sessionId.value === sid) {
        chatMessages.value = []
        sessionId.value = null
      }
      
      return true
    } catch (error) {
      console.error('删除会话失败:', error)
      return false
    }
  }

  function clearChat() {
    chatMessages.value = []
    sessionId.value = null
  }

  return {
    chatMessages,
    isChatLoading,
    sessionId,
    sendMessage,
    loadHistory,
    loadSessions,
    deleteSession,
    clearChat
  }
}