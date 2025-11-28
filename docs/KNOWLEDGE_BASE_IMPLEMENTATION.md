# 🧠 知识库闭环与全量字段支持 - 实现文档

## 📋 概述

本次升级完善了 QA-Brain 的 RAG 闭环能力，实现了：

1. **缺陷知识库**：支持 Excel 导入和手动录入历史 Bug
2. **自动化决策入库**：决策创建时自动同步到向量数据库
3. **全量字段支持**：覆盖 QA 业务的所有关键属性

---

## 🎯 核心功能

### 1. 缺陷知识库 (Bug Repository)

#### 数据模型

```python
class BugRecord(Base):
    """历史缺陷知识库表"""
    # 核心描述 (用于向量化)
    summary: str              # 缺陷标题
    description: Text         # 详细描述/复现步骤
    root_cause: Text          # 问题原因 (关键知识)
    solution: Text            # 解决方案 (关键知识)
    impact_scope: str         # 影响范围
    
    # 业务属性 (用于 Metadata / 统计)
    reporter: str             # 报告人
    assignee: str             # 经办人/修复人
    severity: str             # 严重程度 (Critical/Major/Minor)
    category: str             # 缺陷分类 (功能/性能/UI/数据)
    affected_version: str     # 影响版本
    status: str               # 状态
    created_at: DateTime      # 创建日期
```

#### Excel 导入

**支持的列名映射**：

| Excel 列名 | 数据库字段 |
|-----------|-----------|
| 标题/摘要/缺陷标题 | summary |
| 描述/详细描述/复现步骤 | description |
| 原因/根因/问题原因 | root_cause |
| 解决方案/处理结果/修复方案 | solution |
| 影响范围 | impact_scope |
| 报告人/提交人 | reporter |
| 经办人/修复人/处理人 | assignee |
| 严重程度/优先级 | severity |
| 分类/缺陷分类/类型 | category |
| 影响版本/版本 | affected_version |
| 状态 | status |
| 创建时间/创建日期/提交时间 | created_at |

**使用流程**：

1. 点击"下载模板"获取 Excel 模板
2. 填写缺陷数据（支持中文表头）
3. 点击"Excel 导入"上传文件
4. 系统自动解析并批量导入
5. 后台异步建立向量索引

**API 端点**：

```http
GET  /api/knowledge/template/download  # 下载模板
POST /api/knowledge/upload/excel       # 上传 Excel
```

#### 手动录入

**表单字段**：

- 缺陷标题 (必填)
- 详细描述/复现步骤
- 问题原因
- 解决方案
- 影响范围
- 严重程度 (Critical/Major/Minor/Trivial)
- 缺陷分类 (功能/性能/UI/数据)
- 影响版本
- 报告人
- 经办人
- 状态 (Open/In Progress/Closed)

**API 端点**：

```http
POST /api/knowledge/bug  # 创建缺陷记录
GET  /api/knowledge/bugs # 获取缺陷列表
```

---

### 2. 自动化决策入库

#### 实现方式

在 `backend/main.py` 的 `create_decision` 和 `update_decision` 接口中：

```python
# 创建决策时
embedding_content = f"决策标题: {decision.title}\n背景: {decision.context}\n结论: {decision.verdict}"
metadata = {
    "source_type": "decision",
    "db_id": decision.id,
    "status": decision.status.value,
    "owner": decision.owner
}
background_tasks.add_task(
    vector_service.insert_knowledge,
    knowledge_id=decision.id,
    content=embedding_content,
    title=decision.title,
    source_type="decision",
    metadata=metadata
)
```

#### 向量化策略

**决策向量化**：
```
决策标题: {title}
背景: {context}
结论: {verdict}
```

**缺陷向量化**：
```
缺陷: {summary}
现象: {description}
根因: {root_cause}
解决: {solution}
```

---

### 3. 知识库统计

#### 统计指标

- **历史缺陷总数**：从 Excel 导入或手动录入的 Bug 数量
- **已索引决策数**：在决策回溯模块创建的决策数量
- **知识库总量**：缺陷 + 决策的总数
- **系统智商指数**：根据知识库数量计算的指标

#### 分布图表

1. **缺陷严重程度分布** (Pie Chart)
   - Critical / Major / Minor / Trivial

2. **缺陷分类分布** (Pie Chart)
   - 功能 / 性能 / UI / 数据

3. **各版本缺陷数量分布** (Pie Chart)
   - Top 10 版本

**API 端点**：

```http
GET /api/knowledge/stats  # 获取统计数据
```

---

## 🏗️ 技术架构

### 后端架构

```
backend/
├── models.py                      # 数据模型
│   └── BugRecord                  # 缺陷记录模型
├── services/
│   └── knowledge_service.py       # 知识库服务
│       ├── parse_excel()          # Excel 解析
│       ├── build_bug_embedding_text()  # 构建向量化文本
│       └── generate_excel_template()   # 生成模板
├── routers/
│   └── knowledge.py               # 知识库路由
│       ├── POST /upload/excel     # Excel 导入
│       ├── POST /bug              # 创建缺陷
│       ├── GET  /bugs             # 获取缺陷列表
│       └── GET  /stats            # 获取统计
└── utils/
    └── vector_service.py          # 向量服务
        └── insert_knowledge()     # 通用知识插入
```

### 前端架构

```
frontend/src/
├── pages/
│   └── KnowledgeBase/
│       ├── index.tsx              # 主页面 (Tabs)
│       ├── BugRepository.tsx      # 缺陷库管理
│       └── KnowledgeOverview.tsx  # 知识库概览
└── services/
    └── knowledgeApi.ts            # API 服务
```

---

## 📊 数据流程

### Excel 导入流程

```
1. 用户上传 Excel
   ↓
2. 后端解析 Excel (pandas)
   - 列名映射
   - 数据验证
   - 时间处理
   ↓
3. 批量插入 MySQL
   ↓
4. 后台任务：批量向量化
   - 构建向量化文本
   - 调用 Embedding API
   - 插入 Milvus
   ↓
5. 返回导入结果
```

### 决策自动入库流程

```
1. 用户创建决策
   ↓
2. 保存到 MySQL
   ↓
3. 后台任务：自动向量化
   - 构建向量化文本
   - 调用 Embedding API
   - 插入 Milvus
   ↓
4. 返回决策记录
```

### 智能分析检索流程

```
1. 用户提问
   ↓
2. 向量检索 (Milvus)
   - 检索相似决策 (Top 3)
   - 检索相似缺陷 (Top 3)
   ↓
3. LLM 分析
   - 优先引用决策
   - 参考历史缺陷的根因和解决方案
   ↓
4. 返回分析结果
```

---

## 🔧 配置说明

### 依赖安装

```bash
# 后端依赖
pip install pandas openpyxl python-multipart

# 或使用 requirements.txt
pip install -r backend/requirements.txt
```

### 数据库迁移

```python
# 创建 bug_records 表
from backend.models import Base, BugRecord
from backend.utils.database import engine

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

---

## 📝 使用指南

### 1. Excel 导入

**步骤**：

1. 访问"知识库管理"页面
2. 点击"下载模板"获取 Excel 模板
3. 填写缺陷数据（可使用中文表头）
4. 点击"Excel 导入"上传文件
5. 等待导入完成（后台建立索引）

**注意事项**：

- 标题字段为必填
- 支持历史时间导入（创建时间列）
- 建议填写根因和解决方案字段（关键知识）

### 2. 手动录入

**步骤**：

1. 访问"知识库管理"页面
2. 点击"手动录入"按钮
3. 填写表单（标题必填）
4. 点击"确定"保存

### 3. 查看统计

**步骤**：

1. 访问"知识库管理"页面
2. 切换到"知识库概览" Tab
3. 查看统计卡片和分布图表

---

## 🎯 最佳实践

### Excel 导入

1. **使用模板**：下载官方模板，避免列名错误
2. **填写完整**：尽量填写根因和解决方案字段
3. **批量导入**：一次导入多条记录，提高效率
4. **检查结果**：导入后检查错误信息

### 决策记录

1. **及时记录**：遇到重要决策立即记录
2. **详细描述**：背景和结论要详细
3. **自动入库**：无需手动操作，系统自动向量化

### 智能分析

1. **详细提问**：提供足够的上下文信息
2. **参考建议**：系统会引用历史决策和缺陷
3. **持续积累**：知识库越丰富，分析越准确

---

## 🐛 常见问题

### Q1: Excel 导入失败？

**A**: 检查以下几点：
- 文件格式是否为 .xlsx 或 .xls
- 是否包含"标题"列（必填）
- 列名是否使用支持的中文表头
- 查看错误信息详情

### Q2: 向量化失败？

**A**: 检查以下几点：
- Milvus 服务是否正常运行
- Embedding API 是否可访问
- 查看后端日志

### Q3: 智能分析找不到相关知识？

**A**: 可能原因：
- 知识库数据量不足
- 问题描述不够详细
- 向量化尚未完成（后台任务）

### Q4: 如何提高系统智商指数？

**A**: 
- 导入更多历史缺陷
- 记录更多决策
- 填写完整的根因和解决方案

---

## 📚 API 文档

### 知识库 API

```http
# 下载 Excel 模板
GET /api/knowledge/template/download

# 上传 Excel
POST /api/knowledge/upload/excel
Content-Type: multipart/form-data
Body: file (Excel 文件)

# 创建缺陷记录
POST /api/knowledge/bug
Content-Type: application/json
Body: {
  "summary": "缺陷标题",
  "description": "详细描述",
  "root_cause": "问题原因",
  "solution": "解决方案",
  ...
}

# 获取缺陷列表
GET /api/knowledge/bugs?severity=Critical&category=功能&limit=100

# 获取统计数据
GET /api/knowledge/stats
```

---

## 🎉 总结

本次升级实现了完整的知识库闭环：

1. ✅ **缺陷知识库**：Excel 导入 + 手动录入
2. ✅ **自动化入库**：决策创建时自动向量化
3. ✅ **全量字段**：覆盖 QA 业务所有属性
4. ✅ **统计分析**：多维度统计和可视化
5. ✅ **智能检索**：同时检索决策和缺陷

**系统现在具备了完整的知识积累和检索能力！** 🚀

