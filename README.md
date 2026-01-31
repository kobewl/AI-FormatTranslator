# 🚀 AI-FormatTranslator - 智能文档翻译系统

> **项目已升级！** 从 DocTranslator 全面升级为 AI-FormatTranslator，新增专业领域翻译和双模式显示功能。

## 项目愿景

AI-FormatTranslator 是一个基于 AI 的智能文档翻译系统，支持多种文档格式的高质量翻译，完美保持原文档的格式和排版。采用 FastAPI + Vue 3 全栈架构，集成 DeepSeek 等大语言模型，提供企业级翻译解决方案。

## 核心功能

### 已实现功能 ✅

#### 核心翻译功能
- [x] **多格式文档翻译** - 支持 Word、PDF、Excel、PPT、Markdown、TXT
- [x] **双模式显示** - 替换模式 vs 对照模式（原文+译文并排显示）
- [x] **8大专业领域** - 通用、医疗、IT、法律、金融、工程、学术、商务
- [x] **格式完美保持** - 翻译后保留原文档的排版、样式和结构

#### 用户与权限
- [x] **JWT 认证** - 安全的用户登录与权限管理
- [x] **用户注册/登录** - 完整的用户生命周期管理

#### 管理与配置
- [x] **术语对照表管理** - 自定义专业术语翻译规则
- [x] **提示词管理** - 灵活配置 AI 翻译提示词（含领域专用提示词）
- [x] **翻译历史** - 完整的翻译任务记录与进度跟踪
- [x] **系统配置** - 全局参数管理

### 规划功能 🚧
- [ ] **批量翻译** - 多文件同时处理
- [ ] **翻译记忆库** - 智能学习用户偏好，提升翻译一致性
- [ ] **OCR 识别** - 图片/PDF 文字提取与翻译
- [ ] **实时协作** - 多人在线编辑与审校
- [ ] **API 开放平台** - 对外提供翻译服务接口

## 技术栈

### 后端（FastAPI + Python）
- **框架**: FastAPI 0.115+ + Uvicorn
- **数据库**: MySQL 8.0 + SQLAlchemy 2.0（异步支持）
- **数据验证**: Pydantic v2
- **认证**: JWT (python-jose) + 密码哈希 (bcrypt)
- **AI 引擎**: DeepSeek / OpenAI 兼容 API
- **文档处理**: 
  - Word: `python-docx` + 自定义样式保持引擎
  - Excel: `openpyxl`
  - PPT: `python-pptx`
- **其他**: `aiohttp`（异步 HTTP）、`pandas`（数据处理）

### 前端（Vue 3 + TypeScript）
- **框架**: Vue 3.4+ + Composition API (`<script setup>`)
- **构建工具**: Vite 5+
- **语言**: TypeScript 5+
- **状态管理**: Pinia（模块化 store）
- **路由**: Vue Router 4（动态路由 + 路由守卫）
- **UI 组件**: Ant Design Vue 4
- **HTTP 客户端**: Axios（封装统一错误处理）
- **图标**: @ant-design/icons-vue

## 项目结构

```
doc-translator/
├── backend/                    # 后端代码（FastAPI）
│   ├── app/                   # 应用核心代码
│   │   ├── __init__.py       # FastAPI 主应用与路由注册
│   │   ├── config.py         # 配置管理（Pydantic Settings）
│   │   ├── database.py       # 数据库连接与会话管理
│   │   ├── core/             # 核心模块
│   │   │   ├── security.py   # JWT 认证与密码加密
│   │   │   └── deps.py       # 依赖注入（DB 会话、当前用户）
│   │   ├── models/           # SQLAlchemy 2.0 数据模型
│   │   │   ├── customer.py   # 用户模型
│   │   │   ├── translate.py  # 翻译任务模型
│   │   │   ├── prompt.py     # 提示词模型（含领域配置）
│   │   │   └── ...
│   │   ├── schemas/          # Pydantic v2 数据验证
│   │   │   ├── auth.py       # 认证相关 schema
│   │   │   ├── translate.py  # 翻译相关 schema
│   │   │   └── ...
│   │   ├── resources/        # API 路由（RESTful 设计）
│   │   │   ├── auth/         # 认证接口
│   │   │   ├── translate/    # 翻译接口
│   │   │   ├── admin/        # 管理接口
│   │   │   └── ...
│   │   ├── translate/        # 翻译引擎（核心）
│   │   │   ├── engine.py     # 翻译引擎主控制器
│   │   │   ├── ai/           # AI 服务层
│   │   │   │   └── openai.py # DeepSeek/OpenAI 翻译器
│   │   │   ├── formatters/   # 文档格式处理器
│   │   │   │   ├── word.py   # Word 文档翻译器（双模式支持）
│   │   │   │   ├── excel.py  # Excel 处理器
│   │   │   │   └── ppt.py    # PPT 处理器
│   │   │   └── parsers/      # 文档解析器
│   │   └── utils/            # 工具函数
│   ├── db/                   # 数据库脚本
│   │   ├── init.sql          # 数据库初始化脚本
│   │   ├── migrate_add_domain_feature.sql  # 领域功能迁移
│   │   ├── seed_domain_prompts.sql         # 领域提示词种子数据
│   │   ├── fix_prompt_foreign_key.sql      # 外键修复脚本
│   │   ├── migrations/       # Alembic 迁移文件
│   │   └── seeds/            # 种子数据
│   ├── storage/              # 文件存储
│   │   ├── uploads/          # 上传的原始文件
│   │   └── translate/        # 翻译完成的文件
│   ├── logs/                 # 日志目录
│   ├── requirements.txt      # Python 依赖清单
│   ├── .env.example          # 环境变量示例
│   └── run.py               # 应用启动入口
├── frontend/                 # 前端代码（Vue 3）
│   ├── src/
│   │   ├── main.ts          # 应用入口（挂载、初始化）
│   │   ├── App.vue          # 根组件
│   │   ├── pages/           # 页面组件
│   │   │   ├── Login.vue    # 登录页
│   │   │   ├── Translate.vue # 翻译主页（步骤式UI）
│   │   │   ├── History.vue  # 翻译历史
│   │   │   ├── PromptManage.vue # 提示词管理
│   │   │   └── ...
│   │   ├── components/      # 可复用组件
│   │   ├── api/             # API 封装（axios 实例）
│   │   ├── store/           # Pinia 状态管理
│   │   ├── router/          # Vue Router 配置
│   │   ├── types/           # TypeScript 类型定义
│   │   └── utils/           # 工具函数
│   ├── package.json
│   └── vite.config.ts
├── .gitignore
├── LICENSE
└── README.md
```

## 核心特性详解

### 🎯 专业领域翻译（Domain-Specific Translation）

系统内置 **8 个专业领域**的专用翻译策略，针对不同行业的术语和表达习惯进行优化：

| 领域 | 标识 | 适用场景 |
|------|------|----------|
| **通用** | `general` | 日常文档、普通文本 |
| **医疗医学** | `medical` | 病历、医学论文、药品说明 |
| **计算机 IT** | `it` | 技术文档、API 文档、代码注释 |
| **法律法务** | `legal` | 合同、法律条款、诉讼文书 |
| **金融财经** | `finance` | 财报、审计报告、金融分析 |
| **工程技术** | `engineering` | 工程规范、技术手册、CAD 文档 |
| **学术科研** | `academic` | 论文、研究报告、学术期刊 |
| **商务商业** | `business` | 商业计划书、营销材料、商务邮件 |

**实现原理**：
- 领域提示词存储于 `prompts` 表，通过 `category` 字段标识领域
- 翻译时自动加载对应领域的系统提示词，与基础提示词拼接后发送给 AI
- 缓存机制避免重复查询数据库，提升性能

### 📖 双模式显示（Dual Display Modes）

翻译结果支持两种显示方式，适应不同使用场景：

#### 1️⃣ 替换模式（Replace Mode）
- **模式值**: `1`
- **效果**: 原文被译文完全替换
- **适用**: 正式文档交付、直接使用

#### 2️⃣ 对照模式（Parallel Mode）
- **模式值**: `2`
- **效果**: 原文在上，译文在下，译文带有蓝色虚线下划线
- **适用**: 学习对照、审校修改、语言学习

**技术实现**：
- Word 文档使用 `copy.deepcopy` 复制段落，避免元素引用问题
- 原文保持原有样式，译文添加蓝色虚线下划线样式（RGB: 0, 112, 192）
- 段落顺序：原文段 → 译文段 → 下一原文段 → 下一译文段...

### 🎨 现代化前端界面

- **步骤式交互**: 上传 → 配置 → 翻译 → 下载
- **可视化领域选择**: 8 个卡片式领域选项，带图标和描述
- **实时进度**: WebSocket 推送翻译进度，精确到段落级别
- **响应式设计**: 支持桌面和移动端浏览

---

## 快速开始

### 环境要求
- Python 3.10+
- Node.js 16+
- MySQL 8.0+

### 后端启动

1. **配置环境变量**
```bash
cd backend
cp .env.example .env
# 编辑 .env 文件，配置数据库连接和 API 密钥
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **初始化数据库**
```bash
# 方式1：使用 FastAPI 自动创建表（开发环境）
# 应用启动时会自动创建表

# 方式2：手动执行 SQL
mysql -u root -p < db/init.sql
```

4. **启动服务**
```bash
python run.py
# 或使用 uvicorn
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### 前端启动

```bash
cd frontend
npm install
npm run dev
```

### 访问地址
- **前端**: http://localhost:5173
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs （Swagger UI）
- **API 文档**: http://localhost:8000/redoc （ReDoc）

默认管理员: `admin` / `admin123`

## 功能截图

### 翻译主页
- 拖拽上传文档
- 配置翻译参数（语言、模型、线程数）
- 实时进度跟踪
- 下载翻译结果

### 翻译历史
- 分页查看所有翻译任务
- 筛选和搜索功能
- 任务状态和进度显示
- 下载和删除操作

### 管理功能
- 提示词管理（增删改查）
- 术语对照表管理（搜索、筛选）
- 系统配置查看

## API 接口文档

FastAPI 自动生成交互式 API 文档：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 主要端点

#### 认证接口
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/register` - 用户注册
- `GET /api/auth/me` - 获取当前用户信息

#### 翻译接口 ✅
- `POST /api/translate/upload` - 上传文件
- `POST /api/translate/start` - 开始翻译
- `GET /api/translate/list` - 翻译列表
- `GET /api/translate/{id}` - 翻译详情
- `GET /api/translate/{id}/progress` - 查询进度
- `GET /api/translate/{id}/download` - 下载结果
- `DELETE /api/translate/{id}` - 删除任务

#### 管理接口 ✅
- `GET /api/prompt/list` - 提示词列表
- `POST /api/prompt/create` - 创建提示词
- `PUT /api/prompt/{id}` - 更新提示词
- `DELETE /api/prompt/{id}` - 删除提示词
- `GET /api/comparison/list` - 术语对照表列表
- `GET /api/comparison/search` - 搜索术语
- `POST /api/comparison/create` - 创建术语
- `PUT /api/comparison/{id}` - 更新术语
- `DELETE /api/comparison/{id}` - 删除术语
- `GET /api/setting/list` - 系统配置

## FastAPI 核心特性

### 1. 类型提示
```python
@router.post("/login")
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    # 自动数据验证
    ...
```

### 2. 依赖注入
```python
@router.get("/users/me")
async def get_current_user(current_user: Customer = Depends(get_current_user)):
    # 自动认证
    ...
```

### 3. 自动文档
FastAPI 自动生成 OpenAPI 规范和交互式文档

### 4. 异步支持
```python
@router.post("/translate")
async def start_translate(task_id: int):
    # 异步处理
    ...
```

## 开发指南

### 代码规范
- **Python**: 遵循 PEP 8
- **类型注解**: 使用 Python 类型提示
- **Pydantic**: 所有请求/响应使用 Pydantic 模式
- **SQLAlchemy**: 使用 2.0 语法

### 添加新 API
1. 在 `schemas/` 定义 Pydantic 模式
2. 在 `models/` 定义数据模型（如需要）
3. 在 `resources/` 创建路由
4. 在主应用注册路由

### 翻译引擎开发
翻译引擎位于 `app/translate/`：
- `engine.py` - 翻译引擎核心
- `formatters/` - 格式处理器
- `ai/` - AI 翻译服务

## 环境变量说明

主要配置项（.env 文件）：

```bash
# 应用配置
APP_NAME=DocTranslator API
DEBUG=True

# 安全配置
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret

# 数据库配置
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/doc_translator

# AI 翻译配置
OPENAI_API_KEY=your-api-key
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo
```

## 部署说明

### 生产环境配置

1. **设置环境变量**
```bash
DEBUG=False
CORS_ORIGINS=["https://yourdomain.com"]
```

2. **使用生产级 ASGI 服务器**
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

3. **配置 Nginx 反向代理**
```nginx
location /api {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

## License

MIT License
