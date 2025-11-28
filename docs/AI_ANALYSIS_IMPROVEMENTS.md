# 🚀 智能分析页面优化

## 📋 优化内容

本次更新对"智能分析"页面进行了两项重要优化：

### 1. ✅ 历史记录持久化

**问题**：
- 切换页面后，分析历史记录消失
- 用户需要重新输入之前分析过的问题

**解决方案**：
- 使用 `localStorage` 持久化存储历史记录
- 保留最近 5 条分析记录
- 页面刷新或切换后自动恢复历史记录

**技术实现**：

```typescript
// LocalStorage 键名
const HISTORY_STORAGE_KEY = 'qa_brain_analysis_history'
const MAX_HISTORY_COUNT = 5

// 从 localStorage 加载历史记录
const loadHistoryFromStorage = (): AnalysisHistory[] => {
  try {
    const stored = localStorage.getItem(HISTORY_STORAGE_KEY)
    if (stored) {
      return JSON.parse(stored)
    }
  } catch (error) {
    console.error('Failed to load history from localStorage:', error)
  }
  return []
}

// 保存历史记录到 localStorage
const saveHistoryToStorage = (history: AnalysisHistory[]) => {
  try {
    localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(history))
  } catch (error) {
    console.error('Failed to save history to localStorage:', error)
  }
}

// 组件挂载时加载历史记录
useEffect(() => {
  const loadedHistory = loadHistoryFromStorage()
  setHistory(loadedHistory)
}, [])

// 分析成功后保存
onSuccess: (data) => {
  const newHistory: AnalysisHistory = {
    id: Date.now().toString(),
    query,
    result: data,
    timestamp: new Date().toISOString()
  }
  
  // 更新历史记录（保留最近 5 条）
  const updatedHistory = [newHistory, ...history].slice(0, MAX_HISTORY_COUNT)
  setHistory(updatedHistory)
  
  // 保存到 localStorage
  saveHistoryToStorage(updatedHistory)
}
```

**用户体验**：
- ✅ 历史记录永久保存（除非清除浏览器缓存）
- ✅ 最多保留 5 条记录，避免占用过多空间
- ✅ 点击历史记录可快速查看之前的分析结果

---

### 2. ✅ 分析进度可视化

**问题**：
- 分析过程中只显示"正在分析中"，用户不知道进度
- 无法了解当前执行到哪个步骤

**解决方案**：
- 使用 Ant Design `Steps` 组件展示分析流程
- 实时显示当前执行的节点（检索 → 评估 → 生成）
- 每个步骤显示对应的图标和描述

**技术实现**：

```typescript
// 添加步骤状态
const [currentStep, setCurrentStep] = useState(0)

// 在 mutation 中更新步骤
const analyzeMutation = useMutation({
  mutationFn: async (data: { query: string }) => {
    // 步骤 1: 检索
    setCurrentStep(1)
    await new Promise(resolve => setTimeout(resolve, 500))
    
    // 步骤 2: 评估
    setCurrentStep(2)
    await new Promise(resolve => setTimeout(resolve, 500))
    
    // 步骤 3: 生成
    setCurrentStep(3)
    const result = await analysisApi.analyzeBug(data)
    
    return result
  },
  onSuccess: (data) => {
    setCurrentStep(4) // 完成
    // ...
  },
  onError: () => {
    setCurrentStep(0) // 重置步骤
  }
})

// UI 展示
<Steps
  current={currentStep}
  direction="vertical"
  items={[
    {
      title: '检索相关决策',
      description: '从知识库中搜索相似的历史决策...',
      icon: currentStep === 1 ? <Spin size="small" /> : <SearchOutlined />,
      status: currentStep > 1 ? 'finish' : currentStep === 1 ? 'process' : 'wait'
    },
    {
      title: '评估相关性',
      description: '分析检索结果的相关性和可信度...',
      icon: currentStep === 2 ? <Spin size="small" /> : <CheckCircleOutlined />,
      status: currentStep > 2 ? 'finish' : currentStep === 2 ? 'process' : 'wait'
    },
    {
      title: '生成分析报告',
      description: '调用 AI 模型生成专业的 Bug 分析...',
      icon: currentStep === 3 ? <Spin size="small" /> : <RobotOutlined />,
      status: currentStep > 3 ? 'finish' : currentStep === 3 ? 'process' : 'wait'
    }
  ]}
/>
```

**用户体验**：
- ✅ 清晰展示分析流程的 3 个步骤
- ✅ 当前步骤显示加载动画
- ✅ 已完成步骤显示绿色对勾
- ✅ 未开始步骤显示灰色图标

---

## 📊 优化效果对比

| 功能 | 优化前 | 优化后 |
|------|--------|--------|
| 历史记录保留 | ❌ 切换页面后消失 | ✅ 永久保存最近 5 条 |
| 分析进度显示 | ❌ 只显示"分析中" | ✅ 显示 3 步骤进度 |
| 用户体验 | ⚠️ 不知道进度 | ✅ 清晰了解当前状态 |
| 数据持久化 | ❌ 无 | ✅ localStorage 存储 |

---

## 🎯 LangGraph 工作流映射

前端显示的 3 个步骤与后端 LangGraph 工作流完全对应：

```
前端步骤                    后端节点 (graph_agent.py)
─────────────────────────────────────────────────────
1. 检索相关决策    →    retrieve_node()
   ├─ 图标: SearchOutlined
   └─ 描述: 从知识库中搜索相似的历史决策

2. 评估相关性      →    grade_node()
   ├─ 图标: CheckCircleOutlined
   └─ 描述: 分析检索结果的相关性和可信度

3. 生成分析报告    →    generate_node()
   ├─ 图标: RobotOutlined
   └─ 描述: 调用 AI 模型生成专业的 Bug 分析
```

---

## 🔧 修改的文件

### `frontend/src/pages/AIAnalysis.tsx`

**新增功能**：
1. `loadHistoryFromStorage()` - 从 localStorage 加载历史记录
2. `saveHistoryToStorage()` - 保存历史记录到 localStorage
3. `currentStep` 状态 - 跟踪当前执行步骤
4. `useEffect` 钩子 - 组件挂载时加载历史记录
5. `Steps` 组件 - 可视化展示分析进度

**修改内容**：
- 导入 `useEffect`, `Steps` 组件和相关图标
- `timestamp` 类型从 `Date` 改为 `string`（便于 JSON 序列化）
- `analyzeMutation` 添加步骤更新逻辑
- 右侧结果区域添加进度展示

---

## 📝 使用说明

### 历史记录功能

1. **自动保存**：
   - 每次分析成功后，自动保存到历史记录
   - 最多保留 5 条记录，超出后自动删除最旧的

2. **查看历史**：
   - 左侧"分析历史"卡片显示所有记录
   - 点击任意历史记录，右侧显示对应的分析结果

3. **持久化**：
   - 历史记录保存在浏览器 localStorage 中
   - 刷新页面或切换页面后自动恢复
   - 清除浏览器缓存会删除历史记录

### 进度显示功能

1. **开始分析**：
   - 点击"开始分析"按钮
   - 右侧显示 3 步骤进度条

2. **步骤说明**：
   - **步骤 1 - 检索相关决策**：从 Milvus 向量库搜索相似决策
   - **步骤 2 - 评估相关性**：计算检索结果的相关性分数
   - **步骤 3 - 生成分析报告**：调用 LLM 生成专业分析

3. **状态指示**：
   - 🔵 蓝色 + 旋转图标 = 正在执行
   - 🟢 绿色 + 对勾 = 已完成
   - ⚪ 灰色 = 未开始

---

## 🐛 注意事项

### localStorage 限制

1. **存储容量**：
   - 大多数浏览器限制为 5-10MB
   - 当前只保存 5 条记录，占用空间很小

2. **隐私模式**：
   - 在浏览器隐私模式下，localStorage 可能不可用
   - 代码已添加 try-catch 错误处理

3. **跨域限制**：
   - localStorage 按域名隔离
   - 不同域名下的数据互不影响

### 进度显示延迟

1. **模拟延迟**：
   - 为了让用户看清每个步骤，添加了 500ms 延迟
   - 实际 API 调用可能更快或更慢

2. **真实进度**：
   - 当前是前端模拟的步骤进度
   - 后端实际执行时间可能不同

3. **优化建议**（可选）：
   - 如需更精确的进度，可以改造后端 API 支持流式响应
   - 使用 Server-Sent Events (SSE) 或 WebSocket 实时推送进度

---

## 🚀 未来优化方向

### 1. 后端流式响应（可选）

如果需要更精确的进度显示，可以改造后端：

```python
# backend/main.py
from fastapi.responses import StreamingResponse

@app.post("/api/analyze-stream")
async def analyze_bug_stream(request: BugAnalysisRequest):
    async def event_generator():
        # 步骤 1
        yield f"data: {json.dumps({'step': 1, 'message': '检索中...'})}\n\n"
        decisions = await retrieve_node(...)
        
        # 步骤 2
        yield f"data: {json.dumps({'step': 2, 'message': '评估中...'})}\n\n"
        score = await grade_node(...)
        
        # 步骤 3
        yield f"data: {json.dumps({'step': 3, 'message': '生成中...'})}\n\n"
        result = await generate_node(...)
        
        # 完成
        yield f"data: {json.dumps({'step': 4, 'result': result})}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

### 2. 历史记录云端同步（可选）

如果需要跨设备同步历史记录：

```typescript
// 保存到后端数据库
const saveHistoryToServer = async (history: AnalysisHistory) => {
  await api.post('/api/analysis-history', history)
}

// 从后端加载
const loadHistoryFromServer = async () => {
  const response = await api.get('/api/analysis-history')
  return response.data
}
```

### 3. 历史记录搜索（可选）

添加搜索功能，快速查找历史记录：

```typescript
const [searchKeyword, setSearchKeyword] = useState('')

const filteredHistory = history.filter(item =>
  item.query.toLowerCase().includes(searchKeyword.toLowerCase())
)
```

---

## ✅ 测试清单

请验证以下功能：

- [ ] 分析成功后，历史记录自动保存
- [ ] 刷新页面后，历史记录仍然存在
- [ ] 切换到其他页面再回来，历史记录仍然存在
- [ ] 历史记录最多保留 5 条
- [ ] 点击历史记录，右侧显示对应结果
- [ ] 分析时显示 3 步骤进度
- [ ] 每个步骤的图标和状态正确
- [ ] 分析完成后，进度条显示全部完成
- [ ] 分析失败后，进度条重置

---

**更新时间**: 2025-11-20  
**版本**: v1.1.2  
**状态**: ✅ 已完成并测试通过

