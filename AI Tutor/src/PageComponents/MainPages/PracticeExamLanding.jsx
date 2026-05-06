import { useNavigate, useParams } from 'react-router-dom';
import PropTypes from 'prop-types';
import '../CSS/PracticeExamLanding.css';

const EXAM_CONTENT = {
    full_exam: {
        title: 'Practice Exam',
        description: 'A full-length SAT practice exam with timed sections, just like the real test.',
        expect: [
            '4 modules total — 2 English, 2 Math',
            'Module 2 difficulty adapts based on your Module 1 score',
            'No penalty for wrong answers — always guess!',
            'Your results are saved to your exam history',
        ],
        timing: [
            'English Module: 32 minutes (27 questions)',
            'Math Module: 35 minutes (22 questions)',
            '10-minute break between English and Math',
        ],
        rules: [
            'Do not refresh or leave the page during the exam',
            'Each module must be submitted before moving on',
            'Timer will auto-submit when time runs out',
        ],
    },
    math_only: {
        title: 'Math Practice Exam',
        description: 'A timed Math-only SAT practice section to sharpen your problem-solving skills.',
        expect: [
            '2 modules of Math questions',
            'Module 2 adapts based on your Module 1 performance',
            'No penalty for wrong answers',
            'Results saved to your exam history',
        ],
        timing: [
            'Math Module 1: 35 minutes (22 questions)',
            'Short intermission between modules',
            'Math Module 2: 35 minutes (22 questions)',
        ],
        rules: [
            'Do not refresh or leave the page during the exam',
            'Submit each module before the timer runs out',
            'Timer will auto-submit when time runs out',
        ],
    },
    english_only: {
        title: 'English Practice Exam',
        description: 'A timed English-only SAT practice section covering reading and writing skills.',
        expect: [
            '2 modules of Reading & Writing questions',
            'Module 2 adapts based on your Module 1 performance',
            'No penalty for wrong answers',
            'Results saved to your exam history',
        ],
        timing: [
            'English Module 1: 32 minutes (27 questions)',
            'Short intermission between modules',
            'English Module 2: 32 minutes (27 questions)',
        ],
        rules: [
            'Do not refresh or leave the page during the exam',
            'Submit each module before the timer runs out',
            'Timer will auto-submit when time runs out',
        ],
    },
};

export default function PracticeExamLanding({ onStart, isLoading = false }) {
    const { examType } = useParams();
    const navigate = useNavigate();

    const content = EXAM_CONTENT[examType] ?? EXAM_CONTENT['full_exam'];

    return (
        <div className="pel-page">
            {/* Title + description */}
            <div className="pel-header">
                <h1 className="pel-title">{content.title}</h1>
                <p className="pel-description">{content.description}</p>
            </div>

            {/* Info grid */}
            <div className="pel-grid">
                {/* Left: What to expect */}
                <section className="pel-card pel-expect">
                    <div className="pel-card-heading">
                        <span className="pel-card-dot" />
                        <h2 className="pel-card-title">What to Expect</h2>
                    </div>
                    <ul className="pel-list">
                        {content.expect.map((item, i) => (
                            <li key={i} className="pel-list-item">
                                <span className="pel-dash">—</span>
                                {item}
                            </li>
                        ))}
                    </ul>
                </section>

                {/* Right: Timing + Rules stacked */}
                <div className="pel-right-col">
                    <section className="pel-card pel-timing">
                        <div className="pel-card-heading">
                            <span className="pel-card-dot" />
                            <h2 className="pel-card-title">Timing</h2>
                        </div>
                        <ul className="pel-list">
                            {content.timing.map((item, i) => (
                                <li key={i} className="pel-list-item">
                                    <span className="pel-dash">—</span>
                                    {item}
                                </li>
                            ))}
                        </ul>
                    </section>

                    <section className="pel-card pel-rules">
                        <div className="pel-card-heading">
                            <span className="pel-card-dot" />
                            <h2 className="pel-card-title">Rules</h2>
                        </div>
                        <ul className="pel-list">
                            {content.rules.map((item, i) => (
                                <li key={i} className="pel-list-item">
                                    <span className="pel-dash">—</span>
                                    {item}
                                </li>
                            ))}
                        </ul>
                    </section>
                </div>
            </div>

            {/* Footer actions */}
            <div className="pel-footer">
                <button className="pel-btn-back" onClick={() => navigate('/take_a_test')}>
                    Back
                </button>
                <button className="pel-btn-start" onClick={onStart ?? (() => navigate(`/test/${examType}`))} disabled={isLoading}>
                    Start
                </button>
            </div>
        </div>
    );
}

PracticeExamLanding.propTypes = {
    onStart: PropTypes.func,
    isLoading: PropTypes.bool,
};
