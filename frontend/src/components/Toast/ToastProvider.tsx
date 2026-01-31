import { Toaster } from 'sonner';

/**
 * Toast notification provider using Sonner.
 * Positioned at bottom-right with 5-second default duration.
 */
export function ToastProvider() {
  return (
    <Toaster
      position="bottom-right"
      expand={false}
      richColors
      duration={5000}
    />
  );
}
