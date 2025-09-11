import React from 'react';
import { BrowserRouter as Router, Routes, Route} from "react-router-dom";
import './PageComponents/CSS/App.css'
import QueryPage from './PageComponents/MainPages/QueryPage.jsx'
import TrainModel from './PageComponents/MainPages/TrainModel.jsx'
import HomePage from './PageComponents/MainPages/HomePage.jsx'
import Login from './PageComponents/MainPages/Login.jsx'
import Profile from './PageComponents/MainPages/Profile.jsx'
import MathTestPage from './PageComponents/MainPages/MathTestPage.jsx'
import ExamHistory from './PageComponents/MainPages/ExamHistory.jsx'
import TakeATest from './PageComponents/MainPages/TakeATest.jsx'
import EnglishTestPage from './PageComponents/MainPages/EnglishTestPage.jsx'
import MainPracticePage from './PageComponents/MainPages/MainPracticePage.jsx'
import PracticeQuestions from './PageComponents/MainPages/PracticeQuestions.jsx'
import { AuthProvider } from './ClientStuff/AuthContext.jsx'
// import PlaceholderPage from './PlaceholderPage';


const App = () => {
  return (
    <Router>
      <AuthProvider>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<Login />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/query" element={<QueryPage />} />
        <Route path="/train" element={<TrainModel />} /> {/* this is TrainModel page */}
        <Route path="/take_a_test" element={<TakeATest />} />
        <Route path="/math_test" element={<MathTestPage /> } />
        <Route path="/english_test" element={<EnglishTestPage /> } />
        <Route path="/exam_history" element={<ExamHistory /> } />
        <Route path="/practice" element={<MainPracticePage/> } />
        <Route path="/practice-questions" element={<PracticeQuestions/> } />
      </Routes>
      </AuthProvider>
    </Router>
  )
}

export default App
