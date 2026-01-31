import { useState } from 'react';
import { useRuleSettings } from '../../hooks/useRuleSettings';
import { useUnsavedChangesWarning } from '../../hooks/useUnsavedChangesWarning';
import { RuleCategory } from './RuleCategory';
import { DOCUMENT_TYPE_IDS, DOCUMENT_TYPE_LABELS } from '../../types/rules';
import type { DocumentTypeId } from '../../types/rules';
import './Settings.css';

interface SettingsProps {
  onClose: () => void;
}

/**
 * Main Settings component with document type tabs and rule configuration.
 */
export function Settings({ onClose }: SettingsProps) {
  const [activeTab, setActiveTab] = useState<DocumentTypeId>('factsheet');
  const {
    rules,
    isLoading,
    isDirty,
    isSaving,
    saveStatus,
    error,
    toggleRule,
    setSeverity,
    save,
    reset,
  } = useRuleSettings(activeTab);

  // Warn when leaving with unsaved changes
  useUnsavedChangesWarning(isDirty);

  // Handle tab change with unsaved changes warning
  const handleTabChange = (docType: DocumentTypeId) => {
    if (isDirty) {
      const confirmed = window.confirm(
        'You have unsaved changes. Are you sure you want to switch tabs? Changes will be lost.'
      );
      if (!confirmed) return;
    }
    setActiveTab(docType);
  };

  // Handle close with unsaved changes warning
  const handleClose = () => {
    if (isDirty) {
      const confirmed = window.confirm(
        'You have unsaved changes. Are you sure you want to close? Changes will be lost.'
      );
      if (!confirmed) return;
    }
    onClose();
  };

  // Handle reset with confirmation
  const handleReset = async () => {
    const confirmed = window.confirm(
      'Are you sure you want to reset all rules to defaults? This cannot be undone.'
    );
    if (!confirmed) return;
    await reset();
  };

  // Get save button text based on status
  const getSaveButtonText = () => {
    if (isSaving) return 'Saving...';
    if (saveStatus === 'saved') return 'Saved';
    if (saveStatus === 'error') return 'Error - Try Again';
    return 'Save';
  };

  return (
    <div className="settings">
      <div className="settings__header">
        <h2 className="settings__title">Rule Configuration</h2>
        <button
          type="button"
          className="settings__close"
          onClick={handleClose}
          aria-label="Close settings"
        >
          Close
        </button>
      </div>

      <div className="settings__tabs">
        {DOCUMENT_TYPE_IDS.map((docType) => (
          <button
            key={docType}
            type="button"
            className={`settings__tab ${activeTab === docType ? 'settings__tab--active' : ''}`}
            onClick={() => handleTabChange(docType)}
          >
            {DOCUMENT_TYPE_LABELS[docType]}
          </button>
        ))}
      </div>

      <div className="settings__content">
        {isLoading && (
          <div className="settings__loading">Loading rules...</div>
        )}

        {error && (
          <div className="settings__error">
            <p>Failed to load rules: {error}</p>
            <p className="settings__error-hint">
              Make sure the backend server is running and the rules API is available.
            </p>
          </div>
        )}

        {!isLoading && !error && rules && (
          <div className="settings__categories">
            {Object.entries(rules.categories).map(([categoryId, category]) => (
              <RuleCategory
                key={categoryId}
                categoryId={categoryId}
                category={category}
                onToggle={toggleRule}
                onSeverityChange={setSeverity}
              />
            ))}
          </div>
        )}

        {!isLoading && !error && rules && Object.keys(rules.categories).length === 0 && (
          <div className="settings__empty">
            No rules configured for this document type.
          </div>
        )}
      </div>

      <div className="settings__footer">
        <button
          type="button"
          className="settings__button settings__button--reset"
          onClick={handleReset}
          disabled={isSaving}
        >
          Reset to Defaults
        </button>
        <button
          type="button"
          className={`settings__button settings__button--save ${saveStatus === 'saved' ? 'settings__button--saved' : ''}`}
          onClick={save}
          disabled={!isDirty || isSaving}
        >
          {getSaveButtonText()}
        </button>
      </div>
    </div>
  );
}
