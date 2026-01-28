# 📄 DocTranslator - AI 文档翻译系统

## 项目愿景

DocTranslator 是一个基于 AI 的智能文档翻译系统，支持多种文档格式的高质量翻译，完美保持原文档的格式和排版。

## 核心功能

### 已实现功能
- [x] 用户认证与权限管理
- [x] 多格式文档翻译（Word、PDF、Excel、PPT、Markdown、TXT）
- [x] 文件上传与下载
- [x] 翻译任务管理与进度跟踪
- [x] 术语对照表管理
- [x] 翻译提示词管理
- [x] 系统配置管理

### 规划功能
- [ ] 批量翻译优化
- [ ] 翻译记忆功能
- [ ] OCR 图片识别翻译
- [ ] 实时协作编辑

## 技术栈

### 后端（FastAPI）
- **框架**: FastAPI + Uvicorn
- **数据库**: MySQL + SQLAlchemy 2.0
- **数据验证**: Pydantic v2
- **认证**: JWT (python-jose)
- **AI 翻译**: OpenAI 兼容 API
- **文档处理**: python-docx, openpyxl, python-pptx

### 前端
- **框架**: Vue 3 + Vite
- **状态管理**: Pinia
- **路由**: Vue Router
- **UI 组件**: Ant Design Vue
- **构建工具**: Vite

## 项目结构

```
doc-translator/
├── backend/                    # 后端代码
│   ├── app/                   # 应用代码（纯 Python）
│   │   ├── __init__.py       # FastAPI 主应用
│   │   ├── config.py         # 配置管理（Pydantic Settings）
│   │   ├── database.py       # 数据库连接与会话
│   │   ├── core/             # 核心模块
│   │   │   ├── security.py   # JWT/密码加密
│   │   │   └── deps.py       # 依赖注入
│   │   ├── models/           # SQLAlchemy 模型
│   │   ├── schemas/          # Pydantic 模式
│   │   ├── resources/        # API 路由（按功能分类）
│   │   ├── translate/        # 翻译引擎
│   │   └── utils/            # 工具函数
│   ├── db/                   # 数据库相关
│   │   ├── init.sql          # 数据库初始化脚本
│   │   ├── migrations/       # 数据库迁移文件
│   │   └── seeds/            # 种子数据
│   ├── storage/              # 文件存储目录
│   │   ├── uploads/          # 上传文件
│   │   └── translate/        # 翻译结果
│   ├── logs/                 # 日志文件目录
│   ├── requirements.txt      # Python 依赖
│   ├── .env.example          # 环境变量示例
│   ├── .gitignore            # Git 忽略规则
│   └── run.py               # 启动入口
├── frontend/                 # 前端代码
│   ├── src/
│   │   ├── main.ts          # 应用入口
│   │   ├── App.vue          # 根组件
│   │   ├── pages/           # 页面组件
│   │   ├── components/      # 通用组件
│   │   ├── api/             # API 封装
│   │   ├── store/           # Pinia 状态
│   │   ├── router/          # 路由配置
│   │   └── utils/           # 工具函数
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

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
