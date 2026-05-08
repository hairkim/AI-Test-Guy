import PropTypes from 'prop-types';

const SHORTCUTS = [
    { label: 'Practice Exam', route: '/take_a_test' },
    { label: 'Practice Questions', route: '/practice' },
    { label: 'Survival', route: '/survival' },
    { label: 'Ask TutorGuy', route: '/query' },
    { label: 'Exam History', route: '/exam_history' },
];

export default function DashboardShortcuts({ onNavigate }) {
    return (
        <div className="bottom">
            {SHORTCUTS.map((shortcut) => (
                <button key={shortcut.label} onClick={() => onNavigate(shortcut.route)}>
                    {shortcut.label}
                </button>
            ))}
        </div>
    );
}

DashboardShortcuts.propTypes = {
    onNavigate: PropTypes.func.isRequired,
};
