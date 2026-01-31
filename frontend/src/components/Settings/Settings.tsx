import { useState, useCallback } from 'react';
import { useRuleSettings } from '../../hooks/useRuleSettings';
import { useIgnoredRules } from '../../hooks/useIgnoredRules';
import { useUnsavedChangesWarning } from '../../hooks/useUnsavedChangesWarning';
import { RuleCategory } from './RuleCategory';
import { IgnoredRulesTab } from './IgnoredRulesTab';
import { DOCUMENT_TYPE_IDS, DOCUMENT_TYPE_LABELS } from '../../types/rules';
import type { DocumentTypeId } from '../../types/rules';
import './Settings.css';

interface SettingsProps {
  onClose: () => void;
}

/**
 * Main Settings component with document type tabs and rule configuration.
 */
type TabId = DocumentTypeId | 'ignored-rules';

export function Settings({ onClose }: SettingsProps) {
  const [activeTab, setActiveTab] = useState<TabId>('factsheet');
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
    discardChanges,
    resetToDefaults,
  } = useRuleSettings(activeTab === 'ignored-rules' ? 'factsheet' : activeTab);

  // Fetch ignored rules for the Ignored Rules tab
  const {
    ignoredRules,
    loading: ignoredLoading,
    unignoreRule,
  } = useIgnoredRules(null);  // null = fetch all, not scoped to doc type

  // Handle deleting an ignored rule
  const handleDeleteIgnoredRule = useCallback(async (ruleId: string, documentType: string) => {
    try {
      await unignoreRule(ruleId, documentType);
    } catch (e) {
      console.error('Failed to delete ignored rule:', e);
    }
  }, [unignoreRule]);

  // Warn when leaving with unsaved changes
  useUnsavedChangesWarning(isDirty);

  // Handle tab change with unsaved changes warning
  const handleTabChange = (tabId: TabId) => {
    if (isDirty && activeTab !== 'ignored-rules') {
      const confirmed = window.confirm(
        'You have unsaved changes. Are you sure you want to switch tabs? Changes will be lost.'
      );
      if (!confirmed) return;
    }
    setActiveTab(tabId);
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

  // Handle discard changes (local only, no API call)
  const handleDiscard = () => {
    discardChanges();
  };

  // Handle reset to defaults with confirmation (deletes saved overrides)
  const handleResetToDefaults = async () => {
    const confirmed = window.confirm(
      'Are you sure you want to revert to the starter profile? This will delete your saved customizations and cannot be undone.'
    );
    if (!confirmed) return;
    await resetToDefaults();
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
        <button
          type="button"
          className={`settings__tab ${activeTab === 'ignored-rules' ? 'settings__tab--active' : ''}`}
          onClick={() => handleTabChange('ignored-rules')}
        >
          Ignored Rules
        </button>
      </div>

      <div className="settings__content">
        {activeTab === 'ignored-rules' ? (
          <IgnoredRulesTab
            ignoredRules={ignoredRules}
            onDelete={handleDeleteIgnoredRule}
            loading={ignoredLoading}
          />
        ) : (
          <>
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
          </>
        )}
      </div>

      {activeTab !== 'ignored-rules' && (
        <div className="settings__footer">
          <button
            type="button"
            className="settings__button settings__button--reset"
            onClick={handleResetToDefaults}
            disabled={isSaving}
          >
            Revert to Starter Profile
          </button>
          <div className="settings__footer-right">
            <button
              type="button"
              className="settings__button settings__button--discard"
              onClick={handleDiscard}
              disabled={!isDirty || isSaving}
            >
              Discard
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
      )}
    </div>
  );
}
