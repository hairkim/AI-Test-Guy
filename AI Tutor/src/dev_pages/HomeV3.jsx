import { useState } from "react";
import PropTypes from "prop-types";
import {
  ArrowRight,
  ClipboardList,
  Flame,
  GraduationCap,
  History,
  Menu,
  MessageCircleQuestion,
  PenLine,
  UserCircle,
  X,
} from "lucide-react";
import "../PageComponents/CSS/HomeV3.css";

// ── Mock Data ──────────────────────────────────────────────
const mockScores = [
  { date: "Jan 10", score: 1080 },
  { date: "Jan 24", score: 1150 },
  { date: "Feb 7",  score: 1190 },
  { date: "Feb 21", score: 1240 },
  { date: "Mar 6",  score: 1310 },
  { date: "Mar 15", score: 1350 },
];

const mockTasks = [
  { id: 1, label: "Complete 10 Math drills",   done: true  },
  { id: 2, label: "Review comma splice rules",  done: false },
  { id: 3, label: "Take a Reading mini-quiz",   done: false },
  { id: 4, label: "Watch quadratics video",     done: true  },
];

const mockLeaders = [
  { rank: 1, name: "Alex K.",   pts: 4820 },
  { rank: 2, name: "Priya M.",  pts: 4610 },
  { rank: 3, name: "Jordan T.", pts: 4390 },
  { rank: 4, name: "You",       pts: 3940, isUser: true },
  { rank: 5, name: "Sam R.",    pts: 3870 },
];

const mockColleges = [
  { name: "UCLA",          minScore: 1300, logo: "🔵" },
  { name: "UC San Diego",  minScore: 1270, logo: "🔷" },
  { name: "USC",           minScore: 1350, logo: "🔴" },
  { name: "Cal Poly SLO",  minScore: 1230, logo: "🟢" },
  { name: "UC Irvine",     minScore: 1260, logo: "🔵" },
  { name: "Stanford",      minScore: 1500, logo: "🟥" },
];

const sidebarItems = [
  { label: "Practice Exam", Icon: ClipboardList },
  { label: "Practice Question", Icon: PenLine },
  { label: "Survival Mode", Icon: Flame },
  { label: "Ask TutorGuy", Icon: MessageCircleQuestion },
  { label: "Exam History", Icon: History },
];

// ── Mini line chart (pure SVG, no lib) ────────────────────
function ScoreChart({ data }) {
  const W = 620, H = 200, PAD = 40;
  const scores = data.map(d => d.score);
  const minS = Math.min(...scores) - 80;
  const maxS = Math.max(...scores) + 60;
  const xStep = (W - PAD * 2) / (data.length - 1);

  const toX = i => PAD + i * xStep;
  const toY = s => H - PAD - ((s - minS) / (maxS - minS)) * (H - PAD * 2);

  const polyline = data.map((d, i) => `${toX(i)},${toY(d.score)}`).join(" ");
  const area =
    `M${toX(0)},${toY(data[0].score)} ` +
    data.map((d, i) => `L${toX(i)},${toY(d.score)}`).join(" ") +
    ` L${toX(data.length - 1)},${H - PAD} L${toX(0)},${H - PAD} Z`;

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="ht-score-svg" preserveAspectRatio="xMidYMid meet">
      <defs>
        <linearGradient id="htAreaGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#6ee7b7" stopOpacity="0.3" />
          <stop offset="100%" stopColor="#6ee7b7" stopOpacity="0.0" />
        </linearGradient>
      </defs>

      {[0, 0.25, 0.5, 0.75, 1].map(t => {
        const y = H - PAD - t * (H - PAD * 2);
        const val = Math.round(minS + t * (maxS - minS));
        return (
          <g key={t}>
            <line x1={PAD} y1={y} x2={W - PAD} y2={y} stroke="#1e2233" strokeWidth="1" />
            <text x={PAD - 6} y={y + 4} textAnchor="end" className="ht-chart-label">{val}</text>
          </g>
        );
      })}

      <path d={area} fill="url(#htAreaGrad)" />
      <polyline points={polyline} fill="none" stroke="#6ee7b7" strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" />

      {data.map((d, i) => (
        <g key={i}>
          <circle cx={toX(i)} cy={toY(d.score)} r="5" fill="#14171f" stroke="#6ee7b7" strokeWidth="2.5" />
          <text x={toX(i)} y={H - 8} textAnchor="middle" className="ht-chart-label">{d.date}</text>
        </g>
      ))}
    </svg>
  );
}

// ── College Rec Slider ─────────────────────────────────────
function CollegeSlider({ colleges, userScore }) {
  const [idx, setIdx] = useState(0);
  const visible = colleges.slice(idx, idx + 3);

  return (
    <div className="ht-college-slider">
      <button
        className="ht-slider-btn"
        onClick={() => setIdx(i => Math.max(0, i - 1))}
        disabled={idx === 0}
      >‹</button>

      <div className="ht-college-cards">
        {visible.map(c => {
          const reach = userScore < c.minScore;
          return (
            <div key={c.name} className={`ht-college-card ${reach ? "reach" : "match"}`}>
              <span className="ht-college-logo">{c.logo}</span>
              <span className="ht-college-name">{c.name}</span>
              <span className="ht-college-score">Min: {c.minScore}</span>
              <span className={`ht-college-tag ${reach ? "tag-reach" : "tag-match"}`}>
                {reach ? "Reach" : "Match"}
              </span>
            </div>
          );
        })}
      </div>

      <button
        className="ht-slider-btn"
        onClick={() => setIdx(i => Math.min(colleges.length - 3, i + 1))}
        disabled={idx >= colleges.length - 3}
      >›</button>
    </div>
  );
}

// ── Main Component ─────────────────────────────────────────
export default function HomePageTest() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [tasks, setTasks] = useState(mockTasks);
  const userScore = mockScores.at(-1).score;
  const points = 3940;

  const toggleTask = id =>
    setTasks(ts => ts.map(t => (t.id === id ? { ...t, done: !t.done } : t)));

  return (
    <div className="ht-page">
      {/* Header */}
      <header className="ht-header">
        <button
          className="ht-sidebar-toggle"
          aria-label={isSidebarOpen ? "Close sidebar" : "Open sidebar"}
          aria-expanded={isSidebarOpen}
          onClick={() => setIsSidebarOpen(current => !current)}
        >
          {isSidebarOpen ? <X size={23} aria-hidden="true" /> : <Menu size={23} aria-hidden="true" />}
        </button>
        <div className="ht-brand">
          <GraduationCap size={24} aria-hidden="true" />
          <span>TutorGuy SAT</span>
        </div>
        <button className="ht-profile-button" aria-label="Profile">
          <UserCircle size={24} aria-hidden="true" />
          <span>Profile</span>
        </button>
      </header>

      {isSidebarOpen && (
        <button
          className="ht-sidebar-scrim"
          aria-label="Close sidebar"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      <aside className={`ht-sidebar ${isSidebarOpen ? "is-open" : ""}`} aria-label="SAT navigation">
        <div className="ht-sidebar-header">
          <span>Study tools</span>
          <button aria-label="Close sidebar" onClick={() => setIsSidebarOpen(false)}>
            <X size={20} aria-hidden="true" />
          </button>
        </div>
        <nav className="ht-sidebar-nav">
          {sidebarItems.map(({ label, Icon }) => (
            <button key={label} type="button">
              <Icon size={20} aria-hidden="true" />
              <span>{label}</span>
              <ArrowRight size={16} aria-hidden="true" />
            </button>
          ))}
        </nav>
      </aside>

      <section className="ht-dashboard-intro">
        <div>
          <h1 className="ht-welcome">Welcome back, Harris!</h1>
          <p className="ht-welcome-sub">You are on a 6-day streak 🔥 Keep it up.</p>
        </div>
        <div className="ht-points-badge">
          <span className="ht-points-icon">⭐</span>
          <span className="ht-points-value">{points.toLocaleString()} pts</span>
        </div>
      </section>

      {/* Content grid: center | right */}
      <div className="ht-content-grid">
        {/* Center column */}
        <div className="ht-center-col">
          {/* Score chart */}
          <section className="ht-card">
            <div className="ht-card-header">
              <h2 className="ht-card-title">Score Progress</h2>
              <span className="ht-score-latest">
                {userScore} <span className="ht-score-delta">▲ +270</span>
              </span>
            </div>
            <ScoreChart data={mockScores} />
          </section>

          {/* College rec slider */}
          <section className="ht-card">
            <div className="ht-card-header">
              <h2 className="ht-card-title">College Recommendations</h2>
              <span className="ht-card-sub">Based on your current score of {userScore}</span>
            </div>
            <CollegeSlider colleges={mockColleges} userScore={userScore} />
          </section>
        </div>

        {/* Right column */}
        <div className="ht-right-col">
          {/* Daily Tasks */}
          <section className="ht-card">
            <h2 className="ht-card-title">Daily Tasks</h2>
            <ul className="ht-task-list">
              {tasks.map(t => (
                <li
                  key={t.id}
                  className={`ht-task-item ${t.done ? "done" : ""}`}
                  onClick={() => toggleTask(t.id)}
                >
                  <span className="ht-task-check">{t.done ? "✓" : ""}</span>
                  <span className="ht-task-label">{t.label}</span>
                </li>
              ))}
            </ul>
            <p className="ht-tasks-progress">
              {tasks.filter(t => t.done).length}/{tasks.length} completed
            </p>
          </section>

          {/* Leaderboard */}
          <section className="ht-card">
            <h2 className="ht-card-title">Leaderboard</h2>
            <ul className="ht-leader-list">
              {mockLeaders.map(l => (
                <li key={l.rank} className={`ht-leader-item ${l.isUser ? "you" : ""}`}>
                  <span className="ht-leader-rank">#{l.rank}</span>
                  <span className="ht-leader-name">{l.name}</span>
                  <span className="ht-leader-pts">{l.pts.toLocaleString()}</span>
                </li>
              ))}
            </ul>
          </section>
        </div>
      </div>
    </div>
  );
}

ScoreChart.propTypes = {
  data: PropTypes.arrayOf(
    PropTypes.shape({
      date: PropTypes.string.isRequired,
      score: PropTypes.number.isRequired,
    })
  ).isRequired,
};

CollegeSlider.propTypes = {
  colleges: PropTypes.arrayOf(
    PropTypes.shape({
      name: PropTypes.string.isRequired,
      minScore: PropTypes.number.isRequired,
      logo: PropTypes.string.isRequired,
    })
  ).isRequired,
  userScore: PropTypes.number.isRequired,
};
