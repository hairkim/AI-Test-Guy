import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import 'katex/dist/katex.min.css';
import SubjectToggle from '../components/common/SubjectToggle.jsx';
import TutorChatMessages from '../components/tutor/TutorChatMessages.jsx';
import TutorErrorRecovery from '../components/tutor/TutorErrorRecovery.jsx';
import TutorTextInput from '../components/tutor/TutorTextInput.jsx';
import { useTutorChat } from '../hooks/useTutorChat.js';
import { askEnglishTutor } from '../services/tutorService.js';
import '../PageComponents/CSS/EnglishPage.css';

export default function EnglishPage() {
    const navigate = useNavigate();
    const [passage, setPassage] = useState('');
    const tutorChat = useTutorChat({
        emptyPromptError: 'Please enter a question',
        validatePrompt: ({ prompt }) => !!prompt.trim(),
        buildUserMessage: ({ prompt }) => ({
            question: prompt.trim(),
        }),
        submitRequest: ({ prompt, passage: currentPassage }) => (
            askEnglishTutor({ question: prompt, passage: currentPassage })
        ),
    });

    const submitPrompt = () => {
        tutorChat.submitPrompt({ passage });
    };

    const handleKeyDown = (event) => {
        tutorChat.handleKeyDown(event, { passage });
    };

    const handleBackHome = () => {
        navigate('/');
    };

    return (
        <div className="questions_page_container">
            <div className="qpage_toggle_buttons">
                <SubjectToggle />
            </div>
            <div className="english_qpage_chat_box">
                <div className="english_qpage_passage_container">
                    <div className="english_qpage_passage">
                        <textarea
                            className="english_qpage_passage_textarea"
                            value={passage}
                            onChange={(event) => setPassage(event.target.value)}
                            placeholder="Enter passage here..."
                        />
                    </div>
                </div>
                <div className="english_qpage_messages_main_container" ref={tutorChat.chatContainerRef}>
                    <TutorChatMessages
                        chatHistory={tutorChat.chatHistory}
                        emptyMessage="Type something to start a conversation with Tutor Guy!"
                        emptyStateClassName="english_qpage_no_messages"
                        messageContainerClassName="english_qpage_messages_container"
                        onTypingComplete={tutorChat.handleTypingComplete}
                    />
                </div>
            </div>
            <div className="qpage_form">
                <TutorErrorRecovery error={tutorChat.error} onBackHome={handleBackHome} />
                <TutorTextInput
                    value={tutorChat.prompt}
                    onChange={tutorChat.setPrompt}
                    onKeyDown={handleKeyDown}
                    onSubmit={submitPrompt}
                    isLoading={tutorChat.isLoading}
                />
            </div>
        </div>
    );
}
