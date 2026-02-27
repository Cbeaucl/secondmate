import React, { useRef, useEffect } from 'react';
import Editor, { type OnMount } from '@monaco-editor/react';
import type { editor } from 'monaco-editor';
import styles from './SqlEditor.module.css';

interface SqlEditorProps {
    value?: string;
    onChange?: (value: string | undefined) => void;
    onRunQuery?: () => void;
}

export const SqlEditor: React.FC<SqlEditorProps> = ({ value = '', onChange, onRunQuery }) => {
    const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);

    const onRunQueryRef = useRef(onRunQuery);

    useEffect(() => {
        onRunQueryRef.current = onRunQuery;
    }, [onRunQuery]);

    const handleEditorDidMount: OnMount = (editor, monaco) => {
        editorRef.current = editor;

        // Define a custom theme that matches our app
        monaco.editor.defineTheme('spark-dark', {
            base: 'vs-dark',
            inherit: true,
            rules: [
                { token: 'keyword', foreground: '38bdf8' },
                { token: 'string', foreground: 'a5f3fc' },
                { token: 'number', foreground: 'f472b6' },
                { token: 'comment', foreground: '64748b' },
            ],
            colors: {
                'editor.background': '#1e293b',
                'editor.foreground': '#f8fafc',
                'editor.lineHighlightBackground': '#334155',
                'editorLineNumber.foreground': '#64748b',
                'editor.selectionBackground': '#334155',
            }
        });

        monaco.editor.setTheme('spark-dark');

        // Add command for Ctrl+Enter (or Cmd+Enter on Mac)
        editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () => {
            if (onRunQueryRef.current) {
                onRunQueryRef.current();
            }
        });
    };

    return (
        <div className={styles.editorContainer}>
            <Editor
                height="100%"
                defaultLanguage="sql"
                value={value}
                onMount={handleEditorDidMount}
                onChange={onChange}
                options={{
                    minimap: { enabled: false },
                    fontSize: 14,
                    fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
                    padding: { top: 16 },
                    scrollBeyondLastLine: false,
                    automaticLayout: true,
                }}
            />
        </div>
    );
};
