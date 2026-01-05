import React from 'react';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import { Sidebar } from './Sidebar';
import styles from './MainLayout.module.css';

interface MainLayoutProps {
  children: React.ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
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
        <span>Spark: Disconnected (Mock)</span>
      </div>
    </div>
  );
};
