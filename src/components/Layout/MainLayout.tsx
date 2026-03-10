import React from 'react';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import { Sidebar } from './Sidebar';
import { TableOverview } from './TableOverview';
import { DdlModal } from './DdlModal';
import { api, type SystemInfo } from '../../services/api';
import styles from './MainLayout.module.css';

interface MainLayoutProps {
  children: React.ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const [systemInfo, setSystemInfo] = React.useState<SystemInfo | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [overviewTable, setOverviewTable] = React.useState<{ catalog: string, namespace: string, table: string } | null>(null);
  const [ddlTable, setDdlTable] = React.useState<{ catalog: string, namespace: string, table: string } | null>(null);

  React.useEffect(() => {
    const fetchInfo = async () => {
      try {
        const info = await api.getSystemInfo();
        setSystemInfo(info);
      } catch {
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
          <Sidebar
            onTableOverview={(catalog, namespace, table) => setOverviewTable({ catalog, namespace, table })}
            onShowDdl={(catalog, namespace, table) => setDdlTable({ catalog, namespace, table })}
          />
        </Panel>
        <PanelResizeHandle className={styles.resizeHandle} />
        <Panel className={styles.contentPanel}>
          {children}
        </Panel>
      </PanelGroup>

      {overviewTable && (
        <TableOverview
          catalog={overviewTable.catalog}
          namespace={overviewTable.namespace}
          table={overviewTable.table}
          onClose={() => setOverviewTable(null)}
        />
      )}

      {ddlTable && (
        <DdlModal
          catalog={ddlTable.catalog}
          namespace={ddlTable.namespace}
          table={ddlTable.table}
          onClose={() => setDdlTable(null)}
        />
      )}

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
