"""
QA-Brain 安装验证脚本
快速检查所有依赖和服务是否正常
"""
import sys
import importlib


def check_python_version():
    """检查 Python 版本"""
    print("🔍 Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 13:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} (需要 3.13+)")
        return False


def check_package(package_name, display_name=None):
    """检查 Python 包是否安装"""
    display_name = display_name or package_name
    try:
        importlib.import_module(package_name)
        print(f"   ✅ {display_name}")
        return True
    except ImportError:
        print(f"   ❌ {display_name} (未安装)")
        return False


def check_python_packages():
    """检查所有 Python 依赖"""
    print("\n🔍 Checking Python packages...")
    
    packages = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("sqlalchemy", "SQLAlchemy"),
        ("aiomysql", "aiomysql"),
        ("pymilvus", "PyMilvus"),
        ("minio", "MinIO"),
        ("langchain", "LangChain"),
        ("langgraph", "LangGraph"),
        ("openai", "OpenAI"),
        ("pydantic", "Pydantic"),
    ]
    
    results = [check_package(pkg, name) for pkg, name in packages]
    return all(results)


def check_services():
    """检查外部服务连接"""
    print("\n🔍 Checking external services...")
    
    # 检查配置文件
    try:
        from backend.config import settings
        print(f"   ✅ Config loaded")
        
        # 检查 MySQL
        print(f"   📊 MySQL: {settings.MYSQL_HOST}:{settings.MYSQL_PORT}")
        
        # 检查 Milvus
        print(f"   🔍 Milvus: {settings.MILVUS_HOST}:{settings.MILVUS_PORT}")
        
        # 检查 MinIO
        print(f"   📦 MinIO: {settings.MINIO_ENDPOINT}")
        
        # 检查 LLM
        print(f"   🤖 LLM: {settings.LLM_BASE_URL}")
        
        return True
    
    except Exception as e:
        print(f"   ❌ Config error: {e}")
        return False


def test_mysql_connection():
    """测试 MySQL 连接"""
    print("\n🔍 Testing MySQL connection...")
    try:
        from sqlalchemy import create_engine
        from backend.config import settings
        
        engine = create_engine(settings.mysql_sync_url, echo=False)
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print("   ✅ MySQL connection successful")
            engine.dispose()
            return True
    
    except Exception as e:
        print(f"   ❌ MySQL connection failed: {e}")
        return False


def test_milvus_connection():
    """测试 Milvus 连接"""
    print("\n🔍 Testing Milvus connection...")
    try:
        from pymilvus import connections
        from backend.config import settings
        
        connections.connect(
            alias="test",
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT
        )
        print("   ✅ Milvus connection successful")
        connections.disconnect("test")
        return True
    
    except Exception as e:
        print(f"   ❌ Milvus connection failed: {e}")
        return False


def test_minio_connection():
    """测试 MinIO 连接"""
    print("\n🔍 Testing MinIO connection...")
    try:
        from minio import Minio
        from backend.config import settings
        
        client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        
        # 尝试列出 buckets
        buckets = client.list_buckets()
        print(f"   ✅ MinIO connection successful ({len(buckets)} buckets)")
        return True
    
    except Exception as e:
        print(f"   ❌ MinIO connection failed: {e}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("🧪 QA-Brain Installation Test")
    print("=" * 60)
    
    results = []
    
    # 1. 检查 Python 版本
    results.append(check_python_version())
    
    # 2. 检查 Python 包
    results.append(check_python_packages())
    
    # 3. 检查配置
    results.append(check_services())
    
    # 4. 测试数据库连接
    results.append(test_mysql_connection())
    
    # 5. 测试 Milvus 连接
    results.append(test_milvus_connection())
    
    # 6. 测试 MinIO 连接
    results.append(test_minio_connection())
    
    # 总结
    print("\n" + "=" * 60)
    if all(results):
        print("✅ All tests passed! QA-Brain is ready to use.")
        print("=" * 60)
        print("\n🚀 Next steps:")
        print("   1. Run: python backend/init_services.py")
        print("   2. Run: python backend/main.py")
        print("   3. Run: cd frontend && npm run dev")
        print("   4. Visit: http://localhost:1314")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    exit(main())

