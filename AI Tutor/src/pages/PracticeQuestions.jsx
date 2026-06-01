import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext.jsx';
import { usePracticeQuestionSession } from '../hooks/usePracticeQuestionSession';
import PracticeNoQuestions from '../components/practice/PracticeNoQuestions.jsx';
import PracticeQuestionPanel from '../components/practice/PracticeQuestionPanel.jsx';
import PracticeTutorChat from '../components/practice/PracticeTutorChat.jsx';
import '../PageComponents/CSS/PracticeQuestions.css';
import '../PageComponents/CSS/QuestionsPage.css';
import 'katex/dist/katex.min.css';

export default function PracticeQuestions() {
    const location = useLocation();
    const navigate = useNavigate();
    const { session, userData, user } = useAuth();
    const questions = location.state?.questions;
    const hasQuestions = Array.isArray(questions) && questions.length > 0;
    const sessionState = usePracticeQuestionSession({
        questions: hasQuestions ? questions : [],
        token: session?.access_token,
    });

    const handleBackToPractice = () => {
        navigate('/practice');
    };

    if (!hasQuestions) {
        return <PracticeNoQuestions onBackToPractice={handleBackToPractice} />;
    }

    return (
        <div className="practice_question_container">
            <PracticeQuestionPanel
                currentIndex={sessionState.currentIndex}
                question={sessionState.currentQuestion}
                questionCount={questions.length}
                selectedAnswer={sessionState.selectedAnswer}
                isLoading={sessionState.isLoading}
                onAnswerSelect={sessionState.handleAnswerSelect}
                onPrevious={sessionState.handlePreviousQuestion}
                onNext={sessionState.handleNextQuestion}
                onHint={sessionState.requestHint}
                onCheckAnswer={sessionState.checkAnswer}
                onExplainConcept={sessionState.explainConcept}
            />

            <PracticeTutorChat
                chatHistory={sessionState.chatHistory}
                error={sessionState.error}
                isLoading={sessionState.isLoading}
                onBackToPractice={handleBackToPractice}
                onKeyDown={sessionState.handleKeyDown}
                onSubmit={sessionState.submitPrompt}
                onTypingComplete={sessionState.handleTypingComplete}
                onUserQuestionChange={sessionState.setUserQuestion}
                points={userData?.points ?? user?.points ?? ''}
                userQuestion={sessionState.userQuestion}
            />
        </div>
    );
}
