import DashboardOverview from '../components/dashboard/DashboardOverview.jsx';
import DashboardShortcuts from '../components/dashboard/DashboardShortcuts.jsx';
import DashboardSidePanel from '../components/dashboard/DashboardSidePanel.jsx';
import SchoolScroller from '../components/dashboard/SchoolScroller.jsx';
import { useAuth } from '../contexts/AuthContext.jsx';
import { useDashboardData } from '../hooks/useDashboardData.js';
import { useProtectedNavigation } from '../hooks/useProtectedNavigation.js';
import '../PageComponents/CSS/HomePage.css';

export default function HomePage() {
    const { navigateWithAuth } = useProtectedNavigation();
    const { user, session } = useAuth();
    const dashboardData = useDashboardData(session);

    return (
        <div className="home-page">
            <div className="home-left-side">
                <div className="top">
                    <h1>Welcome {user?.user_metadata?.display_name}</h1>
                </div>
                <DashboardShortcuts onNavigate={navigateWithAuth} />
                <DashboardOverview
                    errors={dashboardData.errors}
                    loading={dashboardData.loading}
                    recentExam={dashboardData.recentExam}
                    tasks={dashboardData.tasks}
                />
                <div className="bottom-content">
                    <SchoolScroller previousScore={dashboardData.recentExam?.total_score} />
                </div>
            </div>
            <DashboardSidePanel />
        </div>
    );
}
