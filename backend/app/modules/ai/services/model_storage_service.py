"""
Model Storage Service for AI Model Files (PBI-27).

Handles secure file storage operations including:
- Directory management (create, cleanup)
- File upload and storage
- File retrieval and streaming
- File deletion (soft and permanent)
- Backup and restore operations
"""

import os
import shutil
import aiofiles
import logging
from pathlib import Path
from typing import Optional, AsyncGenerator, Tuple
from datetime import datetime, timezone
from uuid import UUID

from app.core.config import settings

logger = logging.getLogger(__name__)


class ModelStorageError(Exception):
    """Custom exception for model storage errors."""
    
    def __init__(self, message: str, error_code: str = "STORAGE_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ModelStorageService:
    """
    Service for managing AI model file storage.
    
    Features:
    - Organized directory structure by model type and version
    - Secure file operations with atomic writes
    - Backup support before deletion/overwrite
    - File integrity verification
    """
    
    def __init__(self):
        # Base directories
        self.base_dir = Path(settings.MODEL_STORAGE_DIR)
        self.backup_dir = Path(settings.MODEL_STORAGE_BACKUP_DIR)
        self.temp_dir = Path(settings.MODEL_STORAGE_TEMP_DIR)
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Create storage directories if they don't exist."""
        for directory in [self.base_dir, self.backup_dir, self.temp_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            # Add .gitignore to prevent git tracking
            gitignore = directory / ".gitignore"
            if not gitignore.exists():
                gitignore.write_text("*\n")
        
        logger.info(f"Model storage directories initialized:")
        logger.info(f"  Base: {self.base_dir.absolute()}")
        logger.info(f"  Backup: {self.backup_dir.absolute()}")
        logger.info(f"  Temp: {self.temp_dir.absolute()}")
    
    def _get_model_path(
        self, 
        model_type: str, 
        model_id: UUID, 
        version_tag: str
    ) -> Path:
        """
        Get the storage path for a model file.
        
        Directory structure: models/{model_type}/{model_id}/{version_tag}/model.bin
        
        Args:
            model_type: Type of model (detection, classification, etc.)
            model_id: Unique model identifier
            version_tag: Version tag
            
        Returns:
            Path object for the model file
        """
        model_type_clean = model_type.lower().strip()
        return self.base_dir / model_type_clean / str(model_id) / version_tag / "model.bin"
    
    def _get_backup_path(
        self, 
        model_type: str, 
        model_id: UUID, 
        version_tag: str,
        backup_timestamp: Optional[datetime] = None
    ) -> Path:
        """
        Get the backup path for a model file.
        
        Directory structure: models_backup/{model_type}/{model_id}/{version_tag}_{timestamp}/model.bin
        
        Args:
            model_type: Type of model
            model_id: Unique model identifier
            version_tag: Version tag
            backup_timestamp: Timestamp for backup (default: now)
            
        Returns:
            Path object for the backup file
        """
        if backup_timestamp is None:
            backup_timestamp = datetime.now(timezone.utc)
        
        timestamp_str = backup_timestamp.strftime("%Y%m%d_%H%M%S")
        return self.backup_dir / model_type.lower() / str(model_id) / f"{version_tag}_{timestamp_str}" / "model.bin"
    
    async def store_model(
        self,
        file_content: bytes,
        model_type: str,
        model_id: UUID,
        version_tag: str,
        file_hash: str
    ) -> Tuple[str, int]:
        """
        Store a model file securely.
        
        Args:
            file_content: Raw file content as bytes
            model_type: Type of model
            model_id: Unique model identifier
            version_tag: Version tag
            file_hash: Expected hash for integrity verification
            
        Returns:
            Tuple of (file_path, file_size)
            
        Raises:
            ModelStorageError: If storage fails
        """
        try:
            # Get target path
            target_path = self._get_model_path(model_type, model_id, version_tag)
            
            # Create directory structure
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file atomically (write to temp, then move)
            temp_path = self.temp_dir / f"temp_{model_id}_{version_tag}.bin"
            
            async with aiofiles.open(temp_path, 'wb') as temp_file:
                await temp_file.write(file_content)
            
            # Verify hash before finalizing
            import hashlib
            computed_hash = hashlib.sha256(file_content).hexdigest()
            if computed_hash != file_hash.lower():
                temp_path.unlink(missing_ok=True)
                raise ModelStorageError(
                    "File integrity check failed during storage.",
                    error_code="INTEGRITY_CHECK_FAILED"
                )
            
            # Move temp file to target location
            shutil.move(str(temp_path), str(target_path))
            
            file_size = len(file_content)
            logger.info(f"Model stored successfully: {target_path} ({file_size} bytes)")
            
            return str(target_path), file_size
            
        except ModelStorageError:
            raise
        except Exception as e:
            logger.error(f"Failed to store model: {e}")
            raise ModelStorageError(
                f"Failed to store model: {str(e)}",
                error_code="STORAGE_FAILED"
            )
    
    async def store_model_from_upload(
        self,
        upload_file,
        model_type: str,
        model_id: UUID,
        version_tag: str,
        file_hash: str
    ) -> Tuple[str, int]:
        """
        Store a model from an UploadFile object.
        
        Args:
            upload_file: Starlette UploadFile object
            model_type: Type of model
            model_id: Unique model identifier
            version_tag: Version tag
            file_hash: Expected hash for integrity verification
            
        Returns:
            Tuple of (file_path, file_size)
        """
        # Read file content
        file_content = await upload_file.read()
        
        # Store using standard method
        return await self.store_model(
            file_content=file_content,
            model_type=model_type,
            model_id=model_id,
            version_tag=version_tag,
            file_hash=file_hash
        )
    
    async def get_model_file(self, file_path: str) -> bytes:
        """
        Retrieve model file content.
        
        Args:
            file_path: Path to the model file
            
        Returns:
            File content as bytes
            
        Raises:
            ModelStorageError: If file doesn't exist or can't be read
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                raise ModelStorageError(
                    f"Model file not found: {file_path}",
                    error_code="FILE_NOT_FOUND"
                )
            
            async with aiofiles.open(path, 'rb') as f:
                content = await f.read()
            
            return content
            
        except ModelStorageError:
            raise
        except Exception as e:
            logger.error(f"Failed to read model file: {e}")
            raise ModelStorageError(
                f"Failed to read model file: {str(e)}",
                error_code="READ_FAILED"
            )
    
    async def stream_model_file(self, file_path: str, chunk_size: int = 8192) -> AsyncGenerator[bytes, None]:
        """
        Stream model file content in chunks.
        
        Args:
            file_path: Path to the model file
            chunk_size: Size of chunks to yield
            
        Yields:
            File content chunks
            
        Raises:
            ModelStorageError: If file doesn't exist or can't be read
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                raise ModelStorageError(
                    f"Model file not found: {file_path}",
                    error_code="FILE_NOT_FOUND"
                )
            
            async with aiofiles.open(path, 'rb') as f:
                while True:
                    chunk = await f.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
                    
        except ModelStorageError:
            raise
        except Exception as e:
            logger.error(f"Failed to stream model file: {e}")
            raise ModelStorageError(
                f"Failed to stream model file: {str(e)}",
                error_code="STREAM_FAILED"
            )
    
    async def backup_model(
        self,
        file_path: str,
        model_type: str,
        model_id: UUID,
        version_tag: str
    ) -> Optional[str]:
        """
        Create a backup of a model file before deletion/overwrite.
        
        Args:
            file_path: Current path of the model file
            model_type: Type of model
            model_id: Unique model identifier
            version_tag: Version tag
            
        Returns:
            Path to backup file, or None if backup not needed
        """
        try:
            source_path = Path(file_path)
            
            if not source_path.exists():
                logger.warning(f"Model file doesn't exist, skipping backup: {file_path}")
                return None
            
            # Get backup path
            backup_path = self._get_backup_path(model_type, model_id, version_tag)
            
            # Create backup directory
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file to backup
            shutil.copy2(str(source_path), str(backup_path))
            
            logger.info(f"Model backed up to: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"Failed to backup model: {e}")
            # Don't raise - backup failure shouldn't block the main operation
            return None
    
    async def delete_model(
        self,
        file_path: str,
        model_type: str,
        model_id: UUID,
        version_tag: str,
        create_backup: bool = True
    ) -> bool:
        """
        Delete a model file, optionally creating a backup first.
        
        Args:
            file_path: Path to the model file
            model_type: Type of model
            model_id: Unique model identifier
            version_tag: Version tag
            create_backup: Whether to create backup before deletion
            
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            source_path = Path(file_path)
            
            if not source_path.exists():
                logger.warning(f"Model file doesn't exist: {file_path}")
                return False
            
            # Create backup if requested
            if create_backup:
                await self.backup_model(file_path, model_type, model_id, version_tag)
            
            # Delete file
            source_path.unlink()
            
            # Clean up empty directories
            self._cleanup_empty_directories(source_path.parent)
            
            logger.info(f"Model deleted: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete model: {e}")
            raise ModelStorageError(
                f"Failed to delete model: {str(e)}",
                error_code="DELETE_FAILED"
            )
    
    def _cleanup_empty_directories(self, start_path: Path) -> None:
        """
        Clean up empty directories up the tree.
        
        Args:
            start_path: Starting directory path
        """
        current = start_path
        max_depth = 5  # Prevent infinite loops
        
        for _ in range(max_depth):
            if current == self.base_dir or current == self.backup_dir:
                break
            
            try:
                if current.exists() and not any(current.iterdir()):
                    current.rmdir()
                    logger.debug(f"Removed empty directory: {current}")
                current = current.parent
            except Exception:
                break
    
    async def restore_from_backup(
        self,
        backup_path: str,
        target_path: str
    ) -> bool:
        """
        Restore a model from backup.
        
        Args:
            backup_path: Path to backup file
            target_path: Path to restore to
            
        Returns:
            True if restore successful
        """
        try:
            backup = Path(backup_path)
            target = Path(target_path)
            
            if not backup.exists():
                raise ModelStorageError(
                    f"Backup file not found: {backup_path}",
                    error_code="BACKUP_NOT_FOUND"
                )
            
            # Create target directory
            target.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy backup to target
            shutil.copy2(str(backup), str(target))
            
            logger.info(f"Model restored from backup: {backup_path} -> {target_path}")
            return True
            
        except ModelStorageError:
            raise
        except Exception as e:
            logger.error(f"Failed to restore from backup: {e}")
            raise ModelStorageError(
                f"Failed to restore from backup: {str(e)}",
                error_code="RESTORE_FAILED"
            )
    
    def get_file_info(self, file_path: str) -> dict:
        """
        Get information about a stored file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                return {
                    "exists": False,
                    "path": file_path
                }
            
            stat = path.stat()
            
            return {
                "exists": True,
                "path": file_path,
                "size_bytes": stat.st_size,
                "size_mb": stat.st_size / (1024 * 1024),
                "created_at": datetime.fromtimestamp(stat.st_ctime),
                "modified_at": datetime.fromtimestamp(stat.st_mtime),
            }
            
        except Exception as e:
            logger.error(f"Failed to get file info: {e}")
            return {
                "exists": False,
                "path": file_path,
                "error": str(e)
            }
    
    async def cleanup_temp_files(self, max_age_hours: int = 24) -> int:
        """
        Clean up temporary files older than specified age.
        
        Args:
            max_age_hours: Maximum age in hours
            
        Returns:
            Number of files cleaned up
        """
        try:
            if not self.temp_dir.exists():
                return 0
            
            cleaned = 0
            now = datetime.now()
            
            for temp_file in self.temp_dir.glob("temp_*.bin"):
                try:
                    mtime = datetime.fromtimestamp(temp_file.stat().st_mtime)
                    age = now - mtime
                    
                    if age.total_seconds() > max_age_hours * 3600:
                        temp_file.unlink()
                        cleaned += 1
                        logger.debug(f"Cleaned up temp file: {temp_file}")
                except Exception:
                    continue
            
            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} temporary files")
            
            return cleaned
            
        except Exception as e:
            logger.error(f"Failed to cleanup temp files: {e}")
            return 0


# Singleton instance
_storage_service: Optional[ModelStorageService] = None


def get_storage_service() -> ModelStorageService:
    """Get or create the singleton storage service instance."""
    global _storage_service
    if _storage_service is None:
        _storage_service = ModelStorageService()
    return _storage_service
