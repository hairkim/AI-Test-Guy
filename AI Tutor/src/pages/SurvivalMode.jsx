import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import SurvivalSetup from '../components/survival/SurvivalSetup.jsx';
import '../PageComponents/CSS/Survival.css';

export default function SurvivalMode() {
    const [section, setSection] = useState(null);
    const navigate = useNavigate();

    const handleDifficultySelect = (selectedDifficulty) => {
        navigate('/survival/questions', {
            state: {
                section,
                difficulty: selectedDifficulty,
            },
        });
    };

    const handleBack = () => {
        setSection(null);
    };

    return (
        <div className="survival_container">
            <SurvivalSetup
                section={section}
                onSectionSelect={setSection}
                onDifficultySelect={handleDifficultySelect}
                onBack={handleBack}
            />
        </div>
    );
}
