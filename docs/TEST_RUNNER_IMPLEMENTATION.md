# 🧪 Test Runner 实现文档

## 📋 实现概述

本文档详细说明 Test Runner (自动化测试调度中心) 的技术实现细节。

---

## 🏗️ 架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Suite Cards  │  │  Log Modal   │  │ Report View  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │ HTTP/REST API
┌─────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Test Router  │  │ Task Manager │  │ Static Files │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                    Test Execution Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │    Pytest    │  │  Playwright  │  │    Allure    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### 数据流

```
1. 用户点击"执行" 
   → POST /api/tests/run
   → 创建异步任务
   → 立即返回 "running" 状态

2. 后台执行 pytest
   → 实时写入日志文件
   → 生成 Allure JSON 数据
   → 生成 Allure HTML 报告

3. 前端轮询
   → GET /api/tests/suites (每 3 秒)
   → GET /api/tests/logs (每 2 秒，仅在查看日志时)
   → 更新 UI 状态
```

---

## 🔧 后端实现

### 1. 目录结构

```python
BASE_DIR = Path(__file__).resolve().parent.parent
TEST_WORKSPACE = BASE_DIR / "test_workspace"      # 测试脚本
REPORTS_RAW_DIR = REPORTS_DIR / "raw"             # Allure JSON
REPORTS_HTML_DIR = REPORTS_DIR / "html"           # Allure HTML
LOGS_DIR = BASE_DIR / "logs"                      # 测试日志
```

### 2. 核心函数

#### scan_test_suites()

扫描测试套件目录，识别所有包含 `test_*.py` 的子目录。

```python
def scan_test_suites() -> List[TestSuite]:
    suites = []
    for item in TEST_WORKSPACE.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            test_files = list(item.glob("test_*.py"))
            if test_files:
                suites.append(TestSuite(
                    name=item.name,
                    path=str(item.relative_to(BASE_DIR)),
                    test_count=len(test_files),
                    status=task_status.get(item.name, {}).get("status", "idle")
                ))
    return suites
```

**关键点**：
- 动态扫描，不硬编码测试套件名称
- 只识别包含测试文件的目录
- 从全局状态字典获取运行状态

#### run_pytest_async()

异步执行 pytest 命令，实时捕获输出。

```python
async def run_pytest_async(suite_name: str):
    # 1. 构建 pytest 命令
    pytest_cmd = [
        "pytest",
        str(suite_path),
        f"--alluredir={raw_report_dir}",
        "--clean-alluredir",
        "-v",
        "--tb=short"
    ]
    
    # 2. 创建子进程
    process = await asyncio.create_subprocess_exec(
        *pytest_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        cwd=str(BASE_DIR)
    )
    
    # 3. 实时读取输出
    while True:
        line = await process.stdout.readline()
        if not line:
            break
        decoded_line = line.decode('utf-8', errors='ignore')
        log.write(decoded_line)
        log.flush()
    
    # 4. 等待进程结束
    await process.wait()
    
    # 5. 生成 Allure 报告
    allure_cmd = [
        "allure", "generate",
        str(raw_report_dir),
        "-o", str(html_report_dir),
        "--clean"
    ]
    allure_process = await asyncio.create_subprocess_exec(...)
```

**关键点**：
- 使用 `asyncio.create_subprocess_exec` 实现非阻塞
- 合并 stdout 和 stderr 到一个流
- 实时写入日志文件并 flush
- 执行完成后自动生成 Allure 报告

### 3. API 端点

#### GET /api/tests/suites

```python
@router.get("/suites", response_model=List[TestSuite])
async def get_test_suites():
    suites = scan_test_suites()
    return suites
```

#### POST /api/tests/run

```python
@router.post("/run", response_model=RunTestResponse)
async def run_tests(request: RunTestRequest):
    suite_name = request.suite_name
    
    # 并发控制
    if suite_name in running_tasks and not running_tasks[suite_name].done():
        raise HTTPException(status_code=409, detail="Already running")
    
    # 创建异步任务
    task = asyncio.create_task(run_pytest_async(suite_name))
    running_tasks[suite_name] = task
    
    return RunTestResponse(
        status="running",
        log_file=f"{suite_name}.log",
        message="Started successfully"
    )
```

**关键点**：
- 立即返回，不等待测试完成
- 使用全局字典管理任务状态
- 并发控制：同一套件只能运行一个任务

#### GET /api/tests/logs

```python
@router.get("/logs", response_model=LogResponse)
async def get_test_logs(suite_name: str, lines: int = 100):
    log_file = LOGS_DIR / f"{suite_name}.log"
    
    with open(log_file, "r", encoding="utf-8") as f:
        all_lines = f.readlines()
    
    last_lines = all_lines[-lines:]
    logs_content = "".join(last_lines)
    
    is_running = suite_name in running_tasks and not running_tasks[suite_name].done()
    
    return LogResponse(
        suite_name=suite_name,
        logs=logs_content,
        is_running=is_running
    )
```

**关键点**：
- 只返回最后 N 行（默认 100）
- 返回是否正在运行的状态
- 前端根据状态决定是否继续轮询

### 4. 静态文件挂载

```python
# main.py
from fastapi.staticfiles import StaticFiles

REPORTS_DIR = Path(__file__).resolve().parent / "reports"
app.mount("/reports", StaticFiles(directory=str(REPORTS_DIR)), name="reports")
```

**访问方式**：
```
http://localhost:8000/reports/html/{suite_name}/index.html
```

---

## 🎨 前端实现

### 1. 组件结构

```tsx
TestRunner
├── 页面标题 + 刷新按钮
├── 测试套件列表 (Row/Col Grid)
│   └── 测试套件卡片 (Card)
│       ├── 标题 (名称 + 状态图标)
│       ├── 状态标签 (Tag)
│       ├── 卡片内容 (用例数、路径、最后运行时间)
│       └── 操作按钮 (执行、日志、报告)
└── 日志模态框 (Modal)
    ├── 标题 (套件名 + 运行状态)
    ├── 日志内容 (终端样式)
    └── 刷新提示
```

### 2. 数据管理

使用 TanStack Query 管理数据和轮询：

```tsx
// 查询测试套件列表
const { data: suites = [], isLoading, refetch } = useQuery({
  queryKey: ['testSuites'],
  queryFn: testRunnerApi.getSuites,
  refetchInterval: 3000 // 每 3 秒自动刷新
})

// 运行测试 Mutation
const runTestMutation = useMutation({
  mutationFn: testRunnerApi.runTest,
  onSuccess: (data, suiteName) => {
    message.success(`测试套件 "${suiteName}" 已开始执行`)
    queryClient.invalidateQueries({ queryKey: ['testSuites'] })
  }
})
```

### 3. 日志轮询

使用 useEffect 实现日志轮询：

```tsx
useEffect(() => {
  if (!logModalVisible || !currentSuite) return

  const fetchLogs = async () => {
    const response = await testRunnerApi.getLogs(currentSuite)
    setLogs(response.logs)
    setIsLogRunning(response.is_running)
  }

  fetchLogs() // 立即获取一次
  const interval = setInterval(fetchLogs, 2000) // 每 2 秒轮询

  return () => clearInterval(interval)
}, [logModalVisible, currentSuite])
```

**关键点**：
- 只在模态框打开时轮询
- 清理函数清除定时器
- 根据 `is_running` 状态决定是否继续轮询

### 4. 状态显示

```tsx
// 状态图标
const getStatusIcon = (status: string) => {
  switch (status) {
    case 'running': return <LoadingOutlined style={{ color: '#1890ff' }} />
    case 'completed': return <CheckCircleOutlined style={{ color: '#52c41a' }} />
    case 'failed': return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
    default: return <ClockCircleOutlined style={{ color: '#d9d9d9' }} />
  }
}

// 状态标签
const getStatusTag = (status: string) => {
  const config = {
    idle: { color: 'default', text: '空闲' },
    running: { color: 'processing', text: '运行中' },
    completed: { color: 'success', text: '已完成' },
    failed: { color: 'error', text: '失败' }
  }
  return <Tag color={config[status].color}>{config[status].text}</Tag>
}
```

### 5. 日志样式

终端样式的日志显示：

```tsx
<div
  style={{
    backgroundColor: '#1e1e1e',  // 黑色背景
    color: '#00ff00',            // 绿色文字
    padding: 16,
    borderRadius: 4,
    fontFamily: 'Consolas, Monaco, monospace',
    fontSize: 12,
    maxHeight: 500,
    overflow: 'auto',
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-all'
  }}
>
  {logs || '暂无日志内容'}
</div>
```

---

## 🔄 工作流程

### 完整执行流程

```
1. 用户点击"执行"按钮
   ↓
2. 前端调用 POST /api/tests/run
   ↓
3. 后端创建异步任务
   ↓
4. 立即返回 "running" 状态
   ↓
5. 后台执行 pytest
   ├─ 实时写入日志文件
   ├─ 生成 Allure JSON 数据
   └─ 生成 Allure HTML 报告
   ↓
6. 前端轮询更新状态
   ├─ GET /api/tests/suites (每 3 秒)
   └─ GET /api/tests/logs (每 2 秒，仅在查看日志时)
   ↓
7. 测试完成，状态更新为 "completed" 或 "failed"
   ↓
8. 用户点击"报告"查看 Allure HTML
```

### 状态转换

```
idle (空闲)
  ↓ 点击"执行"
running (运行中)
  ↓ 测试完成
completed (已完成) / failed (失败)
  ↓ 再次点击"执行"
running (运行中)
  ...
```

---

## 🎯 关键技术点

### 1. 异步非阻塞执行

**问题**：pytest 执行时间可能很长（几分钟到几小时），不能阻塞 API 请求。

**解决方案**：
- 使用 `asyncio.create_subprocess_exec` 创建子进程
- 立即返回响应，不等待测试完成
- 使用全局字典管理任务状态

### 2. 实时日志捕获

**问题**：需要实时捕获 pytest 的 stdout/stderr 输出。

**解决方案**：
- 使用 `asyncio.subprocess.PIPE` 捕获输出
- 使用 `readline()` 逐行读取
- 实时写入日志文件并 `flush()`

### 3. 并发控制

**问题**：同一测试套件不能同时运行多个任务。

**解决方案**：
- 使用全局字典 `running_tasks` 存储任务引用
- 执行前检查任务是否存在且未完成
- 如果已有任务运行，返回 409 错误

### 4. 状态管理

**问题**：需要跨请求共享任务状态。

**解决方案**：
- 使用全局字典 `task_status` 存储状态
- 包含：status, start_time, end_time, exit_code 等
- 生产环境建议使用 Redis

### 5. 静态文件服务

**问题**：Allure HTML 报告包含大量静态资源（JS/CSS/图片）。

**解决方案**：
- 使用 FastAPI `StaticFiles` 挂载整个 reports 目录
- 自动处理 CORS 和 MIME 类型
- 支持目录浏览和索引文件

---

## 📊 性能优化

### 1. 日志文件大小控制

**问题**：长时间运行的测试可能产生巨大的日志文件。

**优化方案**：
- 只返回最后 N 行（默认 100）
- 定期清理旧日志文件
- 使用日志轮转（logrotate）

### 2. 轮询频率优化

**问题**：频繁轮询可能增加服务器负载。

**优化方案**：
- 套件列表：3 秒轮询（可接受）
- 日志内容：2 秒轮询（仅在查看时）
- 考虑使用 WebSocket 实现实时推送

### 3. 报告文件清理

**问题**：Allure 报告文件会不断累积。

**优化方案**：
- 定期清理旧报告（如保留最近 10 次）
- 使用 `--clean-alluredir` 清理旧数据
- 考虑使用对象存储（如 MinIO）

---

## 🔒 安全考虑

### 1. 路径遍历攻击

**风险**：用户可能通过 `suite_name` 参数访问任意文件。

**防护措施**：
- 验证 `suite_name` 只包含字母、数字、下划线
- 使用 `Path.resolve()` 规范化路径
- 检查路径是否在 `TEST_WORKSPACE` 内

### 2. 命令注入

**风险**：恶意用户可能注入 shell 命令。

**防护措施**：
- 使用 `subprocess` 的列表参数形式（不使用 shell=True）
- 不拼接用户输入到命令字符串
- 验证所有参数

### 3. 资源耗尽

**风险**：恶意用户可能启动大量测试任务。

**防护措施**：
- 限制并发任务数量
- 添加用户认证和授权
- 设置任务超时时间

---

## 🐛 已知限制

### 1. 状态持久化

**限制**：当前使用内存存储，服务重启后状态丢失。

**改进方案**：
- 使用 Redis 存储任务状态
- 使用数据库存储历史记录

### 2. 分布式执行

**限制**：当前只支持单机执行。

**改进方案**：
- 使用 Celery 实现分布式任务队列
- 使用 Kubernetes Job 执行测试

### 3. 实时通知

**限制**：当前需要手动刷新查看状态。

**改进方案**：
- 使用 WebSocket 实现实时推送
- 集成邮件/钉钉/企业微信通知

---

## 📚 参考资料

- [Pytest 官方文档](https://docs.pytest.org/)
- [Playwright 官方文档](https://playwright.dev/)
- [Allure 官方文档](https://docs.qameta.io/allure/)
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [TanStack Query 官方文档](https://tanstack.com/query/)

---

**文档版本**: v1.0.0  
**最后更新**: 2025-11-20  
**作者**: QA-Brain Team

