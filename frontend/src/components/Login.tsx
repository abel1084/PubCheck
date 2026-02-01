import { useState } from 'react';
import { Card, Form, Input, Button, Typography, Alert } from 'antd';
import { LockOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

interface LoginProps {
  onLogin: () => void;
}

export function Login({ onLogin }: LoginProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (values: { password: string }) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password: values.password }),
        credentials: 'include',
      });

      const data = await response.json();

      if (data.authenticated) {
        onLogin();
      } else {
        setError('Incorrect password');
      }
    } catch (e) {
      setError('Failed to connect to server');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      background: '#f5f5f5',
    }}>
      <Card style={{ width: 360, textAlign: 'center' }}>
        <Title level={2} style={{ marginBottom: 8 }}>PubCheck</Title>
        <Text type="secondary" style={{ display: 'block', marginBottom: 24 }}>
          Enter password to continue
        </Text>

        {error && (
          <Alert
            message={error}
            type="error"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}

        <Form onFinish={handleSubmit}>
          <Form.Item
            name="password"
            rules={[{ required: true, message: 'Please enter the password' }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="Password"
              size="large"
              autoFocus
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0 }}>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              size="large"
            >
              Login
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
