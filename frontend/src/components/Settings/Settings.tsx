/**
 * Settings page component for rule configuration.
 * Provides tabbed interface for editing document type rules.
 * Uses Ant Design Modal, Tabs, Collapse, and form components.
 */
import { useState, useCallback } from 'react';
import {
  Modal,
  Tabs,
  Collapse,
  Input,
  InputNumber,
  Select,
  Checkbox,
  Button,
  Space,
  Typography,
  ColorPicker,
  Spin,
  Alert,
  type CollapseProps,
  type TabsProps,
} from 'antd';
import { useSettings } from '../../hooks/useSettings';
import { useAntdApp } from '../../hooks/useAntdApp';
import type {
  DocumentTypeConfig,
  DocumentTypeId,
  RangeValue,
  FontConfig,
  RequiredElementConfig,
} from '../../types/settings';
import { DOCUMENT_TYPE_LABELS } from '../../types/settings';

const { Text } = Typography;

const DOC_TYPES: DocumentTypeId[] = ['factsheet', 'brief', 'working_paper', 'publication'];

interface SettingsProps {
  onClose: () => void;
}

export function Settings({ onClose }: SettingsProps) {
  const { message, modal } = useAntdApp();
  const {
    settings,
    isLoading,
    error,
    isDirty,
    saveSettings,
    resetSettings,
    updateSettings,
  } = useSettings();

  const [activeTab, setActiveTab] = useState<DocumentTypeId>('factsheet');

  const handleSave = async () => {
    if (settings) {
      try {
        await saveSettings(settings);
        message.success('Settings saved! Rules will apply to your next review.');
      } catch {
        message.error('Failed to save settings');
      }
    }
  };

  const handleReset = () => {
    modal.confirm({
      title: 'Reset to Defaults',
      content: 'Reset all settings to defaults? This cannot be undone.',
      okText: 'Reset',
      okType: 'danger',
      onOk: async () => {
        try {
          await resetSettings();
          message.success('Settings reset to defaults');
        } catch {
          message.error('Failed to reset settings');
        }
      },
    });
  };

  const handleClose = () => {
    if (isDirty) {
      modal.confirm({
        title: 'Discard Changes',
        content: 'You have unsaved changes. Discard them?',
        okText: 'Discard',
        okType: 'danger',
        onOk: onClose,
      });
    } else {
      onClose();
    }
  };

  const updateDocType = useCallback(
    (docType: DocumentTypeId, updates: Partial<DocumentTypeConfig>) => {
      if (!settings) return;
      updateSettings({
        ...settings,
        [docType]: { ...settings[docType], ...updates },
      });
    },
    [settings, updateSettings]
  );

  if (isLoading && !settings) {
    return (
      <Modal open onCancel={handleClose} footer={null} title="Settings">
        <div style={{ textAlign: 'center', padding: 40 }}>
          <Spin size="large" />
        </div>
      </Modal>
    );
  }

  if (error && !settings) {
    return (
      <Modal open onCancel={handleClose} footer={null} title="Settings">
        <Alert type="error" message={error} />
      </Modal>
    );
  }

  if (!settings) return null;

  const currentConfig = settings[activeTab];

  const tabItems: TabsProps['items'] = DOC_TYPES.map(docType => ({
    key: docType,
    label: DOCUMENT_TYPE_LABELS[docType],
  }));

  const collapseItems: CollapseProps['items'] = [
    {
      key: 'cover',
      label: 'Cover Page',
      children: <CoverForm config={currentConfig.cover} onChange={cover => updateDocType(activeTab, { cover })} />,
    },
    {
      key: 'typography',
      label: 'Typography',
      children: <TypographyForm config={currentConfig.typography} onChange={typography => updateDocType(activeTab, { typography })} />,
    },
    {
      key: 'images',
      label: 'Images',
      children: <ImagesForm config={currentConfig.images} onChange={images => updateDocType(activeTab, { images })} />,
    },
    {
      key: 'margins',
      label: 'Margins',
      children: <MarginsForm config={currentConfig.margins} onChange={margins => updateDocType(activeTab, { margins })} />,
    },
    {
      key: 'required',
      label: 'Required Elements',
      children: <RequiredElementsForm config={currentConfig.required_elements} onChange={required_elements => updateDocType(activeTab, { required_elements })} />,
    },
    {
      key: 'notes',
      label: 'Custom Rules',
      children: <CustomRulesForm rules={currentConfig.notes} onChange={notes => updateDocType(activeTab, { notes })} />,
    },
  ];

  return (
    <Modal
      open
      onCancel={handleClose}
      title="Settings"
      width={800}
      footer={
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <Button danger onClick={handleReset}>
            Reset to Defaults
          </Button>
          <Space>
            <Button onClick={handleClose}>
              {isDirty ? 'Discard' : 'Close'}
            </Button>
            <Button type="primary" onClick={handleSave} disabled={!isDirty || isLoading}>
              {isLoading ? 'Saving...' : 'Save Changes'}
            </Button>
          </Space>
        </div>
      }
    >
      <Tabs
        activeKey={activeTab}
        onChange={(key) => setActiveTab(key as DocumentTypeId)}
        items={tabItems}
      />

      <Input
        value={currentConfig.description}
        onChange={e => updateDocType(activeTab, { description: e.target.value })}
        placeholder="Document type description..."
        style={{ marginBottom: 16 }}
      />

      <Collapse
        defaultActiveKey={['cover', 'typography', 'images', 'margins', 'required']}
        items={collapseItems}
      />
    </Modal>
  );
}

// RangeInput helper component
interface RangeInputProps {
  label: string;
  value: RangeValue;
  onChange: (value: RangeValue) => void;
}

function RangeInput({ label, value, onChange }: RangeInputProps) {
  return (
    <div style={{ marginBottom: 12 }}>
      <Text type="secondary" style={{ display: 'block', marginBottom: 4 }}>{label}</Text>
      <Space>
        <InputNumber
          value={value.min ?? undefined}
          onChange={v => onChange({ ...value, min: v ?? null })}
          placeholder="Min"
          style={{ width: 80 }}
        />
        <span>-</span>
        <InputNumber
          value={value.max ?? undefined}
          onChange={v => onChange({ ...value, max: v ?? null })}
          placeholder="Max"
          style={{ width: 80 }}
        />
        <Text type="secondary">{value.unit}</Text>
      </Space>
    </div>
  );
}

// CoverForm component
interface CoverFormProps {
  config: DocumentTypeConfig['cover'];
  onChange: (config: DocumentTypeConfig['cover']) => void;
}

function CoverForm({ config, onChange }: CoverFormProps) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12, width: '100%' }}>
      <div>
        <Text type="secondary" style={{ display: 'block', marginBottom: 4 }}>Logo Position</Text>
        <Select
          value={config.logo.position}
          onChange={v => onChange({ ...config, logo: { ...config.logo, position: v } })}
          style={{ width: 200 }}
          options={[
            { value: 'top-right', label: 'Top Right' },
            { value: 'top-left', label: 'Top Left' },
            { value: 'bottom-right', label: 'Bottom Right' },
            { value: 'bottom-left', label: 'Bottom Left' },
          ]}
        />
      </div>
      <Space>
        <div>
          <Text type="secondary" style={{ display: 'block', marginBottom: 4 }}>Logo Min Width (mm)</Text>
          <InputNumber value={config.logo.width_min} onChange={v => onChange({ ...config, logo: { ...config.logo, width_min: v ?? 0 } })} />
        </div>
        <div>
          <Text type="secondary" style={{ display: 'block', marginBottom: 4 }}>Logo Target Width (mm)</Text>
          <InputNumber value={config.logo.width_target} onChange={v => onChange({ ...config, logo: { ...config.logo, width_target: v ?? 0 } })} />
        </div>
      </Space>
      <RangeInput label="Title Size" value={config.title_size} onChange={title_size => onChange({ ...config, title_size })} />
      <RangeInput label="Subtitle Size" value={config.subtitle_size} onChange={subtitle_size => onChange({ ...config, subtitle_size })} />
      <div>
        <Text type="secondary" style={{ display: 'block', marginBottom: 4 }}>Heading Color</Text>
        <Space>
          <ColorPicker value={config.heading_color} onChange={(_, hex) => onChange({ ...config, heading_color: hex })} />
          <Input value={config.heading_color} onChange={e => onChange({ ...config, heading_color: e.target.value })} style={{ width: 100 }} />
        </Space>
      </div>
    </div>
  );
}

// TypographyForm - similar pattern with Checkbox, Input, Select
function TypographyForm({ config, onChange }: { config: DocumentTypeConfig['typography']; onChange: (c: DocumentTypeConfig['typography']) => void }) {
  const fontFields: Array<{ key: keyof typeof config; label: string }> = [
    { key: 'body', label: 'Body Text' },
    { key: 'h1', label: 'Chapter Titles (H1)' },
    { key: 'h2', label: 'Section Headings (H2)' },
    { key: 'h3', label: 'Subsection (H3)' },
    { key: 'h4', label: 'Sub-subsection (H4)' },
    { key: 'captions', label: 'Captions' },
    { key: 'charts', label: 'Charts' },
  ];

  const updateFont = (key: keyof typeof config, updates: Partial<FontConfig>) => {
    onChange({ ...config, [key]: { ...config[key], ...updates } });
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
      {fontFields.map(({ key, label }) => (
        <div key={key} style={{ padding: '8px 0', borderBottom: '1px solid #f0f0f0' }}>
          <Checkbox
            checked={config[key].enabled}
            onChange={e => updateFont(key, { enabled: e.target.checked })}
          >
            {label}
          </Checkbox>
          {config[key].enabled && (
            <div style={{ marginTop: 8, marginLeft: 24 }}>
              <Space wrap>
                <div>
                  <Text type="secondary" style={{ display: 'block', marginBottom: 4 }}>Font Family</Text>
                  <Input value={config[key].family} onChange={e => updateFont(key, { family: e.target.value })} style={{ width: 150 }} />
                </div>
                <RangeInput label="Size" value={config[key].size} onChange={size => updateFont(key, { size })} />
                <div>
                  <Text type="secondary" style={{ display: 'block', marginBottom: 4 }}>Weight</Text>
                  <Select
                    value={config[key].weight}
                    onChange={v => updateFont(key, { weight: v })}
                    style={{ width: 100 }}
                    options={['Light', 'Regular', 'Medium', 'Bold'].map(w => ({ value: w, label: w }))}
                  />
                </div>
                <div>
                  <Text type="secondary" style={{ display: 'block', marginBottom: 4 }}>Color</Text>
                  <Input value={config[key].color ?? ''} onChange={e => updateFont(key, { color: e.target.value || null })} placeholder="#00AEEF" style={{ width: 100 }} />
                </div>
              </Space>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

// ImagesForm
function ImagesForm({ config, onChange }: { config: DocumentTypeConfig['images']; onChange: (c: DocumentTypeConfig['images']) => void }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12, width: '100%' }}>
      <div>
        <Text type="secondary" style={{ display: 'block', marginBottom: 4 }}>Minimum DPI</Text>
        <InputNumber value={config.min_dpi} onChange={v => onChange({ ...config, min_dpi: v ?? 0 })} />
      </div>
      <div>
        <Text type="secondary" style={{ display: 'block', marginBottom: 4 }}>Max Width (mm)</Text>
        <InputNumber value={config.max_width ?? undefined} onChange={v => onChange({ ...config, max_width: v ?? null })} placeholder="No limit" />
      </div>
      <div>
        <Text type="secondary" style={{ display: 'block', marginBottom: 4 }}>Color Spaces</Text>
        <Checkbox.Group
          options={['RGB', 'CMYK']}
          value={config.color_spaces}
          onChange={v => onChange({ ...config, color_spaces: v as string[] })}
        />
      </div>
    </div>
  );
}

// MarginsForm
function MarginsForm({ config, onChange }: { config: DocumentTypeConfig['margins']; onChange: (c: DocumentTypeConfig['margins']) => void }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12, width: '100%' }}>
      <RangeInput label="Top Margin" value={config.top} onChange={top => onChange({ ...config, top })} />
      <RangeInput label="Bottom Margin" value={config.bottom} onChange={bottom => onChange({ ...config, bottom })} />
      <RangeInput label="Inside Margin (Binding)" value={config.inside} onChange={inside => onChange({ ...config, inside })} />
      <RangeInput label="Outside Margin" value={config.outside} onChange={outside => onChange({ ...config, outside })} />
      <Checkbox checked={config.full_bleed_allowed} onChange={e => onChange({ ...config, full_bleed_allowed: e.target.checked })}>
        Allow full-bleed images (won't flag as margin violations)
      </Checkbox>
    </div>
  );
}

// RequiredElementsForm
function RequiredElementsForm({ config, onChange }: { config: DocumentTypeConfig['required_elements']; onChange: (c: DocumentTypeConfig['required_elements']) => void }) {
  const elements: Array<{ key: keyof typeof config; label: string }> = [
    { key: 'isbn', label: 'ISBN' },
    { key: 'doi', label: 'DOI' },
    { key: 'job_number', label: 'Job Number' },
    { key: 'copyright_notice', label: 'Copyright Notice' },
    { key: 'territorial_disclaimer', label: 'Territorial Disclaimer' },
    { key: 'commercial_disclaimer', label: 'Commercial Products Disclaimer' },
    { key: 'views_disclaimer', label: 'Views Expressed Disclaimer' },
    { key: 'suggested_citation', label: 'Suggested Citation' },
    { key: 'sdg_icons', label: 'SDG Icons' },
    { key: 'table_of_contents', label: 'Table of Contents' },
    { key: 'page_numbers', label: 'Page Numbers' },
  ];

  const updateElement = (key: keyof typeof config, updates: Partial<RequiredElementConfig>) => {
    onChange({ ...config, [key]: { ...config[key], ...updates } });
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8, width: '100%' }}>
      {elements.map(({ key, label }) => (
        <div key={key}>
          <Checkbox checked={config[key].required} onChange={e => updateElement(key, { required: e.target.checked })}>
            {label}
          </Checkbox>
          {config[key].required && (
            <Input
              value={config[key].description ?? config[key].pattern ?? ''}
              onChange={e => updateElement(key, { description: e.target.value || null, pattern: null })}
              placeholder="Description or pattern..."
              style={{ marginLeft: 24, width: 'calc(100% - 24px)', marginTop: 4 }}
            />
          )}
        </div>
      ))}
    </div>
  );
}

// CustomRulesForm
function CustomRulesForm({ rules, onChange }: { rules: string[]; onChange: (r: string[]) => void }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8, width: '100%' }}>
      {rules.map((rule, index) => (
        <Space key={index} style={{ width: '100%' }}>
          <Input
            value={rule}
            onChange={e => {
              const newRules = [...rules];
              newRules[index] = e.target.value;
              onChange(newRules);
            }}
            placeholder="e.g., Charts must use UNEP color palette"
            style={{ flex: 1 }}
          />
          <Button danger onClick={() => onChange(rules.filter((_, i) => i !== index))}>
            Remove
          </Button>
        </Space>
      ))}
      <Button type="dashed" onClick={() => onChange([...rules, ''])} block>
        + Add Rule
      </Button>
    </div>
  );
}
