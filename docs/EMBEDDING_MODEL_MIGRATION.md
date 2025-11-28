# Embedding 模型迁移指南

## 📋 概述

本文档说明如何将 QA-Brain 的 Embedding 模型从旧模型迁移到新模型（Qwen3-Embedding-4B）。

---

## 🔄 变更内容

### 旧配置
```
EMBEDDING_API_URL=http://192.168.4.168:8083/embed
EMBEDDING_DIM=1024
```

### 新配置
```
EMBEDDING_MODEL_NAME=Qwen3-Embedding-4B
EMBEDDING_API_URL=http://192.168.22.31:9997/v1/embeddings
EMBEDDING_DIM=2560
```

### API 格式变更

**旧格式**（自定义）：
```bash
curl http://192.168.4.168:8083/embed \
  -H "Content-Type: application/json" \
  -d '{"input": "text"}'
```

**新格式**（OpenAI 兼容）：
```bash
curl http://192.168.22.31:9997/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "input": "The food was delicious and the waiter...",
    "model": "Qwen3-Embedding-4B",
    "encoding_format": "float"
  }'
```

**响应格式**（OpenAI 兼容）：
```json
{
  "object": "list",
  "data": [
    {
      "object": "embedding",
      "embedding": [0.123, -0.456, ...],
      "index": 0
    }
  ],
  "model": "Qwen3-Embedding-4B",
  "usage": {
    "prompt_tokens": 10,
    "total_tokens": 10
  }
}
```

---

## 🛠️ 迁移步骤

### 步骤 1：更新配置文件 ✅

您已经完成了这一步！配置文件已更新：
- `backend/config.py`
- `.env`
- `.env.example`

### 步骤 2：更新代码 ✅

我已经更新了以下文件：

1. **`backend/utils/vector_service.py`**
   - 修改 `get_embedding()` 方法以支持 OpenAI 兼容格式
   - 请求格式：`{"input": text, "model": model_name, "encoding_format": "float"}`
   - 响应解析：`data["data"][0]["embedding"]`

2. **`backend/config.py`**
   - 添加 `EMBEDDING_MODEL_NAME` 字段
   - 修复类型注解（`str` 而不是裸字符串）

3. **`backend/scripts/test_embedding_api.py`**
   - 添加 OpenAI 格式测试
   - 显示 Embedding 维度信息

### 步骤 3：检查 Milvus Collection 维度 ⚠️

**重要**：Milvus Collection 的 Embedding 维度必须与新模型匹配！

运行检查脚本：
```bash
python backend/scripts/rebuild_milvus_collection.py
```

脚本会：
1. 检查当前 Collection 的 Embedding 维度
2. 如果维度不匹配（1024 vs 2560），提示您重建 Collection
3. 如果选择重建，会删除旧 Collection（⚠️ 会丢失现有数据）

**输出示例**：
```
🔍 检查 Milvus Collection...
Collection 名称: qa_decisions
期望的 Embedding 维度: 2560
Embedding 模型: Qwen3-Embedding-4B

✅ 已连接到 Milvus: 192.168.4.168:19530

✅ Collection 'qa_decisions' 已存在
📊 Collection 统计:
   - 实体数量: 10

📋 Schema 信息:
   - id: DataType.INT64
   - embedding: DataType.FLOAT_VECTOR
     当前维度: 1024

⚠️ Embedding 维度不匹配！
   当前维度: 1024
   期望维度: 2560

需要重建 Collection 以使用新的 Embedding 模型
```

### 步骤 4：重建 Milvus Collection（如果需要）

如果维度不匹配，您有两个选择：

#### 选项 A：重建 Collection（推荐）

**优点**：
- 使用新模型，向量质量更好
- 维度匹配，不会出错

**缺点**：
- 会丢失现有的向量数据
- 需要重新导入历史数据

**操作**：
```bash
python backend/scripts/rebuild_milvus_collection.py
# 按提示输入 'yes' 确认
```

#### 选项 B：保留旧 Collection，只对新数据使用新模型

**优点**：
- 保留现有数据

**缺点**：
- 新旧数据使用不同的 Embedding 模型，检索效果可能不一致
- 需要手动管理两个 Collection

**操作**：
修改 `backend/config.py`，使用新的 Collection 名称：
```python
MILVUS_COLLECTION_NAME: str = "qa_decisions_v2"
```

### 步骤 5：测试 Embedding API

运行测试脚本：
```bash
python backend/scripts/test_embedding_api.py
```

**预期输出**：
```
🔍 测试 Embedding API: http://192.168.22.31:9997/v1/embeddings
📝 测试文本: 这是一个测试文本
🤖 模型名称: Qwen3-Embedding-4B

============================================================
测试格式 0 (OpenAI 兼容): {'input': 'text', 'model': '...', 'encoding_format': 'float'}
============================================================
状态码: 200
✅ 成功！响应格式: ['object', 'data', 'model', 'usage']
✅ Embedding 维度: 2560
✅ 前 5 个值: [0.123, -0.456, 0.789, ...]
响应示例: {'object': 'list', 'data': [{'object': 'embedding', 'embedding': [...], 'index': 0}], ...}

🎉 找到正确的格式: openai_format
```

### 步骤 6：启动后端服务

```bash
python -m uvicorn backend.main:app --reload --port 8000
```

**预期日志**：
```
✅ Connected to Milvus: 192.168.4.168:19530
✅ Milvus Collection 'qa_decisions' already exists
✅ Collection 'qa_decisions' loaded into memory
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 步骤 7：测试向量化功能

#### 测试 1：创建新决策

1. 访问前端：`http://localhost:1314`
2. 进入"决策回溯"页面
3. 创建一个新决策
4. 查看后端日志

**预期日志**：
```
✅ Embedding API 成功 (模型: Qwen3-Embedding-4B, 维度: 2560)
✅ Decision #123 inserted into Milvus
```

#### 测试 2：智能分析

1. 进入"智能分析"页面
2. 输入一个问题
3. 查看是否能检索到相关决策

**预期结果**：
- 能够检索到新创建的决策
- 分析结果中引用了相关决策

#### 测试 3：Excel 导入缺陷

1. 进入"知识库管理"页面
2. 下载 Excel 模板
3. 填写测试数据
4. 上传 Excel

**预期结果**：
- 导入成功
- 后台向量化成功
- 能在智能分析中检索到

---

## 🔧 故障排除

### 问题 1：422 Unprocessable Entity

**症状**：
```
❌ Embedding generation failed: Client error '422 Unprocessable Entity'
```

**原因**：
- API 请求格式不正确
- 模型名称错误

**解决方法**：
1. 运行测试脚本验证 API 格式
2. 检查 `EMBEDDING_MODEL_NAME` 是否正确
3. 检查 API URL 是否正确

---

### 问题 2：维度不匹配错误

**症状**：
```
❌ Dimension mismatch: expected 1024, got 2560
```

**原因**：
- Milvus Collection 的维度与新模型不匹配

**解决方法**：
运行重建脚本：
```bash
python backend/scripts/rebuild_milvus_collection.py
```

---

### 问题 3：连接超时

**症状**：
```
❌ Embedding generation failed: Connection timeout
```

**原因**：
- Embedding API 服务未启动
- 网络不通

**解决方法**：
1. 检查 API 服务是否运行
2. 使用 curl 测试连接
3. 检查防火墙设置

---

### 问题 4：数据库初始化失败

**症状**：
```
GET /api/knowledge/stats HTTP/1.1" 500 Internal Server Error
SELECT count(bug_records.id) FROM bug_records
ROLLBACK
```

**原因**：
- `bug_records` 表不存在

**解决方法**：
运行数据库初始化脚本：
```bash
python backend/scripts/init_database.py
```

---

## 📊 性能对比

### 旧模型
- 维度：1024
- 模型：未知
- API：自定义格式

### 新模型（Qwen3-Embedding-4B）
- 维度：2560
- 模型：Qwen3-Embedding-4B
- API：OpenAI 兼容格式
- 优势：
  - 更高的向量维度，表达能力更强
  - 更好的语义理解能力
  - 标准化的 API 格式，易于维护

---

## 📚 相关文档

- **快速开始指南**：`docs/KNOWLEDGE_BASE_QUICKSTART.md`
- **实现文档**：`docs/KNOWLEDGE_BASE_IMPLEMENTATION.md`
- **数据库脚本说明**：`backend/scripts/README.md`

---

## ✅ 检查清单

完成迁移后，请确认以下项目：

- [ ] 配置文件已更新（`.env`, `config.py`）
- [ ] Milvus Collection 维度已检查
- [ ] 如果需要，已重建 Collection
- [ ] Embedding API 测试通过
- [ ] 后端服务启动成功
- [ ] 创建新决策时向量化成功
- [ ] 智能分析能检索到新决策
- [ ] Excel 导入功能正常
- [ ] 知识库统计页面正常显示

---

## 🎉 完成

恭喜！您已成功迁移到新的 Embedding 模型！

如果遇到任何问题，请参考故障排除部分或联系技术支持。

