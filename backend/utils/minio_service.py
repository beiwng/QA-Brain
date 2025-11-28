"""
MinIO 对象存储服务
处理文件上传和下载
"""
import uuid
from minio import Minio
from minio.error import S3Error
from typing import BinaryIO
from backend.config import settings


class MinioService:
    """MinIO 客户端封装"""
    
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME
    
    def ensure_bucket_exists(self) -> None:
        """确保 Bucket 存在，不存在则创建"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                print(f"✅ MinIO Bucket '{self.bucket_name}' created successfully")
            else:
                print(f"✅ MinIO Bucket '{self.bucket_name}' already exists")
        except S3Error as e:
            print(f"❌ MinIO Bucket creation failed: {e}")
            raise
    
    def upload_file(self, file: BinaryIO, filename: str, content_type: str = "application/octet-stream") -> str:
        """
        上传文件到 MinIO
        
        Args:
            file: 文件对象
            filename: 原始文件名
            content_type: MIME 类型
        
        Returns:
            文件访问 URL
        """
        try:
            # 生成唯一文件名 (避免冲突)
            file_extension = filename.split('.')[-1] if '.' in filename else ''
            unique_filename = f"{uuid.uuid4()}.{file_extension}" if file_extension else str(uuid.uuid4())
            
            # 上传文件
            file.seek(0)  # 重置文件指针
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=unique_filename,
                data=file,
                length=-1,  # 自动计算长度
                part_size=10*1024*1024,  # 10MB 分片
                content_type=content_type
            )
            
            # 生成访问 URL
            protocol = "https" if settings.MINIO_SECURE else "http"
            url = f"{protocol}://{settings.MINIO_ENDPOINT}/{self.bucket_name}/{unique_filename}"
            
            return url
        
        except S3Error as e:
            print(f"❌ File upload failed: {e}")
            raise
    
    def delete_file(self, object_name: str) -> None:
        """删除文件"""
        try:
            self.client.remove_object(self.bucket_name, object_name)
        except S3Error as e:
            print(f"❌ File deletion failed: {e}")
            raise


# 全局实例
minio_service = MinioService()

