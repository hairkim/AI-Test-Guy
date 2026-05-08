import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext.jsx';
import GameOver from '../components/survival/GameOver.jsx';
import SurvivalErrorState from '../components/survival/SurvivalErrorState.jsx';
import SurvivalGameView from '../components/survival/SurvivalGameView.jsx';
import { useSurvivalSession } from '../hooks/useSurvivalSession.js';
import '../PageComponents/CSS/SurvivalModeQuestions.css';

export default function SurvivalModeQuestions() {
    const location = useLocation();
    const navigate = useNavigate();
    const { user } = useAuth();
    const { section, difficulty } = location.state || {};
    const survival = useSurvivalSession({
        difficulty,
        section,
        userId: user?.id,
    });

    const handleRetry = () => {
        navigate('/survival', { replace: true });
    };

    if (!section || !difficulty) {
        return (
            <SurvivalErrorState
                message="Choose a section and difficulty before starting survival mode."
                onRetry={handleRetry}
            />
        );
    }

    if (survival.loading && !survival.currentQuestion) {
        return <div className="loading">Loading question...</div>;
    }

    if (survival.error) {
        return (
            <SurvivalErrorState
                message={survival.error}
                onRetry={handleRetry}
            />
        );
    }

    if (survival.gameOver) {
        return (
            <GameOver
                questionsAnswered={survival.questionsAnswered}
                questionsCorrect={survival.questionsCorrect}
                handlePlayAgain={handleRetry}
            />
        );
    }

    return (
        <SurvivalGameView
            difficulty={difficulty}
            gameOver={survival.gameOver}
            lives={survival.lives}
            loading={survival.loading}
            onAnswerSelect={survival.handleAnswerSelect}
            onNextQuestion={survival.handleNextQuestion}
            question={survival.currentQuestion}
            questionsAnswered={survival.questionsAnswered}
            questionsCorrect={survival.questionsCorrect}
            section={section}
            selectedAnswer={survival.selectedAnswer}
            showFeedback={survival.showFeedback}
        />
    );
}
