import { useEffect } from 'react';

/**
 * Hook that adds a beforeunload handler when there are unsaved changes.
 * Shows browser's native "Leave site?" dialog when user tries to navigate away.
 *
 * @param isDirty - Whether there are unsaved changes
 */
export function useUnsavedChangesWarning(isDirty: boolean): void {
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (isDirty) {
        // Standard way to trigger browser's leave confirmation dialog
        e.preventDefault();
        // Required for Chrome - the actual message is ignored by modern browsers
        e.returnValue = '';
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [isDirty]);
}
