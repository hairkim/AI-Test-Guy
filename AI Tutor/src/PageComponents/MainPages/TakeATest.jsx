import { useNavigate } from 'react-router-dom';
import '../CSS/TakeATestPage.css';
import TestModeCard from '../SupportingComponents/TestModeCard.jsx';

const TEST_MODES = [
    {
        icon: '📝',
        title: 'Practice Exam',
        description: 'Simulate a full SAT exam with timed sections. Get a comprehensive score and detailed breakdown of your performance.',
        route: '/test/full_exam',
    },
    {
        icon: '🎯',
        title: 'Practice Questions',
        description: 'Work through individual practice questions at your own pace. Focus on specific topics and build your skills.',
        route: '/practice-questions',
    },
    {
        icon: '⚔️',
        title: 'Survival Mode',
        description: 'Answer as many questions as you can before you run out of lives. How long can you survive?',
        route: '/survival',
    },
];

export default function TakeATest() {
    const navigate = useNavigate();

    return (
        <div className="tap-page">
            {/* Hero row */}
            <div className="tap-hero">
                <div className="tap-hero-text">
                    <h1 className="tap-title">Online Tests</h1>
                    <p className="tap-description">
                        Choose a mode below to start practicing. Whether you want a full
                        timed exam, focused question sets, or a challenge — we have got you covered.
                    </p>
                </div>
                <div className="tap-hero-image">🏆</div>
            </div>

            {/* Mode cards */}
            <div className="tap-cards">
                {TEST_MODES.map((mode) => (
                    <TestModeCard
                        key={mode.title}
                        icon={mode.icon}
                        title={mode.title}
                        description={mode.description}
                        onStart={() => navigate(mode.route)}
                    />
                ))}
            </div>
        </div>
    );
}
