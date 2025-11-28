# 🧠 QA-Brain - 质量大脑

> QA 工程师的智能决策助手，解决"决策无记录"和"Bug 分析靠人工"的痛点

## 📋 项目简介

QA-Brain 是一款基于 RAG (Retrieval-Augmented Generation) 技术的智能质量管理平台，为 QA 工程师提供：

- **决策回溯**：记录和查询历史决策，支持快速搜索和状态管理
- **智能分析**：基于历史决策库的 Bug 智能分析，自动生成专业报告

## 🏗️ 技术架构

### 后端
- **框架**: FastAPI (Python 3.13)
- **AI 引擎**: LangGraph + LangChain
- **数据库**: MySQL (关系型) + Milvus (向量库)
- **对象存储**: MinIO
- **LLM**: Qwen3-Next-80B (私有化部署)

### 前端
- **框架**: React 18 + Vite + TypeScript
- **UI 库**: Ant Design 5.x + ProComponents
- **状态管理**: Zustand
- **数据请求**: TanStack Query (React Query)
- **Markdown 渲染**: react-markdown + rehype-highlight

## 🚀 快速开始

### 1. 环境准备

确保已安装以下服务：
- Python 3.13+
- Node.js 18+
- MySQL 8.0+
- Milvus 2.4+
- MinIO

### 2. 后端启动

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入实际配置

# 初始化服务 (创建数据库表、Milvus Collection、MinIO Bucket)
python backend/init_services.py

# 启动后端服务
python backend/main.py
```

后端服务将运行在 `http://localhost:8000`

### 3. 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端服务将运行在 `http://localhost:1314`

## 📖 API 文档

启动后端后，访问以下地址查看 API 文档：
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

### 核心接口

#### 决策管理
- `GET /api/decisions` - 获取决策列表
- `POST /api/decisions` - 创建新决策

#### 智能分析
- `POST /api/analyze` - 分析 Bug (触发 LangGraph 工作流)

#### 文件上传
- `POST /api/upload` - 上传文件到 MinIO

## 🎯 核心功能

### 1. 决策回溯
- ✅ 记录决策背景、结论、决策人
- ✅ 支持附件上传 (MinIO)
- ✅ 状态管理 (Active/Deprecated)
- ✅ 关键词搜索
- ✅ 自动向量化存储 (后台任务)

### 2. 智能分析
- ✅ LangGraph 工作流: Retrieve -> Grade -> Generate
- ✅ 向量检索相关历史决策
- ✅ 相关性评估 (避免幻觉)
- ✅ AI 生成 Markdown 格式报告
- ✅ 自动判定严重程度 (Blocker/Critical/Major/Minor/Trivial)
- ✅ 引用来源追溯

## 🔧 配置说明

### 环境变量 (.env)

```bash
# 数据库配置
MYSQL_HOST=192.168.80.81
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=123456
MYSQL_DATABASE=qa_brain

# Milvus 配置
MILVUS_HOST=192.168.4.168
MILVUS_PORT=19530

# MinIO 配置
MINIO_ENDPOINT=192.168.4.168:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# AI 模型配置
LLM_API_KEY=sk-6147fa558a704e43b2ae45671f595770
LLM_BASE_URL=http://192.168.22.31:8000/v1
LLM_MODEL=Qwen3-Next-80B-I-FP16

# Embedding 配置
EMBEDDING_API_URL=http://192.168.4.168:8083/embeddings
```

## 📂 项目结构

```
qa_brain/
├── backend/                 # 后端代码
│   ├── config.py           # 配置管理
│   ├── models.py           # 数据模型
│   ├── main.py             # FastAPI 主应用
│   ├── graph_agent.py      # LangGraph 工作流
│   ├── init_services.py    # 服务初始化脚本
│   └── utils/              # 工具类
│       ├── database.py     # 数据库连接
│       ├── vector_service.py   # Milvus 服务
│       ├── minio_service.py    # MinIO 服务
│       └── llm_service.py      # LLM 服务
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── pages/          # 页面组件
│   │   │   ├── Dashboard.tsx
│   │   │   ├── DecisionLog.tsx
│   │   │   └── AIAnalysis.tsx
│   │   ├── components/     # 公共组件
│   │   ├── services/       # API 服务
│   │   ├── store/          # 状态管理
│   │   └── types/          # TypeScript 类型
│   └── package.json
├── requirements.txt        # Python 依赖
└── README.md
```

## 🎨 界面预览

### 决策回溯页面
- 使用 ProTable 展示决策列表
- 支持按状态和关键词搜索
- 弹窗表单创建新决策

### 智能分析页面
- 左侧：输入框 + 历史记录
- 右侧：Markdown 格式的分析结果
- 实时 Loading 状态反馈

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

