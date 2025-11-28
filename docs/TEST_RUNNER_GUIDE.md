# 🧪 Test Runner 使用指南

## 📋 功能概述

Test Runner 是 QA-Brain 的自动化测试调度中心，支持：

- ✅ 扫描和管理 Pytest + Playwright 测试套件
- ✅ 一键执行自动化测试
- ✅ 实时查看测试日志
- ✅ 在线预览 Allure 测试报告

---

## 🔧 系统依赖

### 必需依赖

在使用 Test Runner 之前，请确保已安装以下依赖：

#### 1. Python 依赖

```bash
pip install pytest playwright allure-pytest
playwright install
```

#### 2. Java JDK 1.8+

Allure 报告生成需要 Java 环境。

**检查 Java 版本**：
```bash
java -version
```

**安装 Java**：
- **Windows**: 下载并安装 [Oracle JDK](https://www.oracle.com/java/technologies/downloads/) 或 [OpenJDK](https://adoptium.net/)
- **Mac**: `brew install openjdk@11`
- **Linux**: `sudo apt install openjdk-11-jdk`

#### 3. Allure Commandline

**安装方法**：

- **Windows (使用 Scoop)**:
  ```bash
  scoop install allure
  ```

- **Mac (使用 Homebrew)**:
  ```bash
  brew install allure
  ```

- **Linux (手动安装)**:
  ```bash
  # 下载最新版本
  wget https://github.com/allure-framework/allure2/releases/download/2.24.0/allure-2.24.0.zip
  unzip allure-2.24.0.zip
  sudo mv allure-2.24.0 /opt/allure
  
  # 添加到 PATH
  echo 'export PATH="/opt/allure/bin:$PATH"' >> ~/.bashrc
  source ~/.bashrc
  ```

**验证安装**：
```bash
allure --version
```

---

## 📁 目录结构

Test Runner 使用以下目录结构：

```
backend/
├── test_workspace/          # 测试脚本目录
│   ├── conftest.py         # Pytest 全局配置
│   ├── trade_system/       # 交易系统测试套件
│   │   ├── test_trade_basic.py
│   │   └── test_trade_advanced.py
│   ├── user_system/        # 用户系统测试套件
│   │   └── test_user_management.py
│   └── ...                 # 其他测试套件
├── reports/                # 报告目录
│   ├── raw/                # Allure JSON 数据 (临时)
│   │   ├── trade_system/
│   │   └── user_system/
│   └── html/               # Allure HTML 报告 (最终)
│       ├── trade_system/
│       └── user_system/
└── logs/                   # 测试日志
    ├── trade_system.log
    └── user_system.log
```

---

## 🚀 快速开始

### 1. 创建测试套件

在 `backend/test_workspace/` 目录下创建子系统文件夹，并添加测试文件：

```bash
cd backend/test_workspace
mkdir my_system
cd my_system
```

创建测试文件 `test_example.py`：

```python
"""
示例测试套件
"""
import pytest
import time


class TestExample:
    """示例测试类"""
    
    def test_case_1(self):
        """测试用例 1"""
        print("执行测试用例 1...")
        time.sleep(1)
        assert True, "测试通过"
    
    def test_case_2(self):
        """测试用例 2"""
        print("执行测试用例 2...")
        time.sleep(1)
        assert True, "测试通过"
```

### 2. 启动后端服务

```bash
cd backend
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 启动前端服务

```bash
cd frontend
npm run dev
```

### 4. 访问 Test Runner

打开浏览器访问：
```
http://localhost:1314/test-runner
```

---

## 📖 使用说明

### 界面功能

#### 1. 测试套件卡片

每个测试套件显示为一个卡片，包含：

- **套件名称**: 子系统名称（如 `trade_system`）
- **状态标签**: 
  - 🟢 **空闲** - 未运行
  - 🔵 **运行中** - 正在执行
  - ✅ **已完成** - 执行成功
  - ❌ **失败** - 执行失败
- **测试用例数**: 该套件包含的测试文件数量
- **路径**: 测试套件的相对路径
- **最后运行时间**: 上次执行的时间

#### 2. 操作按钮

每个卡片提供三个操作按钮：

##### ▷ 执行

- 点击后立即开始执行测试
- 执行过程中按钮变为禁用状态
- 同一套件同时只能运行一个任务

##### 📄 日志

- 打开日志模态框
- 显示测试执行的实时控制台输出
- 如果测试正在运行，日志每 2 秒自动刷新
- 日志以终端样式显示（黑色背景，绿色文字）

##### 📊 报告

- 在新标签页中打开 Allure HTML 报告
- 报告包含详细的测试结果、统计图表、失败截图等
- 只有执行过测试后才会生成报告

### 工作流程

```
1. 点击"执行" → 2. 后台运行 Pytest → 3. 生成 Allure 数据 → 4. 生成 HTML 报告
                                    ↓
                              实时写入日志文件
```

---

## 🔍 API 接口

### 1. 获取测试套件列表

```http
GET /api/tests/suites
```

**响应示例**：
```json
[
  {
    "name": "trade_system",
    "path": "test_workspace/trade_system",
    "test_count": 2,
    "status": "idle",
    "last_run": "2025-11-20T10:30:00"
  }
]
```

### 2. 执行测试

```http
POST /api/tests/run
Content-Type: application/json

{
  "suite_name": "trade_system"
}
```

**响应示例**：
```json
{
  "status": "running",
  "log_file": "trade_system.log",
  "message": "Test suite 'trade_system' started successfully"
}
```

### 3. 获取日志

```http
GET /api/tests/logs?suite_name=trade_system&lines=100
```

**响应示例**：
```json
{
  "suite_name": "trade_system",
  "logs": "=== Test Execution Started at 2025-11-20 10:30:00 ===\n...",
  "is_running": true
}
```

### 4. 访问 Allure 报告

```
http://localhost:8000/reports/html/{suite_name}/index.html
```

---

## ⚙️ 高级配置

### 自定义 Pytest 配置

在 `backend/test_workspace/conftest.py` 中添加全局配置：

```python
import pytest
from playwright.sync_api import sync_playwright


@pytest.fixture(scope="session")
def browser():
    """Playwright 浏览器 fixture"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def page(browser):
    """页面 fixture"""
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()
```

### 添加 Allure 装饰器

使用 Allure 装饰器增强报告：

```python
import allure


@allure.feature("用户管理")
@allure.story("用户登录")
class TestUserLogin:
    
    @allure.title("测试正常登录")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_normal_login(self):
        with allure.step("打开登录页面"):
            print("打开登录页面...")
        
        with allure.step("输入用户名和密码"):
            print("输入凭证...")
        
        with allure.step("点击登录按钮"):
            print("点击登录...")
        
        assert True, "登录成功"
```

---

## 🐛 常见问题

### 1. Allure 报告生成失败

**错误信息**：
```
allure: command not found
```

**解决方案**：
- 确保已安装 Java JDK 1.8+
- 确保已安装 allure-commandline
- 确保 `allure` 命令在系统 PATH 中

**验证**：
```bash
java -version
allure --version
```

### 2. 测试执行失败

**错误信息**：
```
pytest: command not found
```

**解决方案**：
```bash
pip install pytest playwright allure-pytest
playwright install
```

### 3. 日志文件不存在

**错误信息**：
```
Log file for 'xxx' not found
```

**原因**：
- 测试套件从未执行过
- 日志文件被手动删除

**解决方案**：
- 先执行一次测试
- 检查 `backend/logs/` 目录权限

### 4. 报告页面打不开

**错误信息**：
```
404 Not Found
```

**原因**：
- 测试执行失败，未生成报告
- Allure 生成报告失败

**解决方案**：
- 查看日志确认测试是否成功执行
- 确认 `backend/reports/html/{suite_name}/` 目录存在
- 手动运行 `allure generate` 命令测试

### 5. 并发执行冲突

**错误信息**：
```
Test suite 'xxx' is already running
```

**原因**：
- 同一套件已有任务在运行

**解决方案**：
- 等待当前任务完成
- 或者在后端手动终止进程

---

## 📊 最佳实践

### 1. 测试套件组织

按子系统或功能模块组织测试：

```
test_workspace/
├── trade_system/       # 交易系统
├── user_system/        # 用户系统
├── payment_system/     # 支付系统
└── report_system/      # 报表系统
```

### 2. 测试命名规范

- 测试文件：`test_*.py`
- 测试类：`Test*`
- 测试方法：`test_*`

### 3. 使用 Fixtures

在 `conftest.py` 中定义可复用的 fixtures：

```python
@pytest.fixture(scope="session")
def test_config():
    """测试配置"""
    return {
        "base_url": "https://example.com",
        "timeout": 30
    }
```

### 4. 添加测试标记

使用 pytest markers 分类测试：

```python
@pytest.mark.smoke
def test_critical_feature():
    """冒烟测试"""
    pass

@pytest.mark.regression
def test_full_feature():
    """回归测试"""
    pass
```

执行特定标记的测试：
```bash
pytest -m smoke
```

---

## 🎯 未来优化方向

- [ ] 支持定时任务（Cron 表达式）
- [ ] 支持测试结果通知（邮件/钉钉/企业微信）
- [ ] 支持测试历史记录查询
- [ ] 支持测试报告对比
- [ ] 支持分布式测试执行
- [ ] 支持测试用例管理（导入/导出）

---

**文档版本**: v1.0.0  
**最后更新**: 2025-11-20  
**维护者**: QA-Brain Team

