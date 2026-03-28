# Figma AI Design Prompt - SkinAid Model Management UI

## Context
I need to design a Model Management interface for the SkinAid Admin Portal that matches the existing design system and integrates seamlessly with the backend API.

## Project Overview
- **Product**: SkinAid - AI-powered wound detection and classification system
- **Feature**: AI Model Management (PBI-27)
- **Users**: Administrators managing AI model lifecycle
- **Tech Stack**: React + TypeScript frontend, FastAPI backend

## Backend API Structure

### Available Endpoints:
```
GET    /api/v1/admin/models              - List models with filters
POST   /api/v1/admin/models/upload       - Upload new model
POST   /api/v1/admin/models/:id/activate - Activate model version
POST   /api/v1/admin/models/:id/rollback - Rollback to previous version
DELETE /api/v1/admin/models/:id          - Soft delete model
GET    /api/v1/admin/models/:id/metadata - Get model metadata
GET    /api/v1/admin/models/:id/logs     - Get audit logs
GET    /api/v1/admin/models/runtime/status - Runtime status
```

### Data Models:
```typescript
interface AIModel {
  model_id: string;
  model_type: 'detection' | 'classification' | 'segmentation' | 'severity_scoring';
  name: string;
  current_version?: string;
  total_versions: number;
  created_at: string;
  updated_at: string;
  metrics?: { accuracy?: number; precision?: number; recall?: number };
  is_active: boolean;
  is_beta: boolean;
}

interface ModelVersion {
  version_id: string;
  version_tag: string;
  version_number: number;
  is_active: boolean;
  is_beta: boolean;
  created_at: string;
  deployed_at?: string;
  metrics?: ModelMetrics;
}
```

## Current Design System

### Color Palette (from existing SkinAid UI):
```
Primary Colors:
- Teal 50:  #f0fdfa   (lightest backgrounds)
- Teal 100: #ccfbf1  (hover states)
- Teal 500: #14b8a6  (primary buttons, accents)
- Teal 600: #0d9488  (active states, gradients)
- Teal 700: #0f766e  (sidebar active)

Neutral Colors:
- Gray 50:  #f9fafb  (card backgrounds)
- Gray 100: #f3f4f6  (borders)
- Gray 500: #6b7280  (secondary text)
- Gray 700: #374151  (primary text)
- Gray 900: #111827  (headings)

Status Colors:
- Success: #10b981 (green)
- Warning: #f59e0b (amber)
- Error:   #ef4444 (red)
- Info:    #3b82f6 (blue)
```

### Typography:
```
Font Family: Inter, system-ui, sans-serif

Sizes:
- xs:   12px (labels, captions)
- sm:   14px (body text, table content)
- base: 16px (regular text)
- lg:   18px (subtitles)
- xl:   20px (section titles)
- 2xl:  24px (page titles)

Weights:
- Regular: 400
- Medium:  500
- Semibold: 600
- Bold:    700
```

### Spacing Scale:
```
4px, 8px, 12px, 16px, 20px, 24px, 32px, 40px, 48px
```

### Border Radius:
```
Small:  6px  (inputs, badges)
Medium: 8px  (cards, buttons)
Large:  12px (modals, sidebar)
```

### Shadows:
```
Small:  0 1px 2px rgba(0,0,0,0.05)
Medium: 0 4px 6px rgba(0,0,0,0.1)
Large:  0 10px 15px rgba(0,0,0,0.1)
```

## Existing Admin Layout Structure

### Sidebar (Left):
- Logo: SkinAid Admin Portal
- Navigation: Dashboard, User Management, First Aid Guidance, **Model Management**, Admin Logs
- System Status card at bottom

### Top Bar:
- Language switcher (EN/VI)
- User profile (name, role, avatar)

### Main Content Area:
- Page title and subtitle
- Action buttons (top right)
- Filters section
- Data table/cards
- Pagination

## Design Requirements

### Page 1: Model Management Main Dashboard

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  Title: AI Model Management                                 │
│  Subtitle: Manage AI model lifecycle                        │
│                                              [Upload Model] │
├─────────────────────────────────────────────────────────────┤
│  Filters:                                                   │
│  [Model Type ▼] [Status ▼] [Search...]                     │
├─────────────────────────────────────────────────────────────┤
│  Data Table:                                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Model Type │ Version │ Status │ Versions │ Actions  │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │ Detection  │ v1.0.0  │ ● Active│   3     │ [⋮]     │  │
│  │ Classif.   │ v2.1.0  │ ○ Inact │   5     │ [⋮]     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Components Needed:**
1. Page header with title, subtitle, and primary action button
2. Filter bar with dropdowns and search
3. Data table with:
   - Model type badge (with icon)
   - Version tag
   - Status indicator (active/inactive with dot)
   - Total versions count
   - Action menu (Activate, Rollback, View Details, Delete)
4. Empty state (when no models)
5. Loading skeleton

### Page 2: Upload Model Modal

**Layout:**
```
┌─────────────────────────────────────────┐
│  Upload AI Model                    [X] │
├─────────────────────────────────────────┤
│                                         │
│  ┌───────────────────────────────────┐ │
│  │     Drag & Drop or Click to      │ │
│  │           Browse                  │ │
│  │                                   │ │
│  │   .pt, .pth, .h5, .onnx,         │ │
│  │   .safetensors (Max 500MB)       │ │
│  └───────────────────────────────────┘ │
│                                         │
│  Model Type *                           │
│  [Detection ▼]                         │
│                                         │
│  Version Tag *                          │
│  [v1.0.0                            ]  │
│                                         │
│  Description                            │
│  [                                   ] │
│  [                                   ] │
│                                         │
│  ☐ Mark as beta version                │
│                                         │
│            [Cancel]  [Upload]           │
└─────────────────────────────────────────┘
```

**Components Needed:**
1. File upload zone (drag & drop with progress bar)
2. Form fields:
   - Model type dropdown (detection, classification, segmentation, severity_scoring)
   - Version tag input (with validation pattern)
   - Description textarea
   - Beta checkbox
3. Progress indicator during upload
4. Success/error states

### Page 3: Model Detail View Modal

**Layout:**
```
┌─────────────────────────────────────────────┐
│  Model Details                          [X] │
├─────────────────────────────────────────────┤
│  ┌─────────────────────────────────────┐   │
│  │  Detection Model                    │   │
│  │  Current Version: v1.0.0 (Active)   │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  Metrics:                                   │
│  ┌─────────┬─────────┬─────────┐           │
│  │Accuracy │Precision│ Recall  │           │
│  │  94.2%  │  92.1%  │  93.5%  │           │
│  └─────────┴─────────┴─────────┘           │
│                                             │
│  Version History:                           │
│  ┌─────────────────────────────────────┐   │
│  │ ● v1.0.0  Active    Jan 15, 2024   │   │
│  │ ○ v0.9.0  Inactive  Jan 10, 2024   │   │
│  │ ○ v0.8.0  Inactive  Jan 5, 2024    │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  File Info:                                 │
│  Path: /models/detection/...                │
│  Size: 245.6 MB                             │
│  Hash: sha256:abc123...                     │
│                                             │
│  [View Audit Logs]  [Close]                 │
└─────────────────────────────────────────────┘
```

### Page 4: Audit Logs View

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│  Audit Logs - Model v1.0.0                          [X] │
├─────────────────────────────────────────────────────────┤
│  Filters: [Action ▼] [Date Range] [User]               │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────┐  │
│  │ Time       │ Action   │ User  │ Details         │  │
│  ├──────────────────────────────────────────────────┤  │
│  │ 10:30 AM   │ Activate │ Admin │ v0.9→v1.0      │  │
│  │ 9:15 AM    │ Upload   │ Admin │ 245MB, .pt     │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Specific Design Requests for Figma AI

Please generate:

1. **Complete UI Kit** with:
   - Color styles matching SkinAid brand (teal palette)
   - Text styles (Inter font family)
   - Component variants (buttons, inputs, cards, tables)
   - Icon set (Lucide React style)

2. **Auto Layout Components**:
   - Responsive table with sortable columns
   - Filter bar with flexible spacing
   - Modal with proper padding and scroll behavior
   - Cards with consistent shadows

3. **Interactive States**:
   - Button hover/active/disabled
   - Input focus/error states
   - Table row hover
   - Loading skeletons

4. **Data Visualization**:
   - Status badges (active/inactive/beta)
   - Progress bars for upload
   - Metric cards with icons
   - Timeline for version history

5. **Responsive Breakpoints**:
   - Desktop: 1440px+
   - Laptop: 1024px
   - Tablet: 768px

6. **Design Tokens** exportable as:
   - CSS variables
   - TypeScript types
   - JSON for theme config

## Additional Requirements

### Accessibility:
- WCAG 2.1 AA compliance
- Proper color contrast (4.5:1 minimum)
- Focus indicators
- Screen reader labels
- Keyboard navigation

### Consistency with Existing UI:
- Match sidebar style from current admin portal
- Use same button styles as User Management page
- Follow same card patterns as Dashboard
- Maintain same modal behavior

### Micro-interactions:
- Smooth transitions (200ms ease)
- Loading states with skeletons
- Toast notifications for actions
- Confirmation dialogs for destructive actions

## Deliverables Expected

1. **Figma File** with:
   - All pages and components
   - Design system library
   - Auto layout enabled
   - Component variants

2. **Export Assets**:
   - Icons (SVG)
   - Illustrations (SVG)
   - Logos (SVG)

3. **Documentation**:
   - Usage guidelines
   - Component props
   - Interaction specs

4. **Developer Handoff**:
   - CSS/Tailwind classes
   - React component structure suggestions
   - Animation specs

## Example Reference Images

[Attach screenshots of existing SkinAid admin pages for reference]

## Notes

- The design should feel professional and enterprise-grade
- Prioritize clarity and usability over decorative elements
- Use consistent spacing and alignment
- Ensure the UI scales well with large datasets (100+ models)
- Consider dark mode compatibility for future implementation

---

**Please use Figma AI to generate:**
1. Complete wireframes for all 4 pages
2. High-fidelity mockups with colors and typography
3. Interactive prototypes showing user flows
4. Component library with variants
5. Design tokens for development
