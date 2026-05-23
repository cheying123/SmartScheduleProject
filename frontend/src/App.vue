<script setup>
import { ref, onMounted } from 'vue'
import { RouterView } from 'vue-router'

const updateInfo = ref(null)
const isDesktop = ref(false)

onMounted(async () => {
  // 检查是否桌面版
  try {
    const res = await fetch('/api/version')
    const data = await res.json()
    isDesktop.value = data.desktop
  } catch {}

  // 检查更新
  try {
    const res = await fetch('/api/check-update')
    const data = await res.json()
    if (data.has_update) {
      updateInfo.value = data
    }
  } catch {}
})
</script>

<template>
  <!-- 版本更新通知 -->
  <div v-if="updateInfo" class="update-banner">
    <span>📦 发现新版本 v{{ updateInfo.latest_version }}</span>
    <a :href="updateInfo.download_url" target="_blank" class="update-link">
      前往下载
    </a>
  </div>

  <RouterView />
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Noto Sans SC', sans-serif;
  background-color: #F8F9FE;
}

.update-banner {
  background: linear-gradient(135deg, #4F46E5, #7C3AED);
  color: white;
  text-align: center;
  padding: 8px 16px;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.update-link {
  color: white;
  background: rgba(255,255,255,0.2);
  padding: 3px 12px;
  border-radius: 12px;
  text-decoration: none;
  font-size: 13px;
}
.update-link:hover {
  background: rgba(255,255,255,0.35);
}
</style>
