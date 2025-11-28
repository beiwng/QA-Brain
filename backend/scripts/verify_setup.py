"""
验证 QA-Brain 系统配置
运行方式：python backend/scripts/verify_setup.py
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import httpx
from pymilvus import connections, utility, Collection
from sqlalchemy import text
from backend.config import settings
from backend.utils.database import engine


async def check_mysql():
    """检查 MySQL 连接和表"""
    print("=" * 60)
    print("1️⃣ 检查 MySQL 数据库")
    print("=" * 60)
    
    try:
        async with engine.begin() as conn:
            # 检查连接
            result = await conn.execute(text("SELECT VERSION()"))
            version = result.scalar()
            print(f"✅ MySQL 连接成功")
            print(f"   版本: {version}")
            
            # 检查数据库
            result = await conn.execute(text("SELECT DATABASE()"))
            db_name = result.scalar()
            print(f"   数据库: {db_name}")
            
            # 检查表
            result = await conn.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result.fetchall()]
            print(f"   表数量: {len(tables)}")
            
            required_tables = ['decisions', 'bug_insights', 'bug_records', 'decision_versions']
            for table in required_tables:
                if table in tables:
                    # 获取表的记录数
                    result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    print(f"   ✅ {table}: {count} 条记录")
                else:
                    print(f"   ❌ {table}: 不存在")
            
            print()
            return True
    
    except Exception as e:
        print(f"❌ MySQL 检查失败: {e}")
        print()
        return False


def check_milvus():
    """检查 Milvus 连接和 Collection"""
    print("=" * 60)
    print("2️⃣ 检查 Milvus 向量数据库")
    print("=" * 60)
    
    try:
        # 连接到 Milvus
        connections.connect(
            alias="default",
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
            user=settings.MILVUS_USER,
            password=settings.MILVUS_PASSWORD
        )
        print(f"✅ Milvus 连接成功")
        print(f"   地址: {settings.MILVUS_HOST}:{settings.MILVUS_PORT}")
        
        # 检查 Collection
        if utility.has_collection(settings.MILVUS_COLLECTION_NAME):
            collection = Collection(settings.MILVUS_COLLECTION_NAME)
            schema = collection.schema
            
            print(f"✅ Collection '{settings.MILVUS_COLLECTION_NAME}' 已存在")
            print(f"   实体数量: {collection.num_entities}")
            
            # 检查 Embedding 维度
            for field in schema.fields:
                if field.name == "embedding":
                    if hasattr(field, 'params') and 'dim' in field.params:
                        current_dim = field.params['dim']
                        print(f"   Embedding 维度: {current_dim}")
                        
                        if current_dim == settings.EMBEDDING_DIM:
                            print(f"   ✅ 维度匹配 ({current_dim} == {settings.EMBEDDING_DIM})")
                        else:
                            print(f"   ❌ 维度不匹配 ({current_dim} != {settings.EMBEDDING_DIM})")
                            print(f"   请运行: python backend/scripts/rebuild_milvus_collection.py")
                            return False
        else:
            print(f"⚠️ Collection '{settings.MILVUS_COLLECTION_NAME}' 不存在")
            print(f"   启动后端服务时会自动创建")
        
        print()
        return True
    
    except Exception as e:
        print(f"❌ Milvus 检查失败: {e}")
        print()
        return False


async def check_embedding_api():
    """检查 Embedding API"""
    print("=" * 60)
    print("3️⃣ 检查 Embedding API")
    print("=" * 60)
    
    try:
        print(f"API URL: {settings.EMBEDDING_API_URL}")
        print(f"模型: {settings.EMBEDDING_MODEL_NAME}")
        print(f"期望维度: {settings.EMBEDDING_DIM}")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                settings.EMBEDDING_API_URL,
                json={
                    "input": "测试文本",
                    "model": settings.EMBEDDING_MODEL_NAME,
                    "encoding_format": "float"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and len(data["data"]) > 0:
                    embedding = data["data"][0]["embedding"]
                    print(f"✅ Embedding API 正常")
                    print(f"   实际维度: {len(embedding)}")
                    
                    if len(embedding) == settings.EMBEDDING_DIM:
                        print(f"   ✅ 维度匹配 ({len(embedding)} == {settings.EMBEDDING_DIM})")
                    else:
                        print(f"   ❌ 维度不匹配 ({len(embedding)} != {settings.EMBEDDING_DIM})")
                        print(f"   请检查配置文件中的 EMBEDDING_DIM")
                        return False
                else:
                    print(f"❌ 响应格式错误: {list(data.keys())}")
                    return False
            else:
                print(f"❌ API 请求失败: {response.status_code}")
                print(f"   响应: {response.text[:200]}")
                return False
        
        print()
        return True
    
    except Exception as e:
        print(f"❌ Embedding API 检查失败: {e}")
        print()
        return False


async def check_llm_api():
    """检查 LLM API"""
    print("=" * 60)
    print("4️⃣ 检查 LLM API")
    print("=" * 60)
    
    try:
        print(f"API URL: {settings.LLM_BASE_URL}")
        print(f"模型: {settings.LLM_MODEL}")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{settings.LLM_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {settings.LLM_API_KEY}"},
                json={
                    "model": settings.LLM_MODEL,
                    "messages": [{"role": "user", "content": "Hello"}],
                    "max_tokens": 10
                }
            )
            
            if response.status_code == 200:
                print(f"✅ LLM API 正常")
            else:
                print(f"⚠️ LLM API 响应异常: {response.status_code}")
                print(f"   这不会影响向量化功能，但会影响智能分析")
        
        print()
        return True
    
    except Exception as e:
        print(f"⚠️ LLM API 检查失败: {e}")
        print(f"   这不会影响向量化功能，但会影响智能分析")
        print()
        return True  # LLM 失败不影响整体


async def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("🔍 QA-Brain 系统配置验证")
    print("=" * 60)
    print()
    
    results = []
    
    # 检查 MySQL
    results.append(await check_mysql())
    
    # 检查 Milvus
    results.append(check_milvus())
    
    # 检查 Embedding API
    results.append(await check_embedding_api())
    
    # 检查 LLM API
    results.append(await check_llm_api())
    
    # 关闭数据库连接
    await engine.dispose()
    
    # 总结
    print("=" * 60)
    print("📊 验证结果总结")
    print("=" * 60)
    
    checks = [
        ("MySQL 数据库", results[0]),
        ("Milvus 向量数据库", results[1]),
        ("Embedding API", results[2]),
        ("LLM API", results[3])
    ]
    
    for name, result in checks:
        status = "✅ 正常" if result else "❌ 异常"
        print(f"{name}: {status}")
    
    print()
    
    if all(results[:3]):  # 前 3 个必须通过
        print("🎉 系统配置正常，可以启动后端服务！")
        print()
        print("启动命令：")
        print("  python -m uvicorn backend.main:app --reload --port 8000")
        print()
    else:
        print("❌ 系统配置存在问题，请根据上面的提示修复")
        print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n❌ 操作已取消")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()

