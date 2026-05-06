const API_BASE_URL = import.meta.env.VITE_BACKEND_PORT;

const buildUrl = (path, queryParams) => {
    const url = new URL(path, API_BASE_URL);

    if (queryParams) {
        Object.entries(queryParams).forEach(([key, value]) => {
            if (value !== undefined && value !== null && value !== '') {
                url.searchParams.set(key, value);
            }
        });
    }

    return url.toString();
};

const parseResponse = async (response) => {
    const text = await response.text();
    const data = text ? JSON.parse(text) : null;

    if (!response.ok) {
        const message = data?.detail || data?.message || `HTTP error! status: ${response.status}`;
        throw new Error(message);
    }

    return data;
};

export const apiRequest = async (path, options = {}) => {
    const {
        method = 'GET',
        body,
        token,
        headers = {},
        queryParams,
    } = options;

    const requestHeaders = {
        ...headers,
    };

    if (body !== undefined && !(body instanceof FormData)) {
        requestHeaders['Content-Type'] = 'application/json';
    }

    if (token) {
        requestHeaders.Authorization = `Bearer ${token}`;
    }

    const response = await fetch(buildUrl(path, queryParams), {
        method,
        headers: requestHeaders,
        body: body instanceof FormData || body === undefined ? body : JSON.stringify(body),
    });

    return parseResponse(response);
};

export const apiBaseUrl = API_BASE_URL;
