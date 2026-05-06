import React, { useState, useEffect } from 'react'
import { ChevronLeft, ChevronRight, Shield, Target, TrendingUp } from 'lucide-react';
import PropTypes from 'prop-types'
import { getCollegeRecommendations } from '../../services/satService';

function SchoolScroller({ previousScore }) {
    const [recommendations, setRecommendations] = useState(null);
    const [activeSection, setActiveSection] = useState('target');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    useEffect(() => {
        const fetchSchools = async () => {
            if (!previousScore) {
                setLoading(false);
                return;
            }
            
            try {
                setLoading(true);
                const data = await getCollegeRecommendations({ score: previousScore });
                console.log(data);
                setRecommendations(data);
            } catch (err) {
                setError(err.message);
                console.error('Error fetching recommendations:', err);
            } finally {
                setLoading(false);
            }
        };
        
        fetchSchools();
    }, [previousScore]);

    const sections = [
        {
            key: 'safety',
            label: 'Safety Schools',
            icon: Shield,
            description: 'High chance of admission',
            color: '#28a745'
        },
        {
            key: 'target',
            label: 'Target Schools', 
            icon: Target,
            description: 'Good fit for your score',
            color: '#007bff'
        },
        {
            key: 'reach',
            label: 'Reach Schools',
            icon: TrendingUp,
            description: 'Ambitious but possible',
            color: '#6f42c1'
        }
    ];

    const currentSection = sections.find(s => s.key === activeSection);
    const currentColleges = recommendations?.recommendations?.[activeSection] || [];

    const navigateSection = (direction) => {
        const currentIndex = sections.findIndex(s => s.key === activeSection);
        let newIndex;
        
        if (direction === 'next') {
            newIndex = (currentIndex + 1) % sections.length;
        } else {
            newIndex = (currentIndex - 1 + sections.length) % sections.length;
        }
        
        setActiveSection(sections[newIndex].key);
    };

    const generateCollegeInitials = (name) => {
        return name
            .split(' ')
            .map(word => word[0])
            .join('')
            .slice(0, 2)
            .toUpperCase();
    };

    const getCollegeColor = (index) => {
        const colors = [
            'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
            'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
            'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
            'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
            'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
            'linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)',
            'linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)'
        ];
        return colors[index % colors.length];
    };

    const styles = {
        container: {
            width: '100%',
            maxWidth: '1200px',
            margin: '0 auto',
            padding: '2rem'
        },
        noScoreMessage: {
            padding: '2rem',
            textAlign: 'center',
            background: 'rgba(255, 255, 255, 0.15)',
            borderRadius: '20px',
            margin: '1rem 0',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(255, 255, 255, 0.2)'
        },
        loadingContainer: {
            padding: '2rem',
            textAlign: 'center',
            background: 'rgba(255, 255, 255, 0.15)',
            borderRadius: '20px',
            margin: '1rem 0'
        },
        spinner: {
            width: '40px',
            height: '40px',
            border: '4px solid #f3f3f3',
            borderTop: '4px solid #f4881c',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto'
        },
        mainContainer: {
            background: 'rgba(255, 255, 255, 0.15)',
            borderRadius: '30px',
            padding: '2rem',
            margin: '2rem 0',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)'
        },
        header: {
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '1.5rem'
        },
        sectionInfo: {
            display: 'flex',
            alignItems: 'center',
            gap: '1rem'
        },
        sectionIcon: {
            width: '48px',
            height: '48px',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: currentSection?.color || '#007bff',
            color: 'white'
        },
        sectionText: {
            color: '#333'
        },
        sectionTitle: {
            margin: '0',
            fontSize: '1.5rem',
            fontWeight: 'bold'
        },
        sectionDescription: {
            margin: '0',
            color: '#666',
            fontSize: '14px'
        },
        navigation: {
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
        },
        navButton: {
            background: 'rgba(255, 255, 255, 0.9)',
            border: 'none',
            borderRadius: '50%',
            width: '48px',
            height: '48px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            transition: 'all 0.3s ease',
            boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)'
        },
        ticker: {
            overflow: 'hidden',
            position: 'relative',
            background: 'rgba(255, 255, 255, 0.1)',
            borderRadius: '20px',
            padding: '1.5rem 0'
        },
        tickerContent: {
            display: 'flex',
            animation: 'scroll 25s linear infinite',
            gap: '1rem'
        },
        collegeItem: {
            display: 'flex',
            alignItems: 'center',
            background: 'white',
            padding: '1rem 1.5rem',
            borderRadius: '25px',
            boxShadow: '0 4px 15px rgba(0, 0, 0, 0.1)',
            minWidth: '320px',
            flexShrink: '0',
            gap: '1rem'
        },
        collegeInitial: {
            width: '44px',
            height: '44px',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontWeight: 'bold',
            fontSize: '16px'
        },
        collegeInfo: {
            flex: '1'
        },
        collegeName: {
            fontWeight: '600',
            color: '#333',
            fontSize: '16px',
            marginBottom: '2px'
        },
        collegeRange: {
            color: '#666',
            fontSize: '14px'
        },
        sectionIndicators: {
            display: 'flex',
            justifyContent: 'center',
            gap: '1rem',
            marginTop: '1.5rem'
        },
        indicatorButton: {
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.75rem 1.5rem',
            borderRadius: '20px',
            border: '1px solid rgba(255, 255, 255, 0.4)',
            background: 'rgba(255, 255, 255, 0.2)',
            color: '#333',
            cursor: 'pointer',
            transition: 'all 0.3s ease',
            fontWeight: '500'
        },
        indicatorButtonActive: {
            background: 'rgba(255, 255, 255, 0.9)',
            borderColor: 'white',
            boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)'
        },
        emptyState: {
            textAlign: 'center',
            padding: '2rem',
            color: '#666'
        }
    };

    if (!previousScore) {
        return (
            <div style={styles.noScoreMessage}>
                <p style={{ color: '#666', fontSize: '1.1rem', margin: 0 }}>
                    Take a practice exam to see college recommendations!
                </p>
            </div>
        );
    }

    if (loading) {
        return (
            <div style={styles.loadingContainer}>
                <div style={styles.spinner}></div>
                <p style={{ marginTop: '1rem', color: '#666' }}>Loading colleges...</p>
            </div>
        );
    }

    if (error || !recommendations) {
        return (
            <div style={styles.noScoreMessage}>
                <p style={{ color: '#e74c3c', margin: 0 }}>
                    {error || 'Unable to load college recommendations'}
                </p>
            </div>
        );
    }

    return (
        <div style={styles.container}>
            <style>
                {`
                    @keyframes spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                    @keyframes scroll {
                        0% { transform: translateX(100%); }
                        100% { transform: translateX(-100%); }
                    }
                    .nav-button:hover {
                        background: white !important;
                        transform: scale(1.1);
                    }
                    .ticker-content:hover {
                        animation-play-state: paused;
                    }
                    .indicator-button:hover {
                        background: rgba(255, 255, 255, 0.3) !important;
                    }
                `}
            </style>
            
            <div style={styles.mainContainer}>
                <div style={styles.header}>
                    <div style={styles.sectionInfo}>
                        <div style={styles.sectionIcon}>
                            {React.createElement(currentSection.icon, { size: 26 })}
                        </div>
                        <div style={styles.sectionText}>
                            <h3 style={styles.sectionTitle}>
                                {currentSection.label}
                            </h3>
                            <p style={styles.sectionDescription}>
                                {currentSection.description} • {currentColleges.length} schools
                            </p>
                        </div>
                    </div>
                    
                    <div style={styles.navigation}>
                        <button 
                            className="nav-button"
                            style={styles.navButton}
                            onClick={() => navigateSection('prev')}
                        >
                            <ChevronLeft size={24} />
                        </button>
                        <button 
                            className="nav-button"
                            style={styles.navButton}
                            onClick={() => navigateSection('next')}
                        >
                            <ChevronRight size={24} />
                        </button>
                    </div>
                </div>

                {currentColleges.length > 0 ? (
                    <div style={styles.ticker}>
                        <div className="ticker-content" style={styles.tickerContent}>
                            {/* Duplicate colleges for seamless scrolling */}
                            {[...currentColleges, ...currentColleges].map((college, index) => (
                                <div 
                                    key={`${college.id}-${index}`} 
                                    style={styles.collegeItem}
                                >
                                    <div 
                                        style={{
                                            ...styles.collegeInitial,
                                            background: getCollegeColor(index)
                                        }}
                                    >
                                        {generateCollegeInitials(college.college_name)}
                                    </div>
                                    <div style={styles.collegeInfo}>
                                        <div style={styles.collegeName}>
                                            {college.college_name}
                                        </div>
                                        <div style={styles.collegeRange}>
                                            SAT: {college.sat_range}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                ) : (
                    <div style={styles.emptyState}>
                        <p>No {activeSection} schools found for your score range.</p>
                    </div>
                )}

                {/* Section indicators */}
                <div style={styles.sectionIndicators}>
                    {sections.map((section) => {
                        const Icon = section.icon;
                        const isActive = section.key === activeSection;
                        return (
                            <button
                                key={section.key}
                                className="indicator-button"
                                onClick={() => setActiveSection(section.key)}
                                style={{
                                    ...styles.indicatorButton,
                                    ...(isActive ? styles.indicatorButtonActive : {})
                                }}
                            >
                                <Icon size={18} />
                                <span>{section.label}</span>
                            </button>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}

SchoolScroller.propTypes = {
    previousScore: PropTypes.number
}

export default SchoolScroller;
