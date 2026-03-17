import { useState, useEffect, useRef, useCallback } from 'react';
import { api, type Job, type QueryResult } from '../services/api';

// Passive polling interval for the full job list (ms)
const LIST_POLL_INTERVAL = 10_000;

// Active polling interval for a specific job (ms)
const JOB_POLL_INTERVAL = 1_500;

export interface UseJobQueueReturn {
    jobs: Job[];
    selectedJob: Job | null;
    selectedJobResult: QueryResult | null;
    isLoadingResult: boolean;
    submitJob: (query: string) => Promise<void>;
    selectJob: (job: Job) => void;
}

export const useJobQueue = (): UseJobQueueReturn => {
    const [jobs, setJobs] = useState<Job[]>([]);
    const [selectedJob, setSelectedJob] = useState<Job | null>(null);
    const [selectedJobResult, setSelectedJobResult] = useState<QueryResult | null>(null);
    const [isLoadingResult, setIsLoadingResult] = useState(false);

    // Refs for polling intervals
    const listPollRef = useRef<ReturnType<typeof setInterval> | null>(null);
    const jobPollRef = useRef<ReturnType<typeof setInterval> | null>(null);

    // -- Passive polling: refresh the full job list every 10s --
    const refreshJobList = useCallback(async () => {
        try {
            const data = await api.listJobs();
            setJobs(data.jobs);

            // If we have a selected job, update it from the fresh list
            setSelectedJob(prev => {
                if (!prev) return null;
                const updated = data.jobs.find(j => j.job_id === prev.job_id);
                return updated || prev;
            });
        } catch (err) {
            console.error('Failed to refresh job list', err);
        }
    }, []);

    useEffect(() => {
        // Initial fetch
        refreshJobList();

        // Set up passive polling
        listPollRef.current = setInterval(refreshJobList, LIST_POLL_INTERVAL);

        return () => {
            if (listPollRef.current) clearInterval(listPollRef.current);
        };
    }, [refreshJobList]);

    // -- Active polling: watch a specific job until it completes --
    const startActivePolling = useCallback((jobId: string) => {
        // Clear any existing active poll
        if (jobPollRef.current) {
            clearInterval(jobPollRef.current);
            jobPollRef.current = null;
        }

        const poll = async () => {
            try {
                const job = await api.getJob(jobId);

                // Update selected job
                setSelectedJob(job);

                // Update in the jobs list too
                setJobs(prev =>
                    prev.map(j => (j.job_id === jobId ? job : j))
                );

                // If terminal, stop polling and fetch results if succeeded
                if (job.status === 'succeeded' || job.status === 'failed') {
                    if (jobPollRef.current) {
                        clearInterval(jobPollRef.current);
                        jobPollRef.current = null;
                    }

                    if (job.status === 'succeeded') {
                        setIsLoadingResult(true);
                        try {
                            const result = await api.getJobResults(jobId);
                            setSelectedJobResult(result);
                        } catch (err) {
                            setSelectedJobResult({
                                error: err instanceof Error ? err.message : 'Failed to load results',
                            });
                        } finally {
                            setIsLoadingResult(false);
                        }
                    } else {
                        // Failed — show the error from the job
                        setSelectedJobResult({
                            error: job.error_message || 'Query execution failed',
                        });
                    }
                }
            } catch (err) {
                console.error('Active poll failed', err);
            }
        };

        // Immediate first check
        poll();

        // Then poll on interval
        jobPollRef.current = setInterval(poll, JOB_POLL_INTERVAL);
    }, []);

    // Cleanup active polling on unmount
    useEffect(() => {
        return () => {
            if (jobPollRef.current) clearInterval(jobPollRef.current);
        };
    }, []);

    // -- Submit a new job --
    const submitJob = useCallback(
        async (query: string) => {
            if (!query.trim()) return;

            try {
                const { job_id } = await api.submitJob(query);

                // Optimistically add to the list
                const optimisticJob: Job = {
                    job_id,
                    query_text: query,
                    status: 'queued',
                    error_message: null,
                    created_at: Date.now() / 1000,
                    started_at: null,
                    completed_at: null,
                };

                setJobs(prev => [optimisticJob, ...prev]);
                setSelectedJob(optimisticJob);
                setSelectedJobResult(null);
                setIsLoadingResult(false);

                // Start actively polling this job
                startActivePolling(job_id);
            } catch (err) {
                console.error('Failed to submit job', err);
            }
        },
        [startActivePolling],
    );

    // -- Select a job from the history --
    const selectJob = useCallback(
        (job: Job) => {
            setSelectedJob(job);
            setSelectedJobResult(null);
            setIsLoadingResult(false);

            if (job.status === 'queued' || job.status === 'running') {
                // Start active polling for in-progress jobs
                startActivePolling(job.job_id);
            } else {
                // Clear any active polling
                if (jobPollRef.current) {
                    clearInterval(jobPollRef.current);
                    jobPollRef.current = null;
                }

                if (job.status === 'succeeded') {
                    // Fetch results immediately
                    setIsLoadingResult(true);
                    api.getJobResults(job.job_id)
                        .then(result => setSelectedJobResult(result))
                        .catch(err =>
                            setSelectedJobResult({
                                error: err instanceof Error ? err.message : 'Failed to load results',
                            }),
                        )
                        .finally(() => setIsLoadingResult(false));
                } else if (job.status === 'failed') {
                    setSelectedJobResult({
                        error: job.error_message || 'Query execution failed',
                    });
                }
            }
        },
        [startActivePolling],
    );

    return {
        jobs,
        selectedJob,
        selectedJobResult,
        isLoadingResult,
        submitJob,
        selectJob,
    };
};
