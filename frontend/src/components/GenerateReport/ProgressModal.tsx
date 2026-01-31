import { useEffect, useRef } from 'react';
import './ProgressModal.css';

interface ProgressModalProps {
  isOpen: boolean;
  message: string;
}

/**
 * Modal dialog showing indeterminate progress during PDF generation.
 * Uses native dialog element for accessibility.
 */
export function ProgressModal({ isOpen, message }: ProgressModalProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (isOpen && !dialog.open) {
      dialog.showModal();
    } else if (!isOpen && dialog.open) {
      dialog.close();
    }
  }, [isOpen]);

  return (
    <dialog ref={dialogRef} className="progress-modal">
      <div className="progress-modal__content">
        <div className="progress-modal__spinner" aria-hidden="true" />
        <p className="progress-modal__message">{message}</p>
      </div>
    </dialog>
  );
}
