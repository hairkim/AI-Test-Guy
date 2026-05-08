import React from 'react'
import PropTypes from 'prop-types'

export default function ExamHistoryRow({ exam }) {
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getScoreColor = (currentScore, examType) => {
    if (!currentScore) return '#6B7280'; // Gray for no score
    
    if (examType === "full_exam") {
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

  const getCompletionStatus = (exam) => {
    if (exam.completed_at) return 'Completed';
    
    // Check if any section has completed modules
    if (exam.sections && exam.sections.length > 0) {
      const completedSections = exam.sections.filter(section => 
        section.module1_completed && section.module2_completed
      ).length;
      
      const totalSections = exam.sections.length;
      
      if (completedSections === totalSections) return 'Completed';
      if (completedSections > 0) return `${completedSections}/${totalSections} Sections`;
      
      // Check for any module 1 completions
      const module1Completed = exam.sections.filter(section => section.module1_completed).length;
      if (module1Completed > 0) return 'In Progress';
    }
    
    return 'Not Started';
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'Completed': return '#10B981';
      case 'In Progress': return '#F59E0B';
      case 'Not Started': return '#6B7280';
      default: 
        if (status.includes('Sections')) return '#3B82F6';
        return '#6B7280';
    }
  };

  const calculateOverallPercentage = (exam) => {
    console.log('calculateOverallPercentage called')
    if (!exam.sections || exam.sections.length === 0) return null;
    console.log("sections: ", exam.sections)
    
    let totalCorrect = 0;
    let totalQuestions = 0;
    
    exam.sections.forEach(section => {
      if (section.total_correct) totalCorrect += section.total_correct;
      if (section.total) totalQuestions += section.total;
    });
    console.log("totalCorrect: ", totalCorrect)
    console.log("totalQuestions: ", totalQuestions)
    
    if (totalQuestions === 0) return null;
    return Math.round((totalCorrect / totalQuestions) * 100);
  };

  const getModuleProgress = (exam) => {
    if (!exam.sections || exam.sections.length === 0) {
      return { display: 'No data', details: [] };
    }
    
    const sectionDetails = exam.sections.map(section => ({
      type: section.section_type,
      m1: `${section.module1_correct || 0}/${section.module1_total || 0}`,
      m2: `${section.module2_correct || 0}/${section.module2_total || 0}`
    }));
    
    return {
      display: `${exam.sections.length} section(s)`,
      details: sectionDetails
    };
  };

  const status = getCompletionStatus(exam);
  const percentage = calculateOverallPercentage(exam);
  const moduleProgress = getModuleProgress(exam);

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '1fr 120px 100px 100px 80px 120px 120px',
      gap: '16px',
      padding: '16px',
      margin: '3rem',
      backgroundColor: 'white',
      borderRadius: '8px',
      boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
      alignItems: 'center',
      minHeight: '60px'
    }}>
      {/* Exam ID (shortened) */}
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        <span style={{ fontSize: '14px', fontWeight: '600', color: '#1F2937' }}>
          {exam.id.substring(0, 8)}...
        </span>
        <span style={{ fontSize: '12px', color: '#6B7280' }}>
          {exam.exam_type.replace('_', ' ').toUpperCase()}
        </span>
      </div>

      {/* Date */}
      <div style={{ fontSize: '12px', color: '#374151' }}>
        {formatDate(exam.created_at)}
      </div>

      {/* Score - Use total_score for full exams, section score for single sections */}
      <div style={{ 
        fontSize: '18px', 
        fontWeight: 'bold', 
        color: getScoreColor(exam.total_score, exam.exam_type),
        textAlign: 'center'
      }}>
        {exam.total_score || 'N/A'}
      </div>

      {/* Percentage */}
      <div style={{ 
        fontSize: '14px', 
        color: '#374151',
        textAlign: 'center'
      }}>
        {percentage ? `${percentage}%` : 'N/A'}
      </div>

      {/* Status */}
      <div style={{
        fontSize: '12px',
        fontWeight: '500',
        color: getStatusColor(status),
        backgroundColor: `${getStatusColor(status)}20`,
        padding: '4px 8px',
        borderRadius: '12px',
        textAlign: 'center'
      }}>
        {status}
      </div>

      {/* Module Progress - Updated for new structure */}
      <div style={{ fontSize: '12px', color: '#6B7280' }}>
        <div style={{ marginBottom: '2px' }}>{moduleProgress.display}</div>
        {moduleProgress.details.map((section, index) => (
          <div key={index} style={{ fontSize: '10px' }}>
            {section.type}: M1:{section.m1} M2:{section.m2}
          </div>
        ))}
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', gap: '8px' }}>
        <button style={{
          fontSize: '12px',
          padding: '6px 12px',
          backgroundColor: '#3B82F6',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer'
        }}>
          View
        </button>
        {!exam.completed_at && (
          <button style={{
            fontSize: '12px',
            padding: '6px 12px',
            backgroundColor: '#10B981',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}>
            Resume
          </button>
        )}
      </div>
    </div>
  );
};

ExamHistoryRow.propTypes = {
  exam: PropTypes.shape({
    id: PropTypes.string.isRequired,
    exam_type: PropTypes.string.isRequired,
    created_at: PropTypes.string,
    completed_at: PropTypes.string,
    total_score: PropTypes.number,
    sections: PropTypes.arrayOf(PropTypes.shape({
      section_type: PropTypes.string,
      module1_completed: PropTypes.bool,
      module2_completed: PropTypes.bool,
      module1_correct: PropTypes.number,
      module1_total: PropTypes.number,
      module2_correct: PropTypes.number,
      module2_total: PropTypes.number,
      total_correct: PropTypes.number,
      total_questions: PropTypes.number
    }))
  }).isRequired
}