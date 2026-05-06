import { apiRequest } from './apiClient';

export const submitTrainingPdf = ({ pdf, examName }) => {
    const formData = new FormData();
    formData.append('pdf', pdf);
    formData.append('exam_name', examName);

    return apiRequest('/submit_pdf', {
        method: 'POST',
        body: formData,
    });
};
