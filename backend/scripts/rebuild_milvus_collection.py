"""
重建 Milvus Collection（用于更换 Embedding 模型时）
运行方式：python backend/scripts/rebuild_milvus_collection.py
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from pymilvus import connections, utility, Collection
from backend.config import settings


def check_collection():
    """检查 Collection 信息"""
    print("🔍 检查 Milvus Collection...")
    print(f"Collection 名称: {settings.MILVUS_COLLECTION_NAME}")
    print(f"期望的 Embedding 维度: {settings.EMBEDDING_DIM}")
    print(f"Embedding 模型: {settings.EMBEDDING_MODEL_NAME}\n")

    try:
        # 连接到 Milvus
        connections.connect(
            alias="default",
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
            user=settings.MILVUS_USER,
            password=settings.MILVUS_PASSWORD
        )
        print(f"✅ 已连接到 Milvus: {settings.MILVUS_HOST}:{settings.MILVUS_PORT}\n")

        # 检查 Collection 是否存在
        if not utility.has_collection(settings.MILVUS_COLLECTION_NAME):
            print(f"⚠️ Collection '{settings.MILVUS_COLLECTION_NAME}' 不存在")
            print("建议：运行后端服务，它会自动创建 Collection\n")
            return None

        # 获取 Collection 信息
        collection = Collection(settings.MILVUS_COLLECTION_NAME)
        schema = collection.schema

        print(f"✅ Collection '{settings.MILVUS_COLLECTION_NAME}' 已存在")
        print(f"📊 Collection 统计:")
        print(f"   - 实体数量: {collection.num_entities}")
        print(f"\n📋 Schema 信息:")

        current_dim = None
        for field in schema.fields:
            print(f"   - {field.name}: {field.dtype}")
            if field.name == "embedding":
                if hasattr(field, 'params') and 'dim' in field.params:
                    current_dim = field.params['dim']
                    print(f"     当前维度: {current_dim}")

        print()

        # 检查维度是否匹配
        if current_dim is not None:
            if current_dim == settings.EMBEDDING_DIM:
                print(f"✅ Embedding 维度匹配 ({current_dim} == {settings.EMBEDDING_DIM})")
                print("无需重建 Collection\n")
                return "match"
            else:
                print(f"⚠️ Embedding 维度不匹配！")
                print(f"   当前维度: {current_dim}")
                print(f"   期望维度: {settings.EMBEDDING_DIM}")
                print(f"\n需要重建 Collection 以使用新的 Embedding 模型\n")
                return "mismatch"
        else:
            print("⚠️ 无法获取当前 Embedding 维度\n")
            return "unknown"

    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def rebuild_collection():
    """重建 Collection"""
    print("=" * 60)
    print("⚠️ 警告：重建 Collection 会删除所有现有数据！")
    print("=" * 60)

    # 确认操作
    confirm = input("\n是否继续？输入 'yes' 确认，其他任何输入取消: ")
    if confirm.lower() != 'yes':
        print("❌ 操作已取消")
        return False

    try:
        # 连接到 Milvus
        connections.connect(
            alias="default",
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
            user=settings.MILVUS_USER,
            password=settings.MILVUS_PASSWORD
        )

        # 删除旧 Collection
        if utility.has_collection(settings.MILVUS_COLLECTION_NAME):
            print(f"\n🗑️ 删除旧 Collection '{settings.MILVUS_COLLECTION_NAME}'...")
            utility.drop_collection(settings.MILVUS_COLLECTION_NAME)
            print("✅ 旧 Collection 已删除")

        print(f"\n📝 新 Collection 将在后端服务启动时自动创建")
        print(f"   - Collection 名称: {settings.MILVUS_COLLECTION_NAME}")
        print(f"   - Embedding 维度: {settings.EMBEDDING_DIM}")
        print(f"   - Embedding 模型: {settings.EMBEDDING_MODEL_NAME}")

        print("\n✅ 重建完成！")
        print("\n📌 下一步：")
        print("1. 启动后端服务（会自动创建新 Collection）")
        print("2. 重新导入历史决策和缺陷数据")
        print("3. 或者创建新的决策，系统会自动向量化\n")

        return True

    except Exception as e:
        print(f"❌ 重建失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("🔧 Milvus Collection 维度检查与重建工具")
    print("=" * 60)
    print()

    rebuild = input("\n是否立即重建？(yes/no): ")
    if rebuild.lower() == 'yes':
        rebuild_collection()
    # # 检查 Collection
    # status = check_collection()
    #
    # if status == "match":
    #     print("🎉 一切正常，无需操作！")
    #     return
    #
    # if status == "mismatch":
    #     print("💡 建议：重建 Collection 以使用新的 Embedding 模型")
    #     rebuild = input("\n是否立即重建？(yes/no): ")
    #     if rebuild.lower() == 'yes':
    #         rebuild_collection()
    #     else:
    #         print("\n❌ 操作已取消")
    #         print("\n⚠️ 注意：如果不重建 Collection，向量化可能会失败！")
    #         print("因为新模型的 Embedding 维度与旧 Collection 不匹配。\n")
    #
    # elif status == "unknown":
    #     print("💡 建议：检查 Milvus 连接和 Collection 配置")
    #
    # elif status is None:
    #     print("💡 建议：检查 Milvus 服务是否正常运行")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ 操作已取消")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()

