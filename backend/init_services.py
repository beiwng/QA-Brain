"""
服务初始化脚本
自动检测并创建 MySQL 表、Milvus Collection 和 MinIO Bucket
"""
import asyncio
from sqlalchemy import create_engine
from backend.config import settings
from backend.models import Base
from backend.utils.vector_service import vector_service
from backend.utils.minio_service import minio_service


def init_mysql():
    """初始化 MySQL 数据库表"""
    print("\n" + "="*60)
    print("📦 Initializing MySQL Database...")
    print("="*60)
    
    try:
        # 使用同步引擎创建表
        engine = create_engine(settings.mysql_sync_url, echo=False)
        Base.metadata.create_all(bind=engine)
        print("✅ MySQL tables created successfully")
        print(f"   - decisions")
        print(f"   - bug_insights")
        engine.dispose()
    
    except Exception as e:
        print(f"❌ MySQL initialization failed: {e}")
        raise


def init_milvus():
    """初始化 Milvus 向量数据库"""
    print("\n" + "="*60)
    print("📦 Initializing Milvus Vector Database...")
    print("="*60)
    
    try:
        vector_service.connect()
        vector_service.create_collection()
        vector_service.load_collection()
        print("✅ Milvus initialization complete")
    
    except Exception as e:
        print(f"❌ Milvus initialization failed: {e}")
        raise


def init_minio():
    """初始化 MinIO 对象存储"""
    print("\n" + "="*60)
    print("📦 Initializing MinIO Object Storage...")
    print("="*60)
    
    try:
        minio_service.ensure_bucket_exists()
        print("✅ MinIO initialization complete")
    
    except Exception as e:
        print(f"❌ MinIO initialization failed: {e}")
        raise


def main():
    """主函数：依次初始化所有服务"""
    print("\n" + "🚀 QA-Brain Service Initialization".center(60, "="))
    
    try:
        # 1. 初始化 MySQL
        init_mysql()
        
        # 2. 初始化 Milvus
        init_milvus()
        
        # 3. 初始化 MinIO
        init_minio()
        
        print("\n" + "="*60)
        print("✅ All services initialized successfully!")
        print("="*60)
        print("\n🎉 QA-Brain is ready to use!\n")
    
    except Exception as e:
        print("\n" + "="*60)
        print(f"❌ Initialization failed: {e}")
        print("="*60)
        exit(1)


if __name__ == "__main__":
    # 需要安装 pymysql: pip install pymysql
    main()

