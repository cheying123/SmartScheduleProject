# SmartSchedule - 智能日程管理系统

一个基于 AI 的智能日程管理应用，支持自然语言创建日程、智能排程、冲突检测、天气提醒和个性化推荐。

## 功能特性

- **自然语言创建日程** — 用日常语言描述即可自动创建日程（如"下周三下午两点开团队会议"）
- **智能查询** — 自然语言查询现有日程（如"这周五有什么安排？"）
- **语音输入** — 支持语音转文字快速创建和查询
- **AI 智能排程** — 输入任务列表，AI 自动分配到最佳时间段
- **冲突检测与解决** — 自动检测时间冲突，提供 AI 建议的替代时段
- **天气提醒** — 结合日程和天气信息，提供出行提醒
- **智能推荐** — 基于用户行为分析，提供日程平衡建议和时间偏好推荐
- **个性化设置** — 自定义工作时间、偏好时段
- **日程导入/导出** — 支持日历数据导入和导出
- **统计分析** — 日程完成情况、时间分配等数据可视化
- **响应式设计** — 适配桌面和移动端

## 技术栈

### 前端

| 技术 | 用途 |
|------|------|
| Vue 3 (Composition API) | 前端框架 |
| Vite | 构建工具 |
| Pinia | 状态管理 |
| Vue Router | 路由管理 |
| Axios | HTTP 请求 |
| Lucide Vue Next | 图标库 |

### 后端

| 技术 | 用途 |
|------|------|
| Flask | Web 框架 |
| SQLAlchemy | ORM 数据库操作 |
| Flask-JWT-Extended | JWT 身份认证 |
| Flask-Migrate | 数据库迁移 |
| Flask-CORS | 跨域支持 |
| MySQL | 数据库 |
| APScheduler | 定时任务 |

### AI 集成

- 通义千问 (Qwen) API — 自然语言解析、智能排程、推荐引擎
- 和风天气 API — 天气数据获取

## 项目结构

```
SmartSchedule/
├── backend/                        # Flask 后端
│   ├── app.py                      # 应用入口
│   ├── config.py                   # 配置文件
│   ├── extensions.py               # 扩展初始化
│   ├── requirements.txt            # Python 依赖
│   ├── models/                     # 数据模型
│   │   ├── user.py                 # 用户模型
│   │   └── schedule.py             # 日程模型
│   ├── routes/                     # API 路由
│   │   ├── auth.py                 # 认证接口
│   │   ├── schedules.py            # 日程 CRUD
│   │   ├── ai.py                   # AI 解析
│   │   ├── analytics.py            # 数据分析
│   │   ├── assistant.py            # 助手对话
│   │   ├── recommendations.py      # 智能推荐
│   │   ├── weather.py              # 天气
│   │   └── location.py             # 定位
│   ├── services/                   # 业务逻辑
│   │   ├── ai_service.py           # AI 服务
│   │   ├── nlp_parser.py           # NLP 解析
│   │   ├── conflict_detector.py    # 冲突检测
│   │   ├── recommendation_engine.py# 推荐引擎
│   │   ├── weather_service.py      # 天气服务
│   │   ├── recurring_service.py    # 重复日程
│   │   └── user_behavior_analyzer.py # 行为分析
│   └── utils/                      # 工具函数
│
├── frontend/                       # Vue 3 前端
│   ├── src/
│   │   ├── main.js                 # 应用入口
│   │   ├── App.vue                 # 根组件
│   │   ├── router/                 # 路由配置
│   │   ├── stores/                 # Pinia 状态管理
│   │   ├── views/                  # 页面组件
│   │   │   ├── HomeView.vue        # 主页面
│   │   │   ├── LoginView.vue       # 登录
│   │   │   ├── RegisterView.vue    # 注册
│   │   │   ├── CalendarView.vue    # 日历视图
│   │   │   └── StatisticsView.vue  # 统计分析
│   │   ├── components/             # 组件
│   │   │   ├── schedule/           # 日程相关
│   │   │   ├── common/             # 通用组件
│   │   │   ├── layout/             # 布局组件
│   │   │   ├── analytics/          # 分析组件
│   │   │   ├── notifications/      # 通知组件
│   │   │   ├── dashboard/          # 仪表盘
│   │   │   ├── profile/            # 个人资料
│   │   │   └── settings/           # 设置
│   │   ├── composables/            # 组合式函数
│   │   ├── constants/              # 常量
│   │   └── utils/                  # 工具函数
│   ├── index.html
│   └── vite.config.js
└── README.md
```

## 快速开始

### 环境要求

- Python 3.9+
- Node.js 20+
- MySQL 8.0+

### 1. 克隆项目

```bash
git clone https://github.com/yourusername/SmartSchedule.git
cd SmartSchedule
```

### 2. 后端配置

```bash
cd backend

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

创建 `.env` 文件（参考下方配置说明），然后启动后端：

```bash
python app.py
```

后端默认运行在 `http://127.0.0.1:5000`。

### 3. 前端配置

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端默认运行在 `http://localhost:5173`。

## 环境变量配置

在 `backend/.env` 中配置：

```env
# 数据库配置（MySQL）
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost:3306
DB_NAME=smart_schedule

# JWT 密钥（可选，不设置会自动生成）
JWT_SECRET_KEY=your_jwt_secret_key

# AI API 配置（通义千问）
AI_API_KEY=your_dashscope_api_key
AI_API_URL=https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation
AI_MODEL=qwen-turbo

# 天气 API（和风天气）
QWEATHER_API_KEY=your_qweather_api_key
```

## API 接口概览

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/auth/register` | POST | 用户注册 |
| `/api/auth/login` | POST | 用户登录 |
| `/api/auth/me` | GET | 获取当前用户信息 |
| `/api/schedules` | GET/POST | 日程列表 / 创建日程 |
| `/api/schedules/:id` | GET/PUT/DELETE | 日程详情 / 更新 / 删除 |
| `/api/schedules/:id/complete` | PATCH | 标记日程完成 |
| `/api/schedules/natural-language` | POST | 自然语言创建日程 |
| `/api/schedules/force-create` | POST | 强制创建（忽略冲突） |
| `/api/recommendations` | GET | 获取智能推荐 |
| `/api/analytics/stats` | GET | 统计数据 |
| `/api/analytics/daily-briefing` | GET | 每日智能摘要 |
| `/api/analytics/auto-schedule` | POST | 智能排程 |
| `/api/weather/current` | GET | 当前天气 |
| `/api/assistant/chat` | POST | AI 助手对话 |

## 主要功能说明

### 自然语言创建

输入如"明天下午3点到5点开团队会议，优先级高"的文本，AI 自动解析并创建包含标题、时间、优先级的完整日程。

### 智能排程

输入任务列表（如"复习数学 60分钟，跑步 30分钟"），AI 根据用户时间偏好和现有日程自动分配到最佳时段。

### 冲突检测

创建日程时自动检测时间冲突，并基于 AI 推荐可用的替代时段，用户可选择采纳或强制创建。

### 每日摘要

每天早上自动生成当日日程概览，包含天气信息、待办事项和时间建议。

## 许可证

MIT License
