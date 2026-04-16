/**
 * 时间格式化工具函数
 * 文件路径：frontend/src/utils/timeUtils.js
 */

/**
 * 获取当前日期时间（用于表单默认值）
 * 格式：2026-03-30T15:45
 */
export function getCurrentDateTime() {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  const hours = String(now.getHours()).padStart(2, '0')
  const minutes = String(now.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day}T${hours}:${minutes}`
}

/**
 * 将 ISO 字符串转换为 datetime-local 输入框的格式
 * @param {string} isoString - ISO 格式的日期字符串 (UTC)
 * @returns {string} 格式：2026-03-30T15:45 (本地时间)
 */
export function formatDateForInput(isoString) {
  if (!isoString) return ''
  // 确保浏览器将其识别为 UTC 时间
  const date = new Date(isoString.endsWith('Z') ? isoString : isoString + 'Z')
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day}T${hours}:${minutes}`
}

/**
 * 格式化日期显示（核心修复：确保 UTC 转本地）
 * @param {string} isoString - ISO 格式的日期字符串 (UTC)
 * @param {string} format - 格式类型：'time' (时间) 或 'full' (完整)
 * @returns {string} 格式化后的本地时间字符串
 */
export function formatDate(isoString, format = 'time') {
  if (!isoString) return ''
  
  // 关键修复：如果字符串不带 Z，手动补上以强制浏览器按 UTC 解析
  const utcString = isoString.endsWith('Z') ? isoString : isoString + 'Z'
  const date = new Date(utcString)
  
  if (isNaN(date.getTime())) return ''

  if (format === 'time') {
    // 只显示时间：15:45 (自动转为本地时区)
    return date.toLocaleTimeString('zh-CN', { 
      hour: '2-digit', 
      minute: '2-digit', 
      hour12: false 
    })
  }
  
  // 显示完整日期时间
  return date.toLocaleString('zh-CN')
}

/**
 * 获取日程的本地化开始时间（用于列表展示）
 */
export function getLocalStartTime(isoString) {
  return formatDate(isoString, 'time')
}

/**
 * 判断日程是否已过期
 * @param {string} isoString - ISO 格式的日期字符串
 * @returns {boolean} 是否已过期
 */
export function isPastSchedule(isoString) {
  if (!isoString) return false
  const scheduleDate = new Date(isoString)
  const now = new Date()
  
  // 比较日期（忽略时间）
  const scheduleDateOnly = new Date(
    scheduleDate.getFullYear(), 
    scheduleDate.getMonth(), 
    scheduleDate.getDate()
  )
  const nowDateOnly = new Date(
    now.getFullYear(), 
    now.getMonth(), 
    now.getDate()
  )
  
  return scheduleDateOnly < nowDateOnly
}

/**
 * 获取时区信息
 * @returns {string} 时区描述，如："北京时间 - 东八区 (UTC+8)"
 */
export function getTimezoneInfo() {
  const now = new Date()
  const timezoneOffset = -now.getTimezoneOffset() // 分钟
  const offsetHours = Math.floor(Math.abs(timezoneOffset) / 60)
  const offsetMinutes = Math.abs(timezoneOffset) % 60
  
  let timezoneName = ''
  let regionName = ''
  
  // 常见时区映射
  if (timezoneOffset === 480) {
    timezoneName = '东八区 (UTC+8)'
    regionName = '北京时间'
  } else if (timezoneOffset === 540) {
    timezoneName = '东九区 (UTC+9)'
    regionName = '东京时间'
  } else if (timezoneOffset === 330) {
    timezoneName = '东五区半 (UTC+5:30)'
    regionName = '印度标准时间'
  } else if (timezoneOffset === 0) {
    timezoneName = '中时区 (UTC+0)'
    regionName = '格林尼治时间'
  } else if (timezoneOffset === -300) {
    timezoneName = '西五区 (UTC-5)'
    regionName = '纽约时间'
  } else if (timezoneOffset === -480) {
    timezoneName = '西八区 (UTC-8)'
    regionName = '洛杉矶时间'
  } else {
    const sign = timezoneOffset >= 0 ? '+' : '-'
    timezoneName = `UTC${sign}${offsetHours}:${String(offsetMinutes).padStart(2, '0')}`
    regionName = '本地时间'
  }
  
  return `${regionName} - ${timezoneName}`
}

/**
 * 格式化录音时长
 * @param {number} seconds - 秒数
 * @returns {string} 格式化后的时长，如："01:30"
 */
export function formatRecordingTime(seconds) {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
}