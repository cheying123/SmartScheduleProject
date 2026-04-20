<template>
  <div class="import-modal" v-if="visible">
    <div class="import-content">
      <div class="import-header">
        <h3><Upload :size="20" /> 导入日程</h3>
        <button class="close-btn" @click="onClose">
          <X :size="20" />
        </button>
      </div>
      
      <div class="import-body">
        <div 
          class="drop-zone"
          @dragover.prevent="handleDragOver"
          @drop.prevent="handleDrop"
          @dragleave="handleDragLeave"
          @click="triggerFileSelect"
          :class="{ 'drag-over': isDragOver }"
        >
          <input 
            type="file" 
            ref="fileInputRef"
            accept=".ics,.ical,.ifb"
            @change="handleFileChange"
            style="display: none"
          />
          <div class="upload-icon">
            <UploadCloud :size="48" />
          </div>
          <p class="upload-text">
            <span class="upload-highlight">点击选择</span> 或 拖拽 iCalendar 文件到此处
          </p>
          <p class="upload-subtext">支持 .ics, .ical, .ifb 格式</p>
        </div>
        
        <div v-if="selectedFile" class="file-info">
          <FileText :size="16" />
          <span class="file-name">{{ selectedFile.name }}</span>
          <span class="file-size">({{ formatFileSize(selectedFile.size) }})</span>
          <button class="remove-file" @click="removeFile">
            <X :size="16" />
          </button>
        </div>
        
        <div v-if="importResult" class="import-result">
          <CheckCircle v-if="importResult.success" :size="24" class="success-icon" />
          <AlertCircle v-else :size="24" class="error-icon" />
          <div class="result-text">
            <p class="result-title">{{ importResult.success ? '导入成功' : '导入失败' }}</p>
            <p class="result-details" v-if="importResult.success">
              成功导入 {{ importResult.imported_count }} 个日程，
              跳过 {{ importResult.skipped_count }} 个重复日程
            </p>
            <p class="result-error" v-else>{{ importResult.message }}</p>
          </div>
        </div>
      </div>
      
      <div class="import-actions">
        <button class="btn-cancel" @click="onClose">关闭</button>
        <button 
          class="btn-import" 
          @click="handleImport"
          :disabled="!selectedFile || isImporting"
        >
          <Upload :size="16" v-if="!isImporting" />
          <Loader2 :size="16" v-else class="animate-spin" />
          {{ isImporting ? '导入中...' : '导入日程' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, defineProps, defineEmits } from 'vue'
import { Upload, X, UploadCloud, FileText, CheckCircle, AlertCircle, Loader2 } from 'lucide-vue-next'
import axios from 'axios'

// Props
const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  API_URL: {
    type: String,
    required: true
  },
  token: {
    type: String,
    required: true
  }
})

// Emits
const emit = defineEmits(['close', 'import-success'])

// 响应式数据
const fileInputRef = ref(null)
const selectedFile = ref(null)
const isDragOver = ref(false)
const isImporting = ref(false)
const importResult = ref(null)

// 处理拖拽事件
function handleDragOver(event) {
  isDragOver.value = true
  event.preventDefault()
}

function handleDragLeave() {
  isDragOver.value = false
}

function handleDrop(event) {
  isDragOver.value = false
  event.preventDefault()
  
  const files = event.dataTransfer.files
  if (files.length > 0) {
    processFile(files[0])
  }
}

// 触发文件选择器
function triggerFileSelect() {
  fileInputRef.value?.click()
}

// 处理文件选择
function handleFileChange(event) {
  const files = event.target.files
  if (files.length > 0) {
    processFile(files[0])
  }
}

// 处理文件
function processFile(file) {
  // 检查文件类型
  const validTypes = ['.ics', '.ical', '.ifb']
  const extension = '.' + file.name.split('.').pop().toLowerCase()
  
  if (!validTypes.includes(extension)) {
    alert('不支持的文件格式，请上传 .ics, .ical 或 .ifb 文件')
    return
  }
  
  selectedFile.value = file
  importResult.value = null
}

// 删除选中文件
function removeFile() {
  selectedFile.value = null
  importResult.value = null
}

// 格式化文件大小
function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 执行导入
async function handleImport() {
  if (!selectedFile.value) return
  
  isImporting.value = true
  importResult.value = null
  
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    
    const response = await axios.post(
      `${props.API_URL}/schedules/import`,
      formData,
      {
        headers: {
          'Authorization': `Bearer ${props.token}`,
          'Content-Type': 'multipart/form-data'
        }
      }
    )
    
    importResult.value = {
      success: true,
      ...response.data
    }
    
    // 发送导入成功的事件
    emit('import-success')
  } catch (error) {
    console.error('导入失败:', error)
    importResult.value = {
      success: false,
      message: error.response?.data?.error || '导入失败，请稍后重试'
    }
  } finally {
    isImporting.value = false
  }
}

// 关闭模态框
function onClose() {
  selectedFile.value = null
  importResult.value = null
  emit('close')
}
</script>

<style scoped>
.import-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.import-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 4px 6px rgba(50, 50, 93, 0.11), 0 1px 3px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.import-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e9ecef;
}

.import-header h3 {
  margin: 0;
  color: #32325D;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.close-btn {
  background: none;
  border: none;
  color: #8898aa;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  transition: all 0.2s;
}

.close-btn:hover {
  background-color: #f8f9fa;
  color: #525F7F;
}

.import-body {
  padding: 1.5rem;
}

.drop-zone {
  border: 2px dashed #e9ecef;
  border-radius: 12px;
  padding: 2rem 1rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  background-color: #f8f9fa;
}

.drop-zone:hover {
  background-color: #edf2f9;
  border-color: #cbd5e0;
}

.drop-zone.drag-over {
  border-color: #5E72E4;
  background-color: #f0f4ff;
}

.upload-icon {
  color: #8898aa;
  margin-bottom: 1rem;
}

.upload-text {
  margin: 0 0 0.5rem 0;
  color: #525F7F;
  font-size: 1rem;
}

.upload-highlight {
  color: #5E72E4;
  font-weight: 600;
}

.upload-subtext {
  margin: 0;
  color: #8898aa;
  font-size: 0.85rem;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 8px;
  margin-top: 1rem;
  font-size: 0.9rem;
}

.file-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  color: #8898aa;
  font-size: 0.8rem;
}

.remove-file {
  background: none;
  border: none;
  color: #8898aa;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  transition: all 0.2s;
}

.remove-file:hover {
  background-color: #e9ecef;
  color: #525F7F;
}

.import-result {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 8px;
  margin-top: 1rem;
}

.success-icon {
  color: #28a745;
  flex-shrink: 0;
}

.error-icon {
  color: #dc3545;
  flex-shrink: 0;
}

.result-text {
  flex: 1;
}

.result-title {
  margin: 0 0 0.25rem 0;
  font-weight: 600;
  color: #32325D;
}

.result-details {
  margin: 0;
  color: #525F7F;
  font-size: 0.9rem;
  line-height: 1.4;
}

.result-error {
  margin: 0;
  color: #dc3545;
  font-size: 0.9rem;
  line-height: 1.4;
}

.import-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding: 1.5rem;
  border-top: 1px solid #e9ecef;
  background-color: #f8f9fa;
}

.btn-cancel, .btn-import {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-cancel {
  background-color: #f4f5f7;
  color: #525F7F;
}

.btn-cancel:hover {
  background-color: #e9ecef;
}

.btn-import {
  background-color: #10b981;
  color: white;
}

.btn-import:hover:not(:disabled) {
  background-color: #059669;
  transform: translateY(-1px);
}

.btn-import:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .import-content {
    width: 95%;
    margin: 1rem;
  }
}
</style>