# Model Management Function - Error Report

**Generated:** 2026-03-28  
**Component:** Backend - AI Module (PBI-27)  
**Scope:** Model Management Router, Services, Repository, and Schemas

---

## Executive Summary

A comprehensive review of the Model Management functionality revealed **12 critical and moderate issues** across the router, services, repository, and schemas. These issues range from missing error handling to schema inconsistencies and unused code.

---

## Critical Issues

### 1. **Missing Error Handling in `get_model_versions` Router**
**File:** `backend/app/modules/ai/routes/model_management_router.py`  
**Line:** ~188-200

**Issue:** The `get_model_versions` endpoint doesn't catch `ModelServiceError` exceptions, unlike other endpoints (`upload_model`, `activate_model`, `rollback_model`, `delete_model`).

```python
@router.get(
    "/{model_id}/versions",
    # ...
)
async def get_model_versions(
    model_id: UUID = Path(...),
    current_user: User = Depends(require_admin_or_moderator),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    service = get_model_service(db)
    result = await service.get_model_versions(model_id)  # ❌ No try-except
    
    return SuccessResponse(
        message="Model versions retrieved successfully",
        data=result,
    )
```

**Impact:** If a model is not found, the error will propagate as a 500 Internal Server Error instead of a proper 400 Bad Request response.

**Fix Required:**
```python
try:
    service = get_model_service(db)
    result = await service.get_model_versions(model_id)
    return SuccessResponse(...)
except ModelServiceError as e:
    return ErrorResponse(
        message=e.message,
        error_code=e.error_code,
        status_code=400
    )
```

---

### 2. **Missing Error Handling in `get_model_metadata` Router**
**File:** `backend/app/modules/ai/routes/model_management_router.py`  
**Line:** ~321-335

**Issue:** Same as Issue #1 - no exception handling for `ModelServiceError`.

```python
@router.get(
    "/{model_id}/metadata",
    # ...
)
async def get_model_metadata(
    model_id: UUID = Path(...),
    # ...
) -> SuccessResponse:
    service = get_model_service(db)
    result = await service.get_model_metadata(model_id)  # ❌ No try-except
    
    return SuccessResponse(...)
```

**Impact:** 500 errors when model not found.

---

### 3. **Missing Error Handling in `update_model_metadata` Router**
**File:** `backend/app/modules/ai/routes/model_management_router.py`  
**Line:** ~340-360

**Issue:** No exception handling for `ModelServiceError`.

```python
@router.put(
    "/{model_id}/metadata",
    # ...
)
async def update_model_metadata(
    model_id: UUID = Path(...),
    # ...
) -> SuccessResponse:
    service = get_model_service(db)
    result = await service.update_model_metadata(
        model_id=model_id,
        description=description,
        is_beta=is_beta,
        updated_by=current_user.user_id
    )  # ❌ No try-except
    
    return SuccessResponse(...)
```

---

### 4. **Missing Error Handling in `get_runtime_status` Router**
**File:** `backend/app/modules/ai/routes/model_management_router.py`  
**Line:** ~365-380

**Issue:** No exception handling for `ModelServiceError`.

---

### 5. **Missing Error Handling in `reload_model` Router**
**File:** `backend/app/modules/ai/routes/model_management_router.py`  
**Line:** ~385-430

**Issue:** The `reload_model` endpoint catches `ModelServiceError` but the success response is incomplete - it uses hardcoded "unknown" for `previous_version`.

```python
result = ModelReloadResponse(
    success=True,
    model_type=model_type,
    previous_version="unknown",  # ❌ Hardcoded placeholder
    new_version=version_tag or "active",
    reloaded_at=datetime.now(timezone.utc),
    message=f"Model reload triggered for {model_type}"
)
```

**Impact:** Incomplete implementation. The comment says "Will be filled in Phase 5" but this should be either completed or clearly marked as TODO.

---

### 6. **Inconsistent Response Schema in `get_model_versions`**
**File:** `backend/app/modules/ai/routes/model_management_router.py`  
**Line:** ~188-200

**Issue:** The endpoint returns `SuccessResponse[dict]` instead of using the proper schema `SuccessResponse[ModelVersionListResponse]`.

```python
@router.get(
    "/{model_id}/versions",
    response_model=SuccessResponse[dict],  # ❌ Should use ModelVersionListResponse
    # ...
)
```

**Impact:** Loss of type safety and API documentation clarity.

---

### 7. **Unused Static Method in ModelRepository**
**File:** `backend/app/modules/ai/repository/model_repository.py`  
**Line:** ~169-177

**Issue:** The method `get_active_model_version` is defined as a static method but is never used and has no implementation.

```python
async def get_active_model_version(model_type: str) -> Optional[str]:
    """
    Get the version tag of the active model.
    
    Args:
        model_type: Model type
    
    Returns:
        Version tag if active model exists, None otherwise
    """
    # This is a static method for convenience
    pass  # ❌ No implementation
```

**Impact:** Dead code that may confuse developers. Should be removed or implemented.

---

## Moderate Issues

### 8. **Schema Inconsistency: `ModelMetadataResponse` Missing `model_type` Field**
**File:** `backend/app/modules/ai/schemas/model_schemas.py`  
**Line:** ~221-232

**Issue:** The `ModelMetadataResponse` schema doesn't include `model_type`, but the service returns it in some cases.

```python
class ModelMetadataResponse(BaseModel):
    model_id: UUID = Field(..., description="Model ID")
    version_tag: str = Field(..., description="Version tag")
    description: Optional[str] = Field(None, description="Model description")
    is_beta: bool = Field(..., description="Beta status")
    metrics: Optional[ModelMetrics] = Field(None, description="Performance metrics")
    file_info: Dict[str, Any] = Field(..., description="File information")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    # ❌ Missing: model_type field
```

**Impact:** API consumers cannot determine the model type from metadata endpoint.

---

### 9. **Incorrect File Info Structure in `ModelMetadataResponse`**
**File:** `backend/app/modules/ai/services/model_service.py`  
**Line:** ~468-485

**Issue:** The service returns `file_info` with keys `path`, `size_bytes`, `hash`, but the schema documentation suggests different structure.

```python
return ModelMetadataResponse(
    model_id=model.model_id,
    version_tag=model.version_tag,
    description=model.description,
    is_beta=model.is_beta,
    metrics=ModelMetrics(**model.metrics) if model.metrics else None,
    file_info={
        "path": model.file_path,  # ❌ Inconsistent key naming
        "size_bytes": model.file_size_bytes,
        "hash": model.file_hash
    },
    # ...
)
```

**Impact:** API inconsistency. Should use consistent naming like `file_path`, `file_size_bytes`, `file_hash`.

---

### 10. **Missing Actor Email in Audit Logging**
**File:** `backend/app/modules/ai/services/model_service.py`  
**Multiple locations**

**Issue:** The `AuditService` supports `actor_email` parameter, but the `ModelService` never passes it, only `actor_id` and `actor_ip`.

```python
await self.repository.log_version_change(
    model_id=model_id,
    action="model_upload",
    to_version=request.version_tag,
    actor_id=uploaded_by,
    actor_ip=actor_ip,
    details={...}
)
# ❌ Missing: actor_email
```

**Impact:** Audit logs are incomplete without email information for better traceability.

---

### 11. **`get_actor_info` Returns Optional IP Without Handling**
**File:** `backend/app/modules/ai/routes/model_management_router.py`  
**Line:** ~56-60

**Issue:** The helper function returns `Optional[str]` for IP, but `request.client` could be `None` in some deployment scenarios (e.g., behind certain proxies).

```python
def get_actor_info(request: Request, current_user: User) -> tuple[Optional[UUID], Optional[str]]:
    """Extract actor information from request."""
    return current_user.user_id, request.client.host if request.client else None
```

**Recommendation:** Consider extracting IP from headers (X-Forwarded-For, X-Real-IP) for production deployments.

---

### 12. **Test File: Inconsistent Error Status Code Assertion**
**File:** `backend/tests/test_model_management_router.py`  
**Line:** ~237-242

**Issue:** The test `test_get_model_details_not_found` has a vague assertion that accepts multiple status codes.

```python
def test_get_model_details_not_found():
    """Test getting non-existent model returns error."""
    # ...
    res = client.get(f"/api/v1/admin/models/{model_id}")
    # The router catches service errors and returns error response
    assert res.status_code in [200, 400]  # ❌ Unclear expectation
```

**Impact:** Test doesn't verify the correct behavior. Should assert for a specific status code (likely 400).

---

## Minor Issues / Code Quality

### 13. **Duplicate Import Statement**
**File:** `backend/app/modules/ai/routes/model_management_router.py`  
**Line:** ~17-18

```python
from app.core.dependencies import get_db, require_admin, require_admin_or_moderator
from app.core.dependencies.database import get_db  # ❌ Duplicate import
```

---

### 14. **Inconsistent Logging Format**
**File:** `backend/app/modules/ai/services/model_service.py`

**Issue:** Some log messages use f-strings, others use format strings. Should be consistent.

```python
logger.info(f"Starting model upload: {request.model_type} v{request.version_tag}")
logger.info(f"Model uploaded successfully: {model.model_id}")
# But in storage_service.py:
logger.info("Model storage directories initialized:")
```

---

### 15. **Missing Docstring for `get_model_service` Helper**
**File:** `backend/app/modules/ai/routes/model_management_router.py`  
**Line:** ~50-53

```python
def get_model_service(db: AsyncSession) -> ModelService:
    """Get model service with dependencies."""  # ❌ Too brief
    return ModelService(db=db, storage_service=get_storage_service())
```

---

## Summary Table

| # | Issue | Severity | File | Status |
|---|-------|----------|------|--------|
| 1 | Missing error handling in `get_model_versions` | Critical | model_management_router.py | 🔴 |
| 2 | Missing error handling in `get_model_metadata` | Critical | model_management_router.py | 🔴 |
| 3 | Missing error handling in `update_model_metadata` | Critical | model_management_router.py | 🔴 |
| 4 | Missing error handling in `get_runtime_status` | Critical | model_management_router.py | 🔴 |
| 5 | Incomplete `reload_model` implementation | Critical | model_management_router.py | 🔴 |
| 6 | Inconsistent response schema in `get_model_versions` | Moderate | model_management_router.py | 🟡 |
| 7 | Unused static method `get_active_model_version` | Moderate | model_repository.py | 🟡 |
| 8 | Missing `model_type` in `ModelMetadataResponse` | Moderate | model_schemas.py | 🟡 |
| 9 | Inconsistent file_info key naming | Moderate | model_service.py | 🟡 |
| 10 | Missing actor_email in audit logging | Moderate | model_service.py | 🟡 |
| 11 | Incomplete IP address extraction | Minor | model_management_router.py | 🟢 |
| 12 | Unclear test assertion | Minor | test_model_management_router.py | 🟢 |
| 13 | Duplicate import statement | Minor | model_management_router.py | 🟢 |
| 14 | Inconsistent logging format | Minor | model_service.py | 🟢 |
| 15 | Missing docstring detail | Minor | model_management_router.py | 🟢 |

---

## Recommendations

### Immediate Actions (Critical)
1. Add try-except blocks to all endpoints that call `ModelService` methods
2. Complete or mark TODO for `reload_model` implementation
3. Fix response schema for `get_model_versions`

### Short-term (Moderate)
4. Add `model_type` field to `ModelMetadataResponse`
5. Standardize `file_info` structure across service and schema
6. Add actor_email to audit logging (requires fetching user email)
7. Remove or implement unused `get_active_model_version` method

### Long-term (Minor)
8. Improve IP address extraction for production deployments
9. Fix test assertions for clarity
10. Remove duplicate imports
11. Standardize logging format
12. Improve documentation

---

## Files Requiring Changes

1. `backend/app/modules/ai/routes/model_management_router.py` - **Primary**
2. `backend/app/modules/ai/services/model_service.py`
3. `backend/app/modules/ai/schemas/model_schemas.py`
4. `backend/app/modules/ai/repository/model_repository.py`
5. `backend/tests/test_model_management_router.py`

---

## Testing Recommendations

After fixes:
- Run full test suite: `pytest backend/tests/test_model_management_router.py -v`
- Add integration tests for error scenarios
- Add tests for 404 (not found) cases
- Add tests for concurrent model operations
- Add load testing for model upload endpoints

---

**Report End**
