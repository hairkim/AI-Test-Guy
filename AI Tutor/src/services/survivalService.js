import { apiRequest } from './apiClient';

export const getSurvivalQuestion = ({ difficulty, section, excludedQuestionIds, domain }) => (
    apiRequest('/api/survival/question', {
        method: 'POST',
        body: {
            difficulty,
            section,
            domain,
            excluded_question_ids: excludedQuestionIds,
        },
    })
);

export const saveSurvivalSession = ({
    difficulty,
    section,
    questionsAnswered,
    questionsCorrect,
    questionIds,
    answers,
    startTime,
    token,
}) => (
    apiRequest('/api/survival/session/save', {
        method: 'POST',
        token,
        body: {
            difficulty,
            section,
            questions_answered: questionsAnswered,
            questions_correct: questionsCorrect,
            question_ids: questionIds,
            answers,
            start_time: startTime,
        },
    })
);

export const getSurvivalLeaderboard = ({ section, difficulty, limit = 20 }) => (
    apiRequest('/api/survival/leaderboard', {
        queryParams: { section, difficulty, limit },
    })
);
