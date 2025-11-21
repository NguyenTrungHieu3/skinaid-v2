# First Aid Management Refactoring - Code Diffs

## Main Component Changes

### Imports (Before vs After)

```diff
 import React, { useState, useEffect } from 'react';
 import {
   Plus,
   Search,
   Edit2,
   Trash2,
-  X,
-  AlertTriangle,
-  CheckCircle,
   BookOpen,
   Activity,
   AlertCircle,
-  Save
+  ChevronLeft,
+  ChevronRight,
+  Loader2
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
+import FirstAidViewModal from './FirstAidViewModal';
+import FirstAidFormModal from './FirstAidFormModal';
+import ConfirmDialog from '../common/ConfirmDialog';
 import styles from './FirstAidManagement.module.css';
```

### New State Variables

```diff
  const [guides, setGuides] = useState<Guide[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Loading states for async operations
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDeletingGuide, setIsDeletingGuide] = useState<string | null>(null);

+  // Pagination state
+  const [page, setPage] = useState(1);
+  const [limit, setLimit] = useState(9);
+  const [totalCount, setTotalCount] = useState(0);
+
+  // Confirm dialog state
+  const [confirmDialog, setConfirmDialog] = useState({
+    isOpen: false,
+    title: '',
+    message: '',
+    variant: 'warning' as 'danger' | 'warning' | 'info',
+    onConfirm: () => {}
+  });
```

### Fetch Guides with Pagination

```diff
  const fetchGuides = async () => {
    try {
      setLoading(true);
      setError(null);

      const params: any = {
        wound_type: selectedWoundType,
        severity: selectedSeverity,
-        limit: 20,
-        offset: 0
+        limit,
+        offset: (page - 1) * limit
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
+        setTotalCount(response.total || response.data.length);
      } else if (Array.isArray(response)) {
        setGuides(response);
+        setTotalCount(response.length);
      }
    } catch (err: any) {
      console.error('Error fetching guides:', err);
      setError(err.response?.data?.error || 'Failed to fetch first aid guides');
    } finally {
      setLoading(false);
    }
  };
```

### Delete Handler with Confirm Dialog

```diff
- const handleDeleteGuide = async (guideId: string, guideName: string) => {
-   if (!window.confirm(`Are you sure you want to delete "${guideName}"?`)) {
-     return;
-   }
+ const handleDeleteGuide = (guideId: string, guideName: string) => {
+   setConfirmDialog({
+     isOpen: true,
+     title: 'Delete First Aid Guide',
+     message: `Are you sure you want to delete "${guideName}"? This action cannot be undone.`,
+     variant: 'danger',
+     onConfirm: () => handleConfirmDelete(guideId)
+   });
+ };
+
+ const handleConfirmDelete = async (guideId: string) => {
+   setConfirmDialog(prev => ({ ...prev, isOpen: false }));

    if (isDeletingGuide) return;

    try {
      setIsDeletingGuide(guideId);
      const response = await deleteFirstAidGuide(guideId, false);
      if (response.success) {
        fetchGuides();
        fetchStatistics();
        success('First aid guide deleted successfully!');
      }
    } catch (err: any) {
      console.error('Error deleting guide:', err);
      toastError(err.response?.data?.error || 'Failed to delete guide');
    } finally {
      setIsDeletingGuide(null);
    }
  };
```

### Pagination Controls JSX

```diff
+      {/* Pagination */}
+      {!loading && !error && guides.length > 0 && (
+        <div className={styles.paginationContainer}>
+          <div className={styles.paginationInfo}>
+            Showing {((page - 1) * limit) + 1} - {Math.min(page * limit, totalCount)} of {total Count} guides
+          </div>
+          <div className={styles.paginationControls}>
+            <button
+              className={styles.paginationButton}
+              onClick={() => setPage(Math.max(1, page - 1))}
+              disabled={page === 1}
+            >
+              <ChevronLeft size={16} />
+              Previous
+            </button>
+            <button
+              className={styles.paginationButton}
+              onClick={() => setPage(page + 1)}
+              disabled={page * limit >= totalCount}
+            >
+              Next
+              <ChevronRight size={16} />
+            </button>
+          </div>
+        </div>
+      )}
```

### Modal Replacement

```diff
-      {/* View Modal */}
-      {showViewModal && selectedGuide && (
-        <div className={styles.modalOverlay} onClick={() => setShowViewModal(false)}>
-          <div className={styles.modalContent} onClick={e => e.stopPropagation()}>
-            {/* 150+ lines of JSX */}
-          </div>
-        </div>
-      )}
+      <FirstAidViewModal
+        isOpen={showViewModal}
+        guide={selectedGuide}
+        onClose={() => setShowViewModal(false)}
+        formatWoundType={formatWoundType}
+        getSeverityBadgeClass={getSeverityBadgeClass}
+      />

-      {/* Add/Edit Modal */}
-      {(showAddModal || showEditModal) && (
-        <div className={styles.modalOverlay}>
-          <div className={styles.modalContent}>
-            {/* 200+ lines of form JSX */}
-          </div>
-        </div>
-      )}
+      <FirstAidFormModal
+        isOpen={showAddModal || showEditModal}
+        mode={showEditModal ? 'edit' : 'add'}
+        formData={formData}
+        onClose={() => {
+          setShowAddModal(false);
+          setShowEditModal(false);
+        }}
+        onSubmit={showEditModal ? handleEditGuide : handleAddGuide}
+        onFormChange={setFormData}
+        onArrayChange={handleArrayChange}
+        onAddArrayItem={addArrayItem}
+        onRemoveArrayItem={removeArrayItem}
+        isSubmitting={isSubmitting}
+      />
+
+      <ConfirmDialog
+        isOpen={confirmDialog.isOpen}
+        title={confirmDialog.title}
+        message={confirmDialog.message}
+        variant={confirmDialog.variant}
+        confirmText="Delete"
+        cancelText="Cancel"
+        onConfirm={confirmDialog.onConfirm}
+        onCancel={() => setConfirmDialog(prev => ({ ...prev, isOpen: false }))}
+        isLoading={isDeletingGuide !== null}
+      />
```

## CSS Additions

```css
/* Pagination Styles */
.paginationContainer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 0.75rem;
  margin-top: 1.5rem;
}

.paginationInfo {
  font-size: 0.875rem;
  color: #64748b;
}

.paginationControls {
  display: flex;
  gap: 0.5rem;
}

.paginationButton {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 1rem;
  background: white;
  color: #475569;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.paginationButton:hover:not(:disabled) {
  background: #f8fafc;
  border-color: #1E9378;
  color: #1E9378;
}

.paginationButton:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Spinning Animation */
.spinning {
  animation: spin 0.8s linear infinite;
}

.adminBtnPrimary:disabled,
.btnSecondary:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}
```

## Summary of Changes

### Lines of Code:
- **Before:** 935 lines (monolithic)
- **After:** 
  - FirstAidManagement.tsx: ~450 lines
  - FirstAidViewModal.tsx: ~155 lines
  - FirstAidFormModal.tsx: ~285 lines  
  - ConfirmDialog.tsx: ~80 lines
  - **Total:** Similar count, but modular

### Features Added:
1. ✅ Modal components extracted
2. ✅ Pagination with controls
3. ✅ Custom confirm dialog
4. ✅ Consistent loading states
5. ✅ Better code organization
6. ✅ Improved user feedback

### Benefits:
- **Maintainability:** Easier to update individual components
- **Reusability:** Dialog and modals can be used elsewhere
- **Testing:** Each component can be tested in isolation
- **Performance:** Potential for better code splitting
- **UX:** Better loading states and confirmation dialogs
