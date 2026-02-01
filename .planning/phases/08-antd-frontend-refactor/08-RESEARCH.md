# Phase 8: Ant Design Frontend Refactor - Research

**Researched:** 2026-02-01
**Domain:** React UI Component Library Migration (Ant Design)
**Confidence:** HIGH

## Summary

This research covers migrating the PubCheck frontend from custom HTML/CSS components, react-dropzone, TanStack Table, and Sonner to Ant Design (antd). Ant Design is an enterprise-class React UI library providing consistent, accessible components out of the box.

As of January 2026, Ant Design v6 is the current major version. However, since the project uses React 18, both v5.x and v6.x are compatible. **Recommendation: Use Ant Design v6** since it's the current version, React 18 is supported, and it avoids needing to migrate again later. The v6 upgrade from v5 is described as a "smooth migration" with full backward compatibility.

The migration involves 1:1 component replacements for most UI elements. The notable complexity is in replacing TanStack Table with Ant Design Table (different API patterns) and replacing Sonner with Ant Design's message API (requires context provider setup).

**Primary recommendation:** Install antd v6 and @ant-design/icons v6, wrap the app in `<App>` component for message API access, then systematically replace components page by page.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| antd | ^6.2.0 | React UI component library | Current stable, React 18 compatible, CSS-in-JS |
| @ant-design/icons | ^6.0.0 | Icon library for Ant Design | Required companion package, must match antd major version |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| dayjs | ^1.11.x | Date handling (if needed) | Ant Design DatePicker uses dayjs internally |

### Packages to Remove After Migration
| Package | Replacement |
|---------|-------------|
| react-dropzone | antd Upload.Dragger |
| @tanstack/react-table | antd Table |
| sonner | antd message API |

**Installation:**
```bash
npm install antd@^6 @ant-design/icons@^6
npm uninstall react-dropzone @tanstack/react-table sonner
```

## Architecture Patterns

### Recommended App Structure for Ant Design

```
src/
├── App.tsx              # Wrap in <ConfigProvider> and <App> for message API
├── components/
│   ├── DropZone/        # Replace with Upload.Dragger
│   ├── DataTabs/        # Replace with Tabs component
│   ├── SortableTable/   # Replace with Table component
│   ├── CheckResults/    # Replace with Collapse, Tag, Card/List.Item
│   ├── Settings/        # Replace with Tabs, Input, Select, Checkbox
│   └── Toast/           # REMOVE - use App.useApp() message API
├── hooks/
│   └── useAntdMessage.ts # Custom hook wrapping App.useApp() (optional)
└── styles/
    └── theme.ts         # Ant Design theme customization (if needed)
```

### Pattern 1: App Component Wrapper for Static Methods

**What:** Ant Design's message, notification, and Modal.confirm require context. The `<App>` component provides this context.
**When to use:** Always - wrap your root application to enable message API usage throughout.
**Example:**
```typescript
// Source: https://ant.design/components/app/
import { App, ConfigProvider } from 'antd';

// In your root App.tsx
function Root() {
  return (
    <ConfigProvider>
      <App>
        <YourMainApp />
      </App>
    </ConfigProvider>
  );
}

// In any component that needs message/notification
import { App } from 'antd';

function MyComponent() {
  const { message, modal, notification } = App.useApp();

  const handleSave = async () => {
    try {
      await saveData();
      message.success('Settings saved!');
    } catch {
      message.error('Failed to save settings');
    }
  };

  const handleDelete = () => {
    modal.confirm({
      title: 'Confirm Delete',
      content: 'This cannot be undone.',
      onOk: () => performDelete(),
    });
  };

  return <Button onClick={handleSave}>Save</Button>;
}
```

### Pattern 2: Controlled Sorting with Ant Design Table

**What:** Ant Design Table uses a different controlled state pattern than TanStack Table.
**When to use:** When migrating tables that have sorting state.
**Example:**
```typescript
// Source: https://ant.design/components/table/
import { Table, type TableProps } from 'antd';
import type { ColumnsType, SorterResult } from 'antd/es/table/interface';

interface DataType {
  key: string;
  name: string;
  size: number;
}

function SortableTable({ data }: { data: DataType[] }) {
  const [sortedInfo, setSortedInfo] = useState<SorterResult<DataType>>({});

  const handleChange: TableProps<DataType>['onChange'] = (pagination, filters, sorter) => {
    setSortedInfo(sorter as SorterResult<DataType>);
  };

  const columns: ColumnsType<DataType> = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      sorter: (a, b) => a.name.localeCompare(b.name),
      sortOrder: sortedInfo.columnKey === 'name' ? sortedInfo.order : null,
    },
    {
      title: 'Size',
      dataIndex: 'size',
      key: 'size',
      sorter: (a, b) => a.size - b.size,
      sortOrder: sortedInfo.columnKey === 'size' ? sortedInfo.order : null,
    },
  ];

  return <Table columns={columns} dataSource={data} onChange={handleChange} />;
}
```

### Pattern 3: Tabs with items API (Modern Approach)

**What:** Ant Design 5.x+ prefers the `items` prop over nested `TabPane` children.
**When to use:** All new Tabs implementations - TabPane is deprecated.
**Example:**
```typescript
// Source: https://ant.design/components/tabs/
import { Tabs, type TabsProps } from 'antd';

const items: TabsProps['items'] = [
  { key: 'text', label: 'Text (5)', children: <TextTab /> },
  { key: 'images', label: 'Images (12)', children: <ImagesTab /> },
  { key: 'margins', label: 'Margins (10)', children: <MarginsTab /> },
  { key: 'metadata', label: 'Metadata', children: <MetadataTab /> },
];

function DataTabs() {
  const [activeKey, setActiveKey] = useState('text');

  return (
    <Tabs
      activeKey={activeKey}
      onChange={setActiveKey}
      items={items}
    />
  );
}
```

### Pattern 4: Collapse with items API (Modern Approach)

**What:** Ant Design 5.6+ prefers `items` prop over nested `Panel` children.
**When to use:** All new Collapse implementations.
**Example:**
```typescript
// Source: https://ant.design/components/collapse/
import { Collapse, type CollapseProps } from 'antd';

const items: CollapseProps['items'] = categories.map(category => ({
  key: category.id,
  label: (
    <span>
      {category.name}
      <Tag color={category.hasErrors ? 'error' : 'default'}>
        {category.issueCount}
      </Tag>
    </span>
  ),
  children: <CategoryContent category={category} />,
}));

function CategoryList({ categories }) {
  // Categories with errors open by default
  const defaultActiveKeys = categories
    .filter(c => c.error_count > 0)
    .map(c => c.id);

  return (
    <Collapse
      items={items}
      defaultActiveKey={defaultActiveKeys}
    />
  );
}
```

### Anti-Patterns to Avoid

- **Using static message/notification methods:** Always use `App.useApp()` hook to get context-aware message API. Static methods like `message.success()` won't respect ConfigProvider theme.

- **Using deprecated TabPane/Panel children:** Use the `items` prop pattern instead of nested children. The children API is deprecated and may be removed in future versions.

- **Mixing controlled and uncontrolled:** Either fully control a component's state or let it manage internally. Don't mix `value`/`onChange` with `defaultValue`.

- **Targeting internal DOM nodes with CSS:** Ant Design's CSS-in-JS can change internal structures. Use component props for styling instead of CSS selectors.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| File drop zone | Custom drag-drop handlers | Upload.Dragger | Handles edge cases, accessibility, file validation |
| Sortable tables | Custom sort state + UI | Table with `sorter` prop | Built-in icons, multi-column sort, keyboard access |
| Toast notifications | Custom toast component | App.useApp() message | Stacking, animation, theme integration, auto-dismiss |
| Confirmation dialogs | Custom modal | Modal.confirm via useApp | Promise support, keyboard nav, consistent styling |
| Collapsible sections | details/summary HTML | Collapse | Animation, controlled state, accessibility |
| Toggle button groups | Custom button group | Radio.Group + Radio.Button | Proper a11y, keyboard nav, styling |
| Status badges | Custom styled spans | Tag with preset colors | Semantic colors (error/warning/success) |
| Loading spinners | Custom CSS animation | Spin | Consistent, composable, configurable |
| Sticky elements | Custom position:fixed | Affix | Handles scroll containers, offset calculations |

**Key insight:** Ant Design components handle accessibility (ARIA, keyboard navigation), theming, RTL support, and edge cases that custom implementations typically miss.

## Common Pitfalls

### Pitfall 1: Message API Without App Context
**What goes wrong:** Using `message.success()` static method results in warning "Static function can not consume context" and messages don't follow theme.
**Why it happens:** Static methods create detached React trees that can't access ConfigProvider context.
**How to avoid:** Always wrap app in `<App>` component and use `App.useApp()` hook for message/notification/modal.
**Warning signs:** Console warning about static function context.

### Pitfall 2: Table Row Key Missing
**What goes wrong:** Console warning "Each record in table should have a unique `key` prop" and potential rendering issues.
**Why it happens:** Ant Design Table requires unique keys for virtual DOM reconciliation.
**How to avoid:** Either add `key` property to data objects, or use `rowKey` prop: `<Table rowKey="id" />`.
**Warning signs:** React key warning in console.

### Pitfall 3: Checkbox in Form Not Binding
**What goes wrong:** Checkbox initial value not respected, always unchecked on render.
**Why it happens:** Form.Item binds to `value` by default, but Checkbox uses `checked`.
**How to avoid:** Use `valuePropName="checked"` on Form.Item wrapping Checkbox.
**Warning signs:** Checkbox appears unchecked despite initialValues being true.

### Pitfall 4: Tooltip on Custom Component Not Working
**What goes wrong:** Tooltip doesn't appear when hovering custom component.
**Why it happens:** Tooltip requires child to accept mouse/pointer events and ref.
**How to avoid:** Wrap custom components in `<span>` or use `React.forwardRef`.
**Warning signs:** Tooltip works on native elements but not custom components.

### Pitfall 5: Upload.Dragger Accept Prop Breaking Drag
**What goes wrong:** Files can't be dropped when `accept` prop is defined (known issue).
**Why it happens:** Bug in how accept filtering interacts with drag events.
**How to avoid:** Handle file type validation in `beforeUpload` callback instead of relying solely on `accept`.
**Warning signs:** Click-to-upload works but drag-drop doesn't.

### Pitfall 6: Icon Package Version Mismatch
**What goes wrong:** Icons don't render or app crashes.
**Why it happens:** @ant-design/icons major version must match antd major version.
**How to avoid:** Always upgrade both packages together: antd@6 requires @ant-design/icons@6.
**Warning signs:** Import errors or missing icon components.

## Code Examples

Verified patterns from official sources:

### Upload.Dragger for File Drop Zone
```typescript
// Source: https://ant.design/components/upload/
import { Upload, message } from 'antd';
import { InboxOutlined } from '@ant-design/icons';

const { Dragger } = Upload;

interface DropZoneProps {
  onFileAccepted: (file: File) => void;
  isProcessing: boolean;
}

function DropZone({ onFileAccepted, isProcessing }: DropZoneProps) {
  return (
    <Dragger
      name="file"
      accept=".pdf,application/pdf"
      multiple={false}
      disabled={isProcessing}
      showUploadList={false}
      beforeUpload={(file) => {
        // Validate file type manually (workaround for accept + drag issue)
        if (file.type !== 'application/pdf') {
          message.error('Only PDF files are accepted');
          return Upload.LIST_IGNORE;
        }
        onFileAccepted(file);
        return false; // Prevent auto-upload, handle manually
      }}
    >
      <p className="ant-upload-drag-icon">
        <InboxOutlined />
      </p>
      <p className="ant-upload-text">
        {isProcessing ? 'Processing...' : 'Drop PDF here or click to browse'}
      </p>
    </Dragger>
  );
}
```

### Tag for Severity Badges
```typescript
// Source: https://ant.design/components/tag/
import { Tag } from 'antd';
import { ExclamationCircleOutlined, WarningOutlined } from '@ant-design/icons';

type Severity = 'error' | 'warning';

interface SeverityBadgeProps {
  severity: Severity;
  count?: number;
}

function SeverityBadge({ severity, count }: SeverityBadgeProps) {
  const colorMap = {
    error: 'error',      // Red
    warning: 'warning',  // Orange
  } as const;

  const iconMap = {
    error: <ExclamationCircleOutlined />,
    warning: <WarningOutlined />,
  };

  return (
    <Tag color={colorMap[severity]} icon={iconMap[severity]}>
      {severity} {count !== undefined && `(${count})`}
    </Tag>
  );
}
```

### Radio.Group for Toggle Buttons
```typescript
// Source: https://ant.design/components/radio/
import { Radio } from 'antd';

type SeverityFilter = 'all' | 'error' | 'warning';

interface FilterToggleProps {
  value: SeverityFilter;
  onChange: (value: SeverityFilter) => void;
}

function FilterToggle({ value, onChange }: FilterToggleProps) {
  return (
    <Radio.Group
      value={value}
      onChange={(e) => onChange(e.target.value)}
      buttonStyle="solid"
    >
      <Radio.Button value="all">All</Radio.Button>
      <Radio.Button value="error">Errors</Radio.Button>
      <Radio.Button value="warning">Warnings</Radio.Button>
    </Radio.Group>
  );
}
```

### Affix for Sticky Bottom Bar
```typescript
// Source: https://ant.design/components/affix/
import { Affix, Button, Space } from 'antd';

interface SummaryBarProps {
  selectedCount: number;
  onGenerate: () => void;
  isGenerating: boolean;
}

function SummaryBar({ selectedCount, onGenerate, isGenerating }: SummaryBarProps) {
  return (
    <Affix offsetBottom={0}>
      <div style={{ background: '#fff', padding: 16, borderTop: '1px solid #d9d9d9' }}>
        <Space>
          <span>{selectedCount} issues selected</span>
          <Button
            type="primary"
            onClick={onGenerate}
            disabled={selectedCount === 0 || isGenerating}
            loading={isGenerating}
          >
            Generate Report
          </Button>
        </Space>
      </div>
    </Affix>
  );
}
```

### Tooltip for Confidence Indicator
```typescript
// Source: https://ant.design/components/tooltip/
import { Tooltip } from 'antd';
import { QuestionCircleOutlined } from '@ant-design/icons';

type Confidence = 'high' | 'medium' | 'low';

interface ConfidenceIndicatorProps {
  confidence: Confidence;
}

function ConfidenceIndicator({ confidence }: ConfidenceIndicatorProps) {
  if (confidence === 'high') return null; // High confidence is assumed, don't show

  const descriptions = {
    medium: 'Medium confidence - AI analysis may need verification',
    low: 'Low confidence - Manual review recommended',
  };

  const colors = {
    medium: '#faad14', // Warning yellow
    low: '#ff4d4f',    // Error red
  };

  return (
    <Tooltip title={descriptions[confidence]}>
      <QuestionCircleOutlined style={{ color: colors[confidence], marginLeft: 4 }} />
    </Tooltip>
  );
}
```

### Result for Success Banner
```typescript
// Source: https://ant.design/components/result/
import { Result, Button } from 'antd';

interface SuccessBannerProps {
  title: string;
  subtitle?: string;
  onNewCheck: () => void;
}

function SuccessBanner({ title, subtitle, onNewCheck }: SuccessBannerProps) {
  return (
    <Result
      status="success"
      title={title}
      subTitle={subtitle}
      extra={[
        <Button type="primary" key="new" onClick={onNewCheck}>
          Check Another Document
        </Button>,
      ]}
    />
  );
}
```

### Alert for Error Messages
```typescript
// Source: https://ant.design/components/alert/
import { Alert } from 'antd';

interface ErrorAlertProps {
  message: string;
  description?: string;
  onClose?: () => void;
}

function ErrorAlert({ message, description, onClose }: ErrorAlertProps) {
  return (
    <Alert
      message={message}
      description={description}
      type="error"
      showIcon
      closable={!!onClose}
      onClose={onClose}
    />
  );
}
```

### Spin for Loading Indicator
```typescript
// Source: https://ant.design/components/spin/
import { Spin } from 'antd';
import { LoadingOutlined } from '@ant-design/icons';

interface LoadingProps {
  tip?: string;
}

function Loading({ tip = 'Processing...' }: LoadingProps) {
  return (
    <Spin
      indicator={<LoadingOutlined style={{ fontSize: 24 }} spin />}
      tip={tip}
    />
  );
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Tabs.TabPane children | Tabs items prop | antd 5.0+ | TabPane deprecated, use items array |
| Collapse.Panel children | Collapse items prop | antd 5.6+ | Panel deprecated, use items array |
| message.success() static | App.useApp().message | antd 5.1+ | Required for context/theme support |
| Less variables theming | CSS-in-JS + ConfigProvider | antd 5.0 | No more .less files, use theme tokens |
| @ant-design/icons v4 | @ant-design/icons v6 | antd 6.0 | Must match major version |
| React 16/17 support | React 18+ only | antd 6.0 | v6 dropped legacy React support |

**Deprecated/outdated:**
- `Tabs.TabPane`: Use `items` prop instead
- `Collapse.Panel`: Use `items` prop instead
- `Breadcrumb.Item`: Use `items` prop instead
- `Dropdown.Button`: Use `Space.Compact + Dropdown + Button`
- `Input.Group`: Use `Space.Compact`
- Static `message/notification/Modal.confirm`: Use `App.useApp()` hook
- `BackTop`: Use `FloatButton.BackTop`

## Open Questions

Things that couldn't be fully resolved:

1. **Upload.Dragger accept prop + drag issue**
   - What we know: There's a documented bug where drag-drop stops working when `accept` prop is defined
   - What's unclear: Whether this is fixed in v6
   - Recommendation: Use `beforeUpload` for file type validation as workaround

2. **CSS specificity when mixing with existing styles**
   - What we know: Ant Design v5+ uses `:where` selector to lower specificity
   - What's unclear: How existing BEM CSS will interact during migration
   - Recommendation: Remove custom CSS for replaced components as you migrate each one

3. **Bundle size impact**
   - What we know: Ant Design is large but supports tree-shaking
   - What's unclear: Final bundle size delta vs current custom implementation
   - Recommendation: Monitor build output; Ant Design's CSS-in-JS loads styles on demand

## Sources

### Primary (HIGH confidence)
- [Ant Design Official Documentation](https://ant.design/docs/react/introduce/) - Component APIs, patterns
- [Ant Design v6 Migration Guide](https://ant.design/docs/react/migration-v6/) - v5 to v6 differences
- [Ant Design Changelog](https://ant.design/changelog/) - Current version, recent updates
- [Ant Design Table](https://ant.design/components/table/) - Sortable table API
- [Ant Design Upload](https://ant.design/components/upload/) - Upload.Dragger API
- [Ant Design App](https://ant.design/components/app/) - useApp hook for message API

### Secondary (MEDIUM confidence)
- [Ant Design GitHub Issues](https://github.com/ant-design/ant-design/issues) - Known bugs, workarounds
- [Medium: Migrating to Ant Design v6](https://leandroaps.medium.com/migrating-from-ant-design-v5-to-v6-a-practical-guide-for-frontend-teams-12aba4df425d) - Practical migration tips

### Tertiary (LOW confidence)
- WebSearch results for community patterns - Need verification with official docs

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Official documentation, npm package verified
- Architecture: HIGH - Patterns from official Ant Design docs
- Pitfalls: MEDIUM - Some from GitHub issues, verified with official docs where possible
- Code examples: HIGH - Based on official documentation examples

**Research date:** 2026-02-01
**Valid until:** 2026-03-01 (30 days - Ant Design is stable, v6 recently released)
