import { apiRequest } from './apiClient';

export const generateDailyTasks = ({ token }) => (
    apiRequest('/api/daily/tasks/generate-daily', {
        method: 'POST',
        token,
    })
);
