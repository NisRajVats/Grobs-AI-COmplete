"""
Cloud Storage Service

Unified interface for cloud storage operations.
Supports AWS S3, Google Cloud Storage, and local storage.
"""
import os
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod

from app.core.logging import get_logger
from app.core.config import settings
from app.core.exceptions import StorageServiceError

logger = get_logger(__name__)


class StorageProvider(Enum):
    LOCAL = "local"
    AWS_S3 = "s3"
    GOOGLE_GCS = "gcs"


@dataclass
class StorageObject:
    key: str
    url: str
    size: int
    content_type: str
    metadata: Dict[str, Any]


class StorageInterface(ABC):
    @abstractmethod
    def upload_file(self, file_data: bytes, filename: str, content_type: str = "application/pdf", metadata: Optional[Dict[str, str]] = None) -> StorageObject:
        pass
    
    @abstractmethod
    def download_file(self, key: str) -> bytes:
        pass
    
    @abstractmethod
    def delete_file(self, key: str) -> bool:
        pass
    
    @abstractmethod
    def get_file_url(self, key: str, expires_in: int = 3600) -> str:
        pass
    
    @abstractmethod
    def list_files(self, prefix: str = "") -> List[str]:
        pass


class LocalStorageService(StorageInterface):
    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir or settings.upload_path
        os.makedirs(self.base_dir, exist_ok=True)
        logger.info(f"Local storage initialized at: {self.base_dir}")
    
    def _get_file_path(self, key: str) -> str:
        return os.path.join(self.base_dir, key)
    
    def upload_file(self, file_data: bytes, filename: str, content_type: str = "application/pdf", metadata: Optional[Dict[str, str]] = None) -> StorageObject:
        try:
            file_path = self._get_file_path(filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(file_data)
            return StorageObject(
                key=filename,
                url=f"/uploads/{filename}",
                size=len(file_data),
                content_type=content_type,
                metadata=metadata or {}
            )
        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            raise StorageServiceError("Local Storage", str(e))
    
    def download_file(self, key: str) -> bytes:
        try:
            file_path = self._get_file_path(key)
            with open(file_path, "rb") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to download file: {e}")
            raise StorageServiceError("Local Storage", str(e))
    
    def delete_file(self, key: str) -> bool:
        try:
            file_path = self._get_file_path(key)
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            return False
    
    def get_file_url(self, key: str, expires_in: int = 3600) -> str:
        return f"/uploads/{key}"
    
    def list_files(self, prefix: str = "") -> List[str]:
        try:
            dir_path = self._get_file_path(prefix)
            if os.path.isdir(dir_path):
                return [os.path.join(prefix, f) for f in os.listdir(dir_path)]
            return []
        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            return []


class S3StorageService(StorageInterface):
    def __init__(self):
        try:
            import boto3
            self.s3 = boto3.client(
                "s3",
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                region_name=settings.AWS_REGION or "us-east-1"
            )
            self.bucket = settings.AWS_S3_BUCKET
            logger.info(f"S3 storage initialized with bucket: {self.bucket}")
        except Exception as e:
            logger.warning(f"S3 not available: {e}")
            self.s3 = None
    
    def upload_file(self, file_data: bytes, filename: str, content_type: str = "application/pdf", metadata: Optional[Dict[str, str]] = None) -> StorageObject:
        if not self.s3:
            raise StorageServiceError("S3", "S3 client not initialized")
        try:
            extra_args = {"ContentType": content_type}
            if metadata:
                extra_args["Metadata"] = metadata
            self.s3.put_object(Bucket=self.bucket, Key=filename, Body=file_data, **extra_args)
            url = f"https://{self.bucket}.s3.amazonaws.com/{filename}"
            return StorageObject(key=filename, url=url, size=len(file_data), content_type=content_type, metadata=metadata or {})
        except Exception as e:
            logger.error(f"Failed to upload to S3: {e}")
            raise StorageServiceError("S3", str(e))
    
    def download_file(self, key: str) -> bytes:
        if not self.s3:
            raise StorageServiceError("S3", "S3 client not initialized")
        try:
            response = self.s3.get_object(Bucket=self.bucket, Key=key)
            return response["Body"].read()
        except Exception as e:
            logger.error(f"Failed to download from S3: {e}")
            raise StorageServiceError("S3", str(e))
    
    def delete_file(self, key: str) -> bool:
        if not self.s3:
            return False
        try:
            self.s3.delete_object(Bucket=self.bucket, Key=key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete from S3: {e}")
            return False
    
    def get_file_url(self, key: str, expires_in: int = 3600) -> str:
        if not self.s3:
            return ""
        try:
            url = self.s3.generate_presigned_url("get_object", Params={"Bucket": self.bucket, "Key": key}, ExpiresIn=expires_in)
            return url
        except Exception as e:
            logger.error(f"Failed to generate S3 URL: {e}")
            return ""
    
    def list_files(self, prefix: str = "") -> List[str]:
        if not self.s3:
            return []
        try:
            response = self.s3.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
            return [obj["Key"] for obj in response.get("Contents", [])]
        except Exception as e:
            logger.error(f"Failed to list S3 files: {e}")
            return []


class GCSStorageService(StorageInterface):
    def __init__(self):
        try:
            from google.cloud import storage
            self.client = storage.Client()
            self.bucket = self.client.bucket(settings.GCS_BUCKET)
            logger.info(f"GCS storage initialized with bucket: {self.bucket}")
        except Exception as e:
            logger.warning(f"GCS not available: {e}")
            self.client = None
    
    def upload_file(self, file_data: bytes, filename: str, content_type: str = "application/pdf", metadata: Optional[Dict[str, str]] = None) -> StorageObject:
        if not self.client:
            raise StorageServiceError("GCS", "GCS client not initialized")
        try:
            blob = self.bucket.blob(filename)
            blob.upload_from_string(file_data, content_type=content_type, metadata=metadata)
            url = f"https://storage.googleapis.com/{self.bucket.name}/{filename}"
            return StorageObject(key=filename, url=url, size=len(file_data), content_type=content_type, metadata=metadata or {})
        except Exception as e:
            logger.error(f"Failed to upload to GCS: {e}")
            raise StorageServiceError("GCS", str(e))
    
    def download_file(self, key: str) -> bytes:
        if not self.client:
            raise StorageServiceError("GCS", "GCS client not initialized")
        try:
            blob = self.bucket.blob(key)
            return blob.download_as_bytes()
        except Exception as e:
            logger.error(f"Failed to download from GCS: {e}")
            raise StorageServiceError("GCS", str(e))
    
    def delete_file(self, key: str) -> bool:
        if not self.client:
            return False
        try:
            blob = self.bucket.blob(key)
            blob.delete()
            return True
        except Exception as e:
            logger.error(f"Failed to delete from GCS: {e}")
            return False
    
    def get_file_url(self, key: str, expires_in: int = 3600) -> str:
        if not self.client:
            return ""
        try:
            blob = self.bucket.blob(key)
            url = blob.generate_signed_url(version="v4", expiration=expires_in)
            return url
        except Exception as e:
            logger.error(f"Failed to generate GCS URL: {e}")
            return ""
    
    def list_files(self, prefix: str = "") -> List[str]:
        if not self.client:
            return []
        try:
            blobs = self.bucket.list_blobs(prefix=prefix)
            return [blob.name for blob in blobs]
        except Exception as e:
            logger.error(f"Failed to list GCS files: {e}")
            return []


class CloudStorageService:
    def __init__(self, provider: Optional[str] = None):
        self.provider_name = provider or settings.STORAGE_PROVIDER
        self._initialize_provider()
    
    def _initialize_provider(self):
        if self.provider_name == "local":
            self.provider = LocalStorageService()
        elif self.provider_name == "s3":
            self.provider = S3StorageService()
        elif self.provider_name == "gcs":
            self.provider = GCSStorageService()
        else:
            logger.warning(f"Unknown storage provider: {self.provider_name}, using local")
            self.provider = LocalStorageService()
    
    def upload_file(self, file_data: bytes, filename: str, content_type: str = "application/pdf", metadata: Optional[Dict[str, str]] = None) -> StorageObject:
        return self.provider.upload_file(file_data, filename, content_type, metadata)
    
    def download_file(self, key: str) -> bytes:
        return self.provider.download_file(key)
    
    def delete_file(self, key: str) -> bool:
        return self.provider.delete_file(key)
    
    def get_file_url(self, key: str, expires_in: int = 3600) -> str:
        return self.provider.get_file_url(key, expires_in)
    
    def list_files(self, prefix: str = "") -> List[str]:
        return self.provider.list_files(prefix)
    
    def upload_resume(self, user_id: int, file_data: bytes, filename: str, content_type: str = "application/pdf") -> StorageObject:
        import time
        timestamp = int(time.time())
        base_name = os.path.splitext(filename)[0]
        ext = os.path.splitext(filename)[1]
        new_filename = f"{user_id}_{timestamp}_{base_name}{ext}"
        from datetime import datetime
        date_prefix = datetime.now().strftime("%Y/%m/%d")
        key = f"resumes/{date_prefix}/{new_filename}"
        return self.upload_file(file_data, key, content_type)


# Singleton instance
cloud_storage_service = CloudStorageService()
