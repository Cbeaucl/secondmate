import React from 'react';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import { Sidebar } from './Sidebar';
import { api, type SystemInfo } from '../../services/api';
import styles from './MainLayout.module.css';

interface MainLayoutProps {
  children: React.ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const [systemInfo, setSystemInfo] = React.useState<SystemInfo | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    const fetchInfo = async () => {
      try {
        const info = await api.getSystemInfo();
        setSystemInfo(info);
      } catch (_err) {
        setError('Disconnected');
      }
    };

    fetchInfo();

    // Poll every 30 seconds
    const interval = setInterval(fetchInfo, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className={styles.container}>
      <PanelGroup direction="horizontal">
        <Panel defaultSize={20} minSize={15} maxSize={40} className={styles.sidebarPanel}>
          <Sidebar />
        </Panel>
        <PanelResizeHandle className={styles.resizeHandle} />
        <Panel className={styles.contentPanel}>
          {children}
        </Panel>
      </PanelGroup>
      <div className={styles.statusBar}>
        <span>Ready</span>
        {error ? (
          <span>Spark: {error}</span>
        ) : systemInfo ? (
          <span>Spark: Connected (v{systemInfo.spark_version})</span>
        ) : (
          <span>Spark: Connecting...</span>
        )}
      </div>
    </div>
  );
};
