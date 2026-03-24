import { createApp } from 'vue'

// 导入 Vue 的 createApp 函数
import { createPinia } from 'pinia'
import router from './router'

// 导入你的主组件 App.vue
import App from './App.vue'


// 创建 Vue 应用实例
const app = createApp(App)

const pinia = createPinia()

app.use(pinia)
app.use(router)

// 挂载应用到页面上 ID 为 'app' 的元素
app.mount('#app')