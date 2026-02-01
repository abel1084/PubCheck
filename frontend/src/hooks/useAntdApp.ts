import { App } from 'antd';

/**
 * Hook to access Ant Design's message, modal, and notification APIs.
 * Must be used within components wrapped by the antd App component.
 */
export function useAntdApp() {
  return App.useApp();
}
