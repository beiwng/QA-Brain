"""
QA-Brain Configuration Module
加载环境变量并提供全局配置访问
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """全局配置类"""
    
    # === 基础配置 ===
    PROJECT_NAME: str = "QA-Brain"
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    FRONTEND_PORT: int = 1314
    
    # === 数据库配置 ===
    MYSQL_HOST: str = "192.168.80.81"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "123456"
    MYSQL_DATABASE: str = "qa_brain"
    
    # === Milvus 配置 ===
    MILVUS_HOST: str = "192.168.4.168"
    MILVUS_PORT: int = 19530
    MILVUS_USER: str = ""
    MILVUS_PASSWORD: str = ""
    MILVUS_COLLECTION_NAME: str = "qa_decisions"
    
    # === MinIO 配置 ===
    MINIO_ENDPOINT: str = "192.168.4.168:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False
    MINIO_BUCKET_NAME: str = "test"
    
    # === AI 模型配置 ===
    LLM_API_KEY: str = "sk-6147fa558a704e43b2ae45671f595770"
    LLM_BASE_URL: str = "http://192.168.22.31:8000/v1"
    LLM_MODEL: str = "Qwen3-Next-80B-I-FP16"
    
    # === Embedding 配置 ===
    EMBEDDING_MODEL_NAME: str = "Qwen3-Embedding-4B"
    EMBEDDING_API_URL: str = "http://192.168.22.31:9997/v1/embeddings"
    EMBEDDING_DIM: int = 2560  # 根据实际模型调整
    
    # === 其他配置 ===
    DEBUG: bool = True
    CORS_ORIGINS: list = ["http://192.168.72.195:1314", "http://127.0.0.1:1314"]
    
    @property
    def mysql_url(self) -> str:
        """生成 MySQL 连接 URL"""
        return f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
    
    @property
    def mysql_sync_url(self) -> str:
        """生成同步 MySQL 连接 URL (用于初始化)"""
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 全局配置实例
settings = Settings()

