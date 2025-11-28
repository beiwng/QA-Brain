# 数据库脚本说明

## 📋 脚本列表

### 1. `init_database.py` - 数据库初始化脚本（推荐）

**功能**：
- 创建所有必需的数据库表
- 检查表是否已存在，避免重复创建
- 验证表结构
- 显示详细的创建日志

**运行方式**：
```bash
# 方式 1: 从项目根目录运行
python backend/scripts/init_database.py

# 方式 2: 使用 Python 模块方式运行
python -m backend.scripts.init_database
```

**输出示例**：
```
🔧 开始初始化数据库...
📝 创建 bug_records 表...
✅ bug_records 表创建成功！
✅ decisions 表已存在
✅ bug_insights 表已存在
✅ decision_versions 表已存在

🎉 数据库初始化完成！

🔍 验证表结构...
当前数据库中的表 (4 个):
  ✓ bug_insights
  ✓ bug_records
  ✓ decision_versions
  ✓ decisions

✅ 表结构验证完成！
```

---

### 2. `create_bug_records_table.py` - 创建 bug_records 表

**功能**：
- 仅创建 `bug_records` 表
- 适用于已有其他表，只需添加缺陷知识库表的场景

**运行方式**：
```bash
# 方式 1: 从项目根目录运行
python backend/scripts/create_bug_records_table.py

# 方式 2: 使用 Python 模块方式运行
python -m backend.scripts.create_bug_records_table
```

---

## 🚀 快速开始

### 首次安装

如果是首次安装 QA-Brain v2.0，请按以下步骤操作：

1. **确保数据库服务正在运行**
   ```bash
   # 检查 MySQL 是否运行
   # Windows: 服务管理器中查看 MySQL 服务
   # Linux/Mac: systemctl status mysql
   ```

2. **配置数据库连接**
   
   确保 `backend/config.py` 或环境变量中配置了正确的数据库连接信息：
   ```python
   DATABASE_URL = "mysql+aiomysql://user:password@localhost:3306/qa_brain"
   ```

3. **运行初始化脚本**
   ```bash
   python backend/scripts/init_database.py
   ```

4. **验证结果**
   
   脚本会自动验证表是否创建成功，并显示表结构。

---

## 🔧 故障排除

### 问题 1: `ModuleNotFoundError: No module named 'backend'`

**原因**：Python 找不到 backend 模块

**解决方法**：
```bash
# 确保从项目根目录运行
cd d:\test_ai\myproject\qa_brain
python backend/scripts/init_database.py
```

---

### 问题 2: `sqlalchemy.exc.OperationalError: (2003, "Can't connect to MySQL server")`

**原因**：无法连接到 MySQL 数据库

**解决方法**：
1. 检查 MySQL 服务是否运行
2. 检查数据库连接配置是否正确
3. 检查防火墙设置

---

### 问题 3: `sqlalchemy.exc.ProgrammingError: (1007, "Can't create database 'qa_brain'; database exists")`

**原因**：数据库已存在

**解决方法**：
这不是错误！脚本会自动检查表是否存在，不会重复创建。

---

### 问题 4: 表已存在，想重新创建

**解决方法**：
```sql
-- 连接到 MySQL
mysql -u root -p

-- 删除表（谨慎操作！会丢失数据）
USE qa_brain;
DROP TABLE IF EXISTS bug_records;

-- 然后重新运行脚本
```

---

## 📊 表结构说明

### bug_records 表

| 字段名 | 类型 | 说明 | 索引 |
|--------|------|------|------|
| id | INT | 主键，自增 | PRIMARY |
| summary | VARCHAR(500) | 缺陷标题（必填） | YES |
| description | TEXT | 详细描述/复现步骤 | NO |
| root_cause | TEXT | 问题原因（关键知识） | NO |
| solution | TEXT | 解决方案（关键知识） | NO |
| impact_scope | VARCHAR(500) | 影响范围 | NO |
| reporter | VARCHAR(50) | 报告人 | YES |
| assignee | VARCHAR(50) | 经办人/修复人 | YES |
| severity | VARCHAR(50) | 严重程度 | YES |
| category | VARCHAR(50) | 缺陷分类 | YES |
| affected_version | VARCHAR(50) | 影响版本 | YES |
| status | VARCHAR(50) | 状态（默认 Closed） | NO |
| created_at | DATETIME | 创建时间 | YES |
| updated_at | DATETIME | 更新时间 | NO |

**索引列表**：
- `idx_summary` - 标题索引（用于搜索）
- `idx_reporter` - 报告人索引（用于过滤）
- `idx_assignee` - 经办人索引（用于过滤）
- `idx_severity` - 严重程度索引（用于统计）
- `idx_category` - 分类索引（用于统计）
- `idx_version` - 版本索引（用于统计）
- `idx_created` - 创建时间索引（用于排序）

---

## 🎯 最佳实践

1. **首次安装**：使用 `init_database.py` 创建所有表
2. **增量更新**：使用特定的表创建脚本（如 `create_bug_records_table.py`）
3. **定期备份**：在运行脚本前备份数据库
4. **测试环境**：先在测试环境验证，再在生产环境运行

---

## 📚 相关文档

- **快速开始指南**：`docs/KNOWLEDGE_BASE_QUICKSTART.md`
- **实现文档**：`docs/KNOWLEDGE_BASE_IMPLEMENTATION.md`
- **版本发布说明**：`docs/V2.0_RELEASE_NOTES.md`

---

## 🆘 需要帮助？

如果遇到问题，请：
1. 查看上面的故障排除部分
2. 检查数据库连接配置
3. 查看脚本输出的错误信息
4. 联系技术支持

