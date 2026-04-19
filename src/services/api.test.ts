import { describe, it, expect, vi, beforeEach } from 'vitest';
import { api } from './api';

describe('api service', () => {
    beforeEach(() => {
        global.fetch = vi.fn();
    });

    it('should accurately parse bigints without losing precision', async () => {
        // Mock a backend response containing an integer safely larger than Number.MAX_SAFE_INTEGER
        const mockResponseText = '{"data": [{"id": 12345678901234567890}]}';
        const mockResponse = new Response(mockResponseText, {
            status: 200,
            headers: { 'Content-Type': 'application/json' }
        });

        // @ts-ignore
        global.fetch.mockResolvedValue(mockResponse);

        const results = await api.getJobResults('any_job_id');
        
        // Assert json-bigint properly parses it as a string to preserve precision
        expect(results).toBeDefined();
        if (results && results.data) {
            expect(results.data[0].id).toBe('12345678901234567890');
        } else {
            throw new Error('No data returned array');
        }
    });
});
