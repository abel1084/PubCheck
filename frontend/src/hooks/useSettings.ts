/**
 * Hook for managing settings API interactions.
 * Provides functions to load, save, and reset rule configurations.
 */
import { useState, useCallback, useEffect } from 'react';
import type { SettingsConfig } from '../types/settings';

interface UseSettingsResult {
  settings: SettingsConfig | null;
  isLoading: boolean;
  error: string | null;
  isDirty: boolean;
  loadSettings: () => Promise<void>;
  saveSettings: (config: SettingsConfig) => Promise<void>;
  resetSettings: () => Promise<void>;
  updateSettings: (config: SettingsConfig) => void;
}

export function useSettings(): UseSettingsResult {
  const [settings, setSettings] = useState<SettingsConfig | null>(null);
  const [originalSettings, setOriginalSettings] = useState<SettingsConfig | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadSettings = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/settings');
      if (!response.ok) {
        throw new Error(`Failed to load settings: ${response.status}`);
      }
      const data = await response.json();
      setSettings(data);
      setOriginalSettings(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load settings');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const saveSettings = useCallback(async (config: SettingsConfig) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });

      if (!response.ok) {
        throw new Error(`Failed to save settings: ${response.status}`);
      }

      const data = await response.json();
      setSettings(data);
      setOriginalSettings(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save settings');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const resetSettings = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/settings/reset', {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error(`Failed to reset settings: ${response.status}`);
      }

      const data = await response.json();
      setSettings(data);
      setOriginalSettings(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reset settings');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const updateSettings = useCallback((config: SettingsConfig) => {
    setSettings(config);
  }, []);

  // Check if settings have been modified
  const isDirty = settings !== null && originalSettings !== null &&
    JSON.stringify(settings) !== JSON.stringify(originalSettings);

  // Load settings on mount
  useEffect(() => {
    loadSettings();
  }, [loadSettings]);

  return {
    settings,
    isLoading,
    error,
    isDirty,
    loadSettings,
    saveSettings,
    resetSettings,
    updateSettings,
  };
}
