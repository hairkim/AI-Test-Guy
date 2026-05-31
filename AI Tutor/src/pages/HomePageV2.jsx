import {
    ArrowRight,
    BookOpenCheck,
    BrainCircuit,
    ClipboardList,
    Flame,
    GraduationCap,
    History,
    MessageCircleQuestion,
    PenLine,
    Trophy,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext.jsx';
import { useProtectedNavigation } from '../hooks/useProtectedNavigation.js';
import '../PageComponents/CSS/HomePageV2.css';

const toolCards = [
    {
        title: 'Practice Exams',
        description: 'Run full SAT-style sections and build timing discipline before test day.',
        route: '/take_a_test',
        cta: 'Start an exam',
        Icon: ClipboardList,
    },
    {
        title: 'Practice Questions',
        description: 'Target math, reading, and writing skills with focused question sets.',
        route: '/practice',
        cta: 'Drill skills',
        Icon: PenLine,
    },
    {
        title: 'Survival Mode',
        description: 'Answer under pressure and keep your streak alive through harder rounds.',
        route: '/survival',
        cta: 'Enter survival',
        Icon: Flame,
    },
    {
        title: 'Ask TutorGuy',
        description: 'Get guided help, explanations, and next-step coaching when you are stuck.',
        route: '/query',
        cta: 'Ask a question',
        Icon: MessageCircleQuestion,
    },
    {
        title: 'Exam History',
        description: 'Review past exams, spot score trends, and decide what to practice next.',
        route: '/exam_history',
        cta: 'Review scores',
        Icon: History,
    },
];

const studySteps = [
    'Take a diagnostic section',
    'Review missed concepts',
    'Practice targeted questions',
    'Retest and track growth',
];

export default function HomePageV2() {
    const { navigateWithAuth } = useProtectedNavigation();
    const { user } = useAuth();
    const displayName = user?.user_metadata?.display_name || 'there';

    return (
        <main className="home-v2-page">
            <header className="home-v2-header">
                <button className="home-v2-brand" onClick={() => navigateWithAuth('/homeV2')}>
                    <GraduationCap size={24} aria-hidden="true" />
                    <span>TutorGuy SAT</span>
                </button>
                <nav className="home-v2-nav" aria-label="SAT tools">
                    <button onClick={() => navigateWithAuth('/take_a_test')}>Exams</button>
                    <button onClick={() => navigateWithAuth('/practice')}>Practice</button>
                    <button onClick={() => navigateWithAuth('/query')}>TutorGuy</button>
                    <button onClick={() => navigateWithAuth('/exam_history')}>History</button>
                </nav>
            </header>

            <section className="home-v2-hero">
                <div className="home-v2-hero-copy">
                    <p className="home-v2-kicker">Digital SAT prep dashboard</p>
                    <h1>Welcome, {displayName}. Build your SAT score with a focused study loop.</h1>
                    <p className="home-v2-hero-text">
                        Practice like the real exam, review what went wrong, and ask TutorGuy for help while the mistake is still fresh.
                    </p>
                    <div className="home-v2-hero-actions">
                        <button className="home-v2-primary-action" onClick={() => navigateWithAuth('/take_a_test')}>
                            Start practice exam
                            <ArrowRight size={18} aria-hidden="true" />
                        </button>
                        <button className="home-v2-secondary-action" onClick={() => navigateWithAuth('/practice')}>
                            Practice questions
                        </button>
                    </div>
                </div>

                <aside className="home-v2-score-panel" aria-label="SAT prep snapshot">
                    <div className="home-v2-score-topline">
                        <span>Study plan</span>
                        <BookOpenCheck size={22} aria-hidden="true" />
                    </div>
                    <div className="home-v2-score-card">
                        <span className="home-v2-score-label">Target readiness</span>
                        <strong>4-step loop</strong>
                        <div className="home-v2-progress-bar">
                            <span />
                        </div>
                    </div>
                    <ol className="home-v2-study-steps">
                        {studySteps.map((step) => (
                            <li key={step}>{step}</li>
                        ))}
                    </ol>
                </aside>
            </section>

            <section className="home-v2-tool-section" aria-labelledby="home-v2-tools-title">
                <div className="home-v2-section-heading">
                    <p className="home-v2-kicker">Choose your next move</p>
                    <h2 id="home-v2-tools-title">SAT tools</h2>
                </div>
                <div className="home-v2-tools-grid">
                    {toolCards.map(({ title, description, route, cta, Icon }) => (
                        <article className="home-v2-tool-card" key={title}>
                            <div className="home-v2-tool-icon">
                                <Icon size={24} aria-hidden="true" />
                            </div>
                            <h3>{title}</h3>
                            <p>{description}</p>
                            <button onClick={() => navigateWithAuth(route)}>
                                {cta}
                                <ArrowRight size={17} aria-hidden="true" />
                            </button>
                        </article>
                    ))}
                </div>
            </section>

            <section className="home-v2-bottom-band" aria-label="Study guidance">
                <div className="home-v2-guidance">
                    <BrainCircuit size={28} aria-hidden="true" />
                    <div>
                        <h2>Use TutorGuy after each missed question.</h2>
                        <p>Turn errors into short explanations, then jump back into practice while the concept is active.</p>
                    </div>
                    <button onClick={() => navigateWithAuth('/query')}>Ask TutorGuy</button>
                </div>
                <div className="home-v2-metric-strip">
                    <div>
                        <Trophy size={22} aria-hidden="true" />
                        <span>Exam-ready habits</span>
                    </div>
                    <div>
                        <BookOpenCheck size={22} aria-hidden="true" />
                        <span>Math, reading, and writing</span>
                    </div>
                    <div>
                        <History size={22} aria-hidden="true" />
                        <span>Progress reviews</span>
                    </div>
                </div>
            </section>
        </main>
    );
}
