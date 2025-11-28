"""
数据库初始化脚本：创建所有表
运行方式：python backend/scripts/init_database.py
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from sqlalchemy import text
from backend.models import Base, BugRecord, Decision, BugInsight, DecisionVersion
from backend.utils.database import engine


async def check_table_exists(table_name: str) -> bool:
    """检查表是否存在"""
    async with engine.begin() as conn:
        result = await conn.execute(
            text(f"SHOW TABLES LIKE '{table_name}'")
        )
        return result.fetchone() is not None


async def create_all_tables():
    """创建所有表"""
    print("🔧 开始初始化数据库...")
    
    try:
        # 检查 bug_records 表是否存在
        bug_records_exists = await check_table_exists('bug_records')
        
        if bug_records_exists:
            print("✅ bug_records 表已存在")
        else:
            print("📝 创建 bug_records 表...")
            async with engine.begin() as conn:
                await conn.run_sync(BugRecord.__table__.create, checkfirst=True)
            print("✅ bug_records 表创建成功！")
        
        # 检查其他表
        tables_to_check = [
            ('decisions', Decision),
            ('bug_insights', BugInsight),
            ('decision_versions', DecisionVersion)
        ]
        
        for table_name, model in tables_to_check:
            exists = await check_table_exists(table_name)
            if exists:
                print(f"✅ {table_name} 表已存在")
            else:
                print(f"📝 创建 {table_name} 表...")
                async with engine.begin() as conn:
                    await conn.run_sync(model.__table__.create, checkfirst=True)
                print(f"✅ {table_name} 表创建成功！")
        
        print("\n🎉 数据库初始化完成！")
        print("\n表结构说明：")
        print("=" * 60)
        print("\n1. bug_records (历史缺陷知识库)")
        print("   - id: INT PRIMARY KEY AUTO_INCREMENT")
        print("   - summary: VARCHAR(500) NOT NULL (缺陷标题)")
        print("   - description: TEXT (详细描述)")
        print("   - root_cause: TEXT (问题原因)")
        print("   - solution: TEXT (解决方案)")
        print("   - impact_scope: VARCHAR(500) (影响范围)")
        print("   - reporter: VARCHAR(50) (报告人)")
        print("   - assignee: VARCHAR(50) (经办人)")
        print("   - severity: VARCHAR(50) (严重程度)")
        print("   - category: VARCHAR(50) (缺陷分类)")
        print("   - affected_version: VARCHAR(50) (影响版本)")
        print("   - status: VARCHAR(50) DEFAULT 'Closed' (状态)")
        print("   - created_at: DATETIME (创建时间)")
        print("   - updated_at: DATETIME (更新时间)")
        print("\n   索引：")
        print("   - idx_summary, idx_reporter, idx_assignee")
        print("   - idx_severity, idx_category, idx_version, idx_created")
        
        print("\n2. decisions (决策记录)")
        print("   - 存储项目决策和规范")
        
        print("\n3. bug_insights (智能分析记录)")
        print("   - 存储 AI 分析历史")
        
        print("\n4. decision_versions (决策版本)")
        print("   - 存储决策的历史版本")
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()
        raise


async def verify_tables():
    """验证表是否创建成功"""
    print("\n🔍 验证表结构...")
    
    try:
        async with engine.begin() as conn:
            # 获取所有表
            result = await conn.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result.fetchall()]
            
            print(f"\n当前数据库中的表 ({len(tables)} 个):")
            for table in sorted(tables):
                print(f"  ✓ {table}")
            
            # 检查 bug_records 表结构
            if 'bug_records' in tables:
                print("\n📋 bug_records 表结构:")
                result = await conn.execute(text("DESCRIBE bug_records"))
                for row in result.fetchall():
                    print(f"  {row[0]}: {row[1]} {row[2]} {row[3]}")
        
        print("\n✅ 表结构验证完成！")
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """主函数"""
    await create_all_tables()
    await verify_tables()
    
    # 关闭数据库连接
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

