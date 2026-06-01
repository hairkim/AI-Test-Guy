import '../PageComponents/CSS/EnglishTestPage.css';
import SingleSectionExamPage from '../components/exam/SingleSectionExamPage.jsx';

const ENGLISH_EXAM_COPY = {
    title: 'You are about to take a practice English only exam',
    description: [
        'The test includes 2 modules, each with 27 questions',
        'You will be given module 2 questions based on previous scoring',
        'There is no penalty for wrong answers',
        'Good luck!',
    ],
};

const ENGLISH_EXAM_CLASSES = {
    root: 'english_main_container',
    idleContainer: 'english_idle_container',
    idleText: 'english_idle_text',
    idleButton: 'english_idle_button',
    testContainer: 'english_test_container',
    sectionInfo: 'english_section_info',
    timerContainer: 'english_timer_container',
    submitButton: 'english_submit_button',
    navButtons: 'english_test_buttons',
    resultsContainer: 'english_results_container',
};

export default function EnglishTestPage() {
    return (
        <SingleSectionExamPage
            examType="english_only"
            sectionType="English"
            moduleStatePrefix="english"
            timerField="eng_module_time_limit"
            copy={ENGLISH_EXAM_COPY}
            classNames={ENGLISH_EXAM_CLASSES}
        />
    );
}
