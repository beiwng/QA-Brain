# 🧪 Test Runner 使用指南（更新版）

## 📋 目录结构

Test Runner 支持灵活的目录结构，您可以将现有的自动化项目直接放入子系统目录。

### 推荐结构

```
backend/
└── test_workspace/              # 测试工作空间
    ├── search_system/          # 子系统 1（您的自动化项目）
    │   ├── test_case/          # 测试用例目录
    │   │   ├── test_*.py
    │   │   └── ...
    │   ├── test_report/        # 报告目录（自动生成）
    │   ├── myRunner.py         # 自定义执行脚本
    │   ├── conftest.py
    │   └── ...                 # 其他文件
    ├── trade_system/           # 子系统 2
    │   ├── test_case/
    │   ├── test_report/
    │   ├── myRunner.py
    │   └── ...
    └── example_system/         # 示例子系统
        ├── test_case/
        ├── test_report/
        ├── myRunner.py
        └── README.md
```

## 🎯 核心特性

### 1. 灵活的执行方式

Test Runner 支持两种执行方式：

#### 方式 A: 使用 myRunner.py（推荐）

如果子系统目录下存在 `myRunner.py`，Test Runner 会优先执行它。

**优点**：
- ✅ 完全自定义执行逻辑
- ✅ 无需修改现有脚本
- ✅ 支持任何测试框架
- ✅ 可以添加前置/后置处理

**示例**：
```python
# myRunner.py
import pytest
from datetime import datetime

# 生成报告文件名
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
html_report = f"test_report/report_{timestamp}.html"

# 执行 pytest
pytest.main([
    "test_case",
    f"--html={html_report}",
    "--self-contained-html",
    "-v"
])
```

#### 方式 B: 直接使用 pytest

如果没有 `myRunner.py`，Test Runner 会自动执行 `pytest test_case/`。

### 2. 自动报告管理

- 报告自动生成到子系统的 `test_report/` 目录
- 支持多种报告格式：HTML、XML、JSON
- 前端自动识别最新的 HTML 报告
- 点击"报告"按钮即可在线查看

### 3. 实时日志查看

- 实时捕获测试执行的控制台输出
- 日志统一存储在 `backend/logs/` 目录
- 支持轮询刷新（每 2 秒）
- 终端样式显示（黑色背景 + 绿色文字）

## 🚀 快速开始

### 步骤 1: 准备您的自动化项目

假设您有一个现有的自动化项目：

```
my_automation_project/
├── test_case/
│   ├── test_login.py
│   ├── test_search.py
│   └── ...
├── test_report/
├── myRunner.py
├── conftest.py
└── ...
```

### 步骤 2: 复制到 test_workspace

将整个项目复制到 `backend/test_workspace/` 目录下：

```bash
# Windows
xcopy /E /I my_automation_project backend\test_workspace\search_system

# Linux/Mac
cp -r my_automation_project backend/test_workspace/search_system
```

### 步骤 3: 确认目录结构

确保子系统目录包含以下之一：
- `myRunner.py` 文件
- `test_case/` 目录

### 步骤 4: 启动服务

```bash
# 启动后端
python -m uvicorn backend.main:app --reload

# 启动前端
cd frontend
npm run dev
```

### 步骤 5: 执行测试

1. 访问 `http://localhost:1314/test-runner`
2. 找到您的子系统卡片（如 `search_system`）
3. 点击"执行"按钮
4. 点击"日志"查看实时日志
5. 点击"报告"查看测试报告

## 📝 myRunner.py 编写指南

### 基础模板

```python
"""
自定义测试执行脚本
"""
import sys
from pathlib import Path

# 配置
current_dir = Path(__file__).resolve().parent
TEST_CASE_DIR = current_dir / "test_case"
TEST_REPORT_DIR = current_dir / "test_report"

# 确保目录存在
TEST_REPORT_DIR.mkdir(parents=True, exist_ok=True)


def run_tests():
    """执行测试"""
    import pytest
    from datetime import datetime
    
    # 生成报告文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_report = TEST_REPORT_DIR / f"report_{timestamp}.html"
    
    # pytest 参数
    pytest_args = [
        str(TEST_CASE_DIR),
        f"--html={html_report}",
        "--self-contained-html",
        "-v",
        "--tb=short"
    ]
    
    # 执行测试
    exit_code = pytest.main(pytest_args)
    
    print(f"\n📊 报告已生成: {html_report}")
    return exit_code


if __name__ == "__main__":
    sys.exit(run_tests())
```

### 高级示例：Pytest + Allure

```python
import pytest
import subprocess
from pathlib import Path
from datetime import datetime

current_dir = Path(__file__).resolve().parent
TEST_CASE_DIR = current_dir / "test_case"
TEST_REPORT_DIR = current_dir / "test_report"
ALLURE_RESULTS = TEST_REPORT_DIR / "allure-results"
ALLURE_REPORT = TEST_REPORT_DIR / "allure-report"

# 确保目录存在
for dir in [TEST_REPORT_DIR, ALLURE_RESULTS]:
    dir.mkdir(parents=True, exist_ok=True)


def run_tests():
    # 步骤 1: 执行 pytest 生成 Allure 数据
    print("🚀 执行测试...")
    pytest_args = [
        str(TEST_CASE_DIR),
        f"--alluredir={ALLURE_RESULTS}",
        "--clean-alluredir",
        "-v"
    ]
    exit_code = pytest.main(pytest_args)
    
    # 步骤 2: 生成 Allure HTML 报告
    if ALLURE_RESULTS.exists():
        print("\n📊 生成 Allure 报告...")
        subprocess.run([
            "allure", "generate",
            str(ALLURE_RESULTS),
            "-o", str(ALLURE_REPORT),
            "--clean"
        ])
        print(f"✅ 报告已生成: {ALLURE_REPORT}/index.html")
    
    return exit_code


if __name__ == "__main__":
    import sys
    sys.exit(run_tests())
```

### 高级示例：Playwright + pytest

```python
import pytest
from pathlib import Path
from datetime import datetime

current_dir = Path(__file__).resolve().parent
TEST_CASE_DIR = current_dir / "test_case"
TEST_REPORT_DIR = current_dir / "test_report"

# 确保目录存在
TEST_REPORT_DIR.mkdir(parents=True, exist_ok=True)


def run_tests():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_report = TEST_REPORT_DIR / f"report_{timestamp}.html"
    
    pytest_args = [
        str(TEST_CASE_DIR),
        f"--html={html_report}",
        "--self-contained-html",
        "--headed",                    # 显示浏览器
        "--browser=chromium",          # 使用 Chromium
        "--screenshot=only-on-failure", # 失败时截图
        "-v"
    ]
    
    return pytest.main(pytest_args)


if __name__ == "__main__":
    import sys
    sys.exit(run_tests())
```

## 🔍 常见问题

### Q1: 如何查看报告？

**A**: 点击子系统卡片的"报告"按钮，Test Runner 会自动打开最新的 HTML 报告。

报告访问路径：
```
http://localhost:8000/test_workspace/{子系统名}/test_report/{报告文件名}.html
```

### Q2: 报告没有生成怎么办？

**A**: 检查以下几点：
1. 确认 `myRunner.py` 中有生成报告的代码
2. 确认 `test_report/` 目录存在
3. 查看日志确认测试是否执行成功
4. 确认安装了报告生成工具（如 `pytest-html`）

### Q3: 如何支持多种报告格式？

**A**: 在 `myRunner.py` 中同时生成多种格式：

```python
pytest_args = [
    "test_case",
    "--html=test_report/report.html",           # HTML 报告
    "--junitxml=test_report/junit.xml",         # JUnit XML
    "--json-report",                            # JSON 报告
    "--json-report-file=test_report/report.json"
]
```

### Q4: 如何在 myRunner.py 中添加前置处理？

**A**: 在 `run_tests()` 函数前添加：

```python
def setup():
    """前置处理"""
    print("🔧 执行前置处理...")
    # 清理旧报告
    for old_report in TEST_REPORT_DIR.glob("*.html"):
        old_report.unlink()
    # 初始化环境
    # ...


def run_tests():
    setup()  # 调用前置处理
    # 执行测试
    # ...
```

### Q5: 如何传递参数给 myRunner.py？

**A**: 使用环境变量或命令行参数：

```python
import os
import sys

# 方式 1: 环境变量
env = os.getenv("TEST_ENV", "dev")
browser = os.getenv("BROWSER", "chrome")

# 方式 2: 命令行参数
if len(sys.argv) > 1:
    env = sys.argv[1]
```

在 Test Runner 中，可以修改 `backend/routers/test_runner.py` 的执行命令：

```python
test_cmd = ["python", "myRunner.py", "prod", "firefox"]
```

## 📊 报告格式支持

### HTML 报告（推荐）

```bash
pip install pytest-html
```

```python
pytest.main([
    "test_case",
    "--html=test_report/report.html",
    "--self-contained-html"
])
```

### Allure 报告

```bash
pip install allure-pytest
# 安装 Allure commandline (需要 Java)
```

```python
pytest.main([
    "test_case",
    "--alluredir=test_report/allure-results"
])

subprocess.run([
    "allure", "generate",
    "test_report/allure-results",
    "-o", "test_report/allure-report"
])
```

### JUnit XML 报告

```python
pytest.main([
    "test_case",
    "--junitxml=test_report/junit.xml"
])
```

## 🎯 最佳实践

1. **使用时间戳命名报告**
   ```python
   timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
   report_name = f"report_{timestamp}.html"
   ```

2. **清理旧报告**
   ```python
   # 只保留最近 10 个报告
   reports = sorted(TEST_REPORT_DIR.glob("*.html"), key=lambda x: x.stat().st_mtime)
   for old_report in reports[:-10]:
       old_report.unlink()
   ```

3. **添加错误处理**
   ```python
   try:
       exit_code = pytest.main(pytest_args)
   except Exception as e:
       print(f"❌ 执行失败: {e}")
       return 1
   ```

4. **输出详细信息**
   ```python
   print(f"📦 测试用例目录: {TEST_CASE_DIR}")
   print(f"📊 报告输出目录: {TEST_REPORT_DIR}")
   print(f"🔧 执行命令: pytest {' '.join(pytest_args)}")
   ```

## 📚 参考资料

- [Pytest 官方文档](https://docs.pytest.org/)
- [pytest-html 文档](https://pytest-html.readthedocs.io/)
- [Allure 官方文档](https://docs.qameta.io/allure/)
- [Playwright 官方文档](https://playwright.dev/)

---

**提示**: 查看 `backend/test_workspace/example_system/` 目录获取完整的示例代码。

