import React, { useState } from 'react';
import { InlineMath } from 'react-katex';
import 'katex/dist/katex.min.css';
import './StepByStepExplanation.css';
import PropTypes from 'prop-types';


const StepByStepExplanation = ({ solution, explanationSteps }) => {
  const [expandedSteps, setExpandedSteps] = useState(new Set());

  const toggleStep = (index) => {
    const newExpanded = new Set(expandedSteps);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedSteps(newExpanded);
  };

  const expandAllSteps = () => {
    setExpandedSteps(new Set(explanationSteps.map((_, index) => index)));
  };

  const collapseAllSteps = () => {
    setExpandedSteps(new Set());
  };

  const renderMathText = (text) => {
    if (!text) return null;
    
    // Split text by LaTeX expressions and render accordingly
    const parts = text.split(/(\$[^$]*\$)/g);
    
    return parts.map((part, index) => {
      if (part.startsWith('$') && part.endsWith('$')) {
        const mathContent = part.slice(1, -1);
        return <InlineMath key={index} math={mathContent} />;
      }
      return <span key={index}>{part}</span>;
    });
  };

  const parseStepContent = (step) => {
    // Handle new object structure with step and method properties
    if (typeof step === 'object' && step.step) {
      // Extract step number and content from the step property
      const match = step.step.match(/^(\d+)\. (.*)$/s);
      if (match) {
        return {
          number: match[1],
          content: match[2],
          method: step.method || ''
        };
      }
      return {
        number: '',
        content: step.step,
        method: step.method || ''
      };
    }
    
    // Fallback for old string format (backward compatibility)
    const match = step.match(/^(\d+)\. (.*)$/s);
    if (match) {
      return {
        number: match[1],
        content: match[2],
        method: ''
      };
    }
    return {
      number: '',
      content: step,
      method: ''
    };
  };


  if (!solution && (!explanationSteps || explanationSteps.length === 0)) {
    return null;
  }

  return (
    <div className="step-explanation-container">
      {/* Solution Section */}
      {solution && (
        <div className="solution-section">
          <div className="solution-header">
            <h3>📝 Final Answer</h3>
          </div>
          <div className="solution-content">
            {renderMathText(solution)}
          </div>
        </div>
      )}

      {/* Explanation Steps Section */}
      {explanationSteps && explanationSteps.length > 0 && (
        <div className="explanation-section">
          <div className="explanation-header">
            <h3>🔍 Step-by-Step Explanation</h3>
            <div className="step-controls">
              <button 
                className="control-btn expand-all" 
                onClick={expandAllSteps}
                disabled={expandedSteps.size === explanationSteps.length}
              >
                Expand All
              </button>
              <button 
                className="control-btn collapse-all" 
                onClick={collapseAllSteps}
                disabled={expandedSteps.size === 0}
              >
                Collapse All
              </button>
            </div>
          </div>

          <div className="steps-container">
            {explanationSteps.map((step, index) => {
              const { number, content } = parseStepContent(step);
              const isExpanded = expandedSteps.has(index);
              
              return (
                <div key={index} className={`step-item ${isExpanded ? 'expanded' : ''}`}>
                  <div 
                    className="step-header" 
                    onClick={() => toggleStep(index)}
                  >
                    <div className="step-number">
                      {number || (index + 1)}
                    </div>
                    <div className="step-preview">
                      <b>{step.method}</b>
                    </div>
                    <div className="step-toggle">
                      {isExpanded ? '▼' : '▶'}
                    </div>
                  </div>
                  
                  {isExpanded && (
                    <div className="step-content">
                      <div className="step-explanation">
                        {renderMathText(content)}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

StepByStepExplanation.propTypes = {
  solution: PropTypes.string,
  explanationSteps: PropTypes.arrayOf(PropTypes.string)
};


export default StepByStepExplanation;
