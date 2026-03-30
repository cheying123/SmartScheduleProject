/**
 * 常量配置文件
 * 文件路径：frontend/src/constants/index.js
 */

// 导航标签
export const NAVIGATION = {
  tabs: {
    SCHEDULE: 'schedule',
    PROFILE: 'profile',
    NOTIFICATIONS: 'notifications',
    SETTINGS: 'settings'
  },
  titles: {
    schedule: '我的日程',
    profile: '个人信息',
    notifications: '消息通知',
    settings: '系统设置'
  }
}

// 通知类型
export const NOTIFICATION_TYPES = {
  WEATHER: 'weather',
  TIME_PREFERENCE: 'time_preference',
  BALANCE: 'balance',
  INFO: 'info'
}

// 通知标题映射
export const NOTIFICATION_TITLES = {
  weather: '🌤️ 天气提示',
  time_preference: '⏰ 时间偏好',
  balance: '😌 平衡建议',
  info: 'ℹ️ 提示信息'
}

// 优先级级别
export const PRIORITY_LEVELS = [
  { value: 1, label: '⭐ 普通' },
  { value: 2, label: '⭐⭐ 一般' },
  { value: 3, label: '⭐⭐⭐ 重要' },
  { value: 4, label: '⭐⭐⭐⭐ 紧急' },
  { value: 5, label: '⭐⭐⭐⭐⭐ 非常重要' }
]

// 重复模式
export const RECURRING_PATTERNS = [
  { value: 'daily', label: '每天重复' },
  { value: 'weekly', label: '每周重复' },
  { value: 'monthly', label: '每月重复' }
]

// 创建模式
export const CREATE_MODES = {
  FORM: 'form',              // 传统表单模式
  NATURAL: 'natural'         // 自然语言模式
}

// 语音识别配置
export const VOICE_RECOGNITION = {
  LANG: 'zh-CN',                    // 语言
  CONTINUOUS: false,                // 是否连续识别
  INTERIM_RESULTS: false,           // 是否显示中间结果
  MAX_ALTERNATIVES: 1               // 最大备选结果数
}

// 地理位置定位配置
export const GEOLOCATION_OPTIONS = {
  enableHighAccuracy: true,   // 高精度定位
  timeout: 10000,             // 超时时间 10 秒
  maximumAge: 300000          // 缓存时间 5 分钟
}

// API 基础路径
export const API_BASE_PATH = '/api'

// Cookie 配置
export const COOKIE_CONFIG = {
  expires: 7  // 7 天过期
}