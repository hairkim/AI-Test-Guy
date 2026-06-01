import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import 'katex/dist/katex.min.css';
import SubjectToggle from '../components/common/SubjectToggle.jsx';
import DragAndDrop from '../components/tutor/DragAndDrop.jsx';
import TutorChatMessages from '../components/tutor/TutorChatMessages.jsx';
import TutorErrorRecovery from '../components/tutor/TutorErrorRecovery.jsx';
import { useTutorChat } from '../hooks/useTutorChat.js';
import { askMathTutor } from '../services/tutorService.js';
import '../PageComponents/CSS/QuestionsPage.css';

export default function QuestionsPage() {
    const navigate = useNavigate();
    const [image, setImage] = useState(null);
    const tutorChat = useTutorChat({
        emptyPromptError: 'Please enter a question or upload an image',
        validatePrompt: ({ prompt, image: currentImage }) => !!prompt.trim() || !!currentImage,
        buildUserMessage: ({ prompt, image: currentImage }) => ({
            question: prompt.trim() || '(Image uploaded)',
            hasImage: !!currentImage,
        }),
        submitRequest: ({ prompt, image: currentImage }) => (
            askMathTutor({ question: prompt, image: currentImage })
        ),
    });

    const storeImage = (base64String) => {
        console.log('storeImage called with:', base64String ? `${base64String.length} chars` : 'null');
        setImage(base64String);
    };

    const submitPrompt = async () => {
        console.log('Sending request with:', {
            hasQuestion: !!tutorChat.prompt,
            hasImage: !!image,
            imageLength: image?.length,
        });

        await tutorChat.submitPrompt({ image });
        setImage(null);
    };

    const handleBackHome = () => {
        navigate('/');
    };

    return (
        <div className="questions_page_container">
            <div className="qpage_toggle_buttons">
                <SubjectToggle />
            </div>

            <div className="qpage_chat_box" ref={tutorChat.chatContainerRef}>
                <TutorChatMessages
                    chatHistory={tutorChat.chatHistory}
                    emptyMessage="Type something or upload an image to start a conversation with Tutor Guy!"
                    emptyStateClassName="qpage_no_messages"
                    messageContainerClassName="qpage_messages_container"
                    onTypingComplete={tutorChat.handleTypingComplete}
                />
            </div>

            <div className="qpage_form">
                <TutorErrorRecovery error={tutorChat.error} onBackHome={handleBackHome} />
                <DragAndDrop
                    question={tutorChat.prompt}
                    setQuestion={tutorChat.setPrompt}
                    onSubmit={submitPrompt}
                    isLoading={tutorChat.isLoading}
                    storeImage={storeImage}
                />
            </div>
        </div>
    );
}
