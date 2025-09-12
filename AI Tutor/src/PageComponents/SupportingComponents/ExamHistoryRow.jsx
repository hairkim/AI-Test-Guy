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

  const getCompletionStatus = (exam) => {
    if (exam.completed_at) return 'Completed';
    if (exam.module2_completed) return 'Module 2 Done';
    if (exam.module1_completed) return 'Module 1 Done';
    return 'In Progress';
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'Completed': return '#10B981';
      case 'Module 2 Done': return '#3B82F6';
      case 'Module 1 Done': return '#F59E0B';
      default: return '#6B7280';
    }
  };

  const calculatePercentage = (exam) => {
    // if (!exam.correct_answers || !exam.total_questions) return null;
    return Math.round((exam.correct_answers / exam.total_questions) * 100);
  };

  const status = getCompletionStatus(exam);
  const percentage = calculatePercentage(exam);

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

      {/* Score */}
      <div style={{ 
        fontSize: '18px', 
        fontWeight: 'bold', 
        color: getScoreColor(exam.score, exam.exam_type),
        textAlign: 'center'
      }}>
        {exam.score || 'N/A'}
      </div>

      {/* Percentage */}
      <div style={{ 
        fontSize: '14px', 
        color: '#374151',
        textAlign: 'center'
      }}>
        {percentage ? `${percentage}%` : 'Percentage'}
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

      {/* Module Progress */}
      <div style={{ fontSize: '12px', color: '#6B7280' }}>
        <div>M1: {exam.module1_correct || 0}/{exam.module1_total || 0}</div>
        <div>M2: {exam.module2_correct || 0}/{exam.module2_total || 0}</div>
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
  exam: PropTypes.object.isRequired
}