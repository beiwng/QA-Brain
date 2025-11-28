"""
数据库迁移脚本：创建 bug_records 表
运行方式：python -m backend.scripts.create_bug_records_table
"""
import asyncio
from backend.models import Base, BugRecord
from backend.utils.database import engine


async def create_bug_records_table():
    """创建 bug_records 表"""
    print("🔧 开始创建 bug_records 表...")
    
    try:
        async with engine.begin() as conn:
            # 只创建 BugRecord 表
            await conn.run_sync(BugRecord.__table__.create, checkfirst=True)
        
        print("✅ bug_records 表创建成功！")
        print("\n表结构：")
        print("- id: INT PRIMARY KEY AUTO_INCREMENT")
        print("- summary: VARCHAR(500) NOT NULL (缺陷标题)")
        print("- description: TEXT (详细描述)")
        print("- root_cause: TEXT (问题原因)")
        print("- solution: TEXT (解决方案)")
        print("- impact_scope: VARCHAR(500) (影响范围)")
        print("- reporter: VARCHAR(50) (报告人)")
        print("- assignee: VARCHAR(50) (经办人)")
        print("- severity: VARCHAR(50) (严重程度)")
        print("- category: VARCHAR(50) (缺陷分类)")
        print("- affected_version: VARCHAR(50) (影响版本)")
        print("- status: VARCHAR(50) DEFAULT 'Closed' (状态)")
        print("- created_at: DATETIME (创建时间)")
        print("- updated_at: DATETIME (更新时间)")
        print("\n索引：")
        print("- idx_summary (summary)")
        print("- idx_reporter (reporter)")
        print("- idx_assignee (assignee)")
        print("- idx_severity (severity)")
        print("- idx_category (category)")
        print("- idx_version (affected_version)")
        print("- idx_created (created_at)")
        
    except Exception as e:
        print(f"❌ 创建表失败: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(create_bug_records_table())

