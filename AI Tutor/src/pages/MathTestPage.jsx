import '../PageComponents/CSS/MathTestPage.css';
import SingleSectionExamPage from '../components/exam/SingleSectionExamPage.jsx';

const MATH_EXAM_COPY = {
    title: 'You are about to take a practice math only exam',
    description: [
        'The test includes 2 modules, each with 22 questions',
        'You will be given module 2 questions based on previous scoring',
        'There is no penalty for wrong answers',
        'Good luck!',
    ],
};

const MATH_EXAM_CLASSES = {
    root: 'math_main_container',
    idleContainer: 'math_idle_container',
    idleText: 'math_idle_text',
    idleButton: 'math_idle_button',
    testContainer: 'full_test_container',
    sectionInfo: 'full_section_info',
    timerContainer: 'full_timer_container',
    submitButton: 'full_submit_button',
    navButtons: 'full_test_buttons',
    resultsContainer: 'math_results_container',
};

export default function MathTestPage() {
    return (
        <SingleSectionExamPage
            examType="math_only"
            sectionType="Math"
            moduleStatePrefix="math"
            timerField="math_module_time_limit"
            copy={MATH_EXAM_COPY}
            classNames={MATH_EXAM_CLASSES}
        />
    );
}
