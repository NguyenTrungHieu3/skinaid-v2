"""
Model Validator for AI Model Upload (PBI-27).

Provides comprehensive validation for model files including:
- File size validation (min/max limits)
- File extension/type validation
- Model type validation
- Version tag validation
- File integrity checks (hash verification)
"""

import hashlib
import logging
import re
from pathlib import Path
from typing import Optional, List
from starlette.datastructures import UploadFile

from app.core.config import settings

logger = logging.getLogger(__name__)


class ModelValidationError(Exception):
    """Custom exception for model validation errors."""
    
    def __init__(self, message: str, error_code: str = "VALIDATION_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ModelValidator:
    """
    Validator for AI model uploads.
    
    Validates:
    - File size (min: 1KB, max: 500MB by default)
    - File extension (allowed: .pt, .pth, .h5, .onnx, .safetensors)
    - Model type (allowed: detection, classification, segmentation, severity_scoring)
    - Version tag format (alphanumeric with dots, hyphens, underscores)
    - File integrity via hash verification
    """
    
    # Allowed extensions (normalized to lowercase)
    ALLOWED_EXTENSIONS: List[str] = [
        ext.strip().lower() 
        for ext in settings.MODEL_UPLOAD_ALLOWED_EXTENSIONS.split(",")
    ]
    
    # Allowed model types
    ALLOWED_MODEL_TYPES: List[str] = [
        t.strip().lower() 
        for t in settings.MODEL_UPLOAD_ALLOWED_TYPES.split(",")
    ]
    
    # Size limits
    MIN_SIZE: int = settings.MODEL_UPLOAD_MIN_SIZE
    MAX_SIZE: int = settings.MODEL_UPLOAD_MAX_SIZE
    
    # Version tag pattern: alphanumeric, dots, hyphens, underscores (max 50 chars)
    VERSION_TAG_PATTERN = re.compile(r'^[a-zA-Z0-9._-]{1,50}$')
    
    @classmethod
    async def validate_file_size(cls, file: UploadFile) -> int:
        """
        Validate file size is within allowed limits.
        
        Args:
            file: The uploaded file to validate
            
        Returns:
            File size in bytes
            
        Raises:
            ModelValidationError: If file size is outside allowed limits
        """
        # Read file content to get accurate size
        content = await file.read()
        file_size = len(content)
        
        # Reset file pointer for subsequent reads
        await file.seek(0)
        
        if file_size == 0:
            raise ModelValidationError(
                "File is empty. Please upload a valid model file.",
                error_code="FILE_EMPTY"
            )
        
        if file_size < cls.MIN_SIZE:
            raise ModelValidationError(
                f"File size ({file_size} bytes) is below minimum ({cls.MIN_SIZE} bytes).",
                error_code="FILE_TOO_SMALL"
            )
        
        if file_size > cls.MAX_SIZE:
            max_mb = cls.MAX_SIZE / (1024 * 1024)
            actual_mb = file_size / (1024 * 1024)
            raise ModelValidationError(
                f"File size ({actual_mb:.2f}MB) exceeds maximum limit ({max_mb:.0f}MB).",
                error_code="FILE_TOO_LARGE"
            )
        
        return file_size
    
    @classmethod
    def validate_file_type(cls, filename: str) -> bool:
        """
        Validate file extension is allowed.
        
        Args:
            filename: Name of the file to validate
            
        Returns:
            True if extension is allowed
            
        Raises:
            ModelValidationError: If extension is not allowed or filename is missing
        """
        if not filename or not filename.strip():
            raise ModelValidationError(
                "Filename is required.",
                error_code="FILENAME_MISSING"
            )
        
        # Extract extension
        file_ext = Path(filename).suffix.lower()
        
        # FIXED: Add debug logging to help diagnose extension issues
        logger.debug(f"Validating file: '{filename}' -> extension: '{file_ext}'")
        logger.debug(f"Allowed extensions: {cls.ALLOWED_EXTENSIONS}")
        
        if not file_ext:
            raise ModelValidationError(
                f"File must have one of the allowed extensions: {', '.join(cls.ALLOWED_EXTENSIONS)}",
                error_code="EXTENSION_MISSING"
            )
        
        if file_ext not in cls.ALLOWED_EXTENSIONS:
            # FIXED: Enhanced error message with actual parsed extensions
            raise ModelValidationError(
                f"File extension '{file_ext}' is not allowed. "
                f"Allowed extensions: {', '.join(cls.ALLOWED_EXTENSIONS)}",
                error_code="EXTENSION_NOT_ALLOWED"
            )
        
        logger.debug(f"File extension '{file_ext}' is valid")
        return True
    
    @classmethod
    def validate_model_type(cls, model_type: str) -> bool:
        """
        Validate model type is allowed.
        
        Args:
            model_type: The model type to validate
            
        Returns:
            True if model type is allowed
            
        Raises:
            ModelValidationError: If model type is not allowed
        """
        if not model_type or not model_type.strip():
            raise ModelValidationError(
                "Model type is required.",
                error_code="MODEL_TYPE_MISSING"
            )
        
        model_type_lower = model_type.strip().lower()
        
        if model_type_lower not in cls.ALLOWED_MODEL_TYPES:
            raise ModelValidationError(
                f"Model type '{model_type}' is not allowed. "
                f"Allowed types: {', '.join(cls.ALLOWED_MODEL_TYPES)}",
                error_code="MODEL_TYPE_NOT_ALLOWED"
            )
        
        return True
    
    @classmethod
    def validate_version_tag(cls, version_tag: str) -> bool:
        """
        Validate version tag format.
        
        Args:
            version_tag: The version tag to validate
            
        Returns:
            True if version tag format is valid
            
        Raises:
            ModelValidationError: If version tag format is invalid
        """
        if not version_tag or not version_tag.strip():
            raise ModelValidationError(
                "Version tag is required.",
                error_code="VERSION_TAG_MISSING"
            )
        
        version_tag = version_tag.strip()
        
        if not cls.VERSION_TAG_PATTERN.match(version_tag):
            raise ModelValidationError(
                "Version tag can only contain letters, numbers, dots, hyphens, and underscores. "
                "Maximum 50 characters.",
                error_code="VERSION_TAG_INVALID_FORMAT"
            )
        
        return True
    
    @classmethod
    def calculate_file_hash(cls, content: bytes, algorithm: Optional[str] = None) -> str:
        """
        Calculate hash of file content for integrity verification.
        
        Args:
            content: File content as bytes
            algorithm: Hash algorithm to use (default: from settings)
            
        Returns:
            Hexadecimal hash string
        """
        algorithm = algorithm or settings.MODEL_HASH_ALGORITHM
        
        if algorithm == "sha256":
            return hashlib.sha256(content).hexdigest()
        elif algorithm == "md5":
            return hashlib.md5(content).hexdigest()
        elif algorithm == "sha1":
            return hashlib.sha1(content).hexdigest()
        else:
            # Default to SHA-256
            return hashlib.sha256(content).hexdigest()
    
    @classmethod
    async def validate_file_integrity(
        cls, 
        file: UploadFile, 
        expected_hash: Optional[str] = None
    ) -> str:
        """
        Validate file integrity by computing hash.
        
        Args:
            file: The uploaded file to validate
            expected_hash: Optional expected hash to compare against
            
        Returns:
            Computed hash of the file
            
        Raises:
            ModelValidationError: If computed hash doesn't match expected hash
        """
        # Read file content
        content = await file.read()
        
        # Reset file pointer
        await file.seek(0)
        
        # Calculate hash
        computed_hash = cls.calculate_file_hash(content)
        
        # Compare with expected hash if provided
        if expected_hash:
            if computed_hash != expected_hash.lower():
                raise ModelValidationError(
                    "File integrity check failed. Hash mismatch detected.",
                    error_code="HASH_MISMATCH"
                )
        
        return computed_hash
    
    @classmethod
    async def validate_all(
        cls,
        file: UploadFile,
        model_type: str,
        version_tag: str,
        expected_hash: Optional[str] = None
    ) -> dict:
        """
        Perform all validations on an uploaded model file.
        
        Args:
            file: The uploaded file to validate
            model_type: The model type
            version_tag: The version tag
            expected_hash: Optional expected hash for integrity check
            
        Returns:
            Dictionary containing validation results:
            - file_size: Size in bytes
            - file_hash: Computed hash
            - extension_valid: True if extension is valid
            - model_type_valid: True if model type is valid
            - version_tag_valid: True if version tag is valid
            
        Raises:
            ModelValidationError: If any validation fails
        """
        # Validate file size
        file_size = await cls.validate_file_size(file)
        
        # Validate file type
        cls.validate_file_type(file.filename or "")
        
        # Validate model type
        cls.validate_model_type(model_type)
        
        # Validate version tag
        cls.validate_version_tag(version_tag)
        
        # Validate file integrity and compute hash
        file_hash = await cls.validate_file_integrity(file, expected_hash)
        
        # FIXED: Ensure file pointer is reset after all validation
        # This guarantees the file can be read again by storage service
        await file.seek(0)
        
        return {
            "file_size": file_size,
            "file_hash": file_hash,
            "extension_valid": True,
            "model_type_valid": True,
            "version_tag_valid": True,
        }
