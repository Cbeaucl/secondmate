import React from 'react';
import type { Job, JobStatus } from '../../services/api';
import { Clock, History as HistoryIcon, X } from 'lucide-react';
import styles from './QueryHistory.module.css';

interface QueryHistoryProps {
    jobs: Job[];
    selectedJobId: string | null;
    onSelectJob: (job: Job) => void;
    onClose: () => void;
}

const STATUS_LABELS: Record<JobStatus, string> = {
    queued: 'Queued',
    running: 'Running',
    succeeded: 'Succeeded',
    failed: 'Failed',
};

export const QueryHistory: React.FC<QueryHistoryProps> = ({ jobs, selectedJobId, onSelectJob, onClose }) => {
    const formatDate = (timestamp: number) => {
        // Timestamps from backend are in seconds (Python time.time())
        const date = new Date(timestamp * 1000);
        const today = new Date();
        const yesterday = new Date();
        yesterday.setDate(today.getDate() - 1);

        if (date.toDateString() === today.toDateString()) {
            return 'Today';
        } else if (date.toDateString() === yesterday.toDateString()) {
            return 'Yesterday';
        } else {
            return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
        }
    };

    const formatTime = (timestamp: number) => {
        return new Date(timestamp * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    // Group jobs by date
    const groups: { label: string; jobs: Job[] }[] = [];
    jobs.forEach(job => {
        const label = formatDate(job.created_at);
        let group = groups.find(g => g.label === label);
        if (!group) {
            group = { label, jobs: [] };
            groups.push(group);
        }
        group.jobs.push(job);
    });

    const getStatusClass = (status: JobStatus): string => {
        switch (status) {
            case 'queued': return styles.cardQueued;
            case 'running': return styles.cardRunning;
            case 'succeeded': return styles.cardSucceeded;
            case 'failed': return styles.cardFailed;
            default: return '';
        }
    };

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <div className={styles.title}>
                    <HistoryIcon size={16} />
                    <span>Query Queue</span>
                </div>
                <div className={styles.actions}>
                    <button className={styles.closeButton} onClick={onClose} title="Close">
                        <X size={16} />
                    </button>
                </div>
            </div>

            <div className={styles.content}>
                {jobs.length === 0 ? (
                    <div className={styles.emptyState}>
                        <Clock size={32} />
                        <p>No queries submitted yet</p>
                    </div>
                ) : (
                    groups.map((group) => (
                        <div key={group.label} className={styles.group}>
                            <div className={styles.groupLabel}>{group.label}</div>
                            {group.jobs.map((job) => (
                                <div
                                    key={job.job_id}
                                    className={`${styles.card} ${getStatusClass(job.status)} ${
                                        selectedJobId === job.job_id ? styles.cardSelected : ''
                                    }`}
                                    onClick={() => onSelectJob(job)}
                                >
                                    <pre className={styles.queryPreview}>
                                        {job.query_text}
                                    </pre>
                                    <div className={styles.cardFooter}>
                                        <span className={`${styles.statusBadge} ${styles[`badge_${job.status}`]}`}>
                                            {STATUS_LABELS[job.status]}
                                        </span>
                                        <span className={styles.timestamp}>
                                            {formatTime(job.created_at)}
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};
