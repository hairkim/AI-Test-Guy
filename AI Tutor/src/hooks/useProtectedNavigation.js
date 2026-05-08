import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext.jsx';

export const useProtectedNavigation = () => {
    const navigate = useNavigate();
    const { session } = useAuth();

    const navigateWithAuth = (targetPath) => {
        if (session) {
            navigate(targetPath);
            return;
        }

        navigate('/login', {
            state: { redirectTo: targetPath },
        });
    };

    return { navigateWithAuth, isLoggedIn: !!session };
};
