# AI Model Management API Documentation (PBI-27)

## Overview

This API provides comprehensive model lifecycle management for AI models in the SkinAid system. It supports uploading, versioning, activation, rollback, and deletion of AI models with full audit trail.

## Base URL

```
/api/v1/admin/models
```

## Authentication

All endpoints require admin authentication via Bearer token in the Authorization header:

```
Authorization: Bearer <your_token>
```

Some internal endpoints (runtime reload) require API key:

```
X-API-Key: <api_key>
```

---

## Endpoints

### 1. Upload Model

**POST** `/upload`

Upload a new AI model version with validation.

**Request Type:** `multipart/form-data`

**Parameters:**
- `file` (required): Model file (.pt, .pth, .h5, .onnx, .safetensors)
- `model_type` (required): Model type (detection, classification, segmentation, severity_scoring)
- `version_tag` (required): Version tag (e.g., v1.0.0)
- `description` (optional): Model description
- `is_beta` (optional): Mark as beta version (true/false)

**Response:** `ModelUploadResponse`

```json
{
  "success": true,
  "message": "Model uploaded successfully",
  "data": {
    "success": true,
    "model_id": "uuid",
    "version_id": "uuid",
    "version_tag": "v1.0.0",
    "file_size_bytes": 1048576,
    "file_path": "/models/detection/uuid/v1.0.0/model.bin",
    "uploaded_at": "2024-01-01T00:00:00Z",
    "message": "Model detection v1.0.0 uploaded successfully"
  }
}
```

**Validation:**
- File size: 1KB - 500MB
- Allowed extensions: .pt, .pth, .h5, .onnx, .safetensors
- Version tag: alphanumeric, dots, hyphens, underscores (max 50 chars)

---

### 2. List Models

**GET** `/`

List all AI models with filtering and pagination.

**Query Parameters:**
- `model_type` (optional): Filter by model type
- `status` (optional): Filter by status (active, inactive, deprecated, all) - default: "all"
- `include_beta` (optional): Include beta versions - default: true
- `search` (optional): Search in name/description

**Response:** `ModelListResponse`

```json
{
  "success": true,
  "message": "Models retrieved successfully",
  "data": {
    "models": [
      {
        "model_id": "uuid",
        "model_type": "detection",
        "name": "detection - v1.0.0",
        "description": "Wound detection model",
        "current_version": "v1.0.0",
        "total_versions": 3,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-02T00:00:00Z",
        "metrics": {
          "accuracy": 0.94,
          "precision": 0.92,
          "recall": 0.93
        }
      }
    ],
    "active_version": "v1.0.0",
    "total": 1,
    "filters_applied": {
      "model_type": null,
      "status": "all",
      "include_beta": true,
      "search": null
    }
  }
}
```

---

### 3. Get Model Detail

**GET** `/{model_id}`

Get detailed information about a specific model including all versions.

**Path Parameters:**
- `model_id`: Model UUID

**Response:** `ModelDetailResponse`

```json
{
  "success": true,
  "message": "Model details retrieved successfully",
  "data": {
    "model": { ... },
    "versions": [ ... ],
    "active_version": { ... },
    "version_history": [
      {
        "action": "model_upload",
        "from_version": null,
        "to_version": "v1.0.0",
        "actor_id": "uuid",
        "timestamp": "2024-01-01T00:00:00Z",
        "details": { "file_size": 1048576 }
      }
    ]
  }
}
```

---

### 4. Activate Model

**POST** `/{model_id}/activate`

Activate a specific model version. Deactivates any currently active model of the same type.

**Path Parameters:**
- `model_id`: Model UUID to activate

**Query Parameters:**
- `force` (optional): Force activation even if validation fails - default: false

**Response:** `ModelActivateResponse`

```json
{
  "success": true,
  "message": "Model activated successfully",
  "data": {
    "success": true,
    "active_version": "v1.0.0",
    "previous_version": "v0.9.0",
    "activated_at": "2024-01-02T00:00:00Z",
    "model_id": "uuid",
    "message": "Activated detection v1.0.0"
  }
}
```

---

### 5. Rollback Model

**POST** `/{model_id}/rollback`

Rollback to a previous model version.

**Path Parameters:**
- `model_id`: Current model UUID

**Query Parameters:**
- `target_version` (optional): Specific version to rollback to (defaults to previous version)
- `reason` (optional): Reason for rollback

**Response:** `ModelRollbackResponse`

```json
{
  "success": true,
  "message": "Model rolled back successfully",
  "data": {
    "success": true,
    "previous_version": "v1.0.0",
    "rolled_back_version": "v0.9.0",
    "rolled_back_at": "2024-01-02T00:00:00Z",
    "model_id": "uuid",
    "message": "Rolled back to v0.9.0"
  }
}
```

---

### 6. Delete Model

**DELETE** `/{model_id}`

Soft-delete a model version. Cannot delete active models.

**Path Parameters:**
- `model_id`: Model UUID to delete

**Query Parameters:**
- `reason` (optional): Reason for deletion

**Response:** `ModelDeleteResponse`

```json
{
  "success": true,
  "message": "Model deleted successfully",
  "data": {
    "success": true,
    "deleted_version": "v0.8.0",
    "deleted_at": "2024-01-02T00:00:00Z",
    "is_permanent": false,
    "message": "Model v0.8.0 deleted successfully"
  }
}
```

---

### 7. Get Model Metadata

**GET** `/{model_id}/metadata`

Get metadata for a specific model.

**Response:** `ModelMetadata`

```json
{
  "success": true,
  "message": "Model metadata retrieved successfully",
  "data": {
    "model_id": "uuid",
    "version_tag": "v1.0.0",
    "description": "Wound detection model",
    "is_beta": false,
    "metrics": {
      "accuracy": 0.94,
      "precision": 0.92
    },
    "file_info": {
      "path": "/models/detection/uuid/v1.0.0/model.bin",
      "size_bytes": 1048576,
      "hash": "sha256_hash"
    },
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-02T00:00:00Z"
  }
}
```

---

### 8. Update Model Metadata

**PUT** `/{model_id}/metadata`

Update metadata for a specific model.

**Request Body:**
```json
{
  "description": "Updated description",
  "is_beta": false
}
```

**Response:** `ModelMetadata`

---

### 9. Get Runtime Status

**GET** `/runtime/status`

Get runtime status of all loaded models.

**Response:**

```json
{
  "success": true,
  "message": "Runtime status retrieved successfully",
  "data": {
    "detection": {
      "loaded_version": "v1.0.0",
      "model_path": "/models/detection/uuid/v1.0.0/model.bin",
      "loaded_at": "2024-01-02T00:00:00Z",
      "is_ready": true
    },
    "classification": {
      "loaded_version": "v1.0.0",
      "model_path": "/models/classification/uuid/v1.0.0/model.bin",
      "loaded_at": "2024-01-02T00:00:00Z",
      "is_ready": true
    }
  }
}
```

---

### 10. Reload Model (Internal)

**POST** `/runtime/reload`

Reload a model at runtime. Requires API key authentication.

**Request Body:**
```json
{
  "model_type": "detection",
  "version_tag": "v1.0.0",
  "api_key": "your_api_key"
}
```

**Response:** `ModelReloadResponse`

```json
{
  "success": true,
  "message": "Model reload triggered successfully",
  "data": {
    "success": true,
    "model_type": "detection",
    "previous_version": "v0.9.0",
    "new_version": "v1.0.0",
    "reloaded_at": "2024-01-02T00:00:00Z",
    "message": "Model reload triggered for detection"
  }
}
```

---

### 11. Get Model Audit Logs

**GET** `/{model_id}/logs`

Get audit logs for a specific model.

**Path Parameters:**
- `model_id`: Model UUID

**Query Parameters:**
- `limit` (optional): Number of logs to retrieve (1-200) - default: 50

**Response:** `AuditLogListResponse`

```json
{
  "success": true,
  "message": "Audit logs retrieved successfully",
  "data": {
    "logs": [
      {
        "log_id": "uuid",
        "action": "model_activate",
        "resource_type": "ai_model",
        "resource_id": "uuid",
        "actor_id": "uuid",
        "details": { "previous_version": "v0.9.0" },
        "timestamp": "2024-01-02T00:00:00Z",
        "ip_address": "192.168.1.1"
      }
    ],
    "total": 10,
    "filters_applied": {
      "model_id": "uuid",
      "limit": 50
    }
  }
}
```

---

## Error Responses

All endpoints return errors in this format:

```json
{
  "success": false,
  "message": "Error message",
  "error_code": "ERROR_CODE",
  "error_details": { ... },
  "timestamp": "2024-01-02T00:00:00Z",
  "status_code": 400
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Input validation failed |
| `FILE_TOO_LARGE` | File exceeds 500MB limit |
| `FILE_TOO_SMALL` | File below 1KB minimum |
| `EXTENSION_NOT_ALLOWED` | File extension not allowed |
| `MODEL_TYPE_NOT_ALLOWED` | Invalid model type |
| `VERSION_TAG_INVALID_FORMAT` | Invalid version tag format |
| `DUPLICATE_VERSION` | Version tag already exists |
| `MODEL_NOT_FOUND` | Model not found |
| `MODEL_DELETED` | Cannot operate on deleted model |
| `CANNOT_DELETE_ACTIVE` | Cannot delete active model |
| `NO_PREVIOUS_VERSION` | No previous version to rollback to |
| `INVALID_API_KEY` | Invalid API key for internal endpoints |

---

## Audit Trail

All model lifecycle events are logged:

- `model_upload`: New model uploaded
- `model_activate`: Model version activated
- `model_rollback`: Model rolled back
- `model_delete`: Model deleted
- `model_reload`: Model reloaded at runtime
- `validation_failed`: Validation failed during upload

Each log entry includes:
- Actor ID and email
- IP address
- Timestamp
- Action details
- Result status

---

## Best Practices

1. **Version Tags**: Use semantic versioning (vMAJOR.MINOR.PATCH)
2. **Beta Versions**: Mark experimental models as beta
3. **Testing**: Test models in staging before production activation
4. **Rollback Plan**: Always keep previous version available for rollback
5. **Audit Review**: Regularly review audit logs for compliance
6. **File Integrity**: All files are hashed with SHA-256 for integrity verification

---

## Rate Limiting

- Upload: 10 requests per minute
- Other operations: 100 requests per minute

---

## Support

For issues or questions, contact the development team.
