"""
Milvus 向量数据库服务
处理知识库(决策+缺陷)的向量化存储和检索
"""
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
from typing import List, Dict, Any, Optional
from backend.config import settings
import httpx
import asyncio
import json


class VectorService:
    """Milvus 向量数据库封装"""

    def __init__(self):
        self.collection_name = settings.MILVUS_COLLECTION_NAME
        # ✅ 读取 EMBEDDING_DIM
        self.dim = settings.EMBEDDING_DIM
        self.embedding_url = settings.EMBEDDING_API_URL
        self.collection = None
        self.alias = "default"
        # 初始化 HTTP 客户端
        self.client = httpx.AsyncClient(timeout=60.0)  # 增加超时时间防止大模型响应慢

    def connect(self) -> None:
        """连接到 Milvus"""
        try:
            connections.connect(
                alias=self.alias,
                host=settings.MILVUS_HOST,
                port=settings.MILVUS_PORT,
                user=settings.MILVUS_USER,
                password=settings.MILVUS_PASSWORD
            )
            print(f"✅ Connected to Milvus at {settings.MILVUS_HOST}:{settings.MILVUS_PORT}")
        except Exception as e:
            print(f"❌ Milvus connection failed: {e}")
            raise

    def create_collection(self) -> None:
        """
        创建 Milvus Collection (适配 QA-Brain v2.0 Schema)
        Schema: [pk, vector, title, text, metadata, source_type]
        """
        try:
            # 1. 检查是否存在
            if utility.has_collection(self.collection_name):
                print(f"✅ Milvus Collection '{self.collection_name}' already exists.")
                self.collection = Collection(self.collection_name)
                return

            # 2. 定义 Schema (严格对应 insert_knowledge 的插入顺序)
            fields = [
                # [0] 主键 ID (引用 MySQL ID)
                FieldSchema(name="pk", dtype=DataType.INT64, is_primary=True, auto_id=False, description="知识ID"),

                # [1] 向量数据
                # ✅ 修复: 使用 self.dim
                FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=self.dim, description="语义向量"),

                # [2] 标题 (支持超长标题)
                FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=4096, description="标题"),

                # [3] 文本内容 (决策背景 或 缺陷描述+根因)
                FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535, description="全文内容"),

                # [4] 元数据 (关键新增：存储 severity, impact_scope, verdict 等)
                FieldSchema(name="metadata", dtype=DataType.JSON, description="元数据"),

                # [5] 来源类型 (关键新增：区分 'decision' 还是 'bug_history')
                FieldSchema(name="source_type", dtype=DataType.VARCHAR, max_length=100, description="来源类型")
            ]

            schema = CollectionSchema(fields=fields, description="QA-Brain 知识库 (决策+缺陷)")

            # 3. 创建集合
            self.collection = Collection(name=self.collection_name, schema=schema)

            # 4. 创建索引
            # ✅ 修复: 使用 IP (内积) 避免 Metric Type 不匹配问题
            index_params = {"index_type": "IVF_FLAT",
                             "metric_type": "COSINE",  # Inner Product（余弦相似度）
                             "params": {"nlist": 128}
            }

            self.collection.create_index(field_name="vector", index_params=index_params)

            print(f"✅ Milvus Collection '{self.collection_name}' created successfully (Schema v2.0)")

        except Exception as e:
            print(f"❌ Milvus Collection creation failed: {e}")
            raise

    def load_collection(self) -> None:
        """加载 Collection 到内存"""
        try:
            if self.collection is None:
                if not utility.has_collection(self.collection_name):
                    # 尝试自动创建
                    print(f"⚠️ Collection not found, creating...")
                    self.create_collection()
                else:
                    self.collection = Collection(self.collection_name)

            self.collection.load()
            # print(f"✅ Collection loaded")
        except Exception as e:
            print(f"❌ Failed to load collection: {e}")
            raise

    async def get_embedding(self, text: str) -> List[float]:
        """获取向量 (OpenAI 兼容接口 + 自动适配)"""
        if not text: return []

        # 尝试读取配置中的模型名
        model_name = settings.EMBEDDING_MODEL_NAME

        # 构造 OpenAI 标准 Payload
        payload = {
            "model": model_name,
            "input": text,
            "encoding_format": "float"
        }

        try:
            response = await self.client.post(
                self.embedding_url,
                json=payload
            )

            if response.status_code != 200:
                print(f"❌ Embedding API Error {response.status_code}: {response.text}")
                response.raise_for_status()

            data = response.json()

            # 1. OpenAI 标准格式
            if "data" in data and len(data["data"]) > 0:
                if "embedding" in data["data"][0]:
                    return data["data"][0]["embedding"]

            # 2. 兼容格式 A
            if "embeddings" in data:
                return data["embeddings"][0]

            # 3. 兼容格式 B
            if "embedding" in data:
                return data["embedding"]

            raise ValueError(f"Unknown embedding response format: {list(data.keys())}")

        except Exception as e:
            print(f"❌ Embedding generation failed: {e}")
            raise

    async def insert_knowledge(
            self,
            knowledge_id: int,
            content: str,
            title: str,
            source_type: str,
            metadata: Dict[str, Any] = None
    ) -> None:
        """
        通用知识插入方法（支持决策和缺陷）
        """
        try:
            if self.collection is None: self.load_collection()

            embedding = await self.get_embedding(content)
            if metadata is None: metadata = {}

            # ✅ 严格对应 6 个字段的顺序
            entities = [
                [knowledge_id],  # 1. pk
                [embedding],  # 2. vector
                [title],  # 3. title
                [content[:5000]],  # 4. text (限制长度防止RPC超时)
                [metadata],  # 5. metadata (JSON)
                [source_type]  # 6. source_type
            ]

            self.collection.insert(entities)
            # 对于频繁插入，建议注释掉 flush，改由定时任务 flush，或者每 10 条 flush 一次
            self.collection.flush()

            print(f"✅ Knowledge #{knowledge_id} ({source_type}) inserted into Milvus")

        except Exception as e:
            print(f"❌ Knowledge insertion failed: {e}")
            import traceback
            traceback.print_exc()
            raise

    # ✅ 修复: 复用 insert_knowledge，确保数据结构一致
    async def insert_decision(self, decision_id: int, title: str, context: str, verdict: str) -> None:
        """插入决策记录"""
        combined_text = f"决策标题: {title}\n背景: {context}\n结论: {verdict}"
        metadata = {
            "source_type": "decision",
            "verdict": verdict,
            "context_snippet": context[:500]
        }
        await self.insert_knowledge(
            knowledge_id=decision_id,
            content=combined_text,
            title=title,
            source_type="decision",
            metadata=metadata
        )

    # ✅ 修复: 通用语义检索方法 (补全了解析逻辑)
    async def search_similar(self, text: str, top_k: int = 5, score_threshold: float = 0.35) -> List[Dict[str, Any]]:
        """
        语义检索 (通用)
        """
        try:
            if self.collection is None: self.load_collection()

            query_embedding = await self.get_embedding(text)
            if not query_embedding: return []

            # 搜索参数 (使用 IP 以匹配 Index)
            search_params = {"metric_type": "COSINE", "params": {"nprobe": 64}}

            # 执行搜索
            results = self.collection.search(
                data=[query_embedding],
                anns_field="vector",  # 必须是 'vector'
                param=search_params,
                limit=top_k,
                output_fields=["pk", "title", "text", "metadata", "source_type"]  # 指定返回字段
            )

            knowledge_list = []
            for hits in results:
                for hit in hits:
                    if hit.score < score_threshold:
                        continue

                    # ✅ 解析逻辑补全
                    # 1. 获取基础字段
                    item = {
                        "id": hit.entity.get("pk"),
                        "title": hit.entity.get("title"),
                        "text": hit.entity.get("text"),
                        "source_type": hit.entity.get("source_type"),
                        "score": hit.score
                    }

                    # 2. 解包 Metadata (JSON) 并合并到 item 中
                    # 这样上层就可以直接访问 item['impact_scope'] 或 item['root_cause']
                    meta = hit.entity.get("metadata")
                    if meta:
                        if isinstance(meta, str):
                            try:
                                meta = json.loads(meta)
                            except:
                                pass
                        if isinstance(meta, dict):
                            item.update(meta)

                    knowledge_list.append(item)

            print(f"🔍 Semantic Search: Input='{text}', Hit={len(knowledge_list)}")
            return knowledge_list

        except Exception as e:
            print(f"❌ Vector search failed: {e}")
            raise


# 全局实例
vector_service = VectorService()