import { Upload, message, Alert, Spin } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';

const { Dragger } = Upload;

interface DropZoneProps {
  onFileAccepted: (file: File) => void;
  isProcessing: boolean;
  error?: string | null;
}

export function DropZone({ onFileAccepted, isProcessing, error }: DropZoneProps) {
  const uploadProps: UploadProps = {
    name: 'file',
    accept: '.pdf,application/pdf',
    multiple: false,
    disabled: isProcessing,
    showUploadList: false,
    beforeUpload: (file) => {
      // Validate file type (workaround for accept + drag issue per RESEARCH.md)
      if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
        message.error('Only PDF files are accepted');
        return Upload.LIST_IGNORE;
      }
      onFileAccepted(file);
      return false; // Prevent auto-upload, handle manually
    },
  };

  return (
    <div style={{ padding: '40px', maxWidth: '600px', width: '100%', margin: '0 auto' }}>
      {error && (
        <Alert
          message="Upload Error"
          description={error}
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      <Dragger {...uploadProps} style={{ padding: '0 40px' }}>
        {isProcessing ? (
          <div style={{ padding: '40px 0' }}>
            <Spin size="large" />
            <p style={{ marginTop: 16, color: 'rgba(0, 0, 0, 0.45)' }}>
              Processing...
            </p>
          </div>
        ) : (
          <>
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text" style={{ padding: '0 24px' }}>
              Drop PDF here or click to browse
            </p>
            <p className="ant-upload-hint">
              Only PDF files are accepted
            </p>
          </>
        )}
      </Dragger>
    </div>
  );
}
