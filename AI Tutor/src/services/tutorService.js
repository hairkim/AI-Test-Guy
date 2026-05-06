import { apiRequest } from './apiClient';

export const askMathTutor = ({ question, image }) => (
    apiRequest('/ask', {
        method: 'POST',
        body: {
            question: question || null,
            image: image || null,
        },
    })
);

export const askEnglishTutor = ({ question, passage }) => (
    apiRequest('/ask_english', {
        method: 'POST',
        body: {
            question,
            passage: passage || null,
        },
    })
);
