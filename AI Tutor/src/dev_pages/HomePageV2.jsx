import {
    ArrowRight,
    BookOpenCheck,
    BrainCircuit,
    ClipboardList,
    Flame,
    GraduationCap,
    History,
    Menu,
    MessageCircleQuestion,
    PenLine,
    Trophy,
    UserCircle,
    X,
} from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext.jsx';
import { useProtectedNavigation } from '../hooks/useProtectedNavigation.js';
import '../PageComponents/CSS/HomePageV2.css';

const sidebarLinks = [
    {
        label: 'Practice Exam',
        route: '/take_a_test',
        Icon: ClipboardList,
    },
    {
        label: 'Practice Question',
        route: '/practice',
        Icon: PenLine,
    },
    {
        label: 'Survival Mode',
        route: '/survival',
        Icon: Flame,
    },
    {
        label: 'Ask TutorGuy',
        route: '/query',
        Icon: MessageCircleQuestion,
    },
    {
        label: 'Exam History',
        route: '/exam_history',
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
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const navigate = useNavigate();
    const { navigateWithAuth } = useProtectedNavigation();
    const { user } = useAuth();
    const displayName = user?.user_metadata?.display_name || 'there';
    const closeSidebar = () => setIsSidebarOpen(false);
    const handleSidebarNavigation = (route) => {
        closeSidebar();
        navigateWithAuth(route);
    };

    return (
        <main className="home-v2-page">
            <header className="home-v2-header">
                <div className="home-v2-header-left">
                    <button
                        className="home-v2-sidebar-toggle"
                        aria-label={isSidebarOpen ? 'Close sidebar' : 'Open sidebar'}
                        aria-expanded={isSidebarOpen}
                        onClick={() => setIsSidebarOpen((current) => !current)}
                    >
                        {isSidebarOpen ? <X size={23} aria-hidden="true" /> : <Menu size={23} aria-hidden="true" />}
                    </button>
                    <button className="home-v2-brand" onClick={() => navigateWithAuth('/homeV2')}>
                        <GraduationCap size={24} aria-hidden="true" />
                        <span>TutorGuy SAT</span>
                    </button>
                </div>
                <button className="home-v2-profile-button" onClick={() => navigate('/profile')}>
                    <UserCircle size={24} aria-hidden="true" />
                    <span>Profile</span>
                </button>
            </header>

            {isSidebarOpen && (
                <button
                    className="home-v2-sidebar-scrim"
                    aria-label="Close sidebar"
                    onClick={closeSidebar}
                />
            )}

            <aside className={`home-v2-sidebar ${isSidebarOpen ? 'is-open' : ''}`} aria-label="SAT navigation">
                <div className="home-v2-sidebar-header">
                    <span>Study tools</span>
                    <button aria-label="Close sidebar" onClick={closeSidebar}>
                        <X size={20} aria-hidden="true" />
                    </button>
                </div>
                <nav className="home-v2-sidebar-nav">
                    {sidebarLinks.map(({ label, route, Icon }) => (
                        <button key={label} onClick={() => handleSidebarNavigation(route)}>
                            <Icon size={20} aria-hidden="true" />
                            <span>{label}</span>
                            <ArrowRight size={16} aria-hidden="true" />
                        </button>
                    ))}
                </nav>
            </aside>

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

            <button
                className="home-v2-chatbot-button"
                aria-label="Ask TutorGuy"
                onClick={() => navigate('/query')}
            >
                <MessageCircleQuestion size={28} aria-hidden="true" />
            </button>
        </main>
    );
}
