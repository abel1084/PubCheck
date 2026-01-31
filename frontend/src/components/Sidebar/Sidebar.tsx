import type { DocumentMetadata, DocumentType, Confidence } from '../../types/extraction';
import './Sidebar.css';

interface SidebarProps {
  filename: string;
  documentType: DocumentType;
  confidence: Confidence;
  metadata: DocumentMetadata;
  onDocumentTypeChange: (type: DocumentType) => void;
  onNewDocument: () => void;
}

const DOCUMENT_TYPES: DocumentType[] = [
  'Factsheet',
  'Policy Brief',
  'Working Paper',
  'Technical Report',
  'Publication',
];

export function Sidebar({
  filename,
  documentType,
  confidence,
  metadata,
  onDocumentTypeChange,
  onNewDocument,
}: SidebarProps) {
  return (
    <aside className="sidebar">
      <div className="sidebar__header">
        <h2>Document Info</h2>
        <button className="sidebar__new-btn" onClick={onNewDocument}>
          New Document
        </button>
      </div>

      <div className="sidebar__section">
        <label className="sidebar__label">Filename</label>
        <p className="sidebar__value">{filename}</p>
      </div>

      <div className="sidebar__section">
        <label className="sidebar__label">Pages</label>
        <p className="sidebar__value">{metadata.page_count}</p>
      </div>

      <div className="sidebar__section">
        <label className="sidebar__label">Document Type</label>
        <select
          className="sidebar__select"
          value={documentType}
          onChange={e => onDocumentTypeChange(e.target.value as DocumentType)}
        >
          {DOCUMENT_TYPES.map(type => (
            <option key={type} value={type}>{type}</option>
          ))}
        </select>
        <span className={`sidebar__confidence sidebar__confidence--${confidence}`}>
          {confidence} confidence
        </span>
      </div>

      {metadata.title && (
        <div className="sidebar__section">
          <label className="sidebar__label">Title</label>
          <p className="sidebar__value sidebar__value--title">{metadata.title}</p>
        </div>
      )}
    </aside>
  );
}
