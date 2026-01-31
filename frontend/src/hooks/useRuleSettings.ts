import { useReducer, useCallback, useEffect } from 'react';
import type { Template, Severity, DocumentTypeId, UserOverrides } from '../types/rules';

/**
 * State for the rules settings reducer.
 */
interface RuleSettingsState {
  rules: Template | null;
  originalRules: Template | null;
  isLoading: boolean;
  isDirty: boolean;
  isSaving: boolean;
  saveStatus: 'idle' | 'saving' | 'saved' | 'error';
  error: string | null;
}

/**
 * Actions for the rules settings reducer.
 */
type RuleSettingsAction =
  | { type: 'LOADING' }
  | { type: 'LOAD'; payload: Template }
  | { type: 'LOAD_ERROR'; error: string }
  | { type: 'TOGGLE_ENABLED'; categoryId: string; ruleId: string }
  | { type: 'SET_SEVERITY'; categoryId: string; ruleId: string; severity: Severity }
  | { type: 'UPDATE_EXPECTED'; categoryId: string; ruleId: string; field: string; value: unknown }
  | { type: 'SAVE_START' }
  | { type: 'SAVE_SUCCESS' }
  | { type: 'SAVE_ERROR'; error: string }
  | { type: 'RESET' }
  | { type: 'CLEAR_SAVE_STATUS' };

const initialState: RuleSettingsState = {
  rules: null,
  originalRules: null,
  isLoading: false,
  isDirty: false,
  isSaving: false,
  saveStatus: 'idle',
  error: null,
};

/**
 * Deep clone a template to avoid mutation.
 */
function cloneTemplate(template: Template): Template {
  return JSON.parse(JSON.stringify(template));
}

/**
 * Compute user overrides by comparing current rules with original.
 * Only includes fields that differ from the original.
 */
function computeOverrides(original: Template, current: Template): UserOverrides {
  const overrides: UserOverrides = {
    version: current.version,
    overrides: {},
  };

  for (const [categoryId, category] of Object.entries(current.categories)) {
    const originalCategory = original.categories[categoryId];
    if (!originalCategory) continue;

    for (const [ruleId, rule] of Object.entries(category.rules)) {
      const originalRule = originalCategory.rules[ruleId];
      if (!originalRule) continue;

      const ruleOverride: Record<string, unknown> = {};

      if (rule.enabled !== originalRule.enabled) {
        ruleOverride.enabled = rule.enabled;
      }
      if (rule.severity !== originalRule.severity) {
        ruleOverride.severity = rule.severity;
      }
      if (JSON.stringify(rule.expected) !== JSON.stringify(originalRule.expected)) {
        ruleOverride.expected = rule.expected;
      }

      if (Object.keys(ruleOverride).length > 0) {
        if (!overrides.overrides[categoryId]) {
          overrides.overrides[categoryId] = {};
        }
        overrides.overrides[categoryId][ruleId] = ruleOverride;
      }
    }
  }

  return overrides;
}

/**
 * Reducer for rule settings state management.
 */
function rulesReducer(state: RuleSettingsState, action: RuleSettingsAction): RuleSettingsState {
  switch (action.type) {
    case 'LOADING':
      return {
        ...state,
        isLoading: true,
        error: null,
      };

    case 'LOAD':
      return {
        ...state,
        rules: cloneTemplate(action.payload),
        originalRules: cloneTemplate(action.payload),
        isLoading: false,
        isDirty: false,
        error: null,
      };

    case 'LOAD_ERROR':
      return {
        ...state,
        isLoading: false,
        error: action.error,
      };

    case 'TOGGLE_ENABLED': {
      if (!state.rules) return state;
      const newRules = cloneTemplate(state.rules);
      const category = newRules.categories[action.categoryId];
      const rule = category?.rules[action.ruleId];
      if (rule) {
        rule.enabled = !rule.enabled;
      }
      return {
        ...state,
        rules: newRules,
        isDirty: true,
      };
    }

    case 'SET_SEVERITY': {
      if (!state.rules) return state;
      const newRules = cloneTemplate(state.rules);
      const category = newRules.categories[action.categoryId];
      const rule = category?.rules[action.ruleId];
      if (rule) {
        rule.severity = action.severity;
      }
      return {
        ...state,
        rules: newRules,
        isDirty: true,
      };
    }

    case 'UPDATE_EXPECTED': {
      if (!state.rules) return state;
      const newRules = cloneTemplate(state.rules);
      const category = newRules.categories[action.categoryId];
      const rule = category?.rules[action.ruleId];
      if (rule) {
        rule.expected = {
          ...rule.expected,
          [action.field]: action.value,
        };
      }
      return {
        ...state,
        rules: newRules,
        isDirty: true,
      };
    }

    case 'SAVE_START':
      return {
        ...state,
        isSaving: true,
        saveStatus: 'saving',
      };

    case 'SAVE_SUCCESS':
      return {
        ...state,
        originalRules: state.rules ? cloneTemplate(state.rules) : null,
        isSaving: false,
        isDirty: false,
        saveStatus: 'saved',
      };

    case 'SAVE_ERROR':
      return {
        ...state,
        isSaving: false,
        saveStatus: 'error',
        error: action.error,
      };

    case 'RESET':
      return {
        ...state,
        rules: state.originalRules ? cloneTemplate(state.originalRules) : null,
        isDirty: false,
      };

    case 'CLEAR_SAVE_STATUS':
      return {
        ...state,
        saveStatus: 'idle',
      };

    default:
      return state;
  }
}

/**
 * Hook result interface.
 */
export interface UseRuleSettingsResult {
  rules: Template | null;
  isLoading: boolean;
  isDirty: boolean;
  isSaving: boolean;
  saveStatus: 'idle' | 'saving' | 'saved' | 'error';
  error: string | null;
  toggleRule: (categoryId: string, ruleId: string) => void;
  setSeverity: (categoryId: string, ruleId: string, severity: Severity) => void;
  updateExpected: (categoryId: string, ruleId: string, field: string, value: unknown) => void;
  save: () => Promise<void>;
  discardChanges: () => void;
  resetToDefaults: () => Promise<void>;
  reload: () => Promise<void>;
}

/**
 * Hook for managing rule settings state.
 * Fetches rules from the backend API and provides methods for editing, saving, and resetting.
 */
export function useRuleSettings(documentType: DocumentTypeId): UseRuleSettingsResult {
  const [state, dispatch] = useReducer(rulesReducer, initialState);

  // Load rules from API
  const loadRules = useCallback(async () => {
    dispatch({ type: 'LOADING' });
    try {
      const response = await fetch(`http://localhost:8002/api/rules/${documentType}`);
      if (!response.ok) {
        throw new Error(`Failed to load rules: ${response.statusText}`);
      }
      const rules: Template = await response.json();
      dispatch({ type: 'LOAD', payload: rules });
    } catch (err) {
      dispatch({
        type: 'LOAD_ERROR',
        error: err instanceof Error ? err.message : 'Failed to load rules',
      });
    }
  }, [documentType]);

  // Load rules on mount or document type change
  useEffect(() => {
    loadRules();
  }, [loadRules]);

  // Clear save status after a delay
  useEffect(() => {
    if (state.saveStatus === 'saved') {
      const timer = setTimeout(() => {
        dispatch({ type: 'CLEAR_SAVE_STATUS' });
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [state.saveStatus]);

  // Toggle rule enabled state
  const toggleRule = useCallback((categoryId: string, ruleId: string) => {
    dispatch({ type: 'TOGGLE_ENABLED', categoryId, ruleId });
  }, []);

  // Set rule severity
  const setSeverity = useCallback((categoryId: string, ruleId: string, severity: Severity) => {
    dispatch({ type: 'SET_SEVERITY', categoryId, ruleId, severity });
  }, []);

  // Update expected field
  const updateExpected = useCallback((categoryId: string, ruleId: string, field: string, value: unknown) => {
    dispatch({ type: 'UPDATE_EXPECTED', categoryId, ruleId, field, value });
  }, []);

  // Save current rules to backend
  const save = useCallback(async () => {
    if (!state.rules || !state.originalRules) return;

    dispatch({ type: 'SAVE_START' });
    try {
      const overrides = computeOverrides(state.originalRules, state.rules);
      const response = await fetch(`http://localhost:8002/api/rules/${documentType}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(overrides),
      });
      if (!response.ok) {
        throw new Error(`Failed to save rules: ${response.statusText}`);
      }
      dispatch({ type: 'SAVE_SUCCESS' });
    } catch (err) {
      dispatch({
        type: 'SAVE_ERROR',
        error: err instanceof Error ? err.message : 'Failed to save rules',
      });
    }
  }, [documentType, state.rules, state.originalRules]);

  // Discard local unsaved changes (revert to last saved state)
  const discardChanges = useCallback(() => {
    dispatch({ type: 'RESET' });
  }, []);

  // Reset to template defaults via API (deletes user overrides)
  const resetToDefaults = useCallback(async () => {
    try {
      const response = await fetch(`http://localhost:8002/api/rules/${documentType}/reset`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error(`Failed to reset rules: ${response.statusText}`);
      }
      // Reload rules after reset
      await loadRules();
    } catch (err) {
      dispatch({
        type: 'LOAD_ERROR',
        error: err instanceof Error ? err.message : 'Failed to reset rules',
      });
    }
  }, [documentType, loadRules]);

  // Reload rules from API
  const reload = useCallback(async () => {
    await loadRules();
  }, [loadRules]);

  return {
    rules: state.rules,
    isLoading: state.isLoading,
    isDirty: state.isDirty,
    isSaving: state.isSaving,
    saveStatus: state.saveStatus,
    error: state.error,
    toggleRule,
    setSeverity,
    updateExpected,
    save,
    discardChanges,
    resetToDefaults,
    reload,
  };
}
