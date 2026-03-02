import React, { useState, useEffect } from 'react';
import { X, Save } from 'lucide-react';
import { api, type ConfigOption } from '../../services/api';
import styles from './ConfigModal.module.css';

interface ConfigModalProps {
    isOpen: boolean;
    onClose: () => void;
    configs: ConfigOption[];
    onSaved: () => void;
}

export const ConfigModal: React.FC<ConfigModalProps> = ({ isOpen, onClose, configs, onSaved }) => {
    const [values, setValues] = useState<Record<string, any>>({});
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (isOpen) {
            const initialValues: Record<string, any> = {};
            configs.forEach(c => {
                initialValues[c.id] = c.current_value ?? c.default_value ?? '';
            });
            setValues(initialValues);
            setError(null);
        }
    }, [isOpen, configs]);

    if (!isOpen) return null;

    const handleSave = async () => {
        setIsSaving(true);
        setError(null);
        try {
            await api.saveConfigs(values);
            onSaved();
            onClose();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred while saving configurations');
        } finally {
            setIsSaving(false);
        }
    };

    const handleChange = (id: string, value: any) => {
        setValues(prev => ({ ...prev, [id]: value }));
    };

    const renderInput = (config: ConfigOption) => {
        const val = values[config.id];

        switch (config.ui_input_type) {
            case 'select':
                return (
                    <select
                        className={styles.select}
                        value={val}
                        onChange={(e) => handleChange(config.id, e.target.value)}
                    >
                        {config.options?.map(opt => (
                            <option key={opt.value} value={opt.value}>{opt.label}</option>
                        ))}
                    </select>
                );
            case 'radio':
                return (
                    <div className={styles.radioGroup}>
                        {config.options?.map(opt => (
                            <label key={opt.value} className={styles.radioOption}>
                                <input
                                    type="radio"
                                    name={config.id}
                                    value={opt.value}
                                    checked={val === opt.value}
                                    onChange={() => handleChange(config.id, opt.value)}
                                />
                                {opt.label}
                            </label>
                        ))}
                    </div>
                );
            case 'toggle':
                return (
                    <label className={styles.toggleContainer}>
                        <input
                            type="checkbox"
                            checked={!!val}
                            onChange={(e) => handleChange(config.id, e.target.checked)}
                        />
                        <span>{val ? 'Enabled' : 'Disabled'}</span>
                    </label>
                );
            case 'text':
            default:
                return (
                    <input
                        className={styles.input}
                        type={config.data_type === 'integer' ? 'number' : 'text'}
                        value={val}
                        onChange={(e) => {
                            const v = config.data_type === 'integer' ? parseInt(e.target.value, 10) : e.target.value;
                            handleChange(config.id, isNaN(v as any) ? e.target.value : v);
                        }}
                    />
                );
        }
    };

    return (
        <div className={styles.modalOverlay} onClick={onClose}>
            <div className={styles.modal} onClick={e => e.stopPropagation()}>
                <div className={styles.header}>
                    <h2>Spark Configuration</h2>
                    <button className={styles.closeButton} onClick={onClose}>
                        <X size={20} />
                    </button>
                </div>
                <div className={styles.body}>
                    {error && (
                        <div className={styles.errorBanner}>
                            {error}
                        </div>
                    )}

                    {isSaving ? (
                        <div className={styles.loadingOverlay}>
                            <div className={styles.spinner} />
                            <p>Settings are being updated...</p>
                        </div>
                    ) : (
                        <div className={styles.form}>
                            {configs.map(config => (
                                <div key={config.id} className={styles.formGroup}>
                                    <label>
                                        {config.label}
                                        {config.is_required && <span className={styles.required}>*</span>}
                                    </label>
                                    {renderInput(config)}
                                </div>
                            ))}
                        </div>
                    )}
                </div>
                <div className={styles.footer}>
                    <button
                        className={styles.cancelButton}
                        onClick={onClose}
                        disabled={isSaving}
                    >
                        Cancel
                    </button>
                    <button
                        className={styles.saveButton}
                        onClick={handleSave}
                        disabled={isSaving}
                    >
                        <Save size={16} />
                        Save
                    </button>
                </div>
            </div>
        </div>
    );
};
