import { useState } from 'react';
import { Descriptions, Button, Typography } from 'antd';
import type { DocumentMetadata } from '../../types/extraction';

const { Text } = Typography;

interface MetadataTabProps {
  metadata: DocumentMetadata;
}

export function MetadataTab({ metadata }: MetadataTabProps) {
  const [showAll, setShowAll] = useState(false);

  const items = [
    { key: 'title', label: 'Title', children: metadata.title || <Text type="secondary">Not found</Text> },
    { key: 'author', label: 'Author', children: metadata.author || <Text type="secondary">Not found</Text> },
    { key: 'isbn', label: 'ISBN', children: metadata.isbn || <Text type="secondary">Not found</Text> },
    { key: 'doi', label: 'DOI', children: metadata.doi || <Text type="secondary">Not found</Text> },
    { key: 'job_number', label: 'Job Number', children: metadata.job_number || <Text type="secondary">Not found</Text> },
    { key: 'creation_date', label: 'Creation Date', children: metadata.creation_date || <Text type="secondary">Not found</Text> },
    { key: 'producer', label: 'Producer', children: metadata.producer || <Text type="secondary">Not found</Text> },
  ];

  return (
    <div className="metadata-tab">
      <Descriptions column={1} size="small" items={items} />
      <Button
        type="link"
        onClick={() => setShowAll(!showAll)}
        style={{ marginTop: 8, padding: 0 }}
      >
        {showAll ? 'Hide details' : 'Show all metadata'}
      </Button>
      {showAll && (
        <pre style={{
          marginTop: 8,
          padding: 12,
          background: '#f5f5f5',
          borderRadius: 4,
          fontSize: 12,
          overflow: 'auto'
        }}>
          {JSON.stringify(metadata, null, 2)}
        </pre>
      )}
    </div>
  );
}
