import { useCallback, useState } from 'react';
import { useDropzone, FileRejection } from 'react-dropzone';
import './DropZone.css';

interface DropZoneProps {
  onFileAccepted: (file: File) => void;
  isProcessing: boolean;
  error?: string | null;
}

export function DropZone({ onFileAccepted, isProcessing, error }: DropZoneProps) {
  const [rejectionMessage, setRejectionMessage] = useState<string | null>(null);

  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: FileRejection[]) => {
    setRejectionMessage(null);

    if (rejectedFiles.length > 0) {
      const rejection = rejectedFiles[0];
      const rejectionError = rejection?.errors?.[0];
      if (!rejectionError) {
        setRejectionMessage('File was rejected');
      } else if (rejectionError.code === 'file-invalid-type') {
        setRejectionMessage('Only PDF files are accepted');
      } else if (rejectionError.code === 'too-many-files') {
        setRejectionMessage('Please upload one file at a time');
      } else {
        setRejectionMessage(rejectionError.message);
      }
      return;
    }

    const file = acceptedFiles[0];
    if (file) {
      onFileAccepted(file);
    }
  }, [onFileAccepted]);

  const { getRootProps, getInputProps, isDragActive, isDragAccept, isDragReject } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 1,
    disabled: isProcessing,
    multiple: false,
  });

  const displayError = error || rejectionMessage;

  const classNames = [
    'drop-zone',
    isDragActive ? 'drop-zone--active' : '',
    isDragAccept ? 'drop-zone--accept' : '',
    isDragReject ? 'drop-zone--reject' : '',
    isProcessing ? 'drop-zone--processing' : '',
    displayError ? 'drop-zone--error' : '',
  ].filter(Boolean).join(' ');

  return (
    <div {...getRootProps()} className={classNames}>
      <input {...getInputProps()} />

      {isProcessing ? (
        <div className="drop-zone__content">
          <div className="drop-zone__spinner" />
          <p className="drop-zone__text">Processing...</p>
        </div>
      ) : displayError ? (
        <div className="drop-zone__content drop-zone__content--error">
          <p className="drop-zone__error">{displayError}</p>
          <p className="drop-zone__secondary">Drop another PDF or click to browse</p>
        </div>
      ) : isDragActive ? (
        <div className="drop-zone__content">
          <p className="drop-zone__text">Drop PDF here...</p>
        </div>
      ) : (
        <div className="drop-zone__content">
          <div className="drop-zone__icon">
            <span className="drop-zone__icon-text">PDF</span>
          </div>
          <p className="drop-zone__text">Drop PDF here</p>
          <p className="drop-zone__secondary">or click to browse</p>
        </div>
      )}
    </div>
  );
}
