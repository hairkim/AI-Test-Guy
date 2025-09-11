import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types'

export default function ScoreCircle({ examType, score }) {
  const [animatedScore, setAnimatedScore] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);

  const size = 200
  const animationDuration = 2000;
  const maxScore = examType === "full_sat" ? 1600: 800;

  // Calculate percentage (0-100)
//   const percentage = Math.min((score / maxScore) * 100, 100);
  const animatedPercentage = Math.min((animatedScore / maxScore) * 100, 100);
  
  // SVG circle properties
  const radius = (size - 20) / 2; // Leave space for stroke
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (animatedPercentage / 100) * circumference;

  // Animate the score on mount
  useEffect(() => {
    setIsAnimating(true);
    const startTime = Date.now();
    
    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / animationDuration, 1);
      
      // Easing function for smooth animation
      const easeOutCubic = 1 - Math.pow(1 - progress, 3);
      
      setAnimatedScore(score * easeOutCubic);
      
      if (progress < 1) {
        requestAnimationFrame(animate);
      } else {
        setIsAnimating(false);
      }
    };
    
    requestAnimationFrame(animate);
  }, [score, animationDuration]);

  // Get color based on score
  const getScoreColor = (currentScore, examType) => {
    if (examType === "full_sat") {
        if (currentScore >= 1400) return '#10B981'; // Green
        if (currentScore >= 1200) return '#F59E0B'; // Yellow
        if (currentScore >= 1000) return '#F97316'; // Orange
        return '#EF4444'; // Red
    } else {
        if (currentScore >= 700) return '#10B981'; // Green
        if (currentScore >= 550) return '#F59E0B'; // Yellow
        if (currentScore >= 400) return '#F97316'; // Orange
        return '#EF4444'; // Red
    }
  };

  const scoreColor = getScoreColor(score, examType);

  return (
    <div className="score-circle-container" style={{ position: 'relative', display: 'inline-block' }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="#E5E7EB"
          strokeWidth="8"
          fill="transparent"
        />
        
        {/* Progress circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={scoreColor}
          strokeWidth="8"
          fill="transparent"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          style={{
            transition: isAnimating ? 'none' : 'stroke-dashoffset 0.3s ease',
          }}
        />
      </svg>
      
      {/* Score text overlay */}
      <div
        style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          textAlign: 'center',
          color: '#1F2937',
        }}
      >
        <div style={{ fontSize: `${size * 0.15}px`, fontWeight: 'bold', lineHeight: '1' }}>
          {Math.round(animatedScore)}
        </div>
        <div style={{ fontSize: `${size * 0.08}px`, color: '#6B7280', marginTop: '4px' }}>
          {examType} Score
        </div>
      </div>
    </div>
  );
};

// // Example usage component
// const ScoreDashboard = () => {
//   const [currentScore, setCurrentScore] = useState(1480);

//   const testScores = [800, 1200, 1480, 1600];

//   return (
//     <div style={{ padding: '20px', backgroundColor: '#F9FAFB', minHeight: '100vh' }}>
//       <div style={{ textAlign: 'center', marginBottom: '40px' }}>
//         <h1 style={{ fontSize: '24px', marginBottom: '20px', color: '#1F2937' }}>
//           Recent SAT Score
//         </h1>
        
//         <ScoreCircle score={currentScore} />
        
//         <div style={{ marginTop: '30px' }}>
//           <p style={{ marginBottom: '15px', color: '#6B7280' }}>
//             Try different scores:
//           </p>
//           <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', flexWrap: 'wrap' }}>
//             {testScores.map((score) => (
//               <button
//                 key={score}
//                 onClick={() => setCurrentScore(score)}
//                 style={{
//                   padding: '8px 16px',
//                   backgroundColor: currentScore === score ? '#3B82F6' : '#E5E7EB',
//                   color: currentScore === score ? 'white' : '#374151',
//                   border: 'none',
//                   borderRadius: '6px',
//                   cursor: 'pointer',
//                   fontSize: '14px',
//                   fontWeight: '500',
//                 }}
//               >
//                 {score}
//               </button>
//             ))}
//           </div>
//         </div>
//       </div>

//       {/* Multiple sizes example */}
//       <div style={{ textAlign: 'center' }}>
//         <h2 style={{ fontSize: '20px', marginBottom: '20px', color: '#1F2937' }}>
//           Different Sizes
//         </h2>
//         <div style={{ display: 'flex', gap: '20px', justifyContent: 'center', alignItems: 'center', flexWrap: 'wrap' }}>
//           <ScoreCircle score={1350} size={120} />
//           <ScoreCircle score={1480} size={160} />
//           <ScoreCircle score={1200} size={200} />
//         </div>
//       </div>
//     </div>
//   );
// };


ScoreCircle.propTypes = {
    examType: PropTypes.string.isRequired,
    score: PropTypes.number.isRequired,
};
    