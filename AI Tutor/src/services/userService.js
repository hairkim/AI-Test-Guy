import { apiRequest } from './apiClient';

export const syncUser = ({ id, name, email, createdAt, pictureUrl = '', token }) => (
    apiRequest('/api/users/sync', {
        method: 'POST',
        token,
        body: {
            id,
            name,
            email,
            created_at: createdAt,
            picture_url: pictureUrl,
        },
    })
);

export const getProtectedUser = ({ token }) => (
    apiRequest('/protected', { token })
);
