import React, { useState } from 'react'
import '../CSS/Survival.css'
import { useNavigate } from 'react-router-dom'

//survival page layout:
//choose math or english, then it will transition to easy, medium, or hard
//then take you to questions page (fetch question first)

export default function SurvivalMode() {
    const [section, setSection] = useState(null)
    const [difficulty, setDifficulty] = useState(null)
    const navigate = useNavigate()

    const handleDifficultySelect = (selectedDifficulty) => {
        setDifficulty(selectedDifficulty)
        // Navigate to questions page with section and difficulty
        navigate('/survival/questions', { 
            state: { 
                section: section, 
                difficulty: selectedDifficulty 
            } 
        })
    }

    const handleBack = () => {
        setSection(null)
        setDifficulty(null)
    }

    return(
        <div className='survival_container'>
            {!section && (
                <div className='survival_section_container'>
                    <h1>Choose a Section</h1>
                    <div className='survival_section_button_container'>
                        <button onClick={() => setSection("Math")}>Math</button>
                        <button onClick={() => setSection("English")}>English</button>
                    </div>
                </div>
            )}
            {section && !difficulty && (
                <div className='survival_domain_main_container'>
                    <button onClick={handleBack} className='back-button'>
                        ← Back
                    </button>
                    <div className='survival_domain_container'>
                        <h1>Choose Difficulty</h1>
                        <div className='survival_section_button_container'>
                            <button onClick={() => handleDifficultySelect("Easy")}>Easy</button>
                            <button onClick={() => handleDifficultySelect("Medium")}>Medium</button>
                            <button onClick={() => handleDifficultySelect("Hard")}>Hard</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}