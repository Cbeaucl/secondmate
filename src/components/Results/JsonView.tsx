import React from 'react';
import Editor from '@monaco-editor/react';
import styles from './JsonView.module.css';

interface JsonViewProps {
    data: unknown[];
}

export const JsonView: React.FC<JsonViewProps> = ({ data }) => {
    const jsonString = JSON.stringify(data, null, 2);

    return (
        <div className={styles.container}>
            <Editor
                height="100%"
                defaultLanguage="json"
                value={jsonString}
                theme="spark-dark"
                options={{
                    readOnly: true,
                    minimap: { enabled: false },
                    fontSize: 13,
                    fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
                    scrollBeyondLastLine: false,
                    automaticLayout: true,
                    folding: true,
                    lineNumbers: 'on',
                    wordWrap: 'on',
                }}
            />
        </div>
    );
};
