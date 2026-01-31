import { useState } from 'react';
import type { DocumentMetadata } from '../../types/extraction';

interface MetadataTabProps {
  metadata: DocumentMetadata;
}

export function MetadataTab({ metadata }: MetadataTabProps) {
  const [showAll, setShowAll] = useState(false);

  const keyFields = [
    { label: 'Title', value: metadata.title },
    { label: 'Author', value: metadata.author },
    { label: 'ISBN', value: metadata.isbn },
    { label: 'DOI', value: metadata.doi },
    { label: 'Job Number', value: metadata.job_number },
    { label: 'Creation Date', value: metadata.creation_date },
    { label: 'Producer', value: metadata.producer },
  ];

  return (
    <div className="metadata-tab">
      <table className="metadata-table">
        <tbody>
          {keyFields.map(field => (
            <tr key={field.label}>
              <th>{field.label}</th>
              <td>{field.value || <span className="metadata-empty">Not found</span>}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <button
        className="metadata-toggle"
        onClick={() => setShowAll(!showAll)}
      >
        {showAll ? 'Hide details' : 'Show all metadata'}
      </button>
      {showAll && (
        <pre className="metadata-raw">
          {JSON.stringify(metadata, null, 2)}
        </pre>
      )}
    </div>
  );
}
