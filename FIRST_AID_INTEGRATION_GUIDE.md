# FirstAidManagement.tsx - Key Integration Points

## This document shows the exact changes needed to integrate the new components

### 1. Update Imports (Lines 1-24)

```typescript
import React, { useState, useEffect } from 'react';
import {
  Plus,
  Search,
  Edit2,
  Trash2,
  BookOpen,
  Activity,
  AlertCircle,
  ChevronLeft,    // NEW - for pagination
  ChevronRight,   // NEW - for pagination
  Loader2         // NEW - for loading states
} from 'lucide-react';
import {
  searchFirstAidGuides,
  getWoundTypes,
  getFirstAidStatistics,
  createFirstAidGuide,
  updateFirstAidGuide,
  deleteFirstAidGuide
} from '../../services/firstAidService';
import { useToast } from '../../contexts/ToastContext';
// NEW IMPORTS
import FirstAidViewModal from './FirstAidViewModal';
import FirstAidFormModal from './FirstAidFormModal';
import ConfirmDialog from '../common/ConfirmDialog';
import styles from './FirstAidManagement.module.css';
```

### 2. Add New State Variables (After line ~100)

```typescript
  // Existing states...
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDeletingGuide, setIsDeletingGuide] = useState<string | null>(null);

  // NEW: Pagination state
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(9);
  const [totalCount, setTotalCount] = useState(0);

  // NEW: Confirm dialog state  
  const [confirmDialog, setConfirmDialog] = useState({
    isOpen: false,
    title: '',
    message: '',
    variant: 'warning' as 'danger' | 'warning' | 'info',
    onConfirm: () => {}
  });
```

### 3. Update fetchGuides Function (Around line 145)

```typescript
  const fetchGuides = async () => {
    try {
      setLoading(true);
      setError(null);

      const params: any = {
        wound_type: selectedWoundType,
        severity: selectedSeverity,
        limit,                          // CHANGED: use state variable
        offset: (page - 1) * limit      // CHANGED: calculate from page
      };

      if (selectedActiveStatus !== 'all') {
        params.is_active = selectedActiveStatus === 'true';
      }

      if (searchTerm) {
        params.search = searchTerm;
      }

      const response = await searchFirstAidGuides(params);

      if (response.success && response.data) {
        setGuides(response.data);
        setTotalCount(response.total || response.data.length);  // NEW: set total count
      } else if (Array.isArray(response)) {
        setGuides(response);
        setTotalCount(response.length);  // NEW: set total count
      }
    } catch (err: any) {
      console.error('Error fetching guides:', err);
      setError(err.response?.data?.error || 'Failed to fetch first aid guides');
    } finally {
      setLoading(false);
    }
  };
```

### 4. Update useEffect to Reset Page on Filter Change (Around line 185)

```typescript
  useEffect(() => {
    setPage(1);  // NEW: Reset to page 1 when filters change
    fetchGuides();
  }, [selectedWoundType, selectedSeverity, selectedActiveStatus, searchTerm]);

  // NEW: Fetch when page changes
  useEffect(() => {
    fetchGuides();
  }, [page, limit]);
```

### 5. Replace Delete Handler (Around line 354)

```typescript
  // REPLACE entire handleDeleteGuide function with:
  const handleDeleteGuide = (guideId: string, guideName: string) => {
    setConfirmDialog({
      isOpen: true,
      title: 'Delete First Aid Guide',
      message: `Are you sure you want to delete "${guideName}"? This action cannot be undone.`,
      variant: 'danger',
      onConfirm: () => handleConfirmDelete(guideId)
    });
  };

  // ADD new function:
  const handleConfirmDelete = async (guideId: string) => {
    setConfirmDialog(prev => ({ ...prev, isOpen: false }));
    
    if (isDeletingGuide) return;

    try {
      setIsDeletingGuide(guideId);
      const response = await deleteFirstAidGuide(guideId, false);
      if (response.success) {
        fetchGuides();
        fetchStatistics();
        success('First aid guide deleted successfully!');
      } else {
        toastError(response.message || 'Failed to delete guide');
      }
    } catch (err: any) {
      console.error('Error deleting guide:', err);
      toastError(err.response?.data?.error || 'Failed to delete guide');
    } finally {
      setIsDeletingGuide(null);
    }
  };
```

### 6. Update Delete Button in Guide Card (Around line 620)

```typescript
  {guide.is_active && (
    <button
      className={styles.btnDelete}
      onClick={() => handleDeleteGuide(guide.firstaidguide_id, guide.title)}
      title="Delete"
      disabled={isDeletingGuide === guide.firstaidguide_id}
    >
      {isDeletingGuide === guide.firstaidguide_id ? (
        <Loader2 size={16} className={styles.spinning} />
      ) : (
        <Trash2 size={16} />
      )}
    </button>
  )}
```

### 7. Add Pagination UI (After guides grid, around line 636)

```typescript
      {/* REPLACE the entire guides grid closing tag with this: */}
      {!loading && !error && (
        <>
          <div className={styles.guidesGrid}>
            {/* ...existing guide cards... */}
          </div>

          {/* NEW: Pagination Controls */}
          {guides.length > 0 && (
            <div className={styles.paginationContainer}>
              <div className={styles.paginationInfo}>
                Showing {((page - 1) * limit) + 1} - {Math.min(page * limit, totalCount)} of {totalCount} guides
              </div>
              <div className={styles.paginationControls}>
                <button
                  className={styles.paginationButton}
                  onClick={() => setPage(Math.max(1, page - 1))}
                  disabled={page === 1}
                >
                  <ChevronLeft size={16} />
                  Previous
                </button>
                <button
                  className={styles.paginationButton}
                  onClick={() => setPage(page + 1)}
                  disabled={page * limit >= totalCount}
                >
                  Next
                  <ChevronRight size={16} />
                </button>
              </div>
            </div>
          )}
        </>
      )}
```

### 8. Replace View Modal (Around line 640)

```typescript
      {/* REPLACE entire View Modal section with: */}
      <FirstAidViewModal
        isOpen={showViewModal}
        guide={selectedGuide}
        onClose={() => setShowViewModal(false)}
        formatWoundType={formatWoundType}
        getSeverityBadgeClass={getSeverityBadgeClass}
      />
```

### 9. Replace Add/Edit Modal (Around line 750)

```typescript
      {/* REPLACE entire Add/Edit Modal section with: */}
      <FirstAidFormModal
        isOpen={showAddModal || showEditModal}
        mode={showEditModal ? 'edit' : 'add'}
        formData={formData}
        onClose={() => {
          setShowAddModal(false);
          setShowEditModal(false);
        }}
        onSubmit={showEditModal ? handleEditGuide : handleAddGuide}
        onFormChange={setFormData}
        onArrayChange={handleArrayChange}
        onAddArrayItem={addArrayItem}
        onRemoveArrayItem={removeArrayItem}
        isSubmitting={isSubmitting}
      />
```

### 10. Add Confirm Dialog (At the end, before closing div)

```typescript
      {/* NEW: Add before the final closing </div> */}
      <ConfirmDialog
        isOpen={confirmDialog.isOpen}
        title={confirmDialog.title}
        message={confirmDialog.message}
        variant={confirmDialog.variant}
        confirmText="Delete"
        cancelText="Cancel"
        onConfirm={confirmDialog.onConfirm}
        onCancel={() => setConfirmDialog(prev => ({ ...prev, isOpen: false }))}
        isLoading={isDeletingGuide !== null}
      />
    </div>
  );
}
```

---

## Summary of Changes by Line Numbers (Approximate)

| Line Range | Change | Type |
|------------|--------|------|
| 1-24 | Add new imports | Addition |
| ~100-120 | Add pagination & confirm dialog state | Addition |
| ~150-160 | Update params with pagination | Modification |
| ~185-195 | Add useEffect for page changes | Addition |
| ~354-376 | Replace delete handler | Replacement |
| ~620-628 | Update delete button with loading | Modification |
| ~636-670 | Add pagination UI | Addition |
| ~640-750 | Replace view modal with component | Replacement |
| ~750-890 | Replace form modal with component | Replacement |
| ~930 | Add confirm dialog | Addition |

---

## Files That Must Exist

Ensure these files are created before integrating:

1. ✅ `/frontend/src/components/common/ConfirmDialog.tsx`
2. ✅ `/frontend/src/components/common/ConfirmDialog.module.css`
3. ✅ `/frontend/src/components/admin/FirstAidViewModal.tsx`
4. ✅ `/frontend/src/components/admin/FirstAidFormModal.tsx`
5. ✅ CSS styles added to `FirstAidManagement.module.css`

---

## Testing After Integration

1. **Build the project:** `npm run build`
2. **Run dev server:** `npm run dev`
3. **Test each feature:**
   - View modal opens and displays data
   - Add modal creates new guides
   - Edit modal updates guides
   - Delete shows custom confirm  
   - Pagination next/prev buttons work
   - Loading states show during operations

---

## Rollback Plan

If issues occur:
1. Keep the new component files
2. Comment out new imports
3. Restore old modal JSX from git history
4. Remove pagination UI section
5. Restore old delete handler

The new components can still be used independently later.

---

**Integration Difficulty:** Medium  
**Estimated Time:** 30-45 minutes  
**Risk Level:** Low (non-breaking changes)
