import os
import shutil
import hashlib
from typing import Optional
from fastapi import HTTPException
from app.core.config import settings


class StorageService:
    """Persistent report storage manager with path validation and integrity checking."""

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = os.path.abspath(base_dir or settings.STORAGE_DIR)
        os.makedirs(self.base_dir, exist_ok=True)

    def get_file_path(self, file_name: str) -> str:
        """Resolve absolute file path and prevent directory traversal attacks."""
        clean_name = os.path.basename(file_name)
        file_path = os.path.abspath(os.path.join(self.base_dir, clean_name))
        
        # Verify that resolved path is within base_dir
        if not file_path.startswith(self.base_dir):
            raise HTTPException(status_code=400, detail="Invalid file path security violation.")
            
        return file_path

    def file_exists(self, file_name: str) -> bool:
        path = self.get_file_path(file_name)
        return os.path.isfile(path)

    def get_file_size(self, file_name: str) -> int:
        path = self.get_file_path(file_name)
        if not os.path.isfile(path):
            return 0
        return os.path.getsize(path)

    def compute_sha256(self, file_name: str) -> str:
        path = self.get_file_path(file_name)
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def delete_file(self, file_name: str) -> bool:
        path = self.get_file_path(file_name)
        if os.path.isfile(path):
            os.remove(path)
            return True
        return False


storage_service = StorageService()
