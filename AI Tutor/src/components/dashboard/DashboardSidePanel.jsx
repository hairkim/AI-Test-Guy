import ProfilePicture from '../common/ProfilePicture.jsx';
import SurvivalLeaderboard from './SurvivalLeaderboard.jsx';

export default function DashboardSidePanel() {
    return (
        <div className="home-right-side">
            <div className="survival_leaderboard">
                <SurvivalLeaderboard />
            </div>
            <div className="profile-picture">
                <ProfilePicture />
            </div>
        </div>
    );
}
