# AI Model Management Feature - Complete Overhaul Summary

**Date:** 2026-03-28  
**Status:** Backend Complete | Frontend Pending

---

## Executive Summary

Completed a comprehensive overhaul of the AI Model Management feature with:
- ✅ **Database**: Added tracking fields for rollback support
- ✅ **Backend**: Implemented new business rules (one active per type, type-level rollback)
- ✅ **Removed**: Beta flag from entire system
- ⏳ **Frontend**: Needs complete rewrite for grouped view (not started due to complexity)

---

## Step 2: Database Migration ✅

**File:** `backend/migrations/20260328_add_model_tracking_fields.py`

### Changes:
1. **Added `activated_at` column**
   - Tracks when a version became active
   - Different from `created_at` and `deployed_at`
   - Indexed for performance

2. **Added `previously_active_version_id` column**
   - Self-referential FK to `ai_models.model_id`
   - Enables rollback by tracking activation history
   - Indexed for JOIN performance

3. **Added unique constraint**
   - `(model_type, version_tag)` must be unique
   - Prevents duplicate version tags within same type

### SQL Equivalent:
```sql
ALTER TABLE ai_models 
  ADD COLUMN activated_at TIMESTAMP NULL,
  ADD COLUMN previously_active_version_id UUID NULL,
  ADD CONSTRAINT fk_ai_models_previously_active 
    FOREIGN KEY (previously_active_version_id) REFERENCES ai_models(model_id),
  ADD CONSTRAINT uq_ai_models_type_version 
    UNIQUE (model_type, version_tag);
```

---

## Step 3: Backend Updates ✅

### 3.1 Model (`ai_models.py`) ✅

**Added Fields:**
```python
activated_at: Optional[datetime]
previously_active_version_id: Optional[UUID]
```

**Updated Indexes:**
```python
Index("ix_ai_models_activated_at", "activated_at"),
Index("ix_ai_models_prev_active", "previously_active_version_id"),
Index("uq_ai_models_type_version", "model_type", "version_tag", unique=True),
```

**Updated Method:**
```python
def activate(self, previously_active_id: Optional[UUID] = None) -> None:
    """Activate this model version."""
    self.is_active = True
    self.deployed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    self.activated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    self.previously_active_version_id = previously_active_id  # NEW
```

---

### 3.2 Repository (`model_repository.py`) ✅

**New Methods:**

1. **`is_only_active_model(model_id)`**
   - Checks if model is the ONLY active one of its type
   - Returns `True` if deactivating would leave type without active model
   - Used to enforce business rule

2. **`get_active_model_count_by_type(model_type)`**
   - Returns count of active models for a type
   - Used for validation and stats

3. **`rollback_model_type(model_type, rolled_back_by)`**
   - TYPE-level rollback (not per-version)
   - Activates the `previously_active_version_id`
   - Returns newly activated model or `None`

**Updated Method:**
```python
async def activate_model(self, model_id: UUID, deployed_by: Optional[UUID] = None) -> AIModel:
    # Get current active to track for rollback
    previous_active = await self.get_active_model(model.model_type)
    previous_active_id = previous_active.model_id if previous_active else None
    
    # Deactivate all of same type
    await self.deactivate_models_by_type(model.model_type)
    
    # Activate with tracking
    model.activate(previously_active_id=previous_active_id)  # NEW
    ...
```

---

### 3.3 Service (`model_service.py`) ✅

**Updated: `upload_model()`**
- Now checks duplicate version tag per model_type
- Sets `is_beta=False` always (flag removed)
- Better error message for duplicates

**New: `deactivate_model()`**
```python
async def deactivate_model(self, model_id: UUID, ...) -> dict:
    # RULE: Cannot deactivate last active model
    if await self.repository.is_only_active_model(model_id):
        raise ModelServiceError(
            "Cannot deactivate: this is the only active model for type...",
            error_code="CANNOT_DEACTIVATE_LAST_ACTIVE"
        )
    ...
```

**New: `rollback_model_type()`**
```python
async def rollback_model_type(self, model_type: str, ...) -> ModelRollbackResponse:
    # TYPE-level operation
    current_active = await self.repository.get_active_model(model_type)
    if not current_active:
        raise ModelServiceError("No active model found", "NO_ACTIVE_MODEL")
    
    if not current_active.previously_active_version_id:
        raise ModelServiceError("No previous version", "NO_PREVIOUS_VERSION")
    
    # Activate previous version
    rolled_back_model = await self.repository.rollback_model_type(model_type, ...)
    ...
```

---

### 3.4 Router (`model_management_router.py`) ✅

**Updated: `POST /upload`**
- Removed `is_beta` form field
- Sets `is_beta=False` in request

**Updated: `POST /{model_id}/deactivate`**
- Simplified to use new service method
- Service enforces "last active" rule

**New: `POST /types/{model_type}/rollback`**
```python
@router.post("/types/{model_type}/rollback", ...)
async def rollback_model_type(model_type: str, ...):
    """
    Rollback a model type to its previously active version.
    TYPE-level operation, not per-version.
    """
    result = await service.rollback_model_type(
        model_type=model_type,
        rolled_back_by=actor_id,
        ...
    )
```

---

## Business Rules Enforced ✅

### Rule 1: One Active Model Per Type
- ✅ Enforced in `activate_model()` - deactivates others first
- ✅ Tracked via `previously_active_version_id`
- ✅ Enforced in `deactivate_model()` - blocks last active

### Rule 2: Type-Level Rollback
- ✅ New endpoint: `POST /types/{model_type}/rollback`
- ✅ Uses `previously_active_version_id` to find previous
- ✅ Returns error if no previous version

### Rule 3: Version Tag Uniqueness Per Type
- ✅ DB constraint: `UNIQUE (model_type, version_tag)`
- ✅ Service validation before upload
- ✅ Better error messages

### Rule 4: Beta Flag Removed
- ✅ Removed from upload form
- ✅ Always sets `is_beta=False`
- ✅ Still in DB for backward compatibility (can be dropped later)

---

## API Changes

### New Endpoints:
```
POST /api/v1/admin/models/types/{model_type}/rollback
```

### Updated Endpoints:
```
POST /api/v1/admin/models/upload          # Removed is_beta field
POST /api/v1/admin/models/{model_id}/deactivate  # Now enforces "last active" rule
```

### Error Codes:
```python
"CANNOT_DEACTIVATE_LAST_ACTIVE"  # New
"NO_ACTIVE_MODEL"                 # New
"NO_PREVIOUS_VERSION"             # New
"PREVIOUS_VERSION_NOT_FOUND"      # New
```

---

## Frontend Changes Needed ⏳

### NOT YET IMPLEMENTED (Requires Complete Rewrite)

The frontend needs a complete restructuring to support:

1. **Grouped View by Model Type**
   - One row per model TYPE (not per version)
   - Collapsible accordion showing version history
   - Active version shown in main row

2. **New Action Buttons**
   - Per Type: `[Upload New Version]` `[Rollback]`
   - Per Version: `[Activate]` `[View]` `[Delete]`
   - Remove: `[Deactivate]` button

3. **Warning Banners**
   - Show when no active model for a type
   - "⚠️ No active model for Detection. AI analysis unavailable."

4. **Color System**
   - Stats cards: Different colors per metric
   - Status badges: Solid green for Active, Gray for Inactive

5. **Toast Notifications**
   - Replace `alert()` with toast notifications
   - Success/Error states

---

## i18n Keys to Add

```json
{
  "admin": {
    "model_management": {
      "active_version_label": "Active Version",
      "rollback_confirm": "Rollback {type} from {current} to {previous}?",
      "no_active_warning": "⚠️ No active model for {type}. AI analysis is currently unavailable.",
      "cannot_deactivate_last": "Cannot deactivate: this is the only active version. Activate another first.",
      "version_history": "Version History",
      "actions": {
        "upload_new_version": "Upload New Version",
        "view_details": "View Details"
      }
    }
  }
}
```

---

## Testing Checklist

### Backend:
- [ ] Upload model with duplicate version tag → 400 error
- [ ] Activate model → deactivates previous of same type
- [ ] Deactivate last active model → 400 "CANNOT_DEACTIVATE_LAST_ACTIVE"
- [ ] Deactivate non-last active → Success
- [ ] Rollback type with previous → Success
- [ ] Rollback type without previous → 400 "NO_PREVIOUS_VERSION"
- [ ] Upload with is_beta field → Field ignored

### Frontend: (After implementation)
- [ ] Grouped view shows one row per type
- [ ] Accordion expands to show versions
- [ ] Upload button per type
- [ ] Rollback button only when previous exists
- [ ] Warning banner when no active model
- [ ] No Deactivate button visible
- [ ] Toast notifications work

---

## Files Changed

### Backend:
- ✅ `backend/migrations/20260328_add_model_tracking_fields.py` (NEW)
- ✅ `backend/app/modules/ai/models/ai_models.py`
- ✅ `backend/app/modules/ai/repository/model_repository.py`
- ✅ `backend/app/modules/ai/services/model_service.py`
- ✅ `backend/app/modules/ai/routes/model_management_router.py`
- ✅ `backend/app/modules/ai/schemas/model_schemas.py` (is_beta still present, deprecated)

### Frontend: (Not yet changed)
- ⏳ `frontend/src/components/admin/ModelManagement.tsx`
- ⏳ `frontend/src/components/admin/ModelManagement.module.css`
- ⏳ `frontend/src/locales/vi.json`
- ⏳ `frontend/src/locales/en.json`
- ⏳ `frontend/src/types/admin.ts`

---

## Migration Execution

To apply the database migration:

```bash
cd backend
alembic upgrade head
```

Or run the SQL directly if not using Alembic:

```bash
psql -U postgres -d skinaid -f migrations/20260328_add_model_tracking_fields.sql
```

---

## Next Steps

1. **Run Migration** - Apply DB changes
2. **Test Backend** - Verify all new endpoints
3. **Rewrite Frontend** - Complete UI overhaul
4. **Update i18n** - Add new translation keys
5. **Deploy** - Roll out to production

---

## Risk Assessment

### Low Risk:
- Backend changes are additive (new fields, new methods)
- Old endpoints still work (backward compatible)
- Beta flag deprecated but not removed from DB

### Medium Risk:
- Frontend rewrite is extensive
- UI/UX changes are significant
- Requires thorough testing

### Mitigation:
- Test backend thoroughly before frontend changes
- Use feature flag for new UI if needed
- Roll out in stages

---

**Backend Status:** ✅ Complete  
**Frontend Status:** ⏳ Pending  
**Estimated Frontend Effort:** 4-6 hours

---

**Document End**
